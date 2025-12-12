import React, { useState } from 'react';
import { useToast } from '../hooks/useToast';
import * as apiService from '../services/apiService';
import { LoadingSpinner, CheckIcon, ArrowUturnLeftIcon } from './IconComponents';

interface ManualJobCreateProps {
    onBack?: () => void;
}

const initialFormData = {
    title: '',
    company_name: '',
    description: '',
    location: '',
    url: '',
    salary_min: '',
    salary_max: '',
    salary_currency: 'USD',
    remote_status: '' as '' | 'Remote' | 'Hybrid' | 'On-site',
    date_posted: '',
};

export const ManualJobCreate = ({ onBack }: ManualJobCreateProps) => {
    const [formData, setFormData] = useState({ ...initialFormData });

    const [isLoading, setIsLoading] = useState(false);
    const [isParsing, setIsParsing] = useState(false);
    const [rawText, setRawText] = useState('');
    const [submissionStatus, setSubmissionStatus] = useState<'idle' | 'submitting' | 'complete'>('idle');
    const { addToast } = useToast();

    const handleSmartFill = async () => {
        if (!rawText.trim()) return;
        setIsParsing(true);
        try {
            const parsed = await apiService.parseJobDescription(rawText, formData.url);

            setFormData(prev => ({
                ...prev,
                title: parsed.title || prev.title,
                company_name: parsed.company_name || prev.company_name,
                description: parsed.description || prev.description,
                location: parsed.location || prev.location,
                salary_min: parsed.salary_min !== null && parsed.salary_min !== undefined ? String(parsed.salary_min) : prev.salary_min,
                salary_max: parsed.salary_max !== null && parsed.salary_max !== undefined ? String(parsed.salary_max) : prev.salary_max,
                salary_currency: parsed.salary_currency || prev.salary_currency,
                remote_status: parsed.remote_status || prev.remote_status,
                date_posted: parsed.date_posted || prev.date_posted,
            }));

            addToast('Job details auto-filled! Please review before saving.', 'success');
        } catch (error: any) {
            console.error(error);
            // Provide more specific error feedback to the user
            let userMessage = 'Failed to parse job description. Please fill details manually.';
            if (error) {
                // Check for common error types/messages
                if (typeof error === 'string') {
                    if (error.toLowerCase().includes('too short')) {
                        userMessage = 'The text is too short to parse. Please provide more details.';
                    } else if (error.toLowerCase().includes('unable to extract')) {
                        userMessage = 'Unable to extract job details from the provided text.';
                    } else if (error.toLowerCase().includes('service unavailable') || error.toLowerCase().includes('network')) {
                        userMessage = 'AI service is temporarily unavailable. Please try again later.';
                    }
                } else if (error.message) {
                    const msg = error.message.toLowerCase();
                    if (msg.includes('too short')) {
                        userMessage = 'The text is too short to parse. Please provide more details.';
                    } else if (msg.includes('unable to extract')) {
                        userMessage = 'Unable to extract job details from the provided text.';
                    } else if (msg.includes('service unavailable') || msg.includes('network')) {
                        userMessage = 'AI service is temporarily unavailable. Please try again later.';
                    }
                }
            }
            addToast(userMessage, 'error');
        } finally {
            setIsParsing(false);
        }
    };

    const handleInputChange = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const parseNumericField = (value: string) => {
        const parsed = parseFloat(value);
        return Number.isFinite(parsed) ? parsed : undefined;
    };

    const buildJobUrl = () => {
        const trimmedUrl = formData.url.trim();
        if (trimmedUrl) return trimmedUrl;

        const slug = [formData.company_name, formData.title]
            .map(part => part.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-'))
            .filter(Boolean)
            .join('-')
            .replace(/^-+|-+$/g, '');

        return `manual://${slug || 'job'}`;
    };

    const mapRemoteStatus = () => {
        if (!formData.remote_status) return undefined;
        if (formData.remote_status === 'Remote') return true;
        if (formData.remote_status === 'On-site') return false;
        return undefined;
    };

    const handleSubmit = async () => {
        if (!formData.title.trim() || !formData.company_name.trim() || !formData.description.trim()) {
            addToast('Please fill in all required fields (Title, Company, Description)', 'error');
            return;
        }

        setIsLoading(true);
        setSubmissionStatus('submitting');

        try {
            const ingestPayload = {
                site_name: 'manual_entry',
                jobs: [
                    {
                        title: formData.title.trim(),
                        company: formData.company_name.trim(),
                        description: formData.description.trim(),
                        job_url: buildJobUrl(),
                        location: formData.location.trim() || undefined,
                        salary_min: parseNumericField(formData.salary_min),
                        salary_max: parseNumericField(formData.salary_max),
                        is_remote: mapRemoteStatus(),
                        date_posted: formData.date_posted || undefined,
                    },
                ],
            };

            const result = await apiService.ingestJobs(ingestPayload);
            const summary = result?.summary;

            addToast(
                summary?.inserted
                    ? `Saved ${summary.inserted} job${summary.inserted > 1 ? 's' : ''} to the jobs table.`
                    : 'No new jobs inserted (possible duplicate).',
                summary?.inserted ? 'success' : 'warning'
            );

            if ((summary?.skipped_duplicates || summary?.blocked_duplicates) && !summary?.inserted) {
                addToast(
                    `Duplicates skipped: ${summary?.skipped_duplicates || 0}${summary?.blocked_duplicates ? `, blocked: ${summary.blocked_duplicates}` : ''}`,
                    'info'
                );
            }

            if (summary?.errors?.length) {
                addToast(`Issues reported: ${summary.errors[0]}`, 'error');
            }

            // Reset form for quick entry of another job
            setFormData({ ...initialFormData });
            setIsLoading(false);
            setSubmissionStatus('complete');

        } catch (err: any) {
            addToast(`Error: ${err.message}`, 'error');
            setIsLoading(false);
            setSubmissionStatus('idle');
        }
    };

    const getStatusMessage = () => {
        switch (submissionStatus) {
            case 'submitting':
                return 'Saving job to the jobs table...';
            case 'complete':
                return 'Job saved!';
            default:
                return '';
        }
    };

    const inputClass = "mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm text-slate-900 dark:text-white";

    return (
        <div className="max-w-4xl mx-auto p-6">
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700">
                {/* Header */}
                <div className="flex items-center gap-4 mb-6">
                    {onBack && (
                        <button
                            onClick={onBack}
                            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700"
                        >
                            <ArrowUturnLeftIcon className="h-5 w-5" />
                        </button>
                    )}
                    <div>
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                            Add Job Manually
                        </h2>
                        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                            Enter job details to save a job directly into the jobs table for downstream processing
                        </p>
                    </div>
                </div>

                {/* Smart Fill Section */}
                <div className="mb-8 p-5 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl border border-indigo-100 dark:border-indigo-800/50">
                     <div className="flex items-center gap-2 mb-3">
                        <span className="text-lg">✨</span>
                        <h3 className="text-base font-semibold text-indigo-900 dark:text-indigo-100">
                            Smart Fill
                        </h3>
                     </div>
                     <p className="text-sm text-indigo-700 dark:text-indigo-300 mb-4">
                        Paste the full job description below and we'll automatically extract the details for you.
                     </p>
                     <textarea
                        rows={6}
                        className="w-full p-3 bg-white dark:bg-slate-800 border border-indigo-200 dark:border-indigo-800 rounded-lg text-sm text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder-indigo-300 dark:placeholder-indigo-700"
                        placeholder="Paste the raw job posting text here (e.g. CTRL+A, CTRL+C from the job page)..."
                        value={rawText}
                        onChange={(e) => setRawText(e.target.value)}
                     />
                     <div className="mt-4 flex justify-end">
                        <button
                            onClick={handleSmartFill}
                            disabled={isParsing || !rawText.trim()}
                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400 disabled:cursor-not-allowed transition-all"
                        >
                            {isParsing ? (
                                <>
                                    <LoadingSpinner className="mr-2 h-4 w-4" />
                                    Analyzing Text...
                                </>
                            ) : (
                                <>
                                    Auto-Fill Details
                                </>
                            )}
                        </button>
                     </div>
                </div>

                {/* Status indicator */}
                {isLoading && (
                    <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <div className="flex items-center gap-3">
                            <LoadingSpinner className="h-5 w-5" />
                            <span className="text-sm text-blue-700 dark:text-blue-300">
                                {getStatusMessage()}
                            </span>
                        </div>
                    </div>
                )}

                {/* Form */}
                <div className="space-y-6">
                    {/* Required Fields */}
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                        <div className="sm:col-span-2">
                            <label htmlFor="title" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                Job Title <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="text"
                                id="title"
                                value={formData.title}
                                onChange={(e) => handleInputChange('title', e.target.value)}
                                className={inputClass}
                                placeholder="e.g., Senior Software Engineer"
                                required
                                disabled={isLoading}
                            />
                        </div>

                        <div className="sm:col-span-2">
                            <label htmlFor="company_name" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                Company Name <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="text"
                                id="company_name"
                                value={formData.company_name}
                                onChange={(e) => handleInputChange('company_name', e.target.value)}
                                className={inputClass}
                                placeholder="e.g., Google"
                                required
                                disabled={isLoading}
                            />
                        </div>

                        <div className="sm:col-span-2">
                            <label htmlFor="url" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                Job Posting URL
                            </label>
                            <input
                                type="url"
                                id="url"
                                value={formData.url}
                                onChange={(e) => handleInputChange('url', e.target.value)}
                                className={inputClass}
                                placeholder="https://..."
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label htmlFor="location" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                Location
                            </label>
                            <input
                                type="text"
                                id="location"
                                value={formData.location}
                                onChange={(e) => handleInputChange('location', e.target.value)}
                                className={inputClass}
                                placeholder="e.g., San Francisco, CA"
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label htmlFor="remote_status" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                Remote Work
                            </label>
                            <select
                                id="remote_status"
                                value={formData.remote_status}
                                onChange={(e) => handleInputChange('remote_status', e.target.value)}
                                className={inputClass}
                                disabled={isLoading}
                            >
                                <option value="">Select...</option>
                                <option value="Remote">Remote</option>
                                <option value="Hybrid">Hybrid</option>
                                <option value="On-site">On-site</option>
                            </select>
                        </div>
                    </div>

                    {/* Salary Fields */}
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                        <div>
                            <label htmlFor="salary_min" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                Min Salary
                            </label>
                            <input
                                type="number"
                                id="salary_min"
                                value={formData.salary_min}
                                onChange={(e) => handleInputChange('salary_min', e.target.value)}
                                className={inputClass}
                                placeholder="100000"
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label htmlFor="salary_max" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                Max Salary
                            </label>
                            <input
                                type="number"
                                id="salary_max"
                                value={formData.salary_max}
                                onChange={(e) => handleInputChange('salary_max', e.target.value)}
                                className={inputClass}
                                placeholder="150000"
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label htmlFor="salary_currency" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                Currency
                            </label>
                            <select
                                id="salary_currency"
                                value={formData.salary_currency}
                                onChange={(e) => handleInputChange('salary_currency', e.target.value)}
                                className={inputClass}
                                disabled={isLoading}
                            >
                                <option value="USD">USD</option>
                                <option value="EUR">EUR</option>
                                <option value="GBP">GBP</option>
                                <option value="CAD">CAD</option>
                                <option value="AUD">AUD</option>
                            </select>
                        </div>
                    </div>

                    {/* Date Posted */}
                    <div>
                        <label htmlFor="date_posted" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                            Date Posted
                        </label>
                        <input
                            type="date"
                            id="date_posted"
                            value={formData.date_posted}
                            onChange={(e) => handleInputChange('date_posted', e.target.value)}
                            className={inputClass}
                            disabled={isLoading}
                        />
                    </div>

                    {/* Job Description */}
                    <div>
                        <label htmlFor="description" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                            Job Description <span className="text-red-500">*</span>
                        </label>
                        <div className="mt-1">
                            <textarea
                                id="description"
                                rows={12}
                                className="w-full p-3 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg font-mono text-xs text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
                                value={formData.description}
                                onChange={(e) => handleInputChange('description', e.target.value)}
                                placeholder="Paste the full job description here..."
                                required
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    {/* Submit Button */}
                    <div className="flex items-center justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
                        <button
                            onClick={handleSubmit}
                            disabled={isLoading || !formData.title.trim() || !formData.company_name.trim() || !formData.description.trim()}
                            className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
                        >
                            {isLoading ? (
                                <>
                                    <LoadingSpinner className="mr-2 h-4 w-4" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <CheckIcon className="mr-2 h-4 w-4" />
                                    Save Job
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Pro tip */}
                <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                        💡 <strong>Pro Tip:</strong> Jobs are deduplicated by site + URL. Include the original posting
                        URL when possible so the ingestion service can keep your jobs table clean.
                    </p>
                </div>
            </div>
        </div>
    );
};
