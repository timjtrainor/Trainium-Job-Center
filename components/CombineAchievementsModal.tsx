import React from 'react';
import { CombinedAchievementSuggestion } from '../types';

interface CombineAchievementsModalProps {
    isOpen: boolean;
    onClose: () => void;
    suggestions: CombinedAchievementSuggestion[];
    onApplySuggestion: (suggestion: CombinedAchievementSuggestion, chosenSuggestion: string) => void;
    originalAccomplishments: string[];
}

export const CombineAchievementsModal = ({ isOpen, onClose, suggestions, onApplySuggestion, originalAccomplishments }: CombineAchievementsModalProps) => {
    if (!isOpen) return null;

    return (
        <div className="relative z-[80]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-3xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                Combine Similar Achievements
                            </h3>
                            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">The AI has found potentially overlapping achievements. Review the suggestions to combine them into more impactful statements.</p>
                            <div className="mt-4 max-h-[70vh] overflow-y-auto pr-4 space-y-6">
                                {suggestions.length === 0 ? (
                                    <p className="py-8 text-center text-slate-500">No similar achievements were found to combine.</p>
                                ) : (
                                    suggestions.map((group, groupIndex) => (
                                        <div key={groupIndex} className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700">
                                            <div>
                                                <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-300">Original Achievements to Combine:</h4>
                                                <ul className="mt-2 list-disc pl-5 space-y-1 text-sm text-slate-500 dark:text-slate-400">
                                                    {group.original_indices.map(idx => (
                                                        <li key={idx}>{originalAccomplishments[idx]}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                            <div className="mt-4">
                                                <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-300">Suggested Combined Versions:</h4>
                                                <div className="mt-2 space-y-2">
                                                    {group.suggestions.map((suggestion, suggIndex) => (
                                                        <div key={suggIndex} className="p-2 rounded-md bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 flex justify-between items-center">
                                                            <p className="text-sm flex-grow">{suggestion}</p>
                                                            <button
                                                                onClick={() => onApplySuggestion(group, suggestion)}
                                                                className="ml-4 flex-shrink-0 text-xs font-semibold text-green-600 hover:underline"
                                                            >
                                                                Use this
                                                            </button>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    ))
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