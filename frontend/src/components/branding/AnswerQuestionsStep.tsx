import React, { useEffect, useMemo, useState } from 'react';
import { ApplicationQuestion } from '../../types';
import { v4 as uuidv4 } from 'uuid';
import { LoadingSpinner, PlusCircleIcon, TrashIcon, DocumentTextIcon, LightBulbIcon } from '../shared/ui/IconComponents';

interface AnswerQuestionsStepProps {
    questions: ApplicationQuestion[];
    setQuestions: (questions: ApplicationQuestion[] | ((prev: ApplicationQuestion[]) => ApplicationQuestion[])) => void;
    onGenerateAllAnswers: () => Promise<void>;
    onSaveApplication: () => void;
    onBack: () => void;
    isLoading: boolean;
    onOpenJobDetailsModal: () => void;
    onOpenAiAnalysisModal: () => void;
    coverLetterDraft: string;
    onCoverLetterChange: (draft: string) => void;
    onGenerateCoverLetter: (options: { tone: 'confident' | 'warm' | 'bold'; hook?: string; includeHumor?: boolean }) => Promise<void> | void;
    onSaveCoverLetter: (draft: string) => Promise<void> | void;
    isGeneratingCoverLetter: boolean;
}

export const AnswerQuestionsStep = ({
    questions,
    setQuestions,
    onGenerateAllAnswers,
    onSaveApplication,
    onBack,
    isLoading,
    onOpenJobDetailsModal,
    onOpenAiAnalysisModal,
    coverLetterDraft,
    onCoverLetterChange,
    onGenerateCoverLetter,
    onSaveCoverLetter,
    isGeneratingCoverLetter,
}: AnswerQuestionsStepProps): React.ReactNode => {
    const [coverLetterHook, setCoverLetterHook] = useState('');
    const [coverLetterTone, setCoverLetterTone] = useState<'confident' | 'warm' | 'bold'>('confident');
    const [includeHumor, setIncludeHumor] = useState(true);
    const [hasCopiedCoverLetter, setHasCopiedCoverLetter] = useState(false);
    
    const handleQuestionChange = (index: number, field: keyof ApplicationQuestion, value: string) => {
        setQuestions(prev =>
            prev.map((item, i) =>
                i === index ? { ...item, [field]: value } : item
            )
        );
    };

    const addQuestion = () => {
        setQuestions(prev => [...prev, { id: uuidv4(), question: '', answer: '', user_thoughts: '' }]);
    };
    
    const removeQuestion = (index: number) => {
        setQuestions(prev => prev.filter((_, i) => i !== index));
    };

    const canSave = questions.every(q => q.question.trim() && q.answer.trim()) || questions.length === 0;

    const coverLetterWordCount = useMemo(() => {
        if (!coverLetterDraft) return 0;
        return coverLetterDraft.trim().split(/\s+/).filter(Boolean).length;
    }, [coverLetterDraft]);

    useEffect(() => {
        setHasCopiedCoverLetter(false);
    }, [coverLetterDraft]);

    const handleGenerateCoverLetterClick = async () => {
        setHasCopiedCoverLetter(false);
        await onGenerateCoverLetter({ tone: coverLetterTone, hook: coverLetterHook.trim(), includeHumor });
    };

    const handleCopyCoverLetter = async () => {
        if (!coverLetterDraft) return;
        try {
            await navigator.clipboard.writeText(coverLetterDraft);
            setHasCopiedCoverLetter(true);
            setTimeout(() => setHasCopiedCoverLetter(false), 2000);
        } catch (err) {
            console.error('Failed to copy cover letter', err);
        }
    };

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Answer Application Questions</h2>
                <p className="mt-1 text-slate-600 dark:text-slate-400">Add any required questions from the application and use the AI to help draft compelling answers for all of them at once.</p>
            </div>

            <div className="flex space-x-2">
                <button
                    type="button"
                    onClick={onOpenJobDetailsModal}
                    className="inline-flex items-center gap-x-1.5 rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600"
                >
                    <DocumentTextIcon className="h-5 w-5" />
                    View Job Details
                </button>
                <button
                    type="button"
                    onClick={onOpenAiAnalysisModal}
                    className="inline-flex items-center gap-x-1.5 rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600"
                >
                    <LightBulbIcon className="h-5 w-5" />
                    View AI Analysis
                </button>
            </div>
            
            <div className="text-center my-4">
                <button
                    type="button"
                    onClick={onGenerateAllAnswers}
                    disabled={isLoading || questions.length === 0 || !questions.some(q => q.question.trim())}
                    className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 disabled:cursor-not-allowed"
                >
                    {isLoading ? <LoadingSpinner /> : 'Generate All Answers with AI'}
                </button>
            </div>
            
            <div className="space-y-4">
                {questions.map((qa, index) => (
                    <div key={qa.id} className="relative p-4 border border-slate-300 dark:border-slate-600 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                        <div className="absolute top-2 right-2">
                             <button type="button" onClick={() => removeQuestion(index)} className="p-1 text-slate-400 hover:text-red-500 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700">
                                <TrashIcon className="h-5 w-5" />
                            </button>
                        </div>
                        <div className="space-y-3">
                             <div>
                                <label htmlFor={`question-${index}`} className="block text-sm font-medium text-slate-700 dark:text-slate-300">Question {index + 1}</label>
                                <textarea
                                    id={`question-${index}`}
                                    rows={2}
                                    value={qa.question}
                                    onChange={(e) => handleQuestionChange(index, 'question', e.target.value)}
                                    placeholder="e.g., Why are you interested in this role at our company?"
                                    className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                    disabled={isLoading}
                                />
                            </div>
                            <div>
                                <label htmlFor={`thoughts-${index}`} className="block text-sm font-medium text-slate-700 dark:text-slate-300">Your Initial Thoughts (Optional)</label>
                                <textarea
                                    id={`thoughts-${index}`}
                                    rows={3}
                                    value={qa.user_thoughts || ''}
                                    onChange={(e) => handleQuestionChange(index, 'user_thoughts', e.target.value)}
                                    placeholder="Jot down key points, experiences, or angles you want the AI to include in the answer..."
                                    className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                    disabled={isLoading}
                                />
                            </div>
                            <div>
                                 <label htmlFor={`answer-${index}`} className="block text-sm font-medium text-slate-700 dark:text-slate-300">Answer</label>
                                <textarea
                                    id={`answer-${index}`}
                                    rows={5}
                                    value={qa.answer}
                                    onChange={(e) => handleQuestionChange(index, 'answer', e.target.value)}
                                    placeholder="Enter your answer or generate one with AI."
                                    className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                    disabled={isLoading}
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-8 p-4 border border-blue-200 dark:border-blue-700 rounded-lg bg-blue-50 dark:bg-blue-900/30">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200">Advanced Cover Letter AI</h3>
                        <p className="text-sm text-blue-700 dark:text-blue-300">Generate a concise, brand-aligned cover letter without leaving this step.</p>
                    </div>
                    <button
                        type="button"
                        onClick={handleGenerateCoverLetterClick}
                        disabled={isGeneratingCoverLetter}
                        className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-400"
                    >
                        {isGeneratingCoverLetter ? <LoadingSpinner /> : 'Generate Cover Letter'}
                    </button>
                </div>

                <div className="mt-4 grid gap-4 md:grid-cols-3">
                    <div className="md:col-span-2">
                        <label htmlFor="cover-letter-hook" className="block text-sm font-medium text-blue-800 dark:text-blue-200">Optional opener or hook</label>
                        <input
                            id="cover-letter-hook"
                            type="text"
                            value={coverLetterHook}
                            onChange={(e) => setCoverLetterHook(e.target.value)}
                            placeholder="e.g., I fix broken data ecosystems and make teams trust what they ship."
                            className="mt-1 w-full rounded-md border border-blue-200 dark:border-blue-600 bg-white dark:bg-blue-950 text-sm px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
                        />
                    </div>
                    <div>
                        <label htmlFor="cover-letter-tone" className="block text-sm font-medium text-blue-800 dark:text-blue-200">Tone</label>
                        <select
                            id="cover-letter-tone"
                            value={coverLetterTone}
                            onChange={(e) => setCoverLetterTone(e.target.value as 'confident' | 'warm' | 'bold')}
                            className="mt-1 w-full rounded-md border border-blue-200 dark:border-blue-600 bg-white dark:bg-blue-950 text-sm px-3 py-2 focus:border-blue-500 focus:ring-blue-500"
                        >
                            <option value="confident">Confident</option>
                            <option value="warm">Warm</option>
                            <option value="bold">Bold</option>
                        </select>
                    </div>
                    <div className="flex items-center gap-2">
                        <input
                            id="cover-letter-humor"
                            type="checkbox"
                            checked={includeHumor}
                            onChange={(e) => setIncludeHumor(e.target.checked)}
                            className="h-4 w-4 rounded border-blue-300 text-blue-600 focus:ring-blue-500"
                        />
                        <label htmlFor="cover-letter-humor" className="text-sm text-blue-800 dark:text-blue-200">Allow light personality</label>
                    </div>
                </div>

                <div className="mt-4">
                    <label htmlFor="cover-letter-draft" className="block text-sm font-medium text-blue-800 dark:text-blue-200">Draft Cover Letter ({coverLetterWordCount} words)</label>
                    <textarea
                        id="cover-letter-draft"
                        rows={8}
                        value={coverLetterDraft}
                        onChange={(e) => onCoverLetterChange(e.target.value)}
                        placeholder="Your AI-generated cover letter will appear here."
                        className="mt-1 block w-full rounded-md border border-blue-200 dark:border-blue-600 bg-white dark:bg-blue-950 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                </div>

                <div className="mt-3 flex flex-wrap items-center gap-2">
                    <button
                        type="button"
                        onClick={handleCopyCoverLetter}
                        disabled={!coverLetterDraft}
                        className="inline-flex items-center rounded-md bg-white dark:bg-blue-950 px-3 py-1.5 text-sm font-semibold text-blue-700 dark:text-blue-200 shadow-sm ring-1 ring-inset ring-blue-200 dark:ring-blue-700 hover:bg-blue-100 dark:hover:bg-blue-900 disabled:opacity-60"
                    >
                        {hasCopiedCoverLetter ? 'Copied!' : 'Copy to Clipboard'}
                    </button>
                    <button
                        type="button"
                        onClick={() => onSaveCoverLetter(coverLetterDraft)}
                        disabled={!coverLetterDraft}
                        className="inline-flex items-center rounded-md bg-green-600 px-3 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:bg-green-400"
                    >
                        Save Cover Letter
                    </button>
                </div>
            </div>

            <div className="mt-4">
                 <button
                    type="button"
                    onClick={addQuestion}
                    className="inline-flex items-center gap-x-1.5 rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600"
                >
                    <PlusCircleIcon className="-ml-0.5 h-5 w-5" />
                    Add Another Question
                </button>
            </div>
            
             <div className="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-slate-700">
                <button
                    type="button"
                    onClick={onBack}
                    disabled={isLoading}
                    className="px-6 py-2 text-base font-medium rounded-lg text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 border border-slate-300 dark:border-slate-500 shadow-sm transition-colors disabled:opacity-50"
                >
                    &larr; Back
                </button>
                <button
                    type="button"
                    onClick={onSaveApplication}
                    disabled={isLoading || !canSave}
                    className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors disabled:bg-green-400"
                >
                    {isLoading ? <LoadingSpinner /> : 'Save & Generate Plan'}
                </button>
            </div>
        </div>
    );
};
