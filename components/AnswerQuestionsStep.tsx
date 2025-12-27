import React, { useState } from 'react';
import { ApplicationQuestion } from '../types';
import { v4 as uuidv4 } from 'uuid';
import { PlusCircleIcon, TrashIcon, Square2StackIcon, LoadingSpinner } from './IconComponents';

interface AnswerQuestionsStepProps {
    questions: ApplicationQuestion[];
    setQuestions: (questions: ApplicationQuestion[] | ((prev: ApplicationQuestion[]) => ApplicationQuestion[])) => void;
    onExportForAi: (includeCoverLetter: boolean) => void;
    onSaveApplication: () => void;
    onFinishApplication: () => void;
    onBack: () => void;
    isLoading: boolean;
}

export const AnswerQuestionsStep = ({
    questions,
    setQuestions,
    onExportForAi,
    onSaveApplication,
    onFinishApplication,
    onBack,
    isLoading,
}: AnswerQuestionsStepProps): React.ReactNode => {
    const [includeCoverLetter, setIncludeCoverLetter] = useState(false);

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

    return (
        <div className="space-y-8 animate-fade-in max-w-4xl mx-auto">
            <div className="border-b border-slate-200 dark:border-slate-700 pb-5">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Prepare Application for AI</h2>
                <p className="mt-2 text-slate-600 dark:text-slate-400">Add any required application questions below. We'll bundle them with the job and company research so you can export a prompt for your Gemini Gem.</p>
            </div>

            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Application Questions</h3>
                    <button
                        type="button"
                        onClick={addQuestion}
                        className="inline-flex items-center gap-x-1.5 rounded-md bg-white dark:bg-slate-800 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700"
                    >
                        <PlusCircleIcon className="-ml-0.5 h-5 w-5 text-blue-600" />
                        Add Question
                    </button>
                </div>

                {questions.length === 0 ? (
                    <div className="text-center py-12 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl">
                        <p className="text-slate-500 dark:text-slate-400">No questions added yet. You can still export the job and company data.</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {questions.map((qa, index) => (
                            <div key={qa.id} className="group relative p-6 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-800/50 shadow-sm transition-all hover:shadow-md">
                                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button type="button" onClick={() => removeQuestion(index)} className="p-2 text-slate-400 hover:text-red-500 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
                                        <TrashIcon className="h-5 w-5" />
                                    </button>
                                </div>
                                <div className="space-y-4">
                                    <div>
                                        <label htmlFor={`question-${index}`} className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">Question {index + 1}</label>
                                        <textarea
                                            id={`question-${index}`}
                                            rows={2}
                                            value={qa.question}
                                            onChange={(e) => handleQuestionChange(index, 'question', e.target.value)}
                                            placeholder="Paste the application question here..."
                                            className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor={`thoughts-${index}`} className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">Your Context / Notes (Optional)</label>
                                        <textarea
                                            id={`thoughts-${index}`}
                                            rows={2}
                                            value={qa.user_thoughts || ''}
                                            onChange={(e) => handleQuestionChange(index, 'user_thoughts', e.target.value)}
                                            placeholder="Add specific points or experiences you want the AI to emphasize for this answer..."
                                            className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-2xl p-8 border border-blue-100 dark:border-blue-800/50">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="space-y-1">
                        <h3 className="text-xl font-bold text-blue-900 dark:text-blue-100">AI Export</h3>
                        <p className="text-blue-700 dark:text-blue-300">Bundle all application context into a single prompt for your Gemini Gem.</p>

                        <div className="flex items-center mt-4 bg-white dark:bg-slate-900/50 self-start px-4 py-2 rounded-full border border-blue-200 dark:border-blue-800 shadow-sm cursor-pointer select-none" onClick={() => setIncludeCoverLetter(!includeCoverLetter)}>
                            <input
                                id="include-cover-letter"
                                type="checkbox"
                                checked={includeCoverLetter}
                                onChange={(e) => setIncludeCoverLetter(e.target.checked)}
                                className="h-5 w-5 rounded border-blue-300 text-blue-600 focus:ring-blue-500 transition-colors"
                                onClick={(e) => e.stopPropagation()}
                            />
                            <label htmlFor="include-cover-letter" className="ml-3 text-sm font-medium text-blue-900 dark:text-blue-200 cursor-pointer">
                                Include Cover Letter Request
                            </label>
                        </div>
                    </div>

                    <button
                        type="button"
                        onClick={() => onExportForAi(includeCoverLetter)}
                        className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-8 py-4 text-lg font-bold text-white shadow-lg shadow-blue-500/30 hover:bg-blue-700 hover:-translate-y-0.5 transition-all active:translate-y-0 focus:outline-none focus:ring-4 focus:ring-blue-500/50"
                    >
                        <Square2StackIcon className="h-6 w-6" />
                        Export Data for AI
                    </button>
                </div>
            </div>

            <div className="flex items-center justify-between pt-8 border-t border-slate-200 dark:border-slate-700">
                <button
                    type="button"
                    onClick={onBack}
                    disabled={isLoading}
                    className="px-6 py-2 text-base font-semibold rounded-lg text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 shadow-sm transition-all disabled:opacity-50"
                >
                    &larr; Back
                </button>
                <div className="flex gap-4">
                    <button
                        type="button"
                        onClick={onFinishApplication}
                        className="px-6 py-2 text-base font-semibold rounded-lg text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 shadow-sm transition-all"
                    >
                        Finish & Exit
                    </button>
                    <button
                        type="button"
                        onClick={onSaveApplication}
                        disabled={isLoading}
                        className="px-6 py-2 text-base font-semibold rounded-lg text-white bg-green-600 hover:bg-green-700 shadow-lg shadow-green-500/20 transition-all active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {isLoading && <LoadingSpinner />}
                        Save & Exit
                    </button>
                </div>
            </div>
        </div>
    );
};
