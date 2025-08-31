import React, { useState } from 'react';
import { Switch } from './Switch';
import { LoadingSpinner } from './IconComponents';
import * as apiService from '../services/apiService';
import { Prompt } from '../types';

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

type HealthStatus = 'idle' | 'loading' | 'success' | 'error';

type HealthState = {
    status: HealthStatus;
    result: { status: number; statusText: string; data: any } | null;
};

const HealthCheckSection = ({ title, url, onCheck, healthState }: { title: string, url: string, onCheck: () => void, healthState: HealthState }) => {
    const getStatusIndicator = () => {
        switch (healthState.status) {
            case 'loading':
                return <div className="flex items-center"><LoadingSpinner /> <span className="ml-2">Checking...</span></div>;
            case 'success':
                return <div className="flex items-center text-green-600 dark:text-green-400 font-semibold">✅ Success</div>;
            case 'error':
                return <div className="flex items-center text-red-600 dark:text-red-400 font-semibold">❌ Error</div>;
            case 'idle':
            default:
                return <div className="text-slate-500 dark:text-slate-400">Ready</div>;
        }
    };
    
    return (
        <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between">
                <div>
                    <h4 className="font-semibold text-slate-700 dark:text-slate-300">{title}</h4>
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">{url}</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-sm min-w-[100px] text-right">{getStatusIndicator()}</div>
                    <button
                        onClick={onCheck}
                        disabled={healthState.status === 'loading'}
                        className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400"
                    >
                        Check
                    </button>
                </div>
            </div>
            {healthState.result && (
                <div className="mt-4">
                    <pre className="text-xs font-mono bg-slate-100 dark:bg-slate-800 p-3 rounded-md overflow-x-auto whitespace-pre-wrap break-all">
                        <strong>Status:</strong> {healthState.result.status} {healthState.result.statusText}
                        <br /><br />
                        <strong>Response Body:</strong>
                        <br />
                        {JSON.stringify(healthState.result.data, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
};


export const PromptEditorView = ({ prompts: initialPrompts, isDebugMode, onSetIsDebugMode, modelName, setModelName }: PromptEditorViewProps) => {
    const [postgrestHealth, setPostgrestHealth] = useState<HealthState>({ status: 'idle', result: null });
    const [fastApiHealth, setFastApiHealth] = useState<HealthState>({ status: 'idle', result: null });
    const [prompts, setPrompts] = useState(initialPrompts);
    const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(prompts[0] || null);

    const handlePromptChange = (field: keyof Prompt, value: string) => {
        if (!selectedPrompt) return;
        const updatedPrompt = { ...selectedPrompt, [field]: value };
        setSelectedPrompt(updatedPrompt);
        setPrompts(prompts.map(p => p.id === updatedPrompt.id ? updatedPrompt : p));
    };

    const handlePostgrestHealthCheck = async () => {
        setPostgrestHealth({ status: 'loading', result: null });
        const result = await apiService.checkPostgrestHealth();
        setPostgrestHealth({
            status: result.status === 200 ? 'success' : 'error',
            result: result,
        });
    };

    const handleFastApiHealthCheck = async () => {
        setFastApiHealth({ status: 'loading', result: null });
        const result = await apiService.checkFastApiHealth();
        setFastApiHealth({
            status: result.status === 200 ? 'success' : 'error',
            result: result,
        });
    };

    return (
        <div className="space-y-6 animate-fade-in">
             <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-6 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Dev Mode</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">Configure AI models, debug settings, and check system health.</p>
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

                <div className="mb-6 pb-6 border-b border-slate-200 dark:border-slate-700">
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">API Health Checks</h3>
                    <div className="space-y-4">
                        <HealthCheckSection 
                            title="PostgREST API"
                            url="http://localhost:3000"
                            onCheck={handlePostgrestHealthCheck}
                            healthState={postgrestHealth}
                        />
                        <HealthCheckSection 
                            title="FastAPI Service"
                            url="http://localhost:8000/health"
                            onCheck={handleFastApiHealthCheck}
                            healthState={fastApiHealth}
                        />
                    </div>
                </div>

                <div>
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Prompt Editor</h3>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                        View and temporarily edit the prompts used by the AI. Changes are not saved between sessions.
                    </p>
                    <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="md:col-span-1 max-h-[60vh] overflow-y-auto pr-2">
                            <ul className="space-y-1">
                                {prompts.map(prompt => (
                                    <li key={prompt.id}>
                                        <button
                                            onClick={() => setSelectedPrompt(prompt)}
                                            className={`w-full text-left p-2 rounded-md text-sm ${
                                                selectedPrompt?.id === prompt.id
                                                    ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 font-semibold'
                                                    : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/50'
                                            }`}
                                        >
                                            {prompt.name}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div className="md:col-span-2 space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                            {selectedPrompt ? (
                                <>
                                    <div>
                                        <label htmlFor="prompt-name" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Name</label>
                                        <input type="text" id="prompt-name" value={selectedPrompt.name} onChange={e => handlePromptChange('name', e.target.value)} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm" />
                                    </div>
                                    <div>
                                        <label htmlFor="prompt-description" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Description</label>
                                        <textarea id="prompt-description" value={selectedPrompt.description} onChange={e => handlePromptChange('description', e.target.value)} rows={3} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm" />
                                    </div>
                                    <div>
                                        <label htmlFor="prompt-content" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Content</label>
                                        <textarea id="prompt-content" value={selectedPrompt.content} onChange={e => handlePromptChange('content', e.target.value)} rows={20} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm font-mono text-xs" />
                                    </div>
                                </>
                            ) : (
                                <p>Select a prompt to view and edit.</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};