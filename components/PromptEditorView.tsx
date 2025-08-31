import React, { useState, useEffect } from 'react';
import { Prompt } from '../types';
import { MarkdownPreview } from './MarkdownPreview';
import { Switch } from './Switch';

interface PromptEditorViewProps {
    prompts: Prompt[];
    isDebugMode: boolean;
    onSetIsDebugMode: (enabled: boolean) => void;
    modelName: string;
    setModelName: (name: string) => void;
}

const availableModels = [
    'gemini-2.5-pro',
    'gemini-2.5-flash',
];


export const PromptEditorView = ({ prompts, isDebugMode, onSetIsDebugMode, modelName, setModelName }: PromptEditorViewProps): React.ReactNode => {
    const [selectedPromptId, setSelectedPromptId] = useState<string>(prompts[0]?.id || '');
    const [currentContent, setCurrentContent] = useState<string>('');

    useEffect(() => {
        const selectedPrompt = prompts.find(p => p.id === selectedPromptId);
        if (selectedPrompt) {
            setCurrentContent(selectedPrompt.content);
        }
    }, [selectedPromptId, prompts]);
    
    const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSelectedPromptId(e.target.value);
    };
    
    const selectedPrompt = prompts.find(p => p.id === selectedPromptId);

    return (
        <div className="space-y-6 animate-fade-in">
             <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-6 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Prompt Formulation</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">View and inspect the prompts and settings used by the AI.</p>
                </div>
                <div className="flex items-center space-x-3 rounded-lg bg-slate-100 dark:bg-slate-800 p-3 border border-slate-200 dark:border-slate-700">
                    <Switch
                        enabled={isDebugMode}
                        onChange={onSetIsDebugMode}
                    />
                    <div className="flex flex-col">
                        <span className="font-semibold text-sm text-slate-700 dark:text-slate-200">Debug Mode</span>
                        <span className="text-xs text-slate-500 dark:text-slate-400">Intercept and inspect AI calls.</span>
                    </div>
                </div>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                <div className="mb-6 pb-6 border-b border-slate-200 dark:border-slate-700">
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">AI Model Configuration</h3>
                    <div className="mt-2">
                        <label htmlFor="model-name" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                            Current Text Model
                        </label>
                        <select
                            id="model-name"
                            value={modelName}
                            onChange={(e) => setModelName(e.target.value)}
                            className="mt-1 block w-full max-w-md rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        >
                            {availableModels.map(model => (
                                <option key={model} value={model}>{model}</option>
                            ))}
                        </select>
                        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                            Change the Gemini model used for text generation across the app.
                        </p>
                    </div>
                </div>
                <div className="mb-6">
                    <label htmlFor="prompt-select" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                        Select Prompt to View
                    </label>
                    <select
                      id="prompt-select"
                      value={selectedPromptId}
                      onChange={handleSelectChange}
                      className="mt-1 block w-full max-w-md rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    >
                      {prompts.map(prompt => (
                        <option key={prompt.id} value={prompt.id}>{prompt.name}</option>
                      ))}
                    </select>
                    {selectedPrompt && <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{selectedPrompt.description}</p>}
                </div>

                <div>
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">Preview</h3>
                    <div className="p-4 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700 min-h-[300px]">
                        <MarkdownPreview markdown={currentContent} />
                    </div>
                </div>
            </div>
        </div>
    );
};