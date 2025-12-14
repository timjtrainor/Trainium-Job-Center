import React, { useState } from 'react';
import { NarrativeSynthesisResult, StrategicNarrativePayload } from '../types';
import { LoadingSpinner, XCircleIcon, PlusCircleIcon } from './shared/ui/IconComponents';

interface CatalyzePathModalProps {
    isOpen: boolean;
    onClose: () => void;
    isLoading: boolean;
    result: NarrativeSynthesisResult | null;
    error: string | null;
    onCreateNarrative: (payload: StrategicNarrativePayload) => Promise<void>;
}

export const CatalyzePathModal = ({ isOpen, onClose, isLoading, result, error, onCreateNarrative }: CatalyzePathModalProps): React.ReactNode => {
    const [creatingNarrative, setCreatingNarrative] = useState<string | null>(null);

    if (!isOpen) return null;
    
    const handleCreateClick = async (path: { suggested_title: string; suggested_positioning_statement: string; }) => {
        setCreatingNarrative(path.suggested_title);
        try {
            await onCreateNarrative({
                narrative_name: path.suggested_title,
                desired_title: path.suggested_title,
                positioning_statement: path.suggested_positioning_statement
            });
            onClose(); // Close on success
        } catch (e) {
            console.error("Failed to create narrative", e);
            // Error handling can be enhanced here
        } finally {
            setCreatingNarrative(null);
        }
    };


    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl">
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
                                Catalyze New Path
                            </h3>
                            <div className="mt-4 max-h-[70vh] overflow-y-auto pr-4 space-y-4">
                                {isLoading && (
                                    <div className="flex flex-col items-center justify-center p-12">
                                        <LoadingSpinner />
                                        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Synthesizing narratives and market data...</p>
                                    </div>
                                )}
                                {error && <p className="text-sm text-red-500">{error}</p>}
                                {result && (
                                    <div className="space-y-6">
                                        <div className="p-4 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                                            <h4 className="font-semibold text-slate-800 dark:text-slate-200">AI Synthesis Summary</h4>
                                            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{result.synthesis_summary}</p>
                                        </div>
                                        <div>
                                            <h4 className="font-semibold text-slate-800 dark:text-slate-200">Suggested Hybrid Paths</h4>
                                            <div className="mt-2 space-y-4">
                                                {(result.suggested_paths || []).map((path, index) => (
                                                    <div key={index} className="p-4 rounded-lg bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
                                                        <div className="flex justify-between items-start gap-4">
                                                            <div className="flex-grow">
                                                                <h5 className="font-bold text-blue-600 dark:text-blue-400">{path.suggested_title}</h5>
                                                                <p className="mt-1 text-sm font-medium text-slate-700 dark:text-slate-300 italic">"{path.suggested_positioning_statement}"</p>
                                                                <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{path.reasoning}</p>
                                                                <div className="mt-3">
                                                                    <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">Next Steps:</p>
                                                                    <ul className="list-disc pl-5 mt-1 text-xs text-slate-500 dark:text-slate-400 space-y-0.5">
                                                                        {(path.next_steps || []).map((step, i) => <li key={i}>{step}</li>)}
                                                                    </ul>
                                                                </div>
                                                            </div>
                                                            <div className="flex-shrink-0">
                                                                 <button
                                                                    onClick={() => handleCreateClick(path)}
                                                                    disabled={!!creatingNarrative}
                                                                    className="inline-flex items-center gap-x-1.5 rounded-md bg-green-600 px-2.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-green-500 disabled:opacity-50"
                                                                >
                                                                    {creatingNarrative === path.suggested_title ? <LoadingSpinner/> : <PlusCircleIcon className="h-4 w-4" />}
                                                                    Create this Narrative
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
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