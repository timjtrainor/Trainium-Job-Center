import React, { useState, useEffect } from 'react';
import { PostResponse, StrategicNarrative, Prompt, PostResponsePayload, PromptContext } from '../types';
import * as geminiService from '../services/geminiService';
import { LoadingSpinner } from './shared/ui/IconComponents';

interface RewriteCommentModalProps {
    isOpen: boolean;
    onClose: () => void;
    response: PostResponse;
    activeNarrative: StrategicNarrative | null;
    onSave: (commentId: string, payload: PostResponsePayload) => Promise<void>;
    prompts: Prompt[];
}

export const RewriteCommentModal = ({ isOpen, onClose, response, activeNarrative, onSave, prompts }: RewriteCommentModalProps) => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [suggestions, setSuggestions] = useState<string[]>([]);

    const handleGenerate = async () => {
        const prompt = prompts.find(p => p.id === 'GENERATE_STRATEGIC_COMMENT');
        if (!prompt) {
            setError("Rewrite comment prompt not found.");
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const userComment = response.conversation.find(c => c.author === 'user')?.text || '';
            const context: PromptContext = {
                COMMENT_TEXT: userComment,
                POST_TEXT: response.post_excerpt,
                NORTH_STAR: activeNarrative?.positioning_statement,
                MASTERY: activeNarrative?.signature_capability,
                NARRATIVE: activeNarrative?.impact_story_body,
            };

            const newComments = await geminiService.generateStrategicComment(context, prompt.content);
            setSuggestions(newComments);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to generate suggestions.');
        } finally {
            setIsLoading(false);
        }
    };
    
    useEffect(() => {
        if (isOpen) {
            handleGenerate(); // Automatically generate when opening
        }
    }, [isOpen]);

    const handleSelectSuggestion = async (suggestion: string) => {
        const newConversation = response.conversation.map(c => 
            c.author === 'user' ? { ...c, text: suggestion } : c
        );
        await onSave(response.comment_id, { conversation: newConversation });
        onClose();
    };

    if (!isOpen) return null;

    const userComment = response.conversation.find(c => c.author === 'user');

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                Rewrite as Strategic Comment
                            </h3>
                            <div className="mt-4 max-h-[70vh] overflow-y-auto pr-4 space-y-4">
                                {error && <p className="text-sm text-red-500">{error}</p>}
                                
                                <div>
                                    <label className="block text-sm font-medium text-slate-500 dark:text-slate-400">Original Comment</label>
                                    <p className="mt-1 text-sm p-2 rounded-md bg-slate-100 dark:bg-slate-700">{userComment?.text || 'N/A'}</p>
                                </div>

                                <div className="p-3 rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700/50">
                                    <h4 className="font-semibold text-sm text-blue-800 dark:text-blue-200">Your Positioning Context</h4>
                                    <p className="text-xs mt-1 text-blue-700 dark:text-blue-300">The AI is using this to align your comment with your brand.</p>
                                    <p className="text-xs mt-2"><strong className="text-slate-500 dark:text-slate-400">Mastery:</strong> {activeNarrative?.signature_capability || 'N/A'}</p>
                                    <p className="text-xs mt-1"><strong className="text-slate-500 dark:text-slate-400">Positioning:</strong> {activeNarrative?.positioning_statement || 'N/A'}</p>
                                </div>
                                
                                <div className="text-center">
                                    <button
                                        type="button"
                                        onClick={handleGenerate}
                                        disabled={isLoading}
                                        className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400"
                                    >
                                        {isLoading ? <LoadingSpinner /> : 'Regenerate Suggestions'}
                                    </button>
                                </div>

                                {suggestions.length > 0 && (
                                    <div>
                                        <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">AI Suggestions</h4>
                                        <div className="mt-2 space-y-2">
                                            {suggestions.map((sugg, i) => (
                                                <div key={i} className="p-2 rounded-md bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600">
                                                    <p className="text-sm">{sugg}</p>
                                                    <div className="text-right mt-1">
                                                        <button
                                                            onClick={() => handleSelectSuggestion(sugg)}
                                                            className="text-xs font-semibold text-green-600 hover:underline"
                                                        >
                                                            Use this Version
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            <button type="button" onClick={onClose} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};