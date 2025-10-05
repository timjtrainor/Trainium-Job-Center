import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../hooks/useToast';
import * as apiService from '../services/apiService';
import { LoadingSpinner, CheckIcon } from './IconComponents';

export const QuickAddLinkedInJob = () => {
    const [url, setUrl] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [reviewStatus, setReviewStatus] = useState<'idle' | 'fetching' | 'reviewing' | 'complete'>('idle');
    const navigate = useNavigate();
    const { addToast } = useToast();

    // Auto-detect LinkedIn URL from clipboard
    useEffect(() => {
        const detectClipboardUrl = async () => {
            try {
                const text = await navigator.clipboard.readText();
                // Detect any LinkedIn job URL format
                if (text.includes('linkedin.com/jobs') && (
                    text.includes('/view/') ||
                    text.includes('currentJobId=') ||
                    /jobs\/\d+/.test(text)
                )) {
                    setUrl(text);
                    addToast('LinkedIn URL detected from clipboard!', 'info');
                }
            } catch {
                // Clipboard permission denied - that's okay
            }
        };

        detectClipboardUrl();
    }, [addToast]);

    const extractJobId = (inputUrl: string): string | null => {
        try {
            // Extract job ID from various LinkedIn URL formats
            const patterns = [
                /linkedin\.com\/jobs\/view\/(\d+)/,           // Standard view URL
                /currentJobId=(\d+)/,                          // Collections URL
                /jobs\/(\d+)/                                  // Short format
            ];

            for (const pattern of patterns) {
                const match = inputUrl.match(pattern);
                if (match && match[1]) {
                    return match[1];
                }
            }
            return null;
        } catch {
            return null;
        }
    };

    const normalizeLinkedInUrl = (inputUrl: string): string => {
        const jobId = extractJobId(inputUrl);
        if (!jobId) {
            throw new Error('Invalid LinkedIn job URL. Please provide a URL containing a job ID.');
        }
        // Return clean LinkedIn job view URL
        return `https://www.linkedin.com/jobs/view/${jobId}/`;
    };

    const handleSubmit = async () => {
        if (!url) return;

        setIsLoading(true);
        setReviewStatus('fetching');

        try {
            // Normalize URL to extract job ID and create clean URL
            const normalizedUrl = normalizeLinkedInUrl(url);

            const result = await apiService.fetchLinkedInJobByUrl(normalizedUrl);

            if (!result.success) {
                handleError(result);
                return;
            }

            // Show success toast
            addToast('Job fetched! AI is reviewing...', 'info');
            setReviewStatus('reviewing');

            // Poll for review completion
            pollReviewStatus(result.job_id!);

        } catch (err: any) {
            addToast(`Error: ${err.message}`, 'error');
            setIsLoading(false);
            setReviewStatus('idle');
        }
    };

    const pollReviewStatus = async (jobId: string) => {
        const maxAttempts = 40; // 40 * 3s = 2 minutes max
        let attempts = 0;

        const interval = setInterval(async () => {
            attempts++;

            try {
                const status = await apiService.getJobReviewStatus(jobId);

                if (status.status === 'complete') {
                    clearInterval(interval);
                    setReviewStatus('complete');
                    setIsLoading(false);

                    addToast(
                        `Review complete! Score: ${status.score}/10 - ${status.recommendation}`,
                        status.recommendation === 'Recommended' ? 'success' : 'warning'
                    );

                    // Navigate to reviewed jobs board
                    setTimeout(() => navigate('/reviewed-jobs'), 1500);
                }

                if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    setIsLoading(false);
                    addToast('Review is taking longer than expected. Check Reviewed Jobs page.', 'warning');
                    navigate('/reviewed-jobs');
                }
            } catch (err) {
                console.error('Poll error:', err);
            }
        }, 3000); // Poll every 3 seconds
    };

    const handleError = (result: any) => {
        setIsLoading(false);
        setReviewStatus('idle');

        switch (result.error) {
            case 'duplicate':
                addToast(result.message, 'warning');
                // Optionally navigate to existing job
                if (result.existing_job_id) {
                    setTimeout(() => {
                        if (result.status === 'rejected') {
                            navigate('/reviewed-jobs?filter=rejected');
                        } else {
                            navigate(`/application/${result.existing_job_id}`);
                        }
                    }, 2000);
                }
                break;

            case 'auth_expired':
                addToast('LinkedIn session expired. Please update your cookie.', 'error');
                // Could open settings modal here
                break;

            case 'rate_limit':
                addToast('LinkedIn rate limit reached. Try again in 15 minutes.', 'warning');
                break;

            case 'fetch_failed':
                addToast(result.message, 'error');
                // Could offer manual entry fallback
                break;

            default:
                addToast('An unexpected error occurred', 'error');
        }
    };

    const getStatusMessage = () => {
        switch (reviewStatus) {
            case 'fetching':
                return 'Fetching job details from LinkedIn...';
            case 'reviewing':
                return 'AI is analyzing job fit...';
            case 'complete':
                return 'Review complete! Redirecting...';
            default:
                return '';
        }
    };

    return (
        <div className="max-w-2xl mx-auto p-6">
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                    Quick Add LinkedIn Job
                </h2>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
                    Paste any LinkedIn job URL - we'll automatically extract the job ID
                </p>

                <div className="space-y-4">
                    <div>
                        <label htmlFor="linkedin-url" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            LinkedIn Job URL
                        </label>
                        <input
                            id="linkedin-url"
                            type="url"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder="Paste any LinkedIn job URL here..."
                            className="w-full p-3 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            autoFocus
                            disabled={isLoading}
                            onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
                        />
                    </div>

                    {/* Status indicator */}
                    {isLoading && (
                        <div className="flex items-center gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                            <LoadingSpinner className="h-5 w-5" />
                            <span className="text-sm text-blue-700 dark:text-blue-300">
                                {getStatusMessage()}
                            </span>
                        </div>
                    )}

                    <button
                        onClick={handleSubmit}
                        disabled={!url || isLoading}
                        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed text-white py-3 px-6 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
                    >
                        {isLoading ? (
                            <>
                                <LoadingSpinner className="h-5 w-5" />
                                Processing...
                            </>
                        ) : (
                            <>
                                <CheckIcon className="h-5 w-5" />
                                Fetch & Review Job
                            </>
                        )}
                    </button>
                </div>

                {/* Pro tip */}
                <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <p className="text-sm text-blue-800 dark:text-blue-200 mb-2">
                        💡 <strong>Pro Tip:</strong> On your phone, tap <strong>Share → Copy Link</strong> in LinkedIn.
                        Then paste here when you're back at your computer.
                    </p>
                    <p className="text-xs text-blue-700 dark:text-blue-300 mt-2">
                        <strong>Supported URL formats:</strong>
                    </p>
                    <ul className="text-xs text-blue-700 dark:text-blue-300 mt-1 ml-4 list-disc">
                        <li>linkedin.com/jobs/view/1234567890</li>
                        <li>linkedin.com/jobs/collections/...?currentJobId=1234567890</li>
                        <li>Any URL containing a LinkedIn job ID</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};
