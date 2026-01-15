import React, { useState } from 'react';
import { PostResponse, PostResponsePayload, StrategicNarrative, Prompt, PromptContext } from '../types';
import * as geminiService from '../services/geminiService';
import { PlusCircleIcon, SparklesIcon, LoadingSpinner } from './IconComponents';

interface ConversationCatalystTabProps {
    postResponses: PostResponse[];
    onCreatePostResponse: (payload: PostResponsePayload) => Promise<void>;
    onUpdatePostResponse: (commentId: string, payload: PostResponsePayload) => void;
    activeNarrative: StrategicNarrative | null;
    // prompts prop removed
}

const ConversationView = ({
    response,
    onUpdateResponse,
    activeNarrative,
    // prompts prop removed
    onClose,
}: {
    response: PostResponse;
    onUpdateResponse: (commentId: string, payload: PostResponsePayload) => void;
    activeNarrative: StrategicNarrative | null;
    // prompts prop removed
    onClose: () => void;
}) => {
    const [newReply, setNewReply] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);
    const [isSaving, setIsSaving] = useState(false);

    const conversation = response.conversation || [];

    const handleAddReply = (author: 'user' | 'other') => {
        if (!newReply.trim()) return;
        setIsSaving(true);
        const updatedConversation = [...conversation, { author, text: newReply }];
        onUpdateResponse(response.comment_id, { conversation: updatedConversation });
        setNewReply('');
        setIsSaving(false);
    };

    const handleGenerateAIReply = async () => {
        setIsGenerating(true);
        setAiSuggestions([]);
        try {
            const history = conversation.map(c => `${c.author.toUpperCase()}: ${c.text}`).join('\n');
            const context: PromptContext = {
                POST_TEXT: response.post_excerpt,
                CONVERSATION_HISTORY: history,
                NORTH_STAR: activeNarrative?.positioning_statement,
                MASTERY: activeNarrative?.signature_capability,
            };

            const result = await geminiService.generateStrategicComment(context, 'GENERATE_STRATEGIC_COMMENT');
            setAiSuggestions(result);
        } catch (error) {
            console.error(error);
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-[60]" onClick={onClose}>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl" onClick={e => e.stopPropagation()}>
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white">Conversation Thread</h3>
                            <div className="mt-4 space-y-4 max-h-[70vh] overflow-y-auto pr-2">
                                <div className="p-3 bg-slate-100 dark:bg-slate-900/50 rounded-md">
                                    <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">Original Post</p>
                                    <p className="mt-1 text-sm text-slate-700 dark:text-slate-300 italic">"{response.post_excerpt}"</p>
                                </div>
                                <div className="space-y-3">
                                    {conversation.map((message, index) => (
                                        <div key={index} className={`flex ${message.author === 'user' ? 'justify-end' : 'justify-start'}`}>
                                            <div className={`max-w-md p-3 rounded-lg ${message.author === 'user' ? 'bg-blue-100 dark:bg-blue-900/50' : 'bg-slate-200 dark:bg-slate-700'}`}>
                                                <p className="text-sm text-slate-800 dark:text-slate-200">{message.text}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <div className="pt-4 border-t border-slate-200 dark:border-slate-700 space-y-2">
                                    <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Add to Conversation</h4>
                                    <textarea value={newReply} onChange={(e) => setNewReply(e.target.value)} rows={3} className="block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm" placeholder="Type new reply..."></textarea>
                                    <div className="flex justify-between items-center">
                                        <div className="flex gap-2">
                                            <button onClick={() => handleAddReply('user')} disabled={isSaving || !newReply} className="px-3 py-1.5 text-sm font-semibold rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50">Add My Reply</button>
                                            <button onClick={() => handleAddReply('other')} disabled={isSaving || !newReply} className="px-3 py-1.5 text-sm font-semibold rounded-md text-slate-700 bg-slate-200 hover:bg-slate-300 disabled:opacity-50 dark:bg-slate-600 dark:text-slate-200 dark:hover:bg-slate-500">Add Their Reply</button>
                                        </div>
                                        <button onClick={handleGenerateAIReply} disabled={isGenerating} className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-semibold rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/50 dark:text-blue-300 dark:hover:bg-blue-900 disabled:opacity-50">
                                            {isGenerating ? <LoadingSpinner /> : <SparklesIcon className="h-4 w-4" />} AI Suggestion
                                        </button>
                                    </div>
                                </div>
                                {aiSuggestions.length > 0 && (
                                    <div className="space-y-2">
                                        {aiSuggestions.map((sugg, i) => (
                                            <div key={i} className="flex items-center justify-between p-2 bg-slate-100 dark:bg-slate-900/50 rounded-md">
                                                <p className="text-sm text-slate-600 dark:text-slate-300 italic">{sugg}</p>
                                                <button onClick={() => setNewReply(sugg)} className="text-xs font-semibold text-blue-600 hover:underline flex-shrink-0 ml-2">Use</button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export const ConversationCatalystTab = ({ postResponses, onCreatePostResponse, onUpdatePostResponse, activeNarrative }: ConversationCatalystTabProps) => {
    const [isCreating, setIsCreating] = useState(false);
    const [newPostExcerpt, setNewPostExcerpt] = useState('');
    const [initialComment, setInitialComment] = useState('');
    const [activeConversation, setActiveConversation] = useState<PostResponse | null>(null);

    const handleStartNewConversation = async () => {
        if (!newPostExcerpt.trim() || !initialComment.trim()) return;
        setIsCreating(true);
        const payload: PostResponsePayload = {
            post_excerpt: newPostExcerpt,
            conversation: [{ author: 'user', text: initialComment }]
        };
        await onCreatePostResponse(payload);
        setNewPostExcerpt('');
        setInitialComment('');
        setIsCreating(false);
    };

    return (
        <>
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700 space-y-6">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Conversation Catalyst</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Track and get AI-powered suggestions for your comments on other people's posts.</p>
                </div>

                <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-600 space-y-3">
                    <h3 className="font-semibold text-slate-800 dark:text-slate-200">Start a New Conversation Thread</h3>
                    <textarea
                        value={newPostExcerpt}
                        onChange={(e) => setNewPostExcerpt(e.target.value)}
                        rows={2}
                        className="block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        placeholder="Paste the original post text here..."
                    />
                    <textarea
                        value={initialComment}
                        onChange={(e) => setInitialComment(e.target.value)}
                        rows={3}
                        className="block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        placeholder="Paste your initial comment here..."
                    />
                    <div className="flex justify-end">
                        <button onClick={handleStartNewConversation} disabled={isCreating || !newPostExcerpt || !initialComment} className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50">
                            <PlusCircleIcon className="h-5 w-5" /> Start Thread
                        </button>
                    </div>
                </div>

                <div className="space-y-3">
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Tracked Conversations</h3>
                    {postResponses.length > 0 ? (
                        postResponses.map(response => {
                            const conversation = response.conversation || [];
                            const lastMessage = conversation[conversation.length - 1];
                            return (
                                <div key={response.comment_id} onClick={() => setActiveConversation(response)} className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/80 hover:border-blue-400 dark:hover:border-blue-500 cursor-pointer">
                                    <p className="text-xs text-slate-500 dark:text-slate-400 italic truncate">"{response.post_excerpt}"</p>
                                    <p className="mt-2 text-sm text-slate-800 dark:text-slate-200">
                                        <span className="font-semibold">{lastMessage?.author === 'user' ? 'You: ' : 'Them: '}</span>
                                        {lastMessage?.text}
                                    </p>
                                </div>
                            )
                        })
                    ) : (
                        <p className="text-center py-8 text-slate-500 dark:text-slate-400">No conversations tracked yet. Start one above.</p>
                    )}
                </div>
            </div>
            {activeConversation && (
                <ConversationView
                    response={activeConversation}
                    onUpdateResponse={onUpdatePostResponse}
                    activeNarrative={activeNarrative}
                    // prompts prop removed
                    onClose={() => setActiveConversation(null)}
                />
            )}
        </>
    );
};