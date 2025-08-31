import React from 'react';
import { ApplicationQuestion } from '../types';
import { LoadingSpinner, PlusCircleIcon, TrashIcon, DocumentTextIcon, LightBulbIcon } from './IconComponents';

interface AnswerQuestionsStepProps {
    questions: ApplicationQuestion[];
    setQuestions: (questions: ApplicationQuestion[]) => void;
    onGenerateAllAnswers: () => Promise<void>;
    onSaveApplication: () => void;
    onBack: () => void;
    isLoading: boolean;
    onOpenJobDetailsModal: () => void;
    onOpenAiAnalysisModal: () => void;
}

export const AnswerQuestionsStep = ({ questions, setQuestions, onGenerateAllAnswers, onSaveApplication, onBack, isLoading, onOpenJobDetailsModal, onOpenAiAnalysisModal }: AnswerQuestionsStepProps): React.ReactNode => {
    
    const handleQuestionChange = (index: number, field: keyof ApplicationQuestion, value: string) => {
        const newQuestions = [...questions];
        (newQuestions[index] as any)[field] = value;
        setQuestions(newQuestions);
    };

    const addQuestion = () => {
        setQuestions([...questions, { question: '', answer: '', user_thoughts: '' }]);
    };
    
    const removeQuestion = (index: number) => {
        setQuestions(questions.filter((_, i) => i !== index));
    };

    const canSave = questions.every(q => q.question.trim() && q.answer.trim()) || questions.length === 0;

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
                    <div key={index} className="relative p-4 border border-slate-300 dark:border-slate-600 rounded-lg bg-slate-50 dark:bg-slate-800/50">
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