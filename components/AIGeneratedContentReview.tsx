import React, { useState } from 'react';
import { JobApplication } from '../types';
import { SparklesIcon, CheckIcon, ClipboardDocumentIcon } from './IconComponents';
import { MarkdownPreview } from './MarkdownPreview';

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

    // Safe parsing for V2 data fields
    const keywordsData = typeof application.keywords === 'string'
        ? JSON.parse(application.keywords) as any
        : application.keywords as any;

    const guidanceData = typeof application.guidance === 'string'
        ? JSON.parse(application.guidance) as any
        : application.guidance as any;

    // Robustly handle analysis data which might come as JSON strings or objects
    const analysisRaw = typeof application.job_problem_analysis_result === 'string'
        ? JSON.parse(application.job_problem_analysis_result)
        : application.job_problem_analysis_result;

    const strategicFitScore = application.strategic_fit_score ?? analysisRaw?.strategic_fit_score;

    const hasAIContent = application.application_message ||
        (application.application_questions && application.application_questions.length > 0) ||
        keywordsData || guidanceData || strategicFitScore;

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

            {/* Resume Tailoring Analysis (V2 Support) */}
            {(keywordsData || guidanceData || strategicFitScore) && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                        Resume Tailoring Analysis
                    </h3>

                    {/* Strategic Fit Score */}
                    {strategicFitScore !== undefined && (
                        <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                                    Strategic Fit Score
                                </span>
                                <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                                    {strategicFitScore.toFixed(1)}/100
                                </span>
                            </div>
                        </div>
                    )}

                    {/* Summary Guidance */}
                    {guidanceData?.summary && guidanceData.summary.length > 0 && (
                        <div className="mb-4">
                            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                                Suggested Summary Focus
                            </h4>
                            <div className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-md border border-slate-200 dark:border-slate-600">
                                <ul className="list-disc pl-5 space-y-1">
                                    {guidanceData.summary.map((item: string, idx: number) => (
                                        <li key={idx} className="text-sm text-slate-700 dark:text-slate-300">{item}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    )}

                    {/* Guidance Bullets */}
                    {guidanceData?.bullets && guidanceData.bullets.length > 0 && (
                        <div className="mb-4">
                            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                                Achievement Guidance
                            </h4>
                            <div className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-md border border-slate-200 dark:border-slate-600">
                                <ul className="list-disc pl-5 space-y-1">
                                    {guidanceData.bullets.map((item: string, idx: number) => (
                                        <li key={idx} className="text-sm text-slate-700 dark:text-slate-300">{item}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    )}

                    {/* Keywords Analysis */}
                    {keywordsData && (keywordsData.hard_keywords?.length > 0 || keywordsData.soft_keywords?.length > 0) && (
                        <div className="mb-4">
                            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                                Keyword Targeting
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {keywordsData.hard_keywords?.slice(0, 10).map((k: any, idx: number) => (
                                    <span key={`hard-${idx}`} className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 text-xs font-medium rounded-full">
                                        {k.keyword}
                                    </span>
                                ))}
                                {keywordsData.soft_keywords?.slice(0, 5).map((k: any, idx: number) => (
                                    <span key={`soft-${idx}`} className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-medium rounded-full">
                                        {k.keyword}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Strategic Alignment Hooks */}
            {application.alignment_strategy && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                        Strategic Alignment Hooks
                    </h3>
                    <div className="space-y-4">
                        {(application.alignment_strategy.alignment_strategy || []).map((item, idx) => (
                            <div key={idx} className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
                                <div className="flex justify-between items-start mb-2">
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between mb-1">
                                            <p className="font-bold text-slate-900 dark:text-white">{item.role}</p>
                                            <button
                                                onClick={() => handleCopy(item.friction_hook, `hook-${idx}`)}
                                                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                                            >
                                                {copiedField === `hook-${idx}` ? 'Copied!' : 'Copy Hook'}
                                            </button>
                                        </div>
                                        <p className="text-sm text-slate-500 dark:text-slate-400">{item.company}</p>
                                    </div>
                                </div>
                                <p className="text-sm italic text-slate-700 dark:text-slate-300 mb-3 bg-white dark:bg-slate-800 p-2 rounded border border-slate-100 dark:border-slate-700">
                                    "{item.friction_hook}"
                                </p>
                                <div className="flex flex-wrap gap-2">
                                    <span className="text-xs px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300 font-medium rounded">
                                        Pillar: {item.mapped_pillar}
                                    </span>
                                    <span className={`text-xs px-2 py-1 rounded font-medium ${item.context_type?.includes('Direct')
                                        ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                                        : 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300'
                                        }`}>
                                        Type: {item.context_type}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
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
