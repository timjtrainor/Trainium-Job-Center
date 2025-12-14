import React, { useState } from 'react';
import { PostResponsePayload } from '../../types';
import { LoadingSpinner } from '../shared/ui/IconComponents';

interface AddPostResponseModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreate: (payload: PostResponsePayload) => Promise<void>;
}

export const AddPostResponseModal = ({ isOpen, onClose, onCreate }: AddPostResponseModalProps) => {
    const [commentText, setCommentText] = useState('');
    const [excerpt, setExcerpt] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!commentText.trim() || !excerpt.trim()) {
            setError('Both fields are required.');
            return;
        }
        setIsLoading(true);
        setError(null);
        try {
            await onCreate({
                post_excerpt: excerpt,
                conversation: [{ author: 'user', text: commentText }]
            });
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save response.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                        <form onSubmit={handleSubmit}>
                            <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                                <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                    Add Post Response
                                </h3>
                                <div className="mt-4 space-y-4">
                                    {error && <p className="text-sm text-red-500">{error}</p>}
                                    <div>
                                        <label htmlFor="excerpt" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                            Original Post Excerpt
                                        </label>
                                        <textarea
                                            id="excerpt"
                                            rows={3}
                                            value={excerpt}
                                            onChange={(e) => setExcerpt(e.target.value)}
                                            className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                            placeholder="A short snippet of the post you commented on..."
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor="comment_text" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                            Your Comment
                                        </label>
                                        <textarea
                                            id="comment_text"
                                            rows={4}
                                            value={commentText}
                                            onChange={(e) => setCommentText(e.target.value)}
                                            className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                            placeholder="The exact text of the comment you wrote..."
                                            required
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                                <button type="submit" disabled={isLoading} className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 sm:ml-3 sm:w-auto disabled:opacity-50">
                                    {isLoading ? <LoadingSpinner /> : 'Save Response'}
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