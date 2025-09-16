import React, { useState, useEffect, useMemo } from 'react';
import { Switch } from './Switch';
import { LoadingSpinner, PlusCircleIcon, TrashIcon } from './IconComponents';
import * as apiService from '../services/apiService';
// FIX: Import Prompt type.
import { SiteSchedule, SiteDetails, SiteSchedulePayload, Prompt } from '../types';
import { useScheduleManager } from '../hooks/useSchedules';
import { v4 as uuidv4 } from 'uuid';

interface PromptEditorViewProps {
    // FIX: Add missing prompts prop to fix type error.
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

// --- Schedule Form Modal Component ---
interface ScheduleFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (payload: SiteSchedulePayload, scheduleId?: string) => Promise<void>;
    sites: SiteDetails[];
    scheduleToEdit: SiteSchedule | null;
}

const ScheduleFormModal = ({ isOpen, onClose, onSave, sites, scheduleToEdit }: ScheduleFormModalProps) => {
    const [formData, setFormData] = useState<Partial<SiteSchedule>>({});
    const [payloadJson, setPayloadJson] = useState('');
    const [jsonError, setJsonError] = useState('');
    const [selectedSiteDetails, setSelectedSiteDetails] = useState<SiteDetails | null>(null);

    useEffect(() => {
        if (isOpen) {
            const initialData = scheduleToEdit || { site_name: sites[0]?.site_name || '', interval_minutes: 60, enabled: true, payload: null };
            setFormData(initialData);
            setPayloadJson(JSON.stringify(initialData.payload || {}, null, 2));
            setJsonError('');
        }
    }, [isOpen, scheduleToEdit, sites]);

    useEffect(() => {
        if (formData.site_name) {
            const details = sites.find(s => s.site_name === formData.site_name);
            setSelectedSiteDetails(details || null);
        } else {
            setSelectedSiteDetails(null);
        }
    }, [formData.site_name, sites]);


    if (!isOpen) return null;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        if (type === 'checkbox') {
            setFormData(prev => ({ ...prev, [name]: (e.target as HTMLInputElement).checked }));
        } else {
            setFormData(prev => ({ ...prev, [name]: name === 'interval_minutes' ? parseInt(value) : value }));
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        let parsedPayload;
        try {
            parsedPayload = payloadJson ? JSON.parse(payloadJson) : {};
            setJsonError('');
        } catch (error) {
            setJsonError('Invalid JSON in Job Payload.');
            return;
        }

        const { id, created_at, updated_at, ...restOfFormData } = formData;

        const payload: SiteSchedulePayload = {
            ...restOfFormData,
            payload: Object.keys(parsedPayload).length > 0 ? parsedPayload : null,
        };
        onSave(payload, scheduleToEdit?.id);
    };

    const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";

    return (
        <div className="relative z-[70]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <form onSubmit={handleSubmit} className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white">{scheduleToEdit ? 'Edit Schedule' : 'Create Schedule'}</h3>
                            <div className="mt-4 space-y-4">
                                <div><label>Site</label><select name="site_name" value={formData.site_name || ''} onChange={handleChange} className={`${inputClass} disabled:bg-slate-100 dark:disabled:bg-slate-700/50`} required disabled={!!scheduleToEdit}>{sites.map(s => <option key={s.site_name} value={s.site_name}>{s.site_name}</option>)}</select></div>
                                <div><label>Interval (minutes)</label><input type="number" name="interval_minutes" value={formData.interval_minutes || 60} onChange={handleChange} className={inputClass} required /></div>
                                <div className="flex items-center gap-2"><Switch enabled={formData.enabled || false} onChange={c => setFormData(p => ({...p, enabled: c}))} /><label>Enabled</label></div>

                                {selectedSiteDetails && (
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                            FastAPI Site Details ({selectedSiteDetails.site_name})
                                        </label>
                                        <pre className="mt-1 text-xs font-mono bg-slate-100 dark:bg-slate-900/50 p-3 rounded-md overflow-x-auto max-h-40">
                                            {JSON.stringify(selectedSiteDetails, null, 2)}
                                        </pre>
                                    </div>
                                )}

                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Job Payload</label>
                                    <textarea value={payloadJson} onChange={e => setPayloadJson(e.target.value)} rows={8} className={`${inputClass} font-mono text-xs`} />
                                    {jsonError && <p className="text-xs text-red-500 mt-1">{jsonError}</p>}
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            <button type="submit" disabled={!!jsonError} className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 sm:ml-3 sm:w-auto disabled:opacity-50">Save</button>
                            <button type="button" onClick={onClose} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 sm:mt-0 sm:w-auto">Cancel</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

// --- Schedule Manager Component ---
const ScheduleManager = () => {
    const {
        schedules,
        sites,
        isLoading,
        error,
        toggleSchedule,
        deleteSchedule,
        refetch,
    } = useScheduleManager();

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingSchedule, setEditingSchedule] = useState<SiteSchedule | null>(null);
    const [expandedSite, setExpandedSite] = useState<string | null>(null);

    const groupedSchedules = useMemo(() => {
        return schedules.reduce((acc, schedule) => {
            const key = schedule.site_name;
            if (!acc[key]) acc[key] = [];
            acc[key].push(schedule);
            return acc;
        }, {} as Record<string, SiteSchedule[]>);
    }, [schedules]);

    const handleToggle = async (schedule: SiteSchedule) => {
        try {
            await toggleSchedule(schedule);
        } catch (err) {
            // Error is already handled in the hook
        }
    };

    const handleDelete = async (scheduleId: string) => {
        if (!window.confirm("Are you sure you want to delete this schedule? This action cannot be undone.")) return;
        try {
            await deleteSchedule(scheduleId);
        } catch (err) {
            // Error is already handled in the hook
        }
    };

    const handleSave = async (payload: SiteSchedulePayload, scheduleId?: string) => {
        setIsModalOpen(false);
        setEditingSchedule(null);

        try {
            if (scheduleId) {
                await apiService.updateSiteSchedule(scheduleId, payload);
            } else {
                await apiService.createSiteSchedule(payload);
            }
            await refetch(); // Refresh the data
        } catch (err) {
            // Basic error handling - the hook provides toast notifications
            console.error('Error saving schedule:', err);
        }
    };

    if (isLoading) return <div className="flex justify-center p-8"><LoadingSpinner /> Loading schedules...</div>;

    return (
        <div>
            {error && (
                <p className="text-red-500 mb-4">
                    {error}
                    <button onClick={refetch} className="ml-2 text-red-600 hover:underline text-sm">
                        Try Again
                    </button>
                </p>
            )}
            <div className="flex justify-end mb-4">
                <button onClick={() => { setEditingSchedule(null); setIsModalOpen(true); }} disabled={sites.length === 0} className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-semibold rounded-md bg-blue-600 text-white shadow-sm hover:bg-blue-500 disabled:opacity-50" title={sites.length === 0 ? "Cannot add schedule: no sites found from FastAPI." : ""}>
                    <PlusCircleIcon className="h-5 w-5"/>Add Schedule
                </button>
            </div>
            <div className="space-y-6">
                {Object.keys(groupedSchedules).map(siteName => {
                    const siteDetails = sites.find(s => s.site_name === siteName);
                    return (
                        <div key={siteName} className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
                            <h4 className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">{siteName}
                                {siteDetails && <button onClick={() => setExpandedSite(expandedSite === siteName ? null : siteName)} className="text-xs text-blue-600 dark:text-blue-400 hover:underline">(Details)</button>}
                            </h4>
                            {expandedSite === siteName && siteDetails && (
                                <div className="mt-2 p-3 bg-slate-100 dark:bg-slate-800 rounded-md text-xs font-mono">
                                    <pre>{JSON.stringify(siteDetails, null, 2)}</pre>
                                </div>
                            )}
                            <div className="mt-2 space-y-2">
                                {groupedSchedules[siteName].map(schedule => (
                                     <div key={schedule.id} className="p-3 bg-white dark:bg-slate-800 rounded-md border border-slate-200 dark:border-slate-700 space-y-2">
                                        {schedule.payload && (
                                            <pre className="text-xs font-mono bg-slate-100 dark:bg-slate-800/50 p-2 rounded-md overflow-x-auto">
                                                {JSON.stringify(schedule.payload, null, 2)}
                                            </pre>
                                        )}
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <Switch enabled={schedule.enabled} onChange={() => handleToggle(schedule)} />
                                                <div className="text-sm">
                                                    <p className="font-medium">Every {schedule.interval_minutes} minutes</p>
                                                    <p className="text-xs text-slate-500 dark:text-slate-400">Next run: {schedule.next_run_at ? new Date(schedule.next_run_at).toLocaleString() : 'N/A'}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <button onClick={() => { setEditingSchedule(schedule); setIsModalOpen(true); }} className="text-xs font-semibold text-blue-600 dark:text-blue-400">Edit</button>
                                                <button onClick={() => handleDelete(schedule.id)} className="p-1 text-slate-400 hover:text-red-500"><TrashIcon className="h-4 w-4"/></button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>
            <ScheduleFormModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onSave={handleSave} sites={sites} scheduleToEdit={editingSchedule} />
        </div>
    );
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


export const PromptEditorView = ({ prompts, isDebugMode, onSetIsDebugMode, modelName, setModelName }: PromptEditorViewProps) => {
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
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Prompt Viewer</h3>
                    <div className="mt-2 space-y-2 max-h-96 overflow-y-auto pr-2">
                        {prompts.map(prompt => (
                            <details key={prompt.id} className="p-2 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
                                <summary className="font-semibold text-sm cursor-pointer text-slate-800 dark:text-slate-200">{prompt.name}</summary>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{prompt.description}</p>
                                <pre className="mt-2 text-xs font-mono bg-slate-100 dark:bg-slate-800 p-2 rounded-md overflow-x-auto whitespace-pre-wrap">
                                    {prompt.content}
                                </pre>
                            </details>
                        ))}
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
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">Job Scrape Scheduler</h3>
                    <ScheduleManager />
                </div>
            </div>
        </div>
    );
};