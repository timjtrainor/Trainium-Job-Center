import React, { useState, useEffect } from 'react';
import { BuyerType, CommunicationStyle, InterviewStrategyState, PersonaDefinition, QuestionDraft, TMAYConfig, Interview, JobApplication } from '../../types';
import { SectionHeader } from './CommandCenterViews';
import { PlusIcon, TrashIcon, UserIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { CheckIcon } from '../IconComponents';
import { generatePersonaDefinition, generateTMAY, generateInterviewQuestions, generateTalkingPoints } from '../../services/apiService';

// Placeholder for a loading spinner component
const LoadingSpinner = ({ className }: { className: string }) => (
    <svg className={`animate-spin ${className} text-indigo-500`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
);

const BUYER_TYPES: BuyerType[] = ['Recruiter', 'Hiring Manager', 'Technical Buyer', 'Peer', 'Executive'];
const COMM_STYLES: CommunicationStyle[] = ['Unknown', 'Driver', 'Analytical', 'Expressive', 'Amiable'];
const QUESTION_TYPES: QuestionDraft['type'][] = ['Behavioral', 'Technical Depth', 'Situational', 'Strategy Case', 'Leadership'];

export const InterviewStrategyView = ({
    strategy,
    application,
    onChange
}: {
    strategy: InterviewStrategyState;
    application: JobApplication;
    onChange: (state: InterviewStrategyState) => void;
}) => {

    const [isAIUpdating, setIsAIUpdating] = useState(false);
    const [isTMAYUpdating, setIsTMAYUpdating] = useState(false);
    const [isQuestionsUpdating, setIsQuestionsUpdating] = useState(false);
    const [talkingPointsUpdating, setTalkingPointsUpdating] = useState<Record<string, boolean>>({});
    const [showOverwriteWarning, setShowOverwriteWarning] = useState(false);

    // Initial default if missing
    useEffect(() => {
        if (strategy?.persona && !strategy.persona.communication_style) {
            onChange({
                ...strategy,
                persona: {
                    ...strategy.persona,
                    communication_style: 'Unknown'
                }
            });
        }
    }, [strategy?.persona?.communication_style]);

    const handlePersonaChange = (field: keyof PersonaDefinition, value: any) => {
        onChange({
            ...strategy,
            persona: {
                ...strategy.persona,
                [field]: value
            }
        });
    };

    const handleRunAI = async () => {
        setIsAIUpdating(true);
        setShowOverwriteWarning(false);

        try {
            const buyerType = strategy.persona.buyer_type;
            const interviewerTitle = strategy.persona.interviewer_title || "Interviewer Job Title";
            const interviewerAbout = strategy.persona.interviewer_linkedin_about || "Extracted from LinkedIn profile...";
            const jdAnalysis = application.ai_summary || application.job_description.substring(0, 200);
            const alignment = application.why_this_job || "";

            // Consolidate Previous Interview Context
            const previousInterviews = application.interviews || [];
            const previousContext = previousInterviews
                .map(int => {
                    const type = int.interview_type;
                    const date = int.interview_date ? ` on ${int.interview_date}` : '';
                    const notes = int.live_notes || '';
                    const debrief = int.post_interview_debrief ?
                        `Wins: ${int.post_interview_debrief.performance_analysis.wins.join(', ')}. Fumbles: ${int.post_interview_debrief.performance_analysis.areas_for_improvement.join(', ')}` : '';
                    return `[${type}${date}] Notes: ${notes}. ${debrief}`;
                })
                .join('\n---\n');

            const aiResponse = await generatePersonaDefinition(
                buyerType,
                interviewerTitle,
                interviewerAbout,
                jdAnalysis,
                alignment,
                application.interview_strategy,
                previousContext
            );

            onChange({
                ...strategy,
                persona: {
                    ...strategy.persona,
                    primary_anxiety: aiResponse.primary_anxiety,
                    win_condition: aiResponse.win_condition,
                    functional_friction_point: aiResponse.functional_friction_point,
                    mirroring_style: aiResponse.mirroring_style
                }
            });
        } catch (error) {
            console.error(error);
        } finally {
            setIsAIUpdating(false);
        }
    };

    const handleRunAITMAY = async () => {
        setIsTMAYUpdating(true);
        try {
            const persona = strategy.persona;
            const alignment = application.why_this_job || JSON.stringify(application.interview_strategy || {});
            const dna = application.resume_summary || "";

            const aiResponse = await generateTMAY(
                persona.primary_anxiety,
                persona.win_condition,
                persona.functional_friction_point,
                persona.mirroring_style,
                alignment,
                dna
            );

            onChange({
                ...strategy,
                tmay: {
                    hook: aiResponse.hook,
                    bridge: aiResponse.bridge,
                    pivot: aiResponse.pivot
                }
            });
        } catch (error) {
            console.error(error);
        } finally {
            setIsTMAYUpdating(false);
        }
    };

    const enhanceWithAIClick = () => {
        const { primary_anxiety, win_condition, functional_friction_point, mirroring_style } = strategy.persona;
        if (primary_anxiety || win_condition || functional_friction_point || mirroring_style) {
            setShowOverwriteWarning(true);
        } else {
            handleRunAI();
        }
    };

    const updateTMAY = (field: keyof TMAYConfig, value: string) => {
        onChange({
            ...strategy,
            tmay: { ...strategy.tmay, [field]: value }
        });
    };

    const addQuestion = () => {
        const newQuestion: QuestionDraft = {
            id: `q-${Date.now()}`,
            type: 'Behavioral',
            question_text: '',
            talking_points: [''],
            framework: 'STAR'
        };
        onChange({
            ...strategy,
            questions: [...strategy.questions, newQuestion]
        });
    };

    const updateQuestion = (id: string, updates: Partial<QuestionDraft>) => {
        onChange({
            ...strategy,
            questions: strategy.questions.map(q => q.id === id ? { ...q, ...updates } : q)
        });
    };

    const removeQuestion = (id: string) => {
        onChange({
            ...strategy,
            questions: strategy.questions.filter(q => q.id !== id)
        });
    };

    const updateDiscoveryQuestion = (index: number, value: string) => {
        const newDiscovery = [...strategy.discovery_questions];
        newDiscovery[index] = value;
        onChange({ ...strategy, discovery_questions: newDiscovery });
    };

    const addDiscoveryQuestion = () => {
        onChange({
            ...strategy,
            discovery_questions: [...strategy.discovery_questions, '']
        });
    };

    const removeDiscoveryQuestion = (index: number) => {
        onChange({
            ...strategy,
            discovery_questions: strategy.discovery_questions.filter((_, i) => i !== index)
        });
    };

    const handleRunAIQuestions = async () => {
        setIsQuestionsUpdating(true);
        try {
            const persona = strategy.persona;
            const buyerType = persona.buyer_type;
            const interviewerTitle = persona.interviewer_title || "";
            const interviewerLinkedin = persona.interviewer_linkedin_about || "";
            const alignmentStrategy = JSON.stringify(application.interview_strategy || {});
            const jdAnalysis = application.ai_summary || application.job_description.substring(0, 500);

            const aiResponse = await generateInterviewQuestions(
                buyerType,
                interviewerTitle,
                interviewerLinkedin,
                alignmentStrategy,
                jdAnalysis
            );

            // Add new questions to the existing ones
            const newQuestions: QuestionDraft[] = aiResponse.questions.map(q => ({
                ...q,
                id: `ai-q-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                talking_points: q.talking_points || ['']
            }));

            onChange({
                ...strategy,
                questions: [...strategy.questions, ...newQuestions]
            });
        } catch (error) {
            console.error('Failed to generate questions:', error);
        } finally {
            setIsQuestionsUpdating(false);
        }
    };

    const handleRunAITalkingPoints = async (questionId: string) => {
        const question = strategy.questions.find(q => q.id === questionId);
        if (!question) return;

        setTalkingPointsUpdating(prev => ({ ...prev, [questionId]: true }));
        try {
            const persona = strategy.persona;
            const dna = application.resume_summary || "";

            const aiResponse = await generateTalkingPoints(
                question.question_text,
                question.framework || "STAR",
                JSON.stringify(persona),
                dna
            );

            onChange({
                ...strategy,
                questions: strategy.questions.map(q =>
                    q.id === questionId
                        ? { ...q, talking_points: aiResponse.talking_points }
                        : q
                )
            });
        } catch (error) {
            console.error('Failed to generate talking points:', error);
        } finally {
            setTalkingPointsUpdating(prev => ({ ...prev, [questionId]: false }));
        }
    };

    return (
        <div className="p-6 space-y-12 max-w-4xl mx-auto pb-32">

            {/* Warning Modal */}
            {showOverwriteWarning && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="bg-white dark:bg-slate-800 rounded-lg p-6 max-w-md shadow-xl border border-slate-200 dark:border-slate-700">
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Overwrite Existing Data?</h3>
                        <p className="text-sm text-slate-600 dark:text-slate-300 mb-6">
                            Running AI analysis will verify and potentially replace your current Anxiety, Win Condition, and Friction Point definitions.
                        </p>
                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setShowOverwriteWarning(false)}
                                className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleRunAI}
                                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
                            >
                                Overwrite & Update
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Persona Definition */}
            <section className="space-y-6">
                <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 pb-4">
                    <SectionHeader
                        title="Persona Definition"
                        description="Who are you talking to? Define their psychology to maximize influence."
                        icon={<UserIcon className="w-5 h-5 text-indigo-500" />}
                    />
                    <button
                        onClick={enhanceWithAIClick}
                        disabled={isAIUpdating}
                        className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-800 transition-colors"
                    >
                        {isAIUpdating ? <LoadingSpinner className="w-3 h-3" /> : <SparklesIcon className="w-3 h-3" />}
                        Auto-Profile with AI
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Must-Haves */}
                    <div className="space-y-4">
                        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Must-Have Definitions</h3>

                        <div className="space-y-1">
                            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Buyer Type</label>
                            <div className="flex flex-wrap gap-2">
                                {BUYER_TYPES.map(type => (
                                    <button
                                        key={type}
                                        onClick={() => handlePersonaChange('buyer_type', type)}
                                        className={`px-3 py-1 text-xs rounded-full border transition-all ${(strategy?.persona?.buyer_type || 'Recruiter') === type
                                            ? 'bg-indigo-600 text-white border-indigo-600'
                                            : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-indigo-400'
                                            }`}
                                    >
                                        {type}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Primary Anxiety</label>
                            <textarea
                                value={strategy.persona.primary_anxiety}
                                onChange={(e) => handlePersonaChange('primary_anxiety', e.target.value)}
                                className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-800 focus:ring-indigo-500 focus:border-indigo-500 min-h-[80px]"
                                placeholder="What keeps them up at night regarding this hire?"
                            />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Interviewer Job Title</label>
                                <input
                                    type="text"
                                    value={strategy.persona.interviewer_title || ''}
                                    onChange={(e) => handlePersonaChange('interviewer_title', e.target.value)}
                                    className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-800 focus:ring-indigo-500 focus:border-indigo-500"
                                    placeholder="e.g. VP of Engineering"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Interviewer LinkedIn About</label>
                                <input
                                    type="text"
                                    value={strategy.persona.interviewer_linkedin_about || ''}
                                    onChange={(e) => handlePersonaChange('interviewer_linkedin_about', e.target.value)}
                                    className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-800 focus:ring-indigo-500 focus:border-indigo-500"
                                    placeholder="Paste LinkedIn bio/summary..."
                                />
                            </div>
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Win Condition</label>
                            <textarea
                                value={strategy.persona.win_condition}
                                onChange={(e) => handlePersonaChange('win_condition', e.target.value)}
                                className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-800 focus:ring-indigo-500 focus:border-indigo-500 min-h-[80px]"
                                placeholder="What is their personal 'win' if this hire succeeds?"
                            />
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Functional Friction Point</label>
                            <textarea
                                value={strategy.persona.functional_friction_point}
                                onChange={(e) => handlePersonaChange('functional_friction_point', e.target.value)}
                                className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-800 focus:ring-indigo-500 focus:border-indigo-500 min-h-[80px]"
                                placeholder="Where will they scrutinize the most?"
                            />
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Mirroring Style (Suggested Tone)</label>
                            <textarea
                                value={strategy.persona.mirroring_style || ''}
                                onChange={(e) => handlePersonaChange('mirroring_style', e.target.value)}
                                className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-800 focus:ring-indigo-500 focus:border-indigo-500 min-h-[60px]"
                                placeholder="How should you match their energy? (e.g., Carnegie-style rapport)"
                            />
                        </div>
                    </div>

                    {/* Could-Haves */}
                    <div className="space-y-4">
                        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Could-Have Signals</h3>
                        <div className="space-y-1">
                            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Communication Style</label>
                            <div className="flex flex-wrap gap-2">
                                {COMM_STYLES.map(style => (
                                    <button
                                        key={style}
                                        onClick={() => handlePersonaChange('communication_style', style)}
                                        className={`px-3 py-1 text-xs rounded-full border transition-all ${(strategy.persona.communication_style || 'Unknown') === style
                                            ? 'bg-emerald-600 text-white border-emerald-600'
                                            : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-emerald-400'
                                            }`}
                                    >
                                        {style}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Professional Pedigree</label>
                            <input
                                type="text"
                                value={strategy.persona.professional_pedigree || ''}
                                onChange={(e) => handlePersonaChange('professional_pedigree', e.target.value)}
                                className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-800 focus:ring-indigo-500 focus:border-indigo-500"
                                placeholder="Ex-Google, Startup Founder, etc."
                            />
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Objection Triggers</label>
                            <input
                                type="text"
                                value={strategy.persona.objection_triggers ? strategy.persona.objection_triggers.join(', ') : ''}
                                onChange={(e) => handlePersonaChange('objection_triggers', (e.target.value || '').split(',').map(s => s.trim()))}
                                className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-800 focus:ring-indigo-500 focus:border-indigo-500"
                                placeholder="Comma separated triggers (e.g. Job hoping, Non-technical background)"
                            />
                        </div>

                        <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-100 dark:border-slate-700 text-xs text-slate-500">
                            <p><strong>Tip:</strong> Use the "Auto-Profile with AI" button to analyse the Job Description and your LinkedIn research to automatically populate the Must-Have definitions.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* TMAY Section */}
            <section className="space-y-6">
                <div className="flex items-center justify-between">
                    <SectionHeader
                        title="Tell Me About Yourself (TMAY)"
                        description="The most important 2 minutes. Draft your high-impact script."
                    />
                    <button
                        onClick={handleRunAITMAY}
                        disabled={isTMAYUpdating}
                        className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 disabled:opacity-50 rounded-lg transition-colors border border-indigo-100"
                    >
                        {isTMAYUpdating ? (
                            <LoadingSpinner className="w-3 h-3" />
                        ) : (
                            <SparklesIcon className="w-3 h-3" />
                        )}
                        Auto-Generate TMAY
                    </button>
                </div>
                <div className="grid grid-cols-1 gap-6">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">The Hook (Past / Personal Narrative)</label>
                        <textarea
                            value={strategy?.tmay?.hook || ''}
                            onChange={(e) => updateTMAY('hook', e.target.value)}
                            className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-800 min-h-[100px]"
                            placeholder="Connect your background to the role's mission..."
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">The Bridge (Present / Tangible Wins)</label>
                        <textarea
                            value={strategy?.tmay?.bridge || ''}
                            onChange={(e) => updateTMAY('bridge', e.target.value)}
                            className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-800 min-h-[100px]"
                            placeholder="Explain why you are uniquely qualified based on recent successes..."
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">The Pivot (Future / Why This Job)</label>
                        <textarea
                            value={strategy?.tmay?.pivot || ''}
                            onChange={(e) => updateTMAY('pivot', e.target.value)}
                            className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-800 min-h-[100px]"
                            placeholder="Why this company and why now?"
                        />
                    </div>
                </div>
            </section>

            {/* Question Drafts Section */}
            <section className="space-y-6">
                <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 pb-4">
                    <SectionHeader
                        title="Question Bank & Talking Points"
                        description="Define the specific questions you anticipate and your strategic responses."
                    />
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleRunAIQuestions}
                            disabled={isQuestionsUpdating}
                            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 disabled:opacity-50 rounded-lg transition-colors border border-indigo-100"
                        >
                            {isQuestionsUpdating ? (
                                <LoadingSpinner className="w-3 h-3" />
                            ) : (
                                <SparklesIcon className="w-3 h-3" />
                            )}
                            Auto-Generate Questions
                        </button>
                        <button
                            onClick={addQuestion}
                            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800 transition-colors"
                        >
                            <PlusIcon className="w-3 h-3" />
                            Add Question
                        </button>
                    </div>
                </div>

                <div className="space-y-4">
                    {(strategy?.questions || []).map((q, idx) => (
                        <div key={q.id} className="p-6 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm space-y-4 relative group">
                            <button
                                onClick={() => removeQuestion(q.id)}
                                className="absolute top-4 right-4 text-slate-400 hover:text-red-500 transition-colors"
                            >
                                <TrashIcon className="w-4 h-4" />
                            </button>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-slate-500 uppercase">Question Category</label>
                                    <select
                                        value={q.type}
                                        onChange={(e) => updateQuestion(q.id, { type: e.target.value as QuestionDraft['type'] })}
                                        className="w-full p-1 text-xs border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 rounded"
                                    >
                                        {QUESTION_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                                    </select>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-slate-500 uppercase">Framework / Logic</label>
                                    <input
                                        type="text"
                                        value={q.framework || ''}
                                        onChange={(e) => updateQuestion(q.id, { framework: e.target.value })}
                                        className="w-full p-1 text-xs border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 rounded"
                                        placeholder="STAR, PREP, etc."
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-slate-500 uppercase">Subtitle Hint</label>
                                    <input
                                        type="text"
                                        value={q.subtitle_hint || ''}
                                        onChange={(e) => updateQuestion(q.id, { subtitle_hint: e.target.value })}
                                        className="w-full p-1 text-xs border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 rounded"
                                        placeholder="Short hint (e.g. Talk about the Q3 reorg)"
                                    />
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase leading-none">The Question</label>
                                <textarea
                                    value={q.question_text}
                                    onChange={(e) => updateQuestion(q.id, { question_text: e.target.value })}
                                    className="w-full text-sm font-semibold border-none focus:ring-0 p-0 bg-transparent resize-none min-h-[40px]"
                                    placeholder="Enter the anticipated question..."
                                    rows={2}
                                />
                            </div>

                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <label className="text-xs font-bold text-slate-500 uppercase tracking-tighter">Strategic Talking Points (Bullets)</label>
                                    <button
                                        onClick={() => handleRunAITalkingPoints(q.id)}
                                        disabled={talkingPointsUpdating[q.id]}
                                        className="flex items-center gap-1.5 px-2 py-1 text-[10px] font-semibold text-indigo-600 hover:text-indigo-700 disabled:opacity-50 transition-colors"
                                    >
                                        {talkingPointsUpdating[q.id] ? (
                                            <LoadingSpinner className="w-2.5 h-2.5" />
                                        ) : (
                                            <SparklesIcon className="w-2.5 h-2.5" />
                                        )}
                                        Build Talking Points with AI
                                    </button>
                                </div>
                                <textarea
                                    value={q.talking_points.join('\n')}
                                    onChange={(e) => updateQuestion(q.id, { talking_points: e.target.value.split('\n') })}
                                    className="w-full text-sm border-slate-200 dark:border-slate-700 dark:bg-slate-900 rounded-md min-h-[100px]"
                                    placeholder="One bullet per line..."
                                />
                            </div>
                        </div>
                    ))}

                    {strategy.questions.length === 0 && (
                        <div className="text-center py-12 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl text-slate-400 italic">
                            No questions added yet. Click "Add Question" to start building your bank.
                        </div>
                    )}
                </div>
            </section>

            {/* Discovery Questions Section */}
            <section className="space-y-6">
                <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 pb-4">
                    <SectionHeader
                        title="Discovery (Ask Them)"
                        description="Great candidates lead with curiosity. Draft the questions you want to ask them."
                    />
                    <button
                        onClick={addDiscoveryQuestion}
                        className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-800 transition-colors"
                    >
                        <PlusIcon className="w-3 h-3" />
                        Add Question
                    </button>
                </div>

                <div className="grid grid-cols-1 gap-3">
                    {(strategy?.discovery_questions || []).map((q, idx) => (
                        <div key={idx} className="flex items-center gap-3">
                            <textarea
                                value={q}
                                onChange={(e) => updateDiscoveryQuestion(idx, e.target.value)}
                                className="flex-1 text-sm rounded-md border-slate-200 dark:border-slate-700 dark:bg-slate-800 py-2 resize-none min-h-[60px]"
                                placeholder="e.g. How does the product team prioritize requests from engineering?"
                            />
                            <button
                                onClick={() => removeDiscoveryQuestion(idx)}
                                className="text-slate-400 hover:text-red-500 transition-colors"
                            >
                                <TrashIcon className="w-4 h-4" />
                            </button>
                        </div>
                    ))}
                    {strategy.discovery_questions.length === 0 && (
                        <div className="text-center py-8 text-slate-400 italic text-sm">
                            Add discovery questions to lead the second half of the interview.
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
};
