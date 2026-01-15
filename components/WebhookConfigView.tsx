import React, { useState, useEffect } from 'react';
import { Switch } from './Switch';
import { LoadingSpinner, PlusCircleIcon, TrashIcon, XCircleIcon, LinkIcon, BeakerIcon } from './IconComponents';
import { WebhookConfiguration, WebhookConfigurationPayload } from '../types';
import { useWebhookManager } from '../hooks/useWebhooks';

interface WebhookFormModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (payload: WebhookConfigurationPayload, id?: string) => Promise<void>;
    webhookToEdit: WebhookConfiguration | null;
}

const WebhookFormModal = ({ isOpen, onClose, onSave, webhookToEdit }: WebhookFormModalProps) => {
    const [formData, setFormData] = useState<Partial<WebhookConfiguration>>({});
    const [validationErrors, setValidationErrors] = useState<string[]>([]);

    useEffect(() => {
        if (isOpen) {
            const initialData = webhookToEdit || {
                name: '',
                redis_channel: 'job_review_webhook',
                webhook_url: '',
                auth_token: '',
                active: true,
                description: ''
            };
            setFormData(initialData);
            setValidationErrors([]);
        }
    }, [isOpen, webhookToEdit]);

    if (!isOpen) return null;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value, type } = e.target;
        if (type === 'checkbox') {
            setFormData(prev => ({ ...prev, [name]: (e.target as HTMLInputElement).checked }));
        } else {
            setFormData(prev => ({ ...prev, [name]: value }));
        }
    };

    const validateForm = () => {
        const errors: string[] = [];
        if (!formData.name) errors.push('Name is required');
        if (!formData.redis_channel) errors.push('Redis channel is required');
        if (!formData.webhook_url) errors.push('Webhook URL is required');
        try {
            new URL(formData.webhook_url || '');
        } catch (_) {
            errors.push('Invalid Webhook URL');
        }
        setValidationErrors(errors);
        return errors.length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!validateForm()) return;

        const { id, created_at, updated_at, ...cleanPayload } = formData as any;
        await onSave(cleanPayload, webhookToEdit?.id);
    };

    const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2";

    return (
        <div className="relative z-[70]" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <form onSubmit={handleSubmit} className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6">
                            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                                {webhookToEdit ? 'Edit Webhook' : 'Add New Webhook'}
                            </h3>

                            {validationErrors.length > 0 && (
                                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-md">
                                    <ul className="text-sm text-red-700 dark:text-red-300 list-disc list-inside">
                                        {validationErrors.map((e, i) => <li key={i}>{e}</li>)}
                                    </ul>
                                </div>
                            )}

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Name (e.g. ActivePieces Job Review)</label>
                                    <input name="name" value={formData.name || ''} onChange={handleChange} className={inputClass} required />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Redis Channel</label>
                                    <input name="redis_channel" value={formData.redis_channel || ''} onChange={handleChange} className={inputClass} required />
                                    <p className="mt-1 text-xs text-slate-500">The Redis channel the bridge listens to (e.g. job_review_webhook)</p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Webhook URL</label>
                                    <input name="webhook_url" value={formData.webhook_url || ''} onChange={handleChange} className={inputClass} required type="url" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Auth Token (Optional)</label>
                                    <input name="auth_token" value={formData.auth_token || ''} onChange={handleChange} className={inputClass} type="password" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Description</label>
                                    <textarea name="description" value={formData.description || ''} onChange={handleChange} className={inputClass} rows={2} />
                                </div>
                                <div className="flex items-center gap-3">
                                    <Switch enabled={formData.active || false} onChange={active => setFormData(prev => ({ ...prev, active }))} />
                                    <label className="text-sm text-slate-700 dark:text-slate-300">Active</label>
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse">
                            <button type="submit" className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 sm:ml-3 sm:w-auto">
                                {webhookToEdit ? 'Update' : 'Save'}
                            </button>
                            <button type="button" onClick={onClose} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 sm:mt-0 sm:w-auto">
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export const WebhookConfigView = () => {
    const { webhooks, isLoading, error, createWebhook, updateWebhook, deleteWebhook, toggleWebhook, refetch } = useWebhookManager();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingWebhook, setEditingWebhook] = useState<WebhookConfiguration | null>(null);

    const handleSave = async (payload: WebhookConfigurationPayload, id?: string) => {
        if (id) {
            await updateWebhook(id, payload);
        } else {
            await createWebhook(payload);
        }
        setIsModalOpen(false);
        setEditingWebhook(null);
    };

    const handleDelete = async (id: string) => {
        if (window.confirm('Delete this webhook configuration?')) {
            await deleteWebhook(id);
        }
    };

    if (isLoading) return <div className="p-8 flex justify-center"><LoadingSpinner /></div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Webhook Routing</h1>
                    <p className="text-slate-600 dark:text-slate-400">Route Redis events to external webhooks (ActivePieces, etc.)</p>
                </div>
                <button onClick={() => { setEditingWebhook(null); setIsModalOpen(true); }} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                    <PlusCircleIcon className="w-5 h-5" /> Add Webhook
                </button>
            </div>

            {error && <div className="p-4 bg-red-50 text-red-700 rounded-md border border-red-200">{error}</div>}

            <div className="grid gap-4">
                {webhooks.length === 0 ? (
                    <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-lg border border-dashed border-slate-300 dark:border-slate-700">
                        <LinkIcon className="mx-auto h-12 w-12 text-slate-400" />
                        <h3 className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">No webhooks</h3>
                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Add a webhook to start routing events.</p>
                    </div>
                ) : (
                    webhooks.map(webhook => (
                        <div key={webhook.id} className="bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 flex justify-between items-center">
                            <div className="flex items-center gap-4">
                                <Switch enabled={webhook.active} onChange={() => toggleWebhook(webhook)} />
                                <div>
                                    <h3 className="font-semibold text-slate-900 dark:text-white">{webhook.name}</h3>
                                    <p className="text-sm text-slate-500 font-mono">{webhook.redis_channel} → {webhook.webhook_url}</p>
                                    {webhook.description && <p className="text-xs text-slate-400 mt-1">{webhook.description}</p>}
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button onClick={() => { setEditingWebhook(webhook); setIsModalOpen(true); }} className="text-blue-600 hover:text-blue-700 p-1">Edit</button>
                                <button onClick={() => handleDelete(webhook.id)} className="text-slate-400 hover:text-red-600 p-1"><TrashIcon className="w-4 h-4" /></button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            <WebhookFormModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSave}
                webhookToEdit={editingWebhook}
            />
        </div>
    );
};
