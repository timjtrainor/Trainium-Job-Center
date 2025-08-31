import React from 'react';
import { JobSummaryResult } from '../types';
import { LoadingSpinner } from './IconComponents';

interface JobSummaryStepProps {
    summary: JobSummaryResult | null;
    onConfirm: (isInterested: boolean) => void;
    isLoading: boolean;
}

export const JobSummaryStep = ({ summary, onConfirm, isLoading }: JobSummaryStepProps): React.ReactNode => {
    
    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center text-center py-24 animate-fade-in">
                <div className="relative w-16 h-16">
                    <div className="absolute inset-0 bg-blue-200 dark:bg-blue-500/30 rounded-full animate-ping"></div>
                    <svg className="relative w-16 h-16 text-blue-600 dark:text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                    </svg>
                </div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-6">Generating Job Snapshot...</h2>
                <p className="mt-2 max-w-md mx-auto text-slate-600 dark:text-slate-400">
                    The AI is creating a concise summary of the role.
                </p>
            </div>
        );
    }
    
    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Step 2: Job Snapshot</h2>
                <p className="mt-1 text-slate-600 dark:text-slate-400">The AI has summarized the key aspects of the role. Is this a good fit for you?</p>
            </div>

            {summary && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="p-4 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700">
                        <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">Key Responsibilities</h3>
                        <ul className="list-disc pl-5 space-y-1 text-sm text-slate-700 dark:text-slate-300">
                            {summary.key_responsibilities.map((item, i) => <li key={`resp-${i}`}>{item}</li>)}
                        </ul>
                    </div>
                     <div className="p-4 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700">
                        <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">Key Qualifications</h3>
                        <ul className="list-disc pl-5 space-y-1 text-sm text-slate-700 dark:text-slate-300">
                             {summary.key_qualifications.map((item, i) => <li key={`qual-${i}`}>{item}</li>)}
                        </ul>
                    </div>
                </div>
            )}
            
             <div className="flex items-center justify-end space-x-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                <button
                onClick={() => onConfirm(false)}
                disabled={isLoading}
                className="px-6 py-2 text-base font-medium rounded-lg text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 border border-slate-300 dark:border-slate-500 shadow-sm transition-colors"
                >
                Not Interested
                </button>
                <button
                onClick={() => onConfirm(true)}
                disabled={isLoading}
                className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
                >
                Yes, I'm Interested!
                </button>
            </div>
        </div>
    );
};
