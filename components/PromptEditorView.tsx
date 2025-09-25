import React, { useState } from 'react';
import { LoadingSpinner } from './IconComponents';
import * as apiService from '../services/apiService';

// All props have been removed as this component no longer needs them.
interface PromptEditorViewProps {}

type HealthStatus = 'idle' | 'loading' | 'success' | 'error';

type HealthState = {
    status: HealthStatus;
    result: { status: number; statusText: string; data: any } | null;
};

// --- Health Check Component ---
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


export const PromptEditorView = (props: PromptEditorViewProps) => {
    const [postgrestHealth, setPostgrestHealth] = useState<HealthState>({ status: 'idle', result: null });
    const [fastApiHealth, setFastApiHealth] = useState<HealthState>({ status: 'idle', result: null });

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
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Health Checks</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">Check the status of your backend API services.</p>
                </div>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-4">API Health Checks</h3>
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
        </div>
    );
};
