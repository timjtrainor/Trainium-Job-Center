import React, { useState } from 'react';
import { PostResponse, PostResponsePayload, StrategicNarrative, Prompt, PromptContext } from '../../types';
import * as geminiService from '../../services/geminiService';
import { PlusCircleIcon } from '../shared/ui/IconComponents';

interface PostResponsesTabProps {
    responses: PostResponse[];
    onOpenAddModal: () => void;
    onOpenRewriteModal: (response: PostResponse) => void;
    onUpdateResponse: (commentId: string, payload: PostResponsePayload) => void;
    activeNarrative: StrategicNarrative | null;
    prompts: Prompt[];
}

const RelevanceBadge = ({ relevance }: { relevance: 'low' | 'medium' | 'high' | undefined }) => {
    const baseClass = "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset";
    const relevanceMap = {
        low: 'bg-red-50 text-red-700 ring-red-600/10 dark:bg-red-400/10 dark:text-red-400 dark:ring-red-400/20',
        medium: 'bg-yellow-50 text-yellow-800 ring-yellow-600/20 dark:bg-yellow-400/10 dark:text-yellow-500 dark:ring-yellow-400/20',
        high: 'bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20',
    };
    return <span className={`${baseClass} ${relevanceMap[relevance || 'low']}`}>{relevance || 'N/A'}</span>;
};

export const PostResponsesTab = ({ responses, onOpenAddModal, onOpenRewriteModal, onUpdateResponse, activeNarrative, prompts }: PostResponsesTabProps) => {
    const [isLoading, setIsLoading] = useState<Record<string, boolean>>({});

    const handleAnalyze = async (response: PostResponse) => {
        setIsLoading(prev => ({ ...prev, [response.comment_id]: true }));
        const prompt = prompts.find(p => p.id === 'ANALYZE_COMMENT_STRATEGICALLY');
        if (!prompt) {
            console.error('Analysis prompt not found');
            setIsLoading(prev => ({ ...prev, [response.comment_id]: false }));
            return;
        }

        try {
            const userComment = response.conversation.find(c => c.author === 'user')?.text || '';
            const context: PromptContext = {
                COMMENT_TEXT: userComment,
                EXCERPT: response.post_excerpt,
                NORTH_STAR: activeNarrative?.positioning_statement,
                MASTERY: activeNarrative?.signature_capability,
                NARRATIVE: activeNarrative?.impact_story_body,
            };
            const analysis = await geminiService.analyzeCommentStrategically(context, prompt.content);
            onUpdateResponse(response.comment_id, { ai_analysis: analysis });
        } catch (error) {
            console.error('Failed to analyze comment', error);
        } finally {
            setIsLoading(prev => ({ ...prev, [response.comment_id]: false }));
        }
    };
    
    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Your Post Responses</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Track and refine your comments on other people's posts.</p>
                </div>
                <button
                    onClick={onOpenAddModal}
                    className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                >
                    <PlusCircleIcon className="w-5 h-5 mr-2 -ml-1" />
                    Add Response
                </button>
            </div>

            <div className="space-y-4">
                {responses.map(response => (
                    <div key={response.comment_id} className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
                        <div className="flex justify-between items-start gap-4">
                            <div className="flex-grow">
                                <p className="text-xs text-slate-500 dark:text-slate-400 italic">"{(response.post_excerpt || '').substring(0, 100)}..."</p>
                                <p className="mt-2 text-sm text-slate-800 dark:text-slate-200">{(response.conversation.find(c => c.author === 'user') || {text: ''}).text}</p>
                            </div>
                            <div className="flex-shrink-0 w-48 text-right space-y-2">
                                {response.ai_analysis ? (
                                    <div className="text-xs space-y-1 text-slate-500 dark:text-slate-400">
                                        <div className="flex justify-end items-center gap-2">Tone: <span className="font-semibold capitalize">{response.ai_analysis.tone}</span></div>
                                        <div className="flex justify-end items-center gap-2">Depth: <span className="font-semibold capitalize">{response.ai_analysis.depth}</span></div>
                                        <div className="flex justify-end items-center gap-2">Relevance: <RelevanceBadge relevance={response.ai_analysis.strategic_relevance} /></div>
                                    </div>
                                ) : (
                                    <span className="text-xs font-semibold text-gray-500">Needs Analysis</span>
                                )}
                            </div>
                        </div>
                        <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-600 flex justify-between items-center">
                            <p className="text-xs text-slate-400">Commented on: {new Date(response.created_at).toLocaleDateString()}</p>
                            <div className="flex gap-2">
                                {!response.ai_analysis && (
                                    <button
                                        onClick={() => handleAnalyze(response)}
                                        disabled={isLoading[response.comment_id]}
                                        className="px-2.5 py-1 text-xs font-semibold rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 disabled:bg-green-400"
                                    >
                                        {isLoading[response.comment_id] ? '...' : 'Analyze'}
                                    </button>
                                )}
                                <button
                                    onClick={() => onOpenRewriteModal(response)}
                                    className="px-2.5 py-1 text-xs font-semibold rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                                >
                                    Rewrite
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
                {responses.length === 0 && (
                    <p className="text-center py-10 text-slate-500">No responses tracked yet.</p>
                )}
            </div>
        </div>
    );
};