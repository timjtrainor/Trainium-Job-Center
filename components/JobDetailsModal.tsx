import React, { useState } from 'react';
import { MarkdownPreview } from './MarkdownPreview';
import { LoadingSpinner } from './IconComponents';

interface JobDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    companyName: string;
    jobTitle: string;
    salary?: string;
    location?: string;
    remoteStatus?: 'Remote' | 'Hybrid' | 'On-site' | '';
    jobLink?: string;
    jobDescription: string;
}

const DetailItem = ({ label, value, isLink = false }: { label: string, value?: string, isLink?: boolean }) => (
    <div>
        <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</dt>
        <dd className="mt-1 text-sm text-slate-900 dark:text-slate-100">
            {isLink && value ? (
                <a href={value} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline dark:text-blue-400 break-all">
                    {value}
                </a>
            ) : (
                value || 'N/A'
            )}
        </dd>
    </div>
);

export const JobDetailsModal = ({ isOpen, onClose, companyName, jobTitle, salary, location, remoteStatus, jobLink, jobDescription }: JobDetailsModalProps): React.ReactNode => {
    if (!isOpen) return null;

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-3xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-xl font-bold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                Job Details
                            </h3>
                            <div className="mt-4 max-h-[70vh] overflow-y-auto pr-4 space-y-6">
                                <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                                    <DetailItem label="Company Name" value={companyName} />
                                    <DetailItem label="Job Title" value={jobTitle} />
                                    <DetailItem label="Salary" value={salary} />
                                    <DetailItem label="Location" value={location} />
                                    <DetailItem label="Remote Status" value={remoteStatus} />
                                    <DetailItem label="Job Posting Link" value={jobLink} isLink />
                                </dl>
                                <div>
                                    <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Job Description</dt>
                                    <dd className="mt-2 p-3 border rounded-md border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
                                        <MarkdownPreview markdown={jobDescription} />
                                    </dd>
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            <button type="button" onClick={onClose} className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};


interface UpdateJdModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (newJd: string) => Promise<void>;
    currentJd: string;
}

export const UpdateJdModal = ({ isOpen, onClose, onSubmit, currentJd }: UpdateJdModalProps): React.ReactNode => {
    const [newJd, setNewJd] = useState(currentJd);
    const [isLoading, setIsLoading] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async () => {
        setIsLoading(true);
        try {
            await onSubmit(newJd);
            onClose(); // Close only on success
        } catch (error) {
            // Error will be displayed in the main App component, so no need to handle here.
            // But we should stop loading.
            console.error("Failed to submit JD for re-analysis:", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                Update Job Description & Re-analyze
                            </h3>
                            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                                Paste the new, more detailed job description below. This will re-run the AI analysis to generate new keywords, guidance, and interview prep data. The previously tailored resume will not be changed.
                            </p>
                            <div className="mt-4">
                                <textarea
                                    rows={15}
                                    value={newJd}
                                    onChange={(e) => setNewJd(e.target.value)}
                                    className="w-full p-2 rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                    placeholder="Paste the full job description here..."
                                    disabled={isLoading}
                                />
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            <button
                                type="button"
                                onClick={handleSubmit}
                                disabled={isLoading || !newJd.trim()}
                                className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 sm:ml-3 sm:w-auto disabled:opacity-50"
                            >
                                {isLoading ? <LoadingSpinner /> : 'Submit & Re-analyze'}
                            </button>
                            <button
                                type="button"
                                onClick={onClose}
                                disabled={isLoading}
                                className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};