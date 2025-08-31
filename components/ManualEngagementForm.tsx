import React, { useState, useEffect } from 'react';
import { LinkedInEngagementPayload, LinkedInPost } from '../types';
import { LoadingSpinner } from './IconComponents';

interface ManualEngagementFormProps {
    isOpen: boolean;
    onClose: () => void;
    onCreate: (payload: LinkedInEngagementPayload) => Promise<void>;
    posts: LinkedInPost[];
}

export const ManualEngagementForm = ({ isOpen, onClose, onCreate, posts }: ManualEngagementFormProps) => {
    const [formData, setFormData] = useState<Partial<LinkedInEngagementPayload>>({
        interaction_type: 'like',
        created_at: new Date().toISOString().split('T')[0],
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            setFormData({
                interaction_type: 'like',
                created_at: new Date().toISOString().split('T')[0],
                post_id: posts[0]?.post_id || ''
            });
            setError(null);
            setIsLoading(false);
        }
    }, [isOpen, posts]);

    if (!isOpen) return null;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.post_id || !formData.contact_name || !formData.contact_title) {
            setError('Please fill out all required fields.');
            return;
        }
        setIsLoading(true);
        setError(null);
        try {
            await onCreate(formData as LinkedInEngagementPayload);
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save engagement.');
        } finally {
            setIsLoading(false);
        }
    };
    
    const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
    const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                        <form onSubmit={handleSubmit}>
                            <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                                <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                    Add Manual Engagement
                                </h3>
                                <div className="mt-4 space-y-4 max-h-[70vh] overflow-y-auto pr-2">
                                    {error && <p className="text-sm text-red-500">{error}</p>}
                                    <div>
                                        <label htmlFor="post_id" className={labelClass}>Select Post *</label>
                                        <select name="post_id" id="post_id" value={formData.post_id || ''} onChange={handleChange} className={inputClass} required>
                                            <option value="">-- Select Post --</option>
                                            {posts.map(p => <option key={p.post_id} value={p.post_id}>{p.theme}</option>)}
                                        </select>
                                    </div>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                        <div><label htmlFor="contact_name" className={labelClass}>Person's Name *</label><input type="text" name="contact_name" id="contact_name" value={formData.contact_name || ''} onChange={handleChange} className={inputClass} required /></div>
                                        <div><label htmlFor="contact_title" className={labelClass}>Job Title *</label><input type="text" name="contact_title" id="contact_title" value={formData.contact_title || ''} onChange={handleChange} className={inputClass} required /></div>
                                    </div>
                                     <div><label htmlFor="contact_linkedin_url" className={labelClass}>LinkedIn Profile URL</label><input type="url" name="contact_linkedin_url" id="contact_linkedin_url" value={formData.contact_linkedin_url || ''} onChange={handleChange} className={inputClass} /></div>
                                     <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                         <div>
                                            <label htmlFor="interaction_type" className={labelClass}>Interaction Type *</label>
                                            <select name="interaction_type" id="interaction_type" value={formData.interaction_type || 'like'} onChange={handleChange} className={inputClass} required>
                                                <option value="like">Like</option>
                                                <option value="comment">Comment</option>
                                                <option value="share">Share</option>
                                            </select>
                                         </div>
                                         <div>
                                            <label htmlFor="created_at" className={labelClass}>Engagement Date *</label>
                                            <input type="date" name="created_at" id="created_at" value={formData.created_at || ''} onChange={handleChange} className={inputClass} required />
                                         </div>
                                    </div>
                                    <div>
                                        <label htmlFor="notes" className={labelClass}>Notes (e.g., their comment text)</label>
                                        <textarea name="notes" id="notes" value={formData.notes || ''} onChange={handleChange} rows={3} className={inputClass}></textarea>
                                    </div>
                                </div>
                            </div>
                            <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                                <button type="submit" disabled={isLoading} className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 sm:ml-3 sm:w-auto disabled:opacity-50">
                                    {isLoading ? <LoadingSpinner /> : 'Save Engagement'}
                                </button>
                                <button type="button" onClick={onClose} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto">
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};