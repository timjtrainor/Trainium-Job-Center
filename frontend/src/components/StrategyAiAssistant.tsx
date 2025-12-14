import React from 'react';
import { LoadingSpinner } from './shared/ui/IconComponents';

interface StrategyAiAssistantProps {
    title: string;
    starterPrompt: string;
    userNotes: string;
    setUserNotes: (notes: string) => void;
    onGenerate: (notes: string) => Promise<any>;
    onUseResult: (result: any) => void;
    generationResult: any | null;
    isLoading: boolean;
}

export const StrategyAiAssistant = ({
    title,
    starterPrompt,
    userNotes,
    setUserNotes,
    onGenerate,
    onUseResult,
    generationResult,
    isLoading
}: StrategyAiAssistantProps) => {

    const handleGenerate = () => {
        onGenerate(userNotes || starterPrompt);
    };

    return (
        <div className="p-4 bg-slate-100 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 mt-4 space-y-3">
            <h4 className="text-md font-semibold text-slate-800 dark:text-slate-200">{title}</h4>
            
            <textarea
                value={userNotes}
                onChange={(e) => setUserNotes(e.target.value)}
                rows={3}
                className="block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                placeholder={starterPrompt}
                disabled={isLoading}
            />
            
            <button
                type="button"
                onClick={handleGenerate}
                disabled={isLoading}
                className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400"
            >
                {isLoading ? <LoadingSpinner /> : 'Generate Ideas'}
            </button>

            {generationResult && (
                <div className="p-3 bg-white dark:bg-slate-700/50 rounded-md border border-slate-300 dark:border-slate-600 space-y-3">
                    <p className="text-sm font-semibold">AI Suggestion:</p>
                    <pre className="text-xs whitespace-pre-wrap font-mono bg-slate-50 dark:bg-slate-900/50 p-2 rounded">
                        {JSON.stringify(generationResult, null, 2)}
                    </pre>
                    <button
                        type="button"
                        onClick={() => onUseResult(generationResult)}
                        className="px-3 py-1 text-xs font-semibold rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700"
                    >
                        Use This Suggestion
                    </button>
                </div>
            )}
        </div>
    );
};