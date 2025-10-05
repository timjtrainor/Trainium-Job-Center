import React, { useState } from 'react';
import { ReviewedJob } from '../types';
import { overrideJobReview, JobReviewOverrideRequest, JobReviewOverrideResponse } from '../services/apiService';
import { LoadingSpinner, CheckIcon, XCircleIcon } from './IconComponents';

interface JobReviewModalProps {
    job: ReviewedJob | null;
    isOpen: boolean;
    onClose: () => void;
    onOverrideSuccess: (updatedJob: ReviewedJob) => void;
}

export const JobReviewModal: React.FC<JobReviewModalProps> = ({
    job,
    isOpen,
    onClose,
    onOverrideSuccess,
}) => {
    const [overrideMode, setOverrideMode] = useState(false);
    const [overrideRecommendation, setOverrideRecommendation] = useState<boolean>(false);
    const [overrideComment, setOverrideComment] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen || !job) return null;

    const mapOverrideToJob = (result: JobReviewOverrideResponse): ReviewedJob => ({
        ...job!,
        recommendation: result.override_recommend ? 'Recommended' : 'Not Recommended',
        is_eligible_for_application: result.override_recommend,
        override_recommend: result.override_recommend,
        override_comment: result.override_comment,
        override_by: result.override_by,
        override_at: result.override_at,
    });

    const handleAgree = async () => {
        setIsSubmitting(true);
        setError(null);

        try {
            const result = await overrideJobReview(job!.job_id, {
                override_recommend: true,
                override_comment: 'Human reviewer confirmed AI recommendation',
            });

            onOverrideSuccess(mapOverrideToJob(result));
            onClose();
        } catch (err) {
            console.error('Failed to record agreement override', err);
            setError(err instanceof Error ? err.message : 'Failed to record agreement');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleOverride = () => {
        setOverrideMode(true);
        setOverrideRecommendation(!job.recommendation.includes('Recommended'));
        setOverrideComment('');
        setError(null);
    };

    const handleSubmitOverride = async () => {
        if (!overrideComment.trim()) {
            setError('Override comment is required');
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            const overrideData: JobReviewOverrideRequest = {
                override_recommend: overrideRecommendation,
                override_comment: overrideComment.trim(),
            };

            const result = await overrideJobReview(job.job_id, overrideData);

            onOverrideSuccess(mapOverrideToJob(result));
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to submit override');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleCancel = () => {
        if (overrideMode) {
            setOverrideMode(false);
            setOverrideComment('');
            setError(null);
        } else {
            onClose();
        }
    };

    const getConfidenceColor = (confidence?: string) => {
        switch (confidence?.toLowerCase()) {
            case 'high': return 'text-green-600 dark:text-green-400';
            case 'medium': return 'text-yellow-600 dark:text-yellow-400';
            case 'low': return 'text-red-600 dark:text-red-400';
            default: return 'text-gray-600 dark:text-gray-400';
        }
    };

    const getRecommendationIcon = (recommendation: string) => {
        return recommendation.includes('Recommended') 
            ? <CheckIcon className="h-5 w-5 text-green-500" />
            : <XCircleIcon className="h-5 w-5 text-red-500" />;
    };

    const isOverridden = job.override_recommend !== null && job.override_recommend !== undefined;

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <div className="flex items-start justify-between">
                                <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                    Job Review Details
                                </h3>
                                <button
                                    onClick={onClose}
                                    className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                                >
                                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>

                            {error && !overrideMode && (
                                <div className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/40 dark:text-red-200">
                                    {error}
                                </div>
                            )}

                            <div className="mt-4 space-y-4 max-h-[70vh] overflow-y-auto pr-2">
                                {/* Job Details */}
                                <div className="border-b border-slate-200 dark:border-slate-600 pb-4">
                                    <h4 className="font-medium text-slate-900 dark:text-white">Job Information</h4>
                                    <div className="mt-2 space-y-1 text-sm">
                                        <p><span className="font-medium">Title:</span> {job.title || '—'}</p>
                                        <p><span className="font-medium">Company:</span> {job.company_name || '—'}</p>
                                        <p><span className="font-medium">Location:</span> {job.location || '—'}</p>
                                        <p><span className="font-medium">Posted:</span> {job.date_posted ? new Date(job.date_posted).toLocaleDateString() : '—'}</p>
                                        {job.url && (
                                            <p>
                                                <span className="font-medium">URL:</span>{' '}
                                                <a href={job.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">
                                                    View Job Posting
                                                </a>
                                            </p>
                                        )}
                                    </div>
                                </div>

                                {/* AI Recommendation */}
                                <div className="border-b border-slate-200 dark:border-slate-600 pb-4">
                                    <h4 className="font-medium text-slate-900 dark:text-white">AI Recommendation</h4>
                                    <div className="mt-2 space-y-2">
                                        <div className="flex items-center gap-2">
                                            {getRecommendationIcon(job.recommendation)}
                                            <span className="font-medium">{job.recommendation}</span>
                                        </div>
                                        <div className="flex items-center gap-4 text-sm">
                                            <span>
                                                <span className="font-medium">Confidence:</span>{' '}
                                                <span className={getConfidenceColor(job.confidence_level)}>
                                                    {job.confidence_level || 'Unknown'}
                                                </span>
                                            </span>
                                            <span>
                                                <span className="font-medium">Score:</span> {job.overall_alignment_score.toFixed(1)}/10
                                            </span>
                                        </div>
                                        {job.rationale && (
                                            <div>
                                                <span className="font-medium">Rationale:</span>
                                                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-700 p-3 rounded-md">
                                                    {job.rationale}
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* HITL Override Status */}
                                {isOverridden && (
                                    <div className="border-b border-slate-200 dark:border-slate-600 pb-4">
                                        <div className="flex items-center gap-2">
                                            <h4 className="font-medium text-slate-900 dark:text-white">Human Override</h4>
                                            <span className="inline-flex items-center rounded-md bg-blue-100 dark:bg-blue-900/50 px-2 py-1 text-xs font-medium text-blue-800 dark:text-blue-300">
                                                HITL Override
                                            </span>
                                        </div>
                                        <div className="mt-2 space-y-2">
                                            <div className="flex items-center gap-2">
                                                {job.override_recommend 
                                                    ? <CheckIcon className="h-5 w-5 text-green-500" />
                                                    : <XCircleIcon className="h-5 w-5 text-red-500" />
                                                }
                                                <span className="font-medium">
                                                    {job.override_recommend ? 'Recommended' : 'Not Recommended'}
                                                </span>
                                            </div>
                                            <p className="text-sm">
                                                <span className="font-medium">Comment:</span> {job.override_comment}
                                            </p>
                                            <div className="text-xs text-slate-500 dark:text-slate-400">
                                                Overridden by {job.override_by} on {job.override_at ? new Date(job.override_at).toLocaleString() : '—'}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Override Form */}
                                {overrideMode && (
                                    <div className="bg-slate-50 dark:bg-slate-700 p-4 rounded-md">
                                        <h4 className="font-medium text-slate-900 dark:text-white mb-3">Override AI Recommendation</h4>
                                        <div className="space-y-3">
                                            <div>
                                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                                    Your Recommendation
                                                </label>
                                                <div className="flex gap-4">
                                                    <label className="flex items-center">
                                                        <input
                                                            type="radio"
                                                            name="override-recommendation"
                                                            checked={overrideRecommendation === true}
                                                            onChange={() => setOverrideRecommendation(true)}
                                                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                                                        />
                                                        <span className="ml-2 text-sm">Apply</span>
                                                    </label>
                                                    <label className="flex items-center">
                                                        <input
                                                            type="radio"
                                                            name="override-recommendation"
                                                            checked={overrideRecommendation === false}
                                                            onChange={() => setOverrideRecommendation(false)}
                                                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                                                        />
                                                        <span className="ml-2 text-sm">Reject</span>
                                                    </label>
                                                </div>
                                            </div>
                                            <div>
                                                <label htmlFor="override-comment" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                                    Override Comment *
                                                </label>
                                                <textarea
                                                    id="override-comment"
                                                    rows={3}
                                                    value={overrideComment}
                                                    onChange={(e) => setOverrideComment(e.target.value)}
                                                    className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                                    placeholder="Explain your reasoning for this override..."
                                                />
                                            </div>
                                            {error && (
                                                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="bg-gray-50 dark:bg-slate-700 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            {overrideMode ? (
                                <>
                                    <button
                                        type="button"
                                        onClick={handleSubmitOverride}
                                        disabled={isSubmitting}
                                        className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 sm:ml-3 sm:w-auto disabled:opacity-50"
                                    >
                                        {isSubmitting ? (
                                            <>
                                                <LoadingSpinner size="sm" />
                                                <span className="ml-2">Submitting...</span>
                                            </>
                                        ) : (
                                            'Submit Override'
                                        )}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={handleCancel}
                                        disabled={isSubmitting}
                                        className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-600 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-white shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-500 hover:bg-gray-50 dark:hover:bg-slate-500 sm:mt-0 sm:w-auto"
                                    >
                                        Cancel
                                    </button>
                                </>
                            ) : (
                                <>
                                    <button
                                        type="button"
                                        onClick={handleAgree}
                                        disabled={isSubmitting}
                                        className="inline-flex w-full justify-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600 sm:ml-3 sm:w-auto disabled:opacity-50"
                                    >
                                        {isSubmitting ? (
                                            <>
                                                <LoadingSpinner size="sm" />
                                                <span className="ml-2">Saving...</span>
                                            </>
                                        ) : (
                                            'Agree'
                                        )}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={handleOverride}
                                        disabled={isSubmitting}
                                        className="mt-3 inline-flex w-full justify-center rounded-md bg-yellow-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-yellow-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-yellow-600 sm:mt-0 sm:w-auto sm:ml-3 disabled:opacity-50"
                                    >
                                        Override
                                    </button>
                                    <button
                                        type="button"
                                        onClick={handleCancel}
                                        disabled={isSubmitting}
                                        className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-600 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-white shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-500 hover:bg-gray-50 dark:hover:bg-slate-500 sm:mt-0 sm:w-auto disabled:opacity-50"
                                    >
                                        Close
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
