import React from 'react';
import { NinetyDayPlan } from '../types';
import { LoadingSpinner, XCircleIcon } from './IconComponents';

interface NinetyDayPlanModalProps {
    isOpen: boolean;
    onClose: () => void;
    plan: NinetyDayPlan | null;
    isLoading: boolean;
    error: string | null;
}

const PlanSection = ({ title, theme, goals }: { title: string, theme: string, goals: string[] }) => (
    <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
        <h4 className="font-bold text-slate-800 dark:text-slate-200">{title}</h4>
        <p className="text-sm font-semibold text-blue-600 dark:text-blue-400 italic">Theme: {theme}</p>
        <ul className="mt-2 list-disc pl-5 space-y-1 text-sm text-slate-600 dark:text-slate-300">
            {(goals || []).map((goal, i) => <li key={i}>{goal}</li>)}
        </ul>
    </div>
);

export const NinetyDayPlanModal = ({ isOpen, onClose, plan, isLoading, error }: NinetyDayPlanModalProps) => {
    if (!isOpen) return null;

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-3xl">
                        <div className="absolute top-0 right-0 pt-4 pr-4">
                            <button
                                type="button"
                                className="rounded-md bg-white dark:bg-slate-800 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                                onClick={onClose}
                            >
                                <span className="sr-only">Close</span>
                                <XCircleIcon className="h-6 w-6" />
                            </button>
                        </div>
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                {plan?.title || 'First 90-Day Plan'}
                            </h3>
                            <div className="mt-4 max-h-[70vh] overflow-y-auto pr-4 space-y-4">
                                {isLoading && (
                                    <div className="flex flex-col items-center justify-center p-12">
                                        <LoadingSpinner />
                                        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Generating your strategic plan...</p>
                                    </div>
                                )}
                                {error && <p className="text-sm text-red-500">{error}</p>}
                                {plan && (
                                    <div className="space-y-4">
                                        <PlanSection title="First 30 Days" theme={plan.thirty_day_plan?.theme} goals={plan.thirty_day_plan?.goals} />
                                        <PlanSection title="60-Day Plan" theme={plan.sixty_day_plan?.theme} goals={plan.sixty_day_plan?.goals} />
                                        <PlanSection title="90-Day Plan" theme={plan.ninety_day_plan?.theme} goals={plan.ninety_day_plan?.goals} />
                                    </div>
                                )}
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