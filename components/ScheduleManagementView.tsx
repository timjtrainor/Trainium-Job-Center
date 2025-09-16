import React, { useState, useEffect, useMemo } from 'react';
import { Switch } from './Switch';
import { LoadingSpinner, PlusCircleIcon, TrashIcon, XCircleIcon, LightBulbIcon, ClockIcon } from './IconComponents';
import { SiteSchedule, SiteDetails, SiteSchedulePayload } from '../types';
import { useScheduleManager, checkScheduleConflicts, getScheduleRequirements } from '../hooks/useSchedules';

// Schedule Form Modal Component
interface ScheduleFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (payload: SiteSchedulePayload, scheduleId?: string) => Promise<void>;
    sites: SiteDetails[];
    schedules: SiteSchedule[];
    scheduleToEdit: SiteSchedule | null;
}

const ScheduleFormModal = ({ isOpen, onClose, onSave, sites, schedules, scheduleToEdit }: ScheduleFormModalProps) => {
    const [formData, setFormData] = useState<Partial<SiteSchedule>>({});
    const [payloadJson, setPayloadJson] = useState('');
    const [jsonError, setJsonError] = useState('');
    const [validationErrors, setValidationErrors] = useState<string[]>([]);

    useEffect(() => {
        if (isOpen) {
            const initialData = scheduleToEdit || { 
                site_name: sites[0]?.site_name || '', 
                interval_minutes: 60, 
                enabled: true, 
                payload: null 
            };
            setFormData(initialData);
            setPayloadJson(JSON.stringify(initialData.payload || {}, null, 2));
            setJsonError('');
            setValidationErrors([]);
        }
    }, [isOpen, scheduleToEdit, sites]);

    const selectedSite = useMemo(() => {
        return sites.find(s => s.site_name === formData.site_name) || null;
    }, [sites, formData.site_name]);

    const conflictInfo = useMemo(() => {
        if (!formData.site_name || !formData.interval_minutes) return null;
        return checkScheduleConflicts(schedules, formData.site_name, formData.interval_minutes, scheduleToEdit?.id);
    }, [schedules, formData.site_name, formData.interval_minutes, scheduleToEdit?.id]);

    const requirementInfo = useMemo(() => {
        if (!formData.site_name) return null;
        return getScheduleRequirements(sites, formData.site_name);
    }, [sites, formData.site_name]);

    if (!isOpen) return null;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        if (type === 'checkbox') {
            setFormData(prev => ({ ...prev, [name]: (e.target as HTMLInputElement).checked }));
        } else {
            setFormData(prev => ({ ...prev, [name]: name === 'interval_minutes' ? parseInt(value) || 0 : value }));
        }
        // Clear validation errors when user makes changes
        if (validationErrors.length > 0) {
            setValidationErrors([]);
        }
    };

    const validateForm = () => {
        const errors: string[] = [];
        
        if (!formData.site_name) {
            errors.push('Site name is required');
        }
        
        if (!formData.interval_minutes || formData.interval_minutes < 30) {
            errors.push('Interval must be at least 30 minutes');
        }
        
        if (formData.interval_minutes && formData.interval_minutes > 1440) {
            errors.push('Interval cannot exceed 24 hours (1440 minutes)');
        }

        try {
            if (payloadJson.trim()) {
                JSON.parse(payloadJson);
            }
            setJsonError('');
        } catch (error) {
            setJsonError('Invalid JSON in payload');
            errors.push('Fix JSON syntax error');
        }

        setValidationErrors(errors);
        return errors.length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        let parsedPayload;
        try {
            parsedPayload = payloadJson.trim() ? JSON.parse(payloadJson) : {};
        } catch (error) {
            return;
        }

        const { id, created_at, updated_at, last_run_at, next_run_at, ...restOfFormData } = formData;

        const payload: SiteSchedulePayload = {
            ...restOfFormData,
            payload: Object.keys(parsedPayload).length > 0 ? parsedPayload : null,
        };

        try {
            await onSave(payload, scheduleToEdit?.id);
        } catch (error) {
            // Error handling is done in the hook
        }
    };

    const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";

    return (
        <div className="relative z-[70]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <form onSubmit={handleSubmit} className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white mb-4">
                                {scheduleToEdit ? 'Edit Schedule' : 'Create Schedule'}
                            </h3>
                            
                            {/* Validation Errors */}
                            {validationErrors.length > 0 && (
                                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                                    <div className="flex">
                                        <XCircleIcon className="h-5 w-5 text-red-400 mr-2 mt-0.5" />
                                        <div>
                                            <h4 className="text-sm font-medium text-red-800 dark:text-red-200">Please fix the following errors:</h4>
                                            <ul className="mt-1 text-sm text-red-700 dark:text-red-300 list-disc list-inside">
                                                {validationErrors.map((error, index) => (
                                                    <li key={index}>{error}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div className="grid grid-cols-1 gap-4">
                                {/* Site Selection */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Job Site</label>
                                    <select 
                                        name="site_name" 
                                        value={formData.site_name || ''} 
                                        onChange={handleChange} 
                                        className={`${inputClass} ${scheduleToEdit ? 'disabled:bg-slate-100 dark:disabled:bg-slate-700/50' : ''}`}
                                        required 
                                        disabled={!!scheduleToEdit}
                                    >
                                        <option value="">Select a job site</option>
                                        {sites.map(s => (
                                            <option key={s.site_name} value={s.site_name}>{s.site_name}</option>
                                        ))}
                                    </select>
                                    {scheduleToEdit && (
                                        <p className="mt-1 text-xs text-slate-500">Site cannot be changed when editing</p>
                                    )}
                                </div>

                                {/* Interval */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Scrape Interval (minutes)</label>
                                    <input 
                                        type="number" 
                                        name="interval_minutes" 
                                        value={formData.interval_minutes || ''} 
                                        onChange={handleChange} 
                                        className={inputClass}
                                        min={30}
                                        max={1440}
                                        required 
                                    />
                                    <p className="mt-1 text-xs text-slate-500">Minimum 30 minutes, maximum 1440 minutes (24 hours)</p>
                                </div>

                                {/* Enabled Toggle */}
                                <div className="flex items-center gap-3">
                                    <Switch 
                                        enabled={formData.enabled || false} 
                                        onChange={(enabled) => setFormData(prev => ({...prev, enabled}))} 
                                    />
                                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Enable this schedule</label>
                                </div>

                                {/* Conflict Warning */}
                                {conflictInfo?.hasConflicts && (
                                    <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
                                        <div className="flex">
                                            <XCircleIcon className="h-5 w-5 text-yellow-400 mr-2" />
                                            <div>
                                                <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Potential Schedule Conflict</h4>
                                                <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                                                    This site already has {conflictInfo.totalSchedulesForSite} active schedule(s). 
                                                    Consider using an interval of {conflictInfo.recommendedInterval} minutes or more to avoid conflicts.
                                                </p>
                                                {conflictInfo.conflicts.map(conflict => (
                                                    <p key={conflict.id} className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
                                                        • Existing schedule: Every {conflict.interval_minutes} minutes
                                                    </p>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Site Details */}
                                {selectedSite && (
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                            Site Configuration ({selectedSite.site_name})
                                        </label>
                                        <div className="text-xs font-mono bg-slate-100 dark:bg-slate-900/50 p-3 rounded-md overflow-x-auto max-h-32">
                                            <pre>{JSON.stringify(selectedSite, null, 2)}</pre>
                                        </div>
                                    </div>
                                )}

                                {/* Payload Editor */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Job Search Payload (JSON)</label>
                                    <textarea 
                                        value={payloadJson} 
                                        onChange={e => setPayloadJson(e.target.value)} 
                                        rows={6} 
                                        className={`${inputClass} font-mono text-xs`}
                                        placeholder='{"search_term": "software engineer", "location": "remote", "results_wanted": 50}'
                                    />
                                    {jsonError && <p className="text-xs text-red-500 mt-1">{jsonError}</p>}
                                    <p className="mt-1 text-xs text-slate-500">Configure search parameters for this job scraping schedule</p>
                                </div>

                                {/* Requirements */}
                                {requirementInfo && (
                                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
                                        <div className="flex">
                                            <LightBulbIcon className="h-5 w-5 text-blue-400 mr-2" />
                                            <div>
                                                <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200">Recommendations</h4>
                                                <ul className="mt-1 text-sm text-blue-700 dark:text-blue-300 list-disc list-inside">
                                                    {requirementInfo.recommendations.map((rec, index) => (
                                                        <li key={index} className="text-xs">{rec}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                        
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            <button 
                                type="submit" 
                                disabled={!!jsonError || validationErrors.length > 0} 
                                className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 sm:ml-3 sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {scheduleToEdit ? 'Update' : 'Create'} Schedule
                            </button>
                            <button 
                                type="button" 
                                onClick={onClose} 
                                className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

// Main Schedule Management View Component
export const ScheduleManagementView = () => {
    const {
        schedules,
        sites,
        isLoading,
        error,
        createSchedule,
        updateSchedule,
        deleteSchedule,
        toggleSchedule,
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

    const handleSave = async (payload: SiteSchedulePayload, scheduleId?: string) => {
        if (scheduleId) {
            await updateSchedule(scheduleId, payload);
        } else {
            await createSchedule(payload);
        }
        setIsModalOpen(false);
        setEditingSchedule(null);
    };

    const handleDelete = async (scheduleId: string) => {
        if (!window.confirm("Are you sure you want to delete this schedule? This action cannot be undone.")) return;
        await deleteSchedule(scheduleId);
    };

    const handleEdit = (schedule: SiteSchedule) => {
        setEditingSchedule(schedule);
        setIsModalOpen(true);
    };

    const handleCreateNew = () => {
        setEditingSchedule(null);
        setIsModalOpen(true);
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center p-8">
                <LoadingSpinner />
                <span className="ml-2">Loading schedules...</span>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-6 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Job Scrape Scheduler</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">
                        Manage automated job scraping schedules for different job boards
                    </p>
                </div>
                <button
                    onClick={handleCreateNew}
                    disabled={sites.length === 0}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-md bg-blue-600 text-white shadow-sm hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    title={sites.length === 0 ? "Cannot add schedule: no job sites available" : ""}
                >
                    <PlusCircleIcon className="h-5 w-5" />
                    Create Schedule
                </button>
            </div>

            {error && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                    <div className="flex">
                        <XCircleIcon className="h-5 w-5 text-red-400 mr-2" />
                        <div>
                            <h4 className="text-sm font-medium text-red-800 dark:text-red-200">Error</h4>
                            <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error}</p>
                            <button 
                                onClick={refetch} 
                                className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
                            >
                                Try Again
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {schedules.length === 0 && !error ? (
                <div className="text-center py-12">
                    <ClockIcon className="mx-auto h-12 w-12 text-slate-400" />
                    <h3 className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">No schedules</h3>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Get started by creating your first scraping schedule.</p>
                    <div className="mt-6">
                        <button
                            onClick={handleCreateNew}
                            disabled={sites.length === 0}
                            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-md bg-blue-600 text-white shadow-sm hover:bg-blue-500 disabled:opacity-50"
                        >
                            <PlusCircleIcon className="h-5 w-5" />
                            Create Schedule
                        </button>
                    </div>
                </div>
            ) : (
                <div className="space-y-6">
                    {Object.keys(groupedSchedules).map(siteName => {
                        const siteDetails = sites.find(s => s.site_name === siteName);
                        const siteSchedules = groupedSchedules[siteName];
                        const enabledCount = siteSchedules.filter(s => s.enabled).length;
                        
                        return (
                            <div key={siteName} className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
                                <div className="p-4 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h3 className="text-lg font-semibold text-slate-900 dark:text-white capitalize">
                                                {siteName}
                                            </h3>
                                            <p className="text-sm text-slate-600 dark:text-slate-400">
                                                {siteSchedules.length} schedule{siteSchedules.length !== 1 ? 's' : ''} 
                                                • {enabledCount} enabled
                                            </p>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {siteDetails && (
                                                <button 
                                                    onClick={() => setExpandedSite(expandedSite === siteName ? null : siteName)}
                                                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                                                >
                                                    {expandedSite === siteName ? 'Hide' : 'Show'} Site Details
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                    
                                    {expandedSite === siteName && siteDetails && (
                                        <div className="mt-3 p-3 bg-white dark:bg-slate-800 rounded-md">
                                            <pre className="text-xs font-mono overflow-x-auto">
                                                {JSON.stringify(siteDetails, null, 2)}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                                
                                <div className="divide-y divide-slate-200 dark:divide-slate-700">
                                    {siteSchedules.map(schedule => (
                                        <div key={schedule.id} className="p-4">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <Switch 
                                                        enabled={schedule.enabled} 
                                                        onChange={() => toggleSchedule(schedule)} 
                                                    />
                                                    <div>
                                                        <p className="font-medium text-slate-900 dark:text-white">
                                                            Every {schedule.interval_minutes} minutes
                                                        </p>
                                                        <p className="text-sm text-slate-500 dark:text-slate-400">
                                                            Next run: {schedule.next_run_at ? new Date(schedule.next_run_at).toLocaleString() : 'Not scheduled'}
                                                        </p>
                                                        {schedule.last_run_at && (
                                                            <p className="text-xs text-slate-400 dark:text-slate-500">
                                                                Last run: {new Date(schedule.last_run_at).toLocaleString()}
                                                            </p>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <button 
                                                        onClick={() => handleEdit(schedule)}
                                                        className="px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md"
                                                    >
                                                        Edit
                                                    </button>
                                                    <button 
                                                        onClick={() => handleDelete(schedule.id)}
                                                        className="p-1 text-slate-400 hover:text-red-500 rounded-md"
                                                    >
                                                        <TrashIcon className="h-4 w-4" />
                                                    </button>
                                                </div>
                                            </div>
                                            
                                            {schedule.payload && Object.keys(schedule.payload).length > 0 && (
                                                <div className="mt-3 p-3 bg-slate-50 dark:bg-slate-900/50 rounded-md">
                                                    <h5 className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">Search Configuration</h5>
                                                    <pre className="text-xs font-mono text-slate-600 dark:text-slate-400 overflow-x-auto">
                                                        {JSON.stringify(schedule.payload, null, 2)}
                                                    </pre>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            <ScheduleFormModal
                isOpen={isModalOpen}
                onClose={() => {
                    setIsModalOpen(false);
                    setEditingSchedule(null);
                }}
                onSave={handleSave}
                sites={sites}
                schedules={schedules}
                scheduleToEdit={editingSchedule}
            />
        </div>
    );
};