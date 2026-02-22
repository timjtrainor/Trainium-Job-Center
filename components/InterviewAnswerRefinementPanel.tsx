import React, { useState, useEffect } from 'react';
import { CommonInterviewAnswer, StrategicNarrative, Prompt, PromptContext, InterviewAnswerScore } from '../types';
import * as geminiService from '../services/geminiService';
import { LoadingSpinner, SparklesIcon } from './IconComponents';

interface InterviewAnswerRefinementPanelProps {
    isOpen: boolean;
    onClose: () => void;
    answerData: CommonInterviewAnswer;
    activeNarrative: StrategicNarrative | null;
    onSave: (updatedAnswer: CommonInterviewAnswer) => void;
    prompts: Prompt[];
    onGenerateSpeakerNotes: (question: string, answer: string) => Promise<void>;
}

const QuickOptionButton = ({ instruction, onClick, isLoading }: { instruction: string; onClick: (instruction: string) => void; isLoading: boolean; }) => (
    <button
        type="button"
        onClick={() => onClick(instruction)}
        disabled={isLoading}
        className="px-2.5 py-1.5 text-xs font-semibold rounded-md shadow-sm text-indigo-600 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/50 ring-1 ring-inset ring-indigo-200 dark:ring-indigo-700 hover:bg-indigo-100 dark:hover:bg-indigo-900/80 disabled:opacity-50"
    >
        {instruction}
    </button>
);

export const InterviewAnswerRefinementPanel = ({ isOpen, onClose, answerData, activeNarrative, onSave, prompts, onGenerateSpeakerNotes }: InterviewAnswerRefinementPanelProps) => {
    const [editableQuestion, setEditableQuestion] = useState('');
    const [currentDraft, setCurrentDraft] = useState('');
    const [conversation, setConversation] = useState<{ author: 'user' | 'ai', text: string }[]>([]);
    const [chatInput, setChatInput] = useState('');
    const [score, setScore] = useState<InterviewAnswerScore | null>(null);
    const [speakerNotes, setSpeakerNotes] = useState('');

    const [isLoading, setIsLoading] = useState(false);
    const [loadingAction, setLoadingAction] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            setEditableQuestion(answerData.question);
            setCurrentDraft(answerData.answer);
            setSpeakerNotes(answerData.speaker_notes || '');
            setConversation([]);
            setScore(null);
            setError(null);
        }
    }, [isOpen, answerData]);

    const handleAction = async (action: () => Promise<void>, actionName: string) => {
        setLoadingAction(actionName);
        setIsLoading(true);
        setError(null);
        try {
            await action();
        } catch (e) {
            setError(e instanceof Error ? e.message : `Failed to ${actionName}.`);
        } finally {
            setIsLoading(false);
            setLoadingAction(null);
        }
    };

    const handleChatSubmit = async (instruction: string) => {
        if (!instruction.trim()) return;

        await handleAction(async () => {
            const prompt = prompts.find(p => p.id === 'REFINE_INTERVIEW_ANSWER_CHAT');
            if (!prompt) throw new Error("Refinement chat prompt not found.");

            const newConversation = [...conversation, { author: 'user' as const, text: instruction }];
            setConversation(newConversation);
            setChatInput('');

            const context: PromptContext = {
                QUESTION: editableQuestion,
                ANSWER: currentDraft,
                USER_FEEDBACK: instruction,
                POSITIONING_STATEMENT: activeNarrative?.positioning_statement,
                MASTERY: activeNarrative?.signature_capability,
                CONVERSATION_HISTORY: newConversation.map(m => `${m.author}: ${m.text}`).join('\n'),
            };

            const result = await geminiService.chatToRefineAnswer(context, prompt.id);
            setCurrentDraft(result);
            setConversation(prev => [...prev, { author: 'ai', text: result }]);
        }, instruction);
    };

    const handleScore = async () => {
        await handleAction(async () => {
            const prompt = prompts.find(p => p.id === 'SCORE_INTERVIEW_ANSWER');
            if (!prompt || !activeNarrative) throw new Error("Scoring prompt or active narrative not found.");

            const context: PromptContext = {
                QUESTION: editableQuestion,
                ANSWER: currentDraft,
                POSITIONING_STATEMENT: activeNarrative.positioning_statement,
                MASTERY: activeNarrative.signature_capability,
                IMPACT_STORY_BODY: activeNarrative.impact_story_body,
            };
            const result = await geminiService.scoreInterviewAnswer(context, prompt.id);
            setScore(result);
        }, 'score');
    };

    const handleGenerateNotes = async () => {
        await handleAction(async () => {
            await onGenerateSpeakerNotes(editableQuestion, currentDraft);
        }, 'generate notes');
    };

    const handleSave = () => {
        onSave({ ...answerData, question: editableQuestion, answer: currentDraft, speaker_notes: speakerNotes });
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="relative z-[70]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-5xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">Answer Refinement Studio</h3>
                            <textarea
                                value={editableQuestion}
                                onChange={e => setEditableQuestion(e.target.value)}
                                rows={2}
                                className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 shadow-sm sm:text-sm font-semibold text-slate-600 dark:text-slate-400"
                            />
                            {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
                            <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-6 max-h-[75vh] overflow-y-auto p-1">
                                {/* Left: Editor and Scoring */}
                                <div className="space-y-4">
                                    <textarea value={currentDraft} onChange={e => setCurrentDraft(e.target.value)} rows={12} className="block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm" />
                                    <div className="p-4 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                                        <div className="flex justify-between items-center">
                                            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">AI Scorecard</h4>
                                            <button onClick={handleScore} disabled={isLoading} className="inline-flex items-center justify-center px-3 py-1 text-xs font-semibold rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400">{loadingAction === 'score' ? <LoadingSpinner /> : "Score Answer"}</button>
                                        </div>
                                        {score ? (
                                            <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                                                <div className="font-semibold text-slate-600 dark:text-slate-300">Overall Score:</div>
                                                <div className="font-bold text-slate-800 dark:text-slate-100">{score.overall_score.toFixed(1)} / 10</div>
                                                <div className="text-slate-500 dark:text-slate-400">Clarity:</div><div>{score.clarity.toFixed(1)}</div>
                                                <div className="text-slate-500 dark:text-slate-400">Impact:</div><div>{score.impact.toFixed(1)}</div>
                                                <div className="text-slate-500 dark:text-slate-400">Brand Alignment:</div><div>{score.brand_alignment.toFixed(1)}</div>
                                            </div>
                                        ) : (<p className="text-xs text-slate-500 mt-2">No score yet.</p>)}
                                    </div>
                                    <div className="p-4 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                                        <div className="flex justify-between items-center">
                                            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Speaker Notes</h4>
                                            <button onClick={handleGenerateNotes} disabled={isLoading} className="inline-flex items-center justify-center px-3 py-1 text-xs font-semibold rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400">{loadingAction === 'generate notes' ? <LoadingSpinner /> : "Generate"}</button>
                                        </div>
                                        <textarea
                                            value={speakerNotes}
                                            onChange={e => setSpeakerNotes(e.target.value)}
                                            rows={4}
                                            disabled={isLoading}
                                            className="mt-2 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-xs"
                                            placeholder="Enter or generate speaker notes..."
                                        />
                                    </div>
                                </div>
                                {/* Right: Chat and Quick Actions */}
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Quick AI Actions</h4>
                                        <div className="flex flex-wrap gap-2">
                                            <QuickOptionButton instruction="Make this more concise." onClick={handleChatSubmit} isLoading={isLoading} />
                                            <QuickOptionButton instruction="Rewrite this using the STAR method." onClick={handleChatSubmit} isLoading={isLoading} />
                                            <QuickOptionButton instruction="Add a specific metric related to my impact story." onClick={handleChatSubmit} isLoading={isLoading} />
                                        </div>
                                    </div>
                                    <div className="h-px bg-slate-200 dark:bg-slate-700"></div>
                                    <div className="space-y-2">
                                        <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Refinement Chat</h4>
                                        <div className="space-y-3 p-3 border rounded-lg border-slate-200 dark:border-slate-700 h-64 overflow-y-auto flex flex-col">
                                            {conversation.map((message, index) => (
                                                <div key={index} className={`flex ${message.author === 'user' ? 'justify-end' : 'justify-start'}`}>
                                                    <div className={`max-w-md p-2 rounded-lg ${message.author === 'user' ? 'bg-blue-100 dark:bg-blue-900/50' : 'bg-slate-100 dark:bg-slate-700'}`}><p className="text-sm text-slate-800 dark:text-slate-200 whitespace-pre-wrap">{message.text}</p></div>
                                                </div>
                                            ))}
                                            {isLoading && loadingAction && loadingAction !== 'score' && loadingAction !== 'generate notes' && <div className="flex justify-start"><div className="max-w-md p-2 rounded-lg bg-slate-100 dark:bg-slate-700"><LoadingSpinner /></div></div>}
                                        </div>
                                        <div className="flex gap-2">
                                            <input value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && !isLoading && handleChatSubmit(chatInput)} disabled={isLoading} placeholder="Your instruction..." className="w-full p-2 text-sm bg-white dark:bg-slate-700 rounded-md border-slate-300 dark:border-slate-600" />
                                            <button onClick={() => handleChatSubmit(chatInput)} disabled={isLoading || !chatInput} className="px-4 py-2 text-sm rounded-md bg-blue-600 text-white font-semibold disabled:bg-blue-400">{isLoading && loadingAction === chatInput ? <LoadingSpinner /> : 'Send'}</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            <button type="button" onClick={handleSave} disabled={isLoading} className="inline-flex w-full justify-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-700 sm:ml-3 sm:w-auto disabled:opacity-50">Save & Close</button>
                            <button type="button" onClick={onClose} disabled={isLoading} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto">Cancel</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
