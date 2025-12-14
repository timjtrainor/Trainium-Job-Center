import React, { useState, useEffect } from 'react';
import { UserProfile, UserProfilePayload } from '../../types';
import { LoadingSpinner, CheckIcon } from '../shared/ui/IconComponents';

interface MyProfileModalProps {
    isOpen: boolean;
    onClose: () => void;
    userProfile: UserProfile;
    onSaveProfile: (payload: UserProfilePayload) => Promise<void>;
}

const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";
const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
const textareaClass = `${inputClass} font-sans`;

export const MyProfileModal = ({ isOpen, onClose, userProfile, onSaveProfile }: MyProfileModalProps) => {
    const [profile, setProfile] = useState<Partial<UserProfile>>(userProfile);
    const [isLoading, setIsLoading] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            setProfile(userProfile);
            setSaveSuccess(false);
            setError(null);
        }
    }, [isOpen, userProfile]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { id, value } = e.target;
        setProfile(prev => ({ ...prev, [id]: value }));
    };

    const handleLinksChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const links = e.target.value.split('\n').filter(link => link.trim() !== '');
        setProfile(prev => ({ ...prev, links }));
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setSaveSuccess(false);
        setError(null);
        try {
            const payload: UserProfilePayload = {
                first_name: profile.first_name,
                last_name: profile.last_name,
                email: profile.email,
                phone_number: profile.phone_number,
                city: profile.city,
                state: profile.state,
                links: profile.links,
            };
            await onSaveProfile(payload);
            setSaveSuccess(true);
            setTimeout(() => {
                setSaveSuccess(false);
                onClose();
            }, 1500);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to save profile.");
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) {
        return null;
    }

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
                        <form onSubmit={handleSave}>
                            <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                                <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                    My Profile
                                </h3>
                                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">This information is used to populate your resume headers and other personal details.</p>
                                <div className="mt-4 space-y-4 max-h-[70vh] overflow-y-auto pr-2">
                                    <div className="grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-6">
                                        <div className="sm:col-span-3">
                                            <label htmlFor="first_name" className={labelClass}>First Name</label>
                                            <input type="text" id="first_name" value={profile.first_name || ''} onChange={handleChange} className={inputClass} />
                                        </div>
                                        <div className="sm:col-span-3">
                                            <label htmlFor="last_name" className={labelClass}>Last Name</label>
                                            <input type="text" id="last_name" value={profile.last_name || ''} onChange={handleChange} className={inputClass} />
                                        </div>
                                        <div className="sm:col-span-4">
                                            <label htmlFor="email" className={labelClass}>Email Address</label>
                                            <input type="email" id="email" value={profile.email || ''} onChange={handleChange} className={inputClass} />
                                        </div>
                                        <div className="sm:col-span-2">
                                            <label htmlFor="phone_number" className={labelClass}>Phone Number</label>
                                            <input type="tel" id="phone_number" value={profile.phone_number || ''} onChange={handleChange} className={inputClass} />
                                        </div>
                                        <div className="sm:col-span-3">
                                            <label htmlFor="city" className={labelClass}>City</label>
                                            <input type="text" id="city" value={profile.city || ''} onChange={handleChange} className={inputClass} />
                                        </div>
                                        <div className="sm:col-span-3">
                                            <label htmlFor="state" className={labelClass}>State / Province</label>
                                            <input type="text" id="state" value={profile.state || ''} onChange={handleChange} className={inputClass} />
                                        </div>
                                        <div className="sm:col-span-6">
                                            <label htmlFor="links" className={labelClass}>Links (LinkedIn, Portfolio, etc.)</label>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">Enter one URL per line.</p>
                                            <textarea id="links" rows={3} value={(profile.links || []).join('\n')} onChange={handleLinksChange} className={textareaClass} />
                                        </div>
                                    </div>
                                    {error && <p className="text-sm text-red-500">{error}</p>}
                                </div>
                            </div>
                            <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                                <button
                                    type="submit"
                                    disabled={isLoading || saveSuccess}
                                    className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 sm:ml-3 sm:w-auto disabled:bg-blue-400"
                                >
                                    {isLoading ? <LoadingSpinner /> : saveSuccess ? <><CheckIcon className="h-5 w-5 mr-1"/> Saved</> : 'Save Profile'}
                                </button>
                                <button type="button" onClick={onClose} disabled={isLoading} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto">
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