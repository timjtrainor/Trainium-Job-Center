import React, { useState } from 'react';
import { InterviewStrategyState, QuestionDraft } from '../../types';
import { ChevronDownIcon, ChevronUpIcon, SparklesIcon, EyeIcon } from '../IconComponents';

// --- Shared Components ---

export const SectionHeader = ({
    title,
    description,
    icon
}: {
    title: string;
    description?: string;
    icon?: React.ReactNode
}) => (
    <div className="space-y-1">
        <div className="flex items-center gap-2">
            {icon}
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 leading-tight">{title}</h3>
        </div>
        {description && <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">{description}</p>}
    </div>
);

export const PowerVocabulary = ({ words }: { words: string[] }) => {
    if (!words || words.length === 0) return null;
    return (
        <div className="mb-6 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-100 dark:border-purple-800">
            <div className="flex items-center gap-2 mb-2 text-purple-700 dark:text-purple-300 font-semibold text-xs uppercase tracking-wider">
                <SparklesIcon className="w-4 h-4" />
                Power Vocabulary
            </div>
            <div className="flex flex-wrap gap-2">
                {words.map((word, idx) => (
                    <span key={idx} className="px-2 py-1 bg-white dark:bg-purple-900/40 text-purple-800 dark:text-purple-100 text-sm font-medium rounded shadow-sm border border-purple-100 dark:border-purple-800">
                        {word}
                    </span>
                ))}
            </div>
            <div className="mt-2 text-[10px] text-purple-500 flex items-center gap-1">
                <EyeIcon className="w-3 h-3" />
                3-Second Rule: Glance. Locate. Respond. Keep eye contact.
            </div>
        </div>
    );
};

export const QuestionCard: React.FC<{ question: QuestionDraft, isOpen: boolean, onToggle: () => void }> = ({ question, isOpen, onToggle }) => {
    return (
        <div className="mb-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-hidden shadow-sm transition-all">
            <div
                className="p-4 flex items-center justify-between cursor-pointer bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-700/50"
                onClick={onToggle}
            >
                <div className="flex-1">
                    <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">{question.framework || 'Q&A'}</div>
                    <h4 className="font-semibold text-slate-800 dark:text-slate-200 whitespace-pre-wrap">{question.question_text}</h4>
                    {question.subtitle_hint && <p className="text-xs text-slate-500 mt-1 italic whitespace-pre-wrap">{question.subtitle_hint}</p>}
                </div>
                <button
                    className="p-1 text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400"
                >
                    {isOpen ? <ChevronUpIcon className="w-5 h-5" /> : <ChevronDownIcon className="w-5 h-5" />}
                </button>
            </div>
            {isOpen && (
                <div className="p-4 border-t border-slate-100 dark:border-slate-700 bg-white dark:bg-slate-800">
                    <ul className="space-y-3">
                        {question.talking_points.map((point, idx) => (
                            <li key={idx} className="flex gap-3 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                                <span className="flex-none w-1.5 h-1.5 mt-2 rounded-full bg-indigo-500" />
                                <span className="whitespace-pre-wrap">{point}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

// --- View Components ---

export const TMAYView = ({ strategy }: { strategy: InterviewStrategyState }) => {
    const { hook, bridge, pivot } = strategy.tmay;
    return (
        <div className="max-w-3xl mx-auto p-6">
            <SectionHeader title="Tell Me About Yourself (TMAY)" />

            <div className="space-y-6">
                <div className="p-5 rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-900 border border-blue-100 dark:border-slate-700">
                    <h4 className="text-sm font-bold text-blue-800 dark:text-blue-300 uppercase mb-2">The Hook (Past/Context)</h4>
                    <p className="text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">{hook || "Draft your hook..."}</p>
                </div>

                <div className="flex justify-center -my-3 relative z-10">
                    <span className="bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-bold px-3 py-1 rounded-full">THEN</span>
                </div>

                <div className="p-5 rounded-xl bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-slate-800 dark:to-slate-900 border border-indigo-100 dark:border-slate-700">
                    <h4 className="text-sm font-bold text-indigo-800 dark:text-indigo-300 uppercase mb-2">The Bridge (Present/Success)</h4>
                    <p className="text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">{bridge || "Draft your bridge..."}</p>
                </div>

                <div className="flex justify-center -my-3 relative z-10">
                    <span className="bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-bold px-3 py-1 rounded-full">THEREFORE</span>
                </div>

                <div className="p-5 rounded-xl bg-gradient-to-br from-purple-50 to-pink-50 dark:from-slate-800 dark:to-slate-900 border border-purple-100 dark:border-slate-700">
                    <h4 className="text-sm font-bold text-purple-800 dark:text-purple-300 uppercase mb-2">The Pivot (Future/Fit)</h4>
                    <p className="text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">{pivot || "Draft your pivot..."}</p>
                </div>
            </div>
        </div>
    );
};

export const StandardQuestionView = ({
    strategy,
    type,
    vocabularyKey
}: {
    strategy: InterviewStrategyState;
    type: QuestionDraft['type'] | 'Discovery';
    vocabularyKey: string;
}) => {
    const questions = type === 'Discovery'
        ? strategy.discovery_questions.map((q, i) => ({ id: `disc-${i}`, type: 'Situational' as const, question_text: q, talking_points: [] })) // Convert string[] to QuestionDraft format for display
        : strategy.questions.filter(q => q.type === type);

    const powerVocab = strategy.power_vocabulary?.[vocabularyKey] || [];
    const [openQuestionIds, setOpenQuestionIds] = useState<Set<string>>(new Set(questions.map(q => q.id))); // All open by default or logic? User said "collapse so you can display multiple" -> maybe start closed or allow toggle. Let's start with first open.

    const toggleQuestion = (id: string) => {
        const newSet = new Set(openQuestionIds);
        if (newSet.has(id)) {
            newSet.delete(id);
        } else {
            newSet.add(id);
        }
        setOpenQuestionIds(newSet);
    };

    return (
        <div className="max-w-4xl mx-auto p-6">
            <PowerVocabulary words={powerVocab} />

            <SectionHeader title={`${type === 'Discovery' ? 'Discovery Questions (Ask Them)' : type}`} />

            {questions.length === 0 ? (
                <div className="text-center py-12 text-slate-400 italic">
                    No questions defined for this section. Go to Interview Strategy to add them.
                </div>
            ) : (
                <div className="space-y-2">
                    {questions.map((q, idx) => (
                        type === 'Discovery' ? (
                            // Simple list for Discovery questions since they are just strings usually? 
                            // Re-reading user request: "Discovery (Ask Them)" is a tab.
                            // User request: "Draft talking points in the format defined for the question or interviewer"
                            // So Discovery questions might also have talking points/rationale?
                            // For now treating as simple list based on typical usage, or reusing QuestionCard if they have details.
                            // Let's stick generic QuestionCard for consistency if possible, but map string to it.
                            <div key={idx} className="p-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm">
                                <h4 className="font-semibold text-slate-900 dark:text-white">{q.question_text}</h4>
                            </div>
                        ) : (
                            <QuestionCard
                                key={q.id}
                                question={q}
                                isOpen={openQuestionIds.has(q.id)}
                                onToggle={() => toggleQuestion(q.id)}
                            />
                        )
                    ))}
                </div>
            )}
        </div>
    );
};
