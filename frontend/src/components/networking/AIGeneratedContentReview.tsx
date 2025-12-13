import React, { useState } from 'react';
import { JobApplication } from '../../types';
import { SparklesIcon, CheckIcon, ClipboardDocumentIcon } from '../shared/ui/IconComponents';
import { MarkdownPreview } from '../shared/ui/MarkdownPreview';

interface AIGeneratedContentReviewProps {
    application: JobApplication;
    onAccept?: () => void;
}

export const AIGeneratedContentReview: React.FC<AIGeneratedContentReviewProps> = ({
    application,
    onAccept
}) => {
    const [copiedField, setCopiedField] = useState<string | null>(null);

    const handleCopy = (text: string, fieldName: string) => {
        navigator.clipboard.writeText(text);
        setCopiedField(fieldName);
        setTimeout(() => setCopiedField(null), 2000);
    };

    const tailoringData = application.tailored_resume_json as any;
    const hasAIContent = application.application_message ||
                        (application.application_questions && application.application_questions.length > 0) ||
                        tailoringData;

    if (!hasAIContent) {
        return (
            <div className="p-8 text-center">
                <SparklesIcon className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900 dark:text-slate-300 mb-2">
                    AI Content Generating
                </h3>
                <p className="text-slate-600 dark:text-slate-400">
                    Your AI-generated resume tailoring, application message, and answers are being created in the background.
                    This usually takes 30-60 seconds. Refresh this page to see the results.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <SparklesIcon className="h-6 w-6 text-green-500" />
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                        AI-Generated Application Content
                    </h2>
                </div>
                {onAccept && (
                    <button
                        onClick={onAccept}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-colors"
                    >
                        <CheckIcon className="h-4 w-4" />
                        Accept & Continue
                    </button>
                )}
            </div>

            {/* Application Message */}
            {application.application_message && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                            Application Message
                        </h3>
                        <button
                            onClick={() => handleCopy(application.application_message!, 'message')}
                            className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                        >
                            {copiedField === 'message' ? (
                                <>
                                    <CheckIcon className="h-4 w-4" />
                                    Copied!
                                </>
                            ) : (
                                <>
                                    <ClipboardDocumentIcon className="h-4 w-4" />
                                    Copy
                                </>
                            )}
                        </button>
                    </div>
                    <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                        {application.application_message}
                    </p>
                </div>
            )}

            {/* Resume Tailoring Summary */}
            {tailoringData && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                        Resume Tailoring Analysis
                    </h3>

                    {/* Alignment Score */}
                    {tailoringData.initial_alignment_score && (
                        <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                                    Initial Alignment Score
                                </span>
                                <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                                    {tailoringData.initial_alignment_score.toFixed(1)}/10
                                </span>
                            </div>
                        </div>
                    )}

                    {/* Summary Suggestions */}
                    {tailoringData.summary_suggestions && tailoringData.summary_suggestions.length > 0 && (
                        <div className="mb-4">
                            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                                Suggested Summary Options
                            </h4>
                            <div className="space-y-3">
                                {tailoringData.summary_suggestions.map((summary: string, idx: number) => (
                                    <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-md border border-slate-200 dark:border-slate-600">
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex-1">
                                                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                                                    Option {idx + 1}
                                                </span>
                                                <p className="text-sm text-slate-700 dark:text-slate-300 mt-1">
                                                    {summary}
                                                </p>
                                            </div>
                                            <button
                                                onClick={() => handleCopy(summary, `summary-${idx}`)}
                                                className="flex-shrink-0 text-xs text-blue-600 dark:text-blue-400 hover:underline"
                                            >
                                                {copiedField === `summary-${idx}` ? (
                                                    <CheckIcon className="h-3 w-3" />
                                                ) : (
                                                    <ClipboardDocumentIcon className="h-3 w-3" />
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* AI Selected Skills */}
                    {tailoringData.ai_selected_skills && tailoringData.ai_selected_skills.length > 0 && (
                        <div className="mb-4">
                            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                                Top Skills for This Role
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {tailoringData.ai_selected_skills.map((skill: string, idx: number) => (
                                    <span
                                        key={idx}
                                        className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 text-xs font-medium rounded-full"
                                    >
                                        {skill}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Missing Keywords */}
                    {tailoringData.missing_keywords && tailoringData.missing_keywords.length > 0 && (
                        <div className="mb-4">
                            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                                Keywords to Add
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {tailoringData.missing_keywords.map((keyword: string, idx: number) => (
                                    <span
                                        key={idx}
                                        className="px-3 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 text-xs font-medium rounded-full"
                                    >
                                        {keyword}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Guidance */}
                    {tailoringData.guidance && (
                        <div>
                            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                                Strategic Guidance
                            </h4>
                            <div className="space-y-2 text-sm">
                                {tailoringData.guidance.summary && tailoringData.guidance.summary.length > 0 && (
                                    <div className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-md">
                                        <span className="font-medium text-slate-600 dark:text-slate-400">Summary:</span>
                                        <ul className="list-disc pl-5 mt-1 space-y-1">
                                            {tailoringData.guidance.summary.map((item: string, idx: number) => (
                                                <li key={idx} className="text-slate-700 dark:text-slate-300">{item}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {tailoringData.guidance.bullets && tailoringData.guidance.bullets.length > 0 && (
                                    <div className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-md">
                                        <span className="font-medium text-slate-600 dark:text-slate-400">Bullets:</span>
                                        <ul className="list-disc pl-5 mt-1 space-y-1">
                                            {tailoringData.guidance.bullets.map((item: string, idx: number) => (
                                                <li key={idx} className="text-slate-700 dark:text-slate-300">{item}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Application Questions & Answers */}
            {application.application_questions && application.application_questions.length > 0 && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                        Application Questions & Answers
                    </h3>
                    <div className="space-y-4">
                        {application.application_questions.map((qa: any, idx: number) => (
                            <div key={idx} className="border-b border-slate-200 dark:border-slate-700 pb-4 last:border-0 last:pb-0">
                                <div className="flex items-start justify-between gap-2 mb-2">
                                    <p className="font-medium text-slate-900 dark:text-white">
                                        {qa.question}
                                    </p>
                                    <button
                                        onClick={() => handleCopy(qa.answer, `qa-${idx}`)}
                                        className="flex-shrink-0 text-xs text-blue-600 dark:text-blue-400 hover:underline"
                                    >
                                        {copiedField === `qa-${idx}` ? (
                                            <CheckIcon className="h-3 w-3" />
                                        ) : (
                                            <ClipboardDocumentIcon className="h-3 w-3" />
                                        )}
                                    </button>
                                </div>
                                <p className="text-sm text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-700/50 p-3 rounded-md">
                                    {qa.answer}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
