import React, { useState, useEffect } from 'react';
import { Resume, StrategicNarrative, Prompt, PromptContext } from '../types';
import * as geminiService from '../services/geminiService';
import { LoadingSpinner } from './IconComponents';

interface SummaryRefinementPanelProps {
    isOpen: boolean;
    onClose: () => void;
    summary: string;
    resume: Resume;
    activeNarrative: StrategicNarrative | null;
    onSave: (newSummary: string) => void;
    prompts: Prompt[];
}

export const SummaryRefinementPanel = ({ isOpen, onClose, summary, resume, activeNarrative, onSave, prompts }: SummaryRefinementPanelProps) => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [suggestions, setSuggestions] = useState<string[]>([]);

    const resumeJsonToText = (res: Resume): string => {
        // This is a simplified version for context, focusing on work experience
        return res.work_experience
            .flatMap(exp => exp.accomplishments.map(acc => acc.description))
            .join('\n');
    };

    const handleGenerate = async () => {
        const prompt = prompts.find(p => p.id === 'REWRITE_SUMMARY');
        if (!prompt) {
            setError("Rewrite summary prompt not found.");
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const context: PromptContext = {
                SUMMARY: summary,
                DESIRED_TITLE: activeNarrative?.desired_title,
                POSITIONING_STATEMENT: activeNarrative?.positioning_statement,
                MASTERY: activeNarrative?.signature_capability,
                RESUME_TEXT: resumeJsonToText(resume),
            };

            const newSummaries = await geminiService.rewriteSummary(context, prompt.content);
            setSuggestions(newSummaries);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to generate summary suggestions.');
        } finally {
            setIsLoading(false);
        }
    };
    
    useEffect(() => {
        if (isOpen) {
            // Automatically generate suggestions when the panel opens
            handleGenerate();
        }
    }, [isOpen]);

    const handleSelectSuggestion = (suggestion: string) => {
        onSave(suggestion);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="relative z-[70]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">Refine Summary</h3>
                            <div className="mt-4 max-h-[70vh] overflow-y-auto pr-4 space-y-4">
                                {error && <p className="text-sm text-red-500">{error}</p>}
                                <div>
                                    <label className="block text-sm font-medium text-slate-500 dark:text-slate-400">Original Summary</label>
                                    <p className="mt-1 text-sm p-2 rounded-md bg-slate-100 dark:bg-slate-700">{summary}</p>
                                </div>
                                <div className="text-center">
                                    <button
                                        type="button"
                                        onClick={handleGenerate}
                                        disabled={isLoading}
                                        className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400"
                                    >
                                        {isLoading ? <LoadingSpinner /> : 'Regenerate Suggestions'}
                                    </button>
                                </div>
                                {suggestions.length > 0 && (
                                    <div>
                                        <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">AI Suggestions</h4>
                                        <div className="mt-2 space-y-2">
                                            {suggestions.map((sugg, i) => (
                                                <div key={i} className="p-2 rounded-md bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600">
                                                    <p className="text-sm">{sugg}</p>
                                                    <div className="text-right mt-1">
                                                        <button
                                                            onClick={() => handleSelectSuggestion(sugg)}
                                                            className="text-xs font-semibold text-green-600 hover:underline"
                                                        >
                                                            Use this
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            <button type="button" onClick={onClose} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};