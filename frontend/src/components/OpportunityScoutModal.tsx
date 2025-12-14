import React from 'react';
import { ScoutedOpportunity } from '../types';
import { LoadingSpinner } from './shared/ui/IconComponents';

interface OpportunityScoutModalProps {
    isOpen: boolean;
    onClose: () => void;
    opportunities: ScoutedOpportunity[];
    isLoading: boolean;
    error: string | null;
}

export const OpportunityScoutModal = ({ isOpen, onClose, opportunities, isLoading, error }: OpportunityScoutModalProps): React.ReactNode => {
    if (!isOpen) return null;

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-3xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                AI-Scouted Opportunities
                            </h3>
                            <div className="mt-4 max-h-[70vh] overflow-y-auto pr-4 space-y-4">
                                {isLoading && <div className="flex justify-center p-8"><LoadingSpinner /> <span className="ml-2">Scouting for roles...</span></div>}
                                {error && <p className="text-sm text-red-500">{error}</p>}
                                {!isLoading && opportunities.length === 0 && !error && (
                                    <p className="text-center text-slate-500 py-8">No high-fit opportunities found at this time. Try again later.</p>
                                )}
                                {opportunities.map((opp, index) => (
                                    <div key={index} className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700">
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <a href={opp.job_url} target="_blank" rel="noopener noreferrer" className="font-bold text-blue-600 dark:text-blue-400 hover:underline">{opp.job_title}</a>
                                                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{opp.company_name}</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-xs text-slate-500 dark:text-slate-400">Fit Score</p>
                                                <p className="text-xl font-bold text-green-600 dark:text-green-400">{opp.fit_score.toFixed(1)}/10</p>
                                            </div>
                                        </div>
                                        <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 italic">AI Reasoning: {opp.reasoning}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            <button
                                type="button"
                                onClick={onClose}
                                className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};