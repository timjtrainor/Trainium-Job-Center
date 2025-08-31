import React from 'react';
import { Message } from '../types';

interface MessageDetailModalProps {
    isOpen: boolean;
    onClose: () => void;
    message: Message | null;
}

export const MessageDetailModal = ({ isOpen, onClose, message }: MessageDetailModalProps) => {
    if (!isOpen || !message) return null;

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                Message Details
                            </h3>
                            <div className="mt-4 space-y-4 max-h-[70vh] overflow-y-auto pr-4">
                                <dl className="divide-y divide-gray-200 dark:divide-slate-700">
                                    <div className="py-3 grid grid-cols-3 gap-4">
                                        <dt className="text-sm font-medium text-gray-500 dark:text-slate-400">Recipient</dt>
                                        <dd className="col-span-2 mt-0 text-sm text-slate-900 dark:text-slate-100">{message.contact?.first_name} {message.contact?.last_name || 'N/A'}</dd>
                                    </div>
                                    <div className="py-3 grid grid-cols-3 gap-4">
                                        <dt className="text-sm font-medium text-gray-500 dark:text-slate-400">Date Sent</dt>
                                        <dd className="col-span-2 mt-0 text-sm text-slate-900 dark:text-slate-100">{new Date(message.created_at).toLocaleString()}</dd>
                                    </div>
                                    <div className="py-3 grid grid-cols-3 gap-4">
                                        <dt className="text-sm font-medium text-gray-500 dark:text-slate-400">Type</dt>
                                        <dd className="col-span-2 mt-0 text-sm text-slate-900 dark:text-slate-100">{message.message_type}</dd>
                                    </div>
                                    <div className="py-3 grid grid-cols-3 gap-4">
                                        <dt className="text-sm font-medium text-gray-500 dark:text-slate-400">Content</dt>
                                        <dd className="col-span-2 mt-0 text-sm text-slate-900 dark:text-slate-100 whitespace-pre-wrap">{message.content}</dd>
                                    </div>
                                </dl>
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            <button
                                type="button"
                                onClick={onClose}
                                className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};