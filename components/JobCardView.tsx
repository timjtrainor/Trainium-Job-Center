import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ReviewedJob } from '../types';
import { overrideJobReview, JobReviewOverrideRequest, JobReviewOverrideResponse } from '../services/apiService';
import * as apiService from '../services/apiService';
import { CheckIcon, XCircleIcon, ChevronLeftIcon, ChevronRightIcon, UsersIcon, ThumbUpIcon, ThumbDownIcon, InformationCircleIcon, SparklesIcon, DocumentTextIcon, XMarkIcon, MapPinIcon, CalendarIcon, CurrencyDollarIcon, GlobeAltIcon } from './IconComponents';
import { MarkdownPreview } from './MarkdownPreview';
import { useToast } from '../hooks/useToast';

interface JobCardViewProps {
    jobs: ReviewedJob[];
    onOverrideSuccess: (jobId: string, message: string) => void;
    currentPage: number;
    onPageChange: (page: number) => void;
    isLoading?: boolean;
    activeNarrativeId?: string | null;
}

export const JobCardView: React.FC<JobCardViewProps> = ({
    jobs,
    onOverrideSuccess,
    currentPage,
    onPageChange,
    isLoading = false,
    activeNarrativeId
}) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [showDetails, setShowDetails] = useState(false);
    const [showJDModal, setShowJDModal] = useState(false);
    const [pendingAction, setPendingAction] = useState<null | 'reject' | 'fast-track' | 'full-ai'>(null);
    const navigate = useNavigate();
    const { addToast } = useToast();

    // Reset index when jobs change
    useEffect(() => {
        setCurrentIndex(0);
    }, [jobs]);

    // Keyboard navigation
    useEffect(() => {
        const handleKeyPress = (event: KeyboardEvent) => {
            // Close modal with Escape
            if (event.key === 'Escape') {
                if (showJDModal) {
                    setShowJDModal(false);
                    event.preventDefault();
                    return;
                }
            }

            // Don't handle other shortcuts if modal is open
            if (showJDModal) return;

            if (event.key === 'ArrowLeft' || event.key === 'r' || event.key === 'R') {
                event.preventDefault();
                handleReject();
            } else if (event.key === 'ArrowRight' || event.key === 'a' || event.key === 'A') {
                event.preventDefault();
                handleFullAI();
            } else if (event.key === 'ArrowUp' || event.key === 'f' || event.key === 'F') {
                event.preventDefault();
                handleFastTrack();
            } else if (event.key === 'i' || event.key === 'I') {
                event.preventDefault();
                setShowDetails(!showDetails);
            } else if (event.key === 'j' || event.key === 'J') {
                event.preventDefault();
                setShowJDModal(!showJDModal);
            }
        };

        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, [currentIndex, jobs, showDetails, showJDModal]);

    const safeIndex = jobs.length > 0
        ? Math.min(currentIndex, Math.max(0, jobs.length - 1))
        : 0;

    const isActionPending = pendingAction !== null;
    const currentJob = jobs[safeIndex] ?? null;

    const humanizeSource = useCallback((value?: string | null) => {
        if (!value) {
            return null;
        }
        const trimmed = value.trim();
        if (!trimmed) {
            return null;
        }
        const looksPlain = /^[a-z0-9_-]+$/.test(trimmed);
        if (!looksPlain) {
            return trimmed;
        }

        return trimmed
            .split(/[_-]/)
            .filter(Boolean)
            .map(part => part.charAt(0).toUpperCase() + part.slice(1))
            .join(' ');
    }, []);

    const extractDomain = useCallback((value?: string | null) => {
        if (!value) {
            return null;
        }
        try {
            const hostname = new URL(value).hostname.replace(/^www\./i, '');
            return hostname || null;
        } catch {
            return null;
        }
    }, []);

    const jobSourceInfo = useMemo(() => {
        const label = humanizeSource(currentJob?.source ?? null) || extractDomain(currentJob?.url ?? null) || null;
        return { label };
    }, [currentJob, humanizeSource, extractDomain]);

    useEffect(() => {
        if (jobs.length === 0) {
            if (currentIndex !== 0) {
                setCurrentIndex(0);
            }
            return;
        }

        if (currentIndex !== safeIndex) {
            setCurrentIndex(safeIndex);
        }
    }, [jobs.length, currentIndex, safeIndex]);

    const nextCard = useCallback(() => {
        if (jobs.length === 0) {
            return;
        }

        if (safeIndex < jobs.length - 1) {
            setCurrentIndex(safeIndex + 1);
        } else {
            onPageChange(currentPage + 1);
        }
    }, [jobs.length, safeIndex, currentPage, onPageChange]);

    const prevCard = useCallback(() => {
        if (safeIndex > 0) {
            setCurrentIndex(safeIndex - 1);
        } else if (currentPage > 1) {
            onPageChange(currentPage - 1);
        }
    }, [safeIndex, currentPage, onPageChange]);

    const handleReject = useCallback(async () => {
        const job = jobs.length > 0 ? jobs[safeIndex] : undefined;
        if (!job) {
            return;
        }

        if (pendingAction) {
            return;
        }

        setPendingAction('reject');
        try {
            await overrideJobReview(job.job_id, {
                override_recommend: false,
                override_comment: 'Human reviewer rejected via swipe',
            });

            onOverrideSuccess(job.job_id, 'Job marked as not recommended');
            nextCard();
        } catch (err) {
            addToast('Failed to update recommendation', 'error');
        } finally {
            setPendingAction(null);
        }
    }, [jobs, safeIndex, nextCard, onOverrideSuccess, pendingAction, addToast]);

    const handleFastTrack = useCallback(async () => {
        const job = jobs.length > 0 ? jobs[safeIndex] : undefined;
        if (!job) {
            return;
        }

        if (pendingAction) {
            return;
        }

        setPendingAction('fast-track');
        try {
            // Create application without AI generation
            await apiService.createApplicationFromJob(job.job_id, 'fast_track', activeNarrativeId || undefined);

            await overrideJobReview(job.job_id, {
                override_recommend: true,
                override_comment: 'Human reviewer fast-tracked application',
            });

            onOverrideSuccess(job.job_id, 'Fast-track application started');

            // Stay in job review mode - no navigation
            nextCard();
        } catch (err) {
            addToast('Failed to fast-track job', 'error');
        } finally {
            setPendingAction(null);
        }
    }, [activeNarrativeId, jobs, safeIndex, nextCard, onOverrideSuccess, pendingAction, addToast]);

    const handleFullAI = useCallback(async () => {
        const job = jobs.length > 0 ? jobs[safeIndex] : undefined;
        if (!job) {
            return;
        }

        if (pendingAction) {
            return;
        }

        setPendingAction('full-ai');
        try {
            // Trigger application creation (no automatic AI)
            await apiService.generateApplicationFromJob(job.job_id, activeNarrativeId || undefined);

            await overrideJobReview(job.job_id, {
                override_recommend: true,
                override_comment: 'Human reviewer approved via full AI workflow',
            });

            onOverrideSuccess(job.job_id, 'AI application created');

            // Stay in job review mode - no navigation
            nextCard();
        } catch (err) {
            addToast('Failed to create AI application', 'error');
        } finally {
            setPendingAction(null);
        }
    }, [activeNarrativeId, jobs, safeIndex, nextCard, onOverrideSuccess, pendingAction, addToast]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-slate-600 dark:text-slate-400">Loading jobs...</span>
            </div>
        );
    }

    if (!currentJob) {
        return (
            <div className="text-center py-12">
                <UsersIcon className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900 dark:text-slate-300 mb-1">No jobs to review</h3>
                <p className="text-slate-600 dark:text-slate-400">All jobs have been reviewed, or filters are too strict.</p>
            </div>
        );
    }
    const hasOverride = currentJob.override_recommend !== null && currentJob.override_recommend !== undefined;

    const getConfidenceColor = (confidence?: string) => {
        switch (confidence?.toLowerCase()) {
            case 'high': return 'from-green-400 to-green-500';
            case 'medium': return 'from-yellow-400 to-yellow-500';
            case 'low': return 'from-red-400 to-red-500';
            default: return 'from-gray-400 to-gray-500';
        }
    };

    const getConfidenceTextColor = (confidence?: string) => {
        switch (confidence?.toLowerCase()) {
            case 'high': return 'text-green-700 dark:text-green-300';
            case 'medium': return 'text-yellow-700 dark:text-yellow-300';
            case 'low': return 'text-red-700 dark:text-red-300';
            default: return 'text-gray-700 dark:text-gray-300';
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 8.25) return 'text-green-600';      // Green: High matches (Exceptional, Strong)
        if (score >= 7.6) return 'text-yellow-600';      // Amber: Medium matches (Good, Borderline)
        return 'text-red-600';                           // Red: Low matches (Concerns, Poor)
    };


    return (
        <div className="max-w-2xl mx-auto p-4">
            {/* Navigation */}
            <div className="flex items-center justify-between mb-4">
                <button
                    onClick={prevCard}
                    disabled={safeIndex === 0 && currentPage === 1}
                    className="p-2 rounded-full bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    <ChevronLeftIcon className="h-5 w-5" />
                </button>

                <div className="text-sm text-slate-600 dark:text-slate-400">
                    Card {safeIndex + 1 + ((currentPage - 1) * 15)} of {jobs.length + ((currentPage - 1) * 15)}
                </div>

                <button
                    onClick={nextCard}
                    className="p-2 rounded-full bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                >
                    <ChevronRightIcon className="h-5 w-5" />
                </button>
            </div>

            {/* Job Card */}
                <div className={`relative w-full max-w-2xl mx-auto rounded-xl shadow-lg overflow-hidden bg-gradient-to-br ${getConfidenceColor(currentJob.confidence_level)}`}>
                    <div className="bg-white dark:bg-slate-800 p-6 min-h-[500px] relative">
                        {/* Score Header */}
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-4">
                                {/* Animated Score Ring */}
                                <div className="relative">
                                    <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                                        <path
                                            d="M18 2.0845
                                              a 15.9155 15.9155 0 0 1 0 31.831
                                              a 15.9155 15.9155 0 0 1 0 -31.831"
                                            fill="none"
                                            stroke="#e5e7eb"
                                            strokeWidth="3"
                                        />
                                        <path
                                            className="transition-all duration-1000 ease-out"
                                            d="M18 2.0845
                                              a 15.9155 15.9155 0 0 1 0 31.831
                                              a 15.9155 15.9155 0 0 1 0 -31.831"
                                            fill="none"
                                            stroke={currentJob.overall_alignment_score >= 8.25 ? "#10b981" : currentJob.overall_alignment_score >= 7.6 ? "#f59e0b" : "#ef4444"}
                                            strokeWidth="3"
                                            strokeLinecap="round"
                                            strokeDasharray={`${(currentJob.overall_alignment_score / 10) * 100}, 100`}
                                            style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))' }}
                                        />
                                    </svg>
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <span className="text-xl font-bold text-slate-900 dark:text-white">
                                            {currentJob.overall_alignment_score.toFixed(0)}
                                        </span>
                                    </div>
                                </div>

                                <div>
                                    <div className="text-2xl font-bold text-slate-900 dark:text-white">
                                        {currentJob.overall_alignment_score.toFixed(1)}/10
                                    </div>
                                    <div className={`text-sm font-medium ${getScoreColor(currentJob.overall_alignment_score)} dark:text-green-400`}>
                                        <span className={currentJob.overall_alignment_score >= 8.5 ? 'text-green-600' :
                                                       currentJob.overall_alignment_score >= 8.25 ? 'text-green-600' :
                                                       currentJob.overall_alignment_score >= 7.9 ? 'text-yellow-600' :
                                                       currentJob.overall_alignment_score >= 7.6 ? 'text-yellow-600' :
                                                       currentJob.overall_alignment_score >= 7.0 ? 'text-red-600' : 'text-red-600'}>
                                            {currentJob.overall_alignment_score >= 8.5 ? 'Exceptional Match' :
                                             currentJob.overall_alignment_score >= 8.25 ? 'Strong Recommendation' :
                                             currentJob.overall_alignment_score >= 7.9 ? 'Good Opportunity' :
                                             currentJob.overall_alignment_score >= 7.6 ? 'Borderline - Consider Carefully' :
                                             currentJob.overall_alignment_score >= 7.0 ? 'Potential Concerns - Research More' : 'Poor Match'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Company Avatar */}
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-lg font-bold text-slate-700 dark:text-slate-300">
                                    {(currentJob.company_name || 'U')[0].toUpperCase()}
                                </div>
                            </div>
                        </div>

                        {/* Job Title and Company */}
                        <div className="mb-4">
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white leading-tight">
                                {currentJob.title || 'Untitled Position'}
                            </h2>
                            <p className="text-lg text-slate-700 dark:text-slate-300 font-medium mt-1">
                                {currentJob.company_name || 'Unknown Company'}
                            </p>
                        </div>

                    {/* Match Percentage Visual */}
                    <div className="mb-4">
                        <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Match Strength</span>
                            <span className="text-xs font-semibold text-slate-900 dark:text-white">{(currentJob.overall_alignment_score * 10).toFixed(0)}%</span>
                        </div>
                        <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                            <div
                                className={`h-full transition-all duration-500 ${
                                    currentJob.overall_alignment_score >= 8 ? 'bg-gradient-to-r from-green-500 to-emerald-600' :
                                    currentJob.overall_alignment_score >= 6 ? 'bg-gradient-to-r from-blue-500 to-cyan-600' :
                                    'bg-gradient-to-r from-yellow-500 to-orange-600'
                                }`}
                                style={{ width: `${(currentJob.overall_alignment_score / 10) * 100}%` }}
                            />
                        </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="grid grid-cols-2 gap-3 mb-4 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg text-sm">
                        <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                            <MapPinIcon className="h-4 w-4 text-slate-500" />
                            <span className="truncate">{currentJob.location || 'Remote'}</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                            <CurrencyDollarIcon className="h-4 w-4 text-slate-500" />
                            <span>{currentJob.salary_range || (currentJob.salary_min ? `$${currentJob.salary_min}` : currentJob.salary_max ? `$${currentJob.salary_max}` : 'Not listed')}</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                            <CalendarIcon className="h-4 w-4 text-slate-500" />
                            <span>{currentJob.date_posted ? new Date(currentJob.date_posted).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—'}</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                            <GlobeAltIcon className="h-4 w-4 text-slate-500" />
                            <span className="truncate">{jobSourceInfo.label || 'Unknown source'}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getConfidenceTextColor(currentJob.confidence_level)} bg-opacity-20 ${
                                currentJob.confidence_level === 'high' ? 'bg-green-500' :
                                currentJob.confidence_level === 'medium' ? 'bg-yellow-500' :
                                'bg-red-500'
                            }`}>
                                {currentJob.confidence_level?.toUpperCase() || 'UNKNOWN'}
                            </span>
                        </div>
                    </div>

                    {/* TL;DR Section - Always Visible */}
                    {(currentJob.tldr_summary || currentJob.rationale) && (
                        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border-l-4 border-blue-500">
                            <div className="flex items-start gap-2">
                                <DocumentTextIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                    <p className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">Job TL;DR</p>
                                    <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                                        {currentJob.tldr_summary || currentJob.rationale}
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Agent Breakdown Section */}
                    <div className="mb-6 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                        <h4 className="text-sm font-semibold text-purple-900 dark:text-purple-100 mb-3 flex items-center gap-2">
                            <InformationCircleIcon className="h-4 w-4" />
                            Career Fit Analysis
                        </h4>
                        <div className="grid grid-cols-1 gap-3">
                            {(() => {
                                const dimensionConfig: Array<{ key: string; name: string; defaultSummary: string }> = [
                                    { key: 'north_star', name: 'North Star Alignment', defaultSummary: 'Evaluating long-term career vision alignment...' },
                                    { key: 'trajectory_mastery', name: 'Trajectory Mastery', defaultSummary: 'Evaluating skill development and growth trajectory...' },
                                    { key: 'values_compass', name: 'Values Alignment', defaultSummary: 'Evaluating culture and values alignment...' },
                                    { key: 'lifestyle_alignment', name: 'Lifestyle Fit', defaultSummary: 'Evaluating work-life balance and lifestyle compatibility...' },
                                    { key: 'compensation_philosophy', name: 'Compensation Match', defaultSummary: 'Evaluating compensation package alignment...' },
                                ];

                                const crewOutput = (currentJob.crew_output ?? {}) as Record<string, { score?: number; summary?: string }>;

                                const realDimensions = dimensionConfig.reduce<Array<{ name: string; score: number; summary: string }>>((acc, config) => {
                                    const dimensionData = crewOutput[config.key];
                                    if (dimensionData && typeof dimensionData.score === 'number') {
                                        acc.push({
                                            name: config.name,
                                            score: dimensionData.score,
                                            summary: dimensionData.summary || config.defaultSummary,
                                        });
                                    }
                                    return acc;
                                }, []);

                                const dimensions = realDimensions.length > 0
                                    ? realDimensions
                                    : [
                                        { name: 'North Star Alignment', score: currentJob.confidence_level === 'high' ? 4.2 : currentJob.confidence_level === 'medium' ? 3.8 : 3.2, summary: 'Placeholder: Long-term vision and purpose alignment' },
                                        { name: 'Trajectory Mastery', score: currentJob.overall_alignment_score >= 8 ? 4.5 : currentJob.overall_alignment_score >= 6 ? 4.0 : 3.5, summary: 'Placeholder: Skill development and career progression' },
                                        { name: 'Values Alignment', score: currentJob.overall_alignment_score >= 7 ? 4.3 : currentJob.overall_alignment_score >= 5 ? 3.9 : 3.4, summary: 'Placeholder: Company values and leadership style' },
                                        { name: 'Lifestyle Fit', score: 4.7, summary: 'Placeholder: Work-life balance and lifestyle preferences' },
                                        ...((currentJob.salary_range || currentJob.salary_min || currentJob.salary_max) ? [{ name: 'Compensation Match', score: 4.3, summary: 'Placeholder: Salary and benefits alignment' }] : []),
                                    ];

                                return dimensions.map((dimension, index) => {
                                    const getProgressWidth = (score: number) => `${(score / 5) * 100}%`;
                                    const getProgressColor = (score: number) => {
                                        if (score >= 4) return 'bg-green-500';
                                        if (score >= 3) return 'bg-yellow-500';
                                        return 'bg-red-500';
                                    };

                                    return (
                                        <div key={dimension.name} className={`flex items-center justify-between text-xs ${index === dimensions.length - 1 ? 'border-t border-purple-200 dark:border-purple-700 pt-2 mt-1' : ''}`}>
                                            <div className="flex items-center gap-2 flex-1">
                                                <span className="font-medium text-slate-700 dark:text-slate-300">{dimension.name}</span>
                                                <button
                                                    className="text-purple-500 hover:text-purple-600 dark:text-purple-400 dark:hover:text-purple-300 p-0.5 rounded"
                                                    title={`Click to view details: ${dimension.summary}`}
                                                    onClick={() => {
                                                        // For now, just alert - could be improved to show a proper modal
                                                        window.alert(`${dimension.name}\n\n${dimension.summary}`);
                                                    }}
                                                >
                                                    <InformationCircleIcon className="h-3 w-3" />
                                                </button>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="w-16 h-2 bg-slate-200 dark:bg-slate-700 rounded-full">
                                                    <div
                                                        className={`h-full rounded-full transition-all ${getProgressColor(dimension.score)}`}
                                                        style={{ width: getProgressWidth(dimension.score) }}
                                                    />
                                                </div>
                                                <span className="text-slate-600 dark:text-slate-400 font-mono">
                                                    {dimension.score}/5
                                                </span>
                                            </div>
                                        </div>
                                    );
                                });
                            })()}
                        </div>
                        <button
                            onClick={() => setShowDetails(!showDetails)}
                            className="mt-3 w-full text-xs text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium"
                        >
                            {showDetails ? 'Hide Full Reasoning' : 'Show Full AI Analysis'}
                        </button>
                    </div>

                    {/* Expanded Full AI Analysis */}
                    {showDetails && currentJob.rationale && (
                        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                            <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2 flex items-center gap-2">
                                <SparklesIcon className="h-4 w-4" />
                                Complete AI Recommendation
                            </h4>
                            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
                                {currentJob.rationale}
                            </p>
                        </div>
                    )}

                    {/* Quick Actions Row */}
                    <div className="flex gap-2 mb-6">
                        <button
                            onClick={() => setShowJDModal(true)}
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-white dark:bg-slate-700 border-2 border-slate-300 dark:border-slate-600 rounded-lg hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-slate-600 transition-colors text-sm font-medium text-slate-700 dark:text-slate-300"
                        >
                            <DocumentTextIcon className="h-4 w-4" />
                            <span>View Full JD</span>
                            <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 rounded border border-slate-300 dark:border-slate-600">J</kbd>
                        </button>
                    </div>

                    {/* HITL Override Badge */}
                    {hasOverride && (
                        <div className="mb-4 flex items-center gap-2">
                            <span className="inline-flex items-center rounded-md bg-blue-100 dark:bg-blue-900/50 px-2 py-1 text-xs font-medium text-blue-800 dark:text-blue-300">
                                Human Override Applied
                            </span>
                            {currentJob.override_recommend ? (
                                <ThumbUpIcon className="h-4 w-4 text-green-500" />
                            ) : (
                                <ThumbDownIcon className="h-4 w-4 text-red-500" />
                            )}
                        </div>
                    )}


                    {/* Action Buttons - Three Options */}
                    <div className="grid grid-cols-3 gap-2 mt-auto">
                        <button
                            onClick={handleReject}
                            className="flex flex-col items-center justify-center gap-1 bg-red-500 hover:bg-red-600 text-white px-3 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 active:scale-95"
                        >
                            <ThumbDownIcon className="h-5 w-5" />
                            <span className="text-xs">Reject</span>
                            <span className="text-[10px] opacity-75">← or R</span>
                        </button>

                        <button
                            onClick={handleFastTrack}
                            className="flex flex-col items-center justify-center gap-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 active:scale-95"
                        >
                            <ThumbUpIcon className="h-5 w-5" />
                            <span className="text-xs">Approve – Fast Track</span>
                            <span className="text-[10px] opacity-75">↑ or F</span>
                        </button>

                        <button
                            onClick={handleFullAI}
                            className="flex flex-col items-center justify-center gap-1 bg-green-500 hover:bg-green-600 text-white px-3 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 active:scale-95"
                        >
                            <SparklesIcon className="h-5 w-5" />
                            <span className="text-xs">Approve – Full AI</span>
                            <span className="text-[10px] opacity-75">→ or A</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Keyboard Shortcuts Help */}
            <div className="mt-6 text-center text-xs text-slate-500 dark:text-slate-400">
                <div className="inline-flex items-center gap-3 px-3 py-1 bg-slate-100 dark:bg-slate-700 rounded-full">
                    <span>← / R: Reject</span>
                    <span>↑ / F: Fast-track</span>
                    <span>→ / A: Full AI</span>
                    <span>J: View JD</span>
                    <span>I: Details</span>
                </div>
            </div>

            {/* Job Description Modal */}
            {showJDModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-end">
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                        onClick={() => setShowJDModal(false)}
                    />

                    {/* Drawer */}
                    <div className="relative h-full w-full sm:w-4/5 bg-white dark:bg-slate-800 shadow-2xl overflow-y-auto transition-transform duration-300 ease-out">
                        {/* Header */}
                        <div className="sticky top-0 z-10 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-4">
                            <div className="flex items-start justify-between">
                                <div className="flex-1 pr-4">
                                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                                        {currentJob.title}
                                    </h2>
                                    <p className="text-lg text-slate-600 dark:text-slate-400 mt-1">
                                        {currentJob.company_name}
                                    </p>
                                </div>
                                <button
                                    onClick={() => setShowJDModal(false)}
                                    className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full transition-colors flex-shrink-0"
                                    aria-label="Close"
                                >
                                    <XMarkIcon className="h-6 w-6" />
                                </button>
                            </div>

                            {/* Quick Stats Bar */}
                            <div className="flex flex-wrap gap-4 mt-3 text-sm text-slate-600 dark:text-slate-400">
                                <span className="flex items-center gap-1">
                                    <MapPinIcon className="h-4 w-4" />
                                    {currentJob.location || 'Remote'}
                                </span>
                                {(currentJob.salary_range || currentJob.salary_min || currentJob.salary_max) && (
                                    <span className="flex items-center gap-1">
                                        <CurrencyDollarIcon className="h-4 w-4" />
                                        {currentJob.salary_range || (currentJob.salary_min ? `$${currentJob.salary_min}` : `$${currentJob.salary_max}`)}
                                    </span>
                                )}
                            <span className="flex items-center gap-1">
                                <CalendarIcon className="h-4 w-4" />
                                Posted {currentJob.date_posted ? new Date(currentJob.date_posted).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Recently'}
                            </span>
                            {jobSourceInfo.label && (
                                <span className="flex items-center gap-1">
                                    <GlobeAltIcon className="h-4 w-4" />
                                    {jobSourceInfo.label}
                                </span>
                            )}
                            {currentJob.url && (
                                <a
                                    href={currentJob.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline"
                                >
                                    View on {jobSourceInfo.label || 'job site'} →
                                </a>
                            )}
                        </div>
                        </div>

                        {/* Body: Full JD */}
                        <div className="px-6 py-6">
                            {currentJob.description ? (
                                <div className="prose dark:prose-invert max-w-none">
                                    <MarkdownPreview markdown={currentJob.description || ''} />
                                </div>
                            ) : (
                                <div className="text-center py-12">
                                    <DocumentTextIcon className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                                    <p className="text-slate-600 dark:text-slate-400">
                                        Job description not available. <a href={currentJob.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">View on {jobSourceInfo.label || 'job site'}</a>
                                    </p>
                                </div>
                            )}
                        </div>

                        {/* Footer: Sticky Actions */}
                        <div className="sticky bottom-0 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 px-6 py-4 shadow-lg">
                            <div className="flex gap-3">
                                <button
                                    onClick={() => { setShowJDModal(false); handleReject(); }}
                                    className="flex-1 flex flex-col items-center justify-center gap-1 bg-red-500 hover:bg-red-600 text-white px-3 py-3 rounded-lg font-semibold transition-all"
                                >
                                    <ThumbDownIcon className="h-5 w-5" />
                                    <span className="text-xs">Reject</span>
                                </button>
                                <button
                                    onClick={() => { setShowJDModal(false); handleFastTrack(); }}
                                    className="flex-1 flex flex-col items-center justify-center gap-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-3 rounded-lg font-semibold transition-all"
                                >
                                    <ThumbUpIcon className="h-5 w-5" />
                                    <span className="text-xs">Fast Track</span>
                                </button>
                                <button
                                    onClick={() => { setShowJDModal(false); handleFullAI(); }}
                                    className="flex-1 flex flex-col items-center justify-center gap-1 bg-green-500 hover:bg-green-600 text-white px-3 py-3 rounded-lg font-semibold transition-all"
                                >
                                    <SparklesIcon className="h-5 w-5" />
                                    <span className="text-xs">Full AI</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default JobCardView;
