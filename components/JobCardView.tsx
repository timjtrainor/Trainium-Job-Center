import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ReviewedJob } from '../types';
import { overrideJobReview, JobReviewOverrideRequest, JobReviewOverrideResponse } from '../services/apiService';
import * as apiService from '../services/apiService';
import { CheckIcon, XCircleIcon, ChevronLeftIcon, ChevronRightIcon, UsersIcon, ThumbUpIcon, ThumbDownIcon, InformationCircleIcon, SparklesIcon, DocumentTextIcon, XMarkIcon, MapPinIcon, CalendarIcon, CurrencyDollarIcon, GlobeAltIcon, ChevronDownIcon, ChevronUpIcon } from './IconComponents';
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
    const [isSnapshotExpanded, setIsSnapshotExpanded] = useState(false);
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

        // Optimistic UI: move to next card immediately
        onOverrideSuccess(job.job_id, 'Job marked as not recommended');
        nextCard();

        // Perform backend update in background
        try {
            await overrideJobReview(job.job_id, {
                override_recommend: false,
                override_comment: 'Human reviewer rejected via swipe',
            });
        } catch (err) {
            addToast('Failed to sync rejection to server', 'error');
            console.error('Optimistic rejection failed:', err);
        }
    }, [jobs, safeIndex, nextCard, onOverrideSuccess, addToast]);

    const handleFastTrack = useCallback(async () => {
        const job = jobs.length > 0 ? jobs[safeIndex] : undefined;
        if (!job) {
            return;
        }

        // Optimistic UI: move to next card immediately
        onOverrideSuccess(job.job_id, 'Fast-track application started');
        nextCard();

        // Perform backend updates in background
        try {
            // Create application without AI generation
            await apiService.createApplicationFromJob(job.job_id, 'fast_track', activeNarrativeId || undefined);

            await overrideJobReview(job.job_id, {
                override_recommend: true,
                override_comment: 'Human reviewer fast-tracked application',
                skip_webhook: true,
            });
        } catch (err) {
            addToast('Failed to sync fast-track to server', 'error');
            console.error('Optimistic fast-track failed:', err);
        }
    }, [activeNarrativeId, jobs, safeIndex, nextCard, onOverrideSuccess, addToast]);

    const handleFullAI = useCallback(async () => {
        const job = jobs.length > 0 ? jobs[safeIndex] : undefined;
        if (!job) {
            return;
        }

        // Optimistic UI: move to next card immediately
        onOverrideSuccess(job.job_id, 'AI application created');
        nextCard();

        // Perform backend updates in background
        try {
            // Trigger application creation (no automatic AI)
            await apiService.generateApplicationFromJob(job.job_id, activeNarrativeId || undefined);

            await overrideJobReview(job.job_id, {
                override_recommend: true,
                override_comment: 'Human reviewer approved via full AI workflow',
                skip_webhook: true,
            });
        } catch (err) {
            addToast('Failed to sync AI application to server', 'error');
            console.error('Optimistic AI application creation failed:', err);
        }
    }, [activeNarrativeId, jobs, safeIndex, nextCard, onOverrideSuccess, addToast]);

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
            <div className="text-center py-20 bg-white dark:bg-slate-800 rounded-xl border border-dashed border-slate-300 dark:border-slate-700">
                <UsersIcon className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900 dark:text-slate-300 mb-1">There are no Job Postings to Review at this time.</h3>
                <p className="text-slate-600 dark:text-slate-400">Please check back later or adjust your filters.</p>
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

            <div className={`relative w-full max-w-2xl mx-auto rounded-xl shadow-lg overflow-hidden bg-white dark:bg-slate-800`}>
                {/* Header Gradient Stripe - Confidence Color */}
                <div className={`h-2 w-full bg-gradient-to-r ${getConfidenceColor(currentJob.confidence_level)}`} />

                <div className="p-6 pb-2 min-h-[500px] relative">
                    {/* Improved Header: Score Circle + Job Details */}
                    <div className="flex items-start gap-5 mb-6">
                        {/* Animated Score Ring */}
                        <div className="relative flex-shrink-0">
                            <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 36 36">
                                <path
                                    d="M18 2.0845
                                          a 15.9155 15.9155 0 0 1 0 31.831
                                          a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none"
                                    stroke="#f1f5f9"
                                    strokeWidth="3"
                                    className="dark:stroke-slate-700"
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
                            <div className="absolute inset-0 flex items-center justify-center flex-col">
                                <span className="text-2xl font-bold text-slate-900 dark:text-white leading-none">
                                    {currentJob.overall_alignment_score.toFixed(1)}
                                </span>
                            </div>
                        </div>

                        {/* Title & Company */}
                        <div className="flex-1 pt-1">
                            <h2 className="text-2xl font-bold text-slate-900 dark:text-white leading-tight mb-1">
                                {currentJob.title || 'Untitled Position'}
                            </h2>
                            <div className="flex items-center gap-2 text-lg text-slate-700 dark:text-slate-300 font-medium">
                                {currentJob.company_name || 'Unknown Company'}
                            </div>
                        </div>
                    </div>

                    {/* Metadata Grid - Clean & Scannable */}
                    <div className="grid grid-cols-2 gap-4 mb-6">
                        {/* Remote Status */}
                        <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/30 rounded-lg">
                            <div className={`p-2 rounded-full ${(currentJob.is_remote ?? currentJob.location?.toLowerCase().includes('remote') ?? (currentJob.crew_output as any)?.job_intake?.is_remote)
                                ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                                : 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-400'
                                }`}>
                                <GlobeAltIcon className="h-5 w-5" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-xs text-slate-500 uppercase font-semibold">Workspace</span>
                                <span className="text-sm font-medium text-slate-900 dark:text-white">
                                    {(currentJob.is_remote ?? (currentJob.crew_output as any)?.job_intake?.is_remote) ? 'Remote' : currentJob.location || 'On-site'}
                                </span>
                            </div>
                        </div>

                        {/* Salary */}
                        <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/30 rounded-lg">
                            <div className="p-2 rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
                                <CurrencyDollarIcon className="h-5 w-5" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-xs text-slate-500 uppercase font-semibold">Compensation</span>
                                <span className="text-sm font-medium text-slate-900 dark:text-white">
                                    {(() => {
                                        const jobIntake = (currentJob.crew_output as any)?.job_intake;
                                        const min = jobIntake?.salary?.min_amount || currentJob.salary_min;
                                        const max = jobIntake?.salary?.max_amount || currentJob.salary_max;

                                        if (!min && !max) return currentJob.salary_range || 'Not listed';

                                        const formatK = (n: number) => (n / 1000).toFixed(0) + 'k';
                                        if (min && max && min === max) return `$${formatK(Number(min))}`;
                                        if (min && max) return `$${formatK(Number(min))} - $${formatK(Number(max))}`;
                                        if (min) return `$${formatK(Number(min))}+`;
                                        if (max) return `Up to $${formatK(Number(max))}`;
                                        return 'Not listed';
                                    })()}
                                </span>
                            </div>
                        </div>

                        {/* Location */}
                        <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/30 rounded-lg">
                            <div className="p-2 rounded-full bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400">
                                <MapPinIcon className="h-5 w-5" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-xs text-slate-500 uppercase font-semibold">Location</span>
                                <span className="text-sm font-medium text-slate-900 dark:text-white truncate max-w-[150px]" title={currentJob.location || ''}>
                                    {currentJob.location || 'See Description'}
                                </span>
                            </div>
                        </div>

                        {/* Confidence Level */}
                        <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/30 rounded-lg">
                            <div className={`p-2 rounded-full ${(currentJob.confidence_level || 'low').toLowerCase() === 'high' ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' :
                                (currentJob.confidence_level || 'low').toLowerCase() === 'medium' ? 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' :
                                    'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400'
                                }`}>
                                <SparklesIcon className="h-5 w-5" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-xs text-slate-500 uppercase font-semibold">Confidence</span>
                                <span className="text-sm font-medium text-slate-900 dark:text-white capitalize">
                                    {(currentJob.confidence_level || 'Low')}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Rationale & TL;DR - Always Visible */}
                    <div className="mb-6 space-y-3">
                        {/* Final Analysis */}
                        {(currentJob.crew_output as any)?.final?.rationale && (
                            <div className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-800">
                                <div className="flex gap-3">
                                    <SparklesIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                                    <div>
                                        <h4 className="text-sm font-bold text-blue-900 dark:text-blue-200 mb-1">Analysis Verdict</h4>
                                        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                                            {(currentJob.crew_output as any)?.final?.rationale}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* TL;DR Summary - Collapsible Accordion */}
                        {(currentJob.tldr_summary || (currentJob.crew_output as any)?.tldr_summary) && (
                            <div className="bg-slate-50 dark:bg-slate-700/30 rounded-xl border border-slate-100 dark:border-slate-700 overflow-hidden transition-all duration-300">
                                <button
                                    onClick={() => setIsSnapshotExpanded(!isSnapshotExpanded)}
                                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors"
                                >
                                    <h4 className="text-xs font-bold text-slate-500 uppercase flex items-center gap-2">
                                        job snapshot
                                    </h4>
                                    {isSnapshotExpanded ? (
                                        <ChevronUpIcon className="h-4 w-4 text-slate-400" />
                                    ) : (
                                        <ChevronDownIcon className="h-4 w-4 text-slate-400" />
                                    )}
                                </button>

                                {isSnapshotExpanded && (
                                    <div className="px-4 pb-4">
                                        <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed animate-fadeIn">
                                            {currentJob.tldr_summary || (currentJob.crew_output as any)?.tldr_summary}
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Career Fit Analysis Dimensions */}
                    <div className="mb-6">
                        <h4 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">Fit Analysis</h4>
                        <div className="space-y-2">
                            {(() => {
                                const dimensionMap: Record<string, string> = {
                                    'north_star': 'North Star Alignment',
                                    'trajectory_mastery': 'Trajectory Mastery',
                                    'values_compass': 'Values Compass',
                                    'lifestyle_alignment': 'Lifestyle Alignment',
                                    'compensation_philosophy': 'Compensation',
                                    'functional_match': 'Functional Match'
                                };

                                const crewOutput = (currentJob.crew_output ?? {}) as any;
                                const sources = crewOutput.sources || [];

                                // Clean parse of dimensions from the new sources array
                                let dimensions: any[] = [];

                                if (Array.isArray(sources)) {
                                    dimensions = sources.map((source: any) => ({
                                        key: source.dimension,
                                        name: dimensionMap[source.dimension] || source.dimension.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
                                        score: source.score,
                                        summary: source.summary
                                    }));
                                } else if (typeof sources === 'object' && sources !== null) {
                                    // Handle case where sources is a dictionary (intermediate format)
                                    Object.keys(sources).forEach((key: string) => {
                                        const source = sources[key];
                                        if (source && typeof source.score === 'number') {
                                            dimensions.push({
                                                key,
                                                name: dimensionMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
                                                score: source.score,
                                                summary: source.summary
                                            });
                                        }
                                    });
                                }

                                // Fallback for old data format if sources array is empty but we have keys directly on crewOutput
                                if (dimensions.length === 0) {
                                    // Attempt to read old format structure if sources missing
                                    Object.keys(dimensionMap).forEach(key => {
                                        if (crewOutput[key] && typeof crewOutput[key].score === 'number') {
                                            dimensions.push({
                                                key,
                                                name: dimensionMap[key],
                                                score: crewOutput[key].score,
                                                summary: crewOutput[key].summary
                                            });
                                        }
                                    });
                                }

                                // Sort dimensions according to user preference
                                const order = [
                                    'functional_match',
                                    'compensation_philosophy',
                                    'north_star',
                                    'trajectory_mastery',
                                    'lifestyle_alignment',
                                    'values_compass'
                                ];

                                dimensions.sort((a, b) => {
                                    const indexA = order.indexOf(a.key);
                                    const indexB = order.indexOf(b.key);
                                    // If both found in order list, sort by index
                                    if (indexA !== -1 && indexB !== -1) return indexA - indexB;
                                    // If only one found, put it first
                                    if (indexA !== -1) return -1;
                                    if (indexB !== -1) return 1;
                                    // Otherwise sort alphabetically
                                    return a.name.localeCompare(b.name);
                                });

                                return dimensions.map((dim: any) => (
                                    <div key={dim.key} className="group relative">
                                        <div className="flex items-center gap-3 p-2 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-colors cursor-help">
                                            <div className="w-32 flex-shrink-0 text-xs font-medium text-slate-600 dark:text-slate-400">
                                                {dim.name}
                                            </div>
                                            <div className="flex-1 h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full ${dim.score >= 4 ? 'bg-green-500' :
                                                        dim.score >= 3 ? 'bg-yellow-500' : 'bg-red-500'
                                                        }`}
                                                    style={{ width: `${(dim.score / 5) * 100}%` }}
                                                />
                                            </div>
                                            <div className="w-8 text-right text-xs font-bold text-slate-700 dark:text-slate-300">
                                                {dim.score}/5
                                            </div>
                                        </div>
                                        {/* Tooltip */}
                                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-slate-900 text-white text-xs rounded-lg shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                                            {dim.summary?.replace(/\\"/g, '"').replace(/^"|"$/g, '')}
                                            <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-slate-900"></div>
                                        </div>
                                    </div>
                                ));
                            })()}
                        </div>
                    </div>

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
                            className="flex flex-col items-center justify-center gap-1 bg-red-50 hover:bg-red-100 text-red-600 dark:bg-red-900/20 dark:text-red-400 dark:hover:bg-red-900/40 px-3 py-3 rounded-lg font-semibold transition-all duration-200 active:scale-95 border border-red-200 dark:border-red-800"
                        >
                            <ThumbDownIcon className="h-5 w-5" />
                            <span className="text-xs">Reject</span>
                            <span className="text-[10px] opacity-75">← or R</span>
                        </button>

                        <button
                            onClick={handleFastTrack}
                            className="flex flex-col items-center justify-center gap-1 bg-blue-50 hover:bg-blue-100 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 dark:hover:bg-blue-900/40 px-3 py-3 rounded-lg font-semibold transition-all duration-200 active:scale-95 border border-blue-200 dark:border-blue-800"
                        >
                            <ThumbUpIcon className="h-5 w-5" />
                            <span className="text-xs">Fast Track</span>
                            <span className="text-[10px] opacity-75">↑ or F</span>
                        </button>

                        <button
                            onClick={handleFullAI}
                            className="flex flex-col items-center justify-center gap-1 bg-green-500 hover:bg-green-600 text-white px-3 py-3 rounded-lg font-semibold transition-all duration-200 shadow-md hover:shadow-lg active:scale-95 border border-transparent"
                        >
                            <SparklesIcon className="h-5 w-5" />
                            <span className="text-xs">Full AI</span>
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
            {
                showJDModal && (
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
                )
            }
        </div >
    );
};

export default JobCardView;
