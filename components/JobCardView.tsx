import React, { useState, useEffect, useCallback } from 'react';
import { ReviewedJob } from '../types';
import { overrideJobReview, JobReviewOverrideRequest } from '../services/apiService';
import { CheckIcon, XCircleIcon, ChevronLeftIcon, ChevronRightIcon, UsersIcon, ThumbUpIcon, ThumbDownIcon, InformationCircleIcon } from './IconComponents';

interface JobCardViewProps {
    jobs: ReviewedJob[];
    onOverrideSuccess: (updatedJob: ReviewedJob) => void;
    currentPage: number;
    onPageChange: (page: number) => void;
    isLoading?: boolean;
}

export const JobCardView: React.FC<JobCardViewProps> = ({
    jobs,
    onOverrideSuccess,
    currentPage,
    onPageChange,
    isLoading = false
}) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [showDetails, setShowDetails] = useState(false);

    // Reset index when jobs change
    useEffect(() => {
        setCurrentIndex(0);
    }, [jobs]);

    // Keyboard navigation
    useEffect(() => {
        const handleKeyPress = (event: KeyboardEvent) => {
            if (event.key === 'ArrowLeft') {
                event.preventDefault();
                handleReject();
            } else if (event.key === 'ArrowRight') {
                event.preventDefault();
                handleAccept();
            } else if (event.key === ' ') {
                event.preventDefault();
                handleAccept();
            } else if (event.key === 'r' || event.key === 'R') {
                event.preventDefault();
                handleReject();
            } else if (event.key === 'i' || event.key === 'I') {
                event.preventDefault();
                setShowDetails(!showDetails);
            } else if (event.key === 'o' || event.key === 'O') {
                event.preventDefault();
                handleOverride();
            }
        };

        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, [currentIndex, jobs]);

    const handleAccept = useCallback(() => {
        // Navigate to applications (could be implemented later)
        console.log('Accepted job:', jobs[currentIndex]);
        nextCard();
    }, [currentIndex, jobs]);

    const handleReject = useCallback(() => {
        console.log('Rejected job:', jobs[currentIndex]);
        nextCard();
    }, [currentIndex, jobs]);

    const handleOverride = useCallback(() => {
        // Open override modal (simplified for now - could expand to full modal later)
        console.log('Override job:', jobs[currentIndex]);
        nextCard();
    }, [currentIndex, jobs]);

    const nextCard = useCallback(() => {
        if (currentIndex < jobs.length - 1) {
            setCurrentIndex(currentIndex + 1);
        } else {
            // Load next page or loop
            onPageChange(currentPage + 1);
        }
    }, [currentIndex, jobs.length, currentPage, onPageChange]);

    const prevCard = useCallback(() => {
        if (currentIndex > 0) {
            setCurrentIndex(currentIndex - 1);
        } else if (currentPage > 1) {
            onPageChange(currentPage - 1);
        }
    }, [currentIndex, currentPage, onPageChange]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-slate-600 dark:text-slate-400">Loading jobs...</span>
            </div>
        );
    }

    if (jobs.length === 0) {
        return (
            <div className="text-center py-12">
                <UsersIcon className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900 dark:text-slate-300 mb-1">No jobs to review</h3>
                <p className="text-slate-600 dark:text-slate-400">All jobs have been reviewed, or filters are too strict.</p>
            </div>
        );
    }

    const currentJob = jobs[currentIndex];
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
        if (score >= 7) return 'text-green-600';
        if (score >= 5) return 'text-yellow-600';
        return 'text-red-600';
    };

    return (
        <div className="max-w-2xl mx-auto p-4">
            {/* Navigation */}
            <div className="flex items-center justify-between mb-4">
                <button
                    onClick={prevCard}
                    disabled={currentIndex === 0 && currentPage === 1}
                    className="p-2 rounded-full bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    <ChevronLeftIcon className="h-5 w-5" />
                </button>

                <div className="text-sm text-slate-600 dark:text-slate-400">
                    Card {currentIndex + 1 + ((currentPage - 1) * 15)} of {jobs.length + ((currentPage - 1) * 15)}
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
                <div className="bg-white dark:bg-slate-800 p-6 min-h-[400px] relative">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white leading-tight">
                                {currentJob.title || 'Untitled Position'}
                            </h2>
                            <p className="text-lg text-slate-700 dark:text-slate-300 font-medium mt-1">
                                {currentJob.company_name || 'Unknown Company'}
                            </p>
                        </div>

                        {/* Score Badge */}
                        <div className={`px-3 py-1 rounded-full text-white text-sm font-semibold ${getScoreColor(currentJob.overall_alignment_score)} bg-white bg-opacity-90`}>
                            {currentJob.overall_alignment_score.toFixed(1)}/10
                        </div>
                    </div>

                    {/* Metadata */}
                    <div className="grid grid-cols-2 gap-4 mb-6 text-sm text-slate-600 dark:text-slate-400">
                        <div>
                            <div className="flex items-center gap-2">
                                <span className="font-medium">Confidence:</span>
                                <span className={`font-semibold ${getConfidenceTextColor(currentJob.confidence_level)}`}>
                                    {currentJob.confidence_level?.toUpperCase() || 'UNKNOWN'}
                                </span>
                            </div>
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <span className="font-medium">Posted:</span>
                                <span>{currentJob.date_posted ? new Date(currentJob.date_posted).toLocaleDateString() : '—'}</span>
                            </div>
                        </div>
                        <div>
                            <span className="font-medium">Location:</span> {currentJob.location || '—'}
                        </div>
                        <div>
                            <span className="font-medium">Salary:</span> {currentJob.salary_min ? `$${currentJob.salary_min}` : '—'}
                        </div>
                    </div>

                    {/* Rationale Preview */}
                    {currentJob.rationale && (
                        <div className="mb-6">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">AI Analysis</span>
                                <button
                                    onClick={() => setShowDetails(!showDetails)}
                                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                                >
                                    <InformationCircleIcon className="h-3 w-3" />
                                    {showDetails ? 'Hide' : 'Show'} Details
                                </button>
                            </div>
                            <p className="text-sm text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-700 p-3 rounded-md leading-relaxed">
                                {showDetails
                                    ? currentJob.rationale
                                    : currentJob.rationale.length > 150
                                        ? `${currentJob.rationale.substring(0, 150)}...`
                                        : currentJob.rationale
                                }
                            </p>
                        </div>
                    )}

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

                    {/* Job URL */}
                    {currentJob.url && (
                        <div className="mb-6">
                            <a
                                href={currentJob.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 text-sm"
                            >
                                View Full Job Posting →
                            </a>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex gap-3 mt-auto">
                        <button
                            onClick={handleReject}
                            className="flex-1 flex items-center justify-center gap-2 bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 active:scale-95"
                        >
                            <ThumbDownIcon className="h-5 w-5" />
                            Reject
                        </button>

                        <button
                            onClick={handleAccept}
                            className="flex-1 flex items-center justify-center gap-2 bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 active:scale-95"
                        >
                            <ThumbUpIcon className="h-5 w-5" />
                            Accept
                        </button>
                    </div>
                </div>
            </div>

            {/* Keyboard Shortcuts Help */}
            <div className="mt-6 text-center text-xs text-slate-500 dark:text-slate-400">
                <div className="inline-flex items-center gap-4 px-3 py-1 bg-slate-100 dark:bg-slate-700 rounded-full">
                    <span>← or R: Reject</span>
                    <span>→ or SPACE: Accept</span>
                    <span>I: Toggle details</span>
                    <span>O: Override</span>
                </div>
            </div>
        </div>
    );
};

export default JobCardView;
