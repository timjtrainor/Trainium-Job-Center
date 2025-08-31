import React, { useState, useEffect } from 'react';
import { JobApplication, Interview, Company, StrategicNarrative, Prompt, ConsultativeClosePlan, StrategicHypothesisDraft, InterviewPayload } from '../types';
import { LoadingSpinner, SparklesIcon, ClipboardDocumentCheckIcon, CheckIcon } from './IconComponents';

interface InterviewStrategyStudioProps {
    application: JobApplication;
    interview: Interview;
    company: Company;
    activeNarrative: StrategicNarrative;
    prompts: Prompt[];
    onBack: () => void;
    onGenerate: (app: JobApplication, interview: Interview, hypothesis: any) => Promise<void>;
    isLoading: boolean;
    strategicHypothesisDraft: StrategicHypothesisDraft | null;
    onSavePlan: (payload: InterviewPayload, interviewId: string) => Promise<void>;
}

const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";
const textareaClass = "mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm font-sans";

const PlanSection = ({ title, theme, goals }: { title: string, theme: string, goals: string[] }) => (
    <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
        <h4 className="font-bold text-slate-800 dark:text-slate-200">{title}</h4>
        <p className="text-sm font-semibold text-blue-600 dark:text-blue-400 italic">Theme: {theme}</p>
        <ul className="mt-2 list-disc pl-5 space-y-1 text-sm text-slate-600 dark:text-slate-300">
            {(goals || []).map((goal, i) => <li key={i}>{goal}</li>)}
        </ul>
    </div>
);

export const InterviewStrategyStudio = (props: InterviewStrategyStudioProps) => {
    const { application, interview, company, activeNarrative, prompts, onBack, onGenerate, isLoading, strategicHypothesisDraft, onSavePlan } = props;

    const [hypothesis, setHypothesis] = useState({
        problem: '',
        evidence: '',
        angle: '',
        outcome: ''
    });
    
    const [editableEmail, setEditableEmail] = useState('');
    const [isSavingEmail, setIsSavingEmail] = useState(false);
    const [copySuccess, setCopySuccess] = useState(false);
    
    useEffect(() => {
        if (strategicHypothesisDraft) {
            setHypothesis({
                problem: strategicHypothesisDraft.problem || '',
                evidence: strategicHypothesisDraft.evidence || '',
                angle: strategicHypothesisDraft.angle || '',
                outcome: strategicHypothesisDraft.outcome || ''
            });
        }
        if (interview.strategic_plan) {
            setEditableEmail(interview.strategic_plan.briefing_email_draft.replace(/\\n/g, '\n'));
        }
    }, [strategicHypothesisDraft, interview.strategic_plan]);

    const handleHypothesisChange = (field: keyof typeof hypothesis, value: string) => {
        setHypothesis(prev => ({ ...prev, [field]: value }));
    };

    const handleGenerate = () => {
        onGenerate(application, interview, hypothesis);
    };

    const handleSaveEmail = async () => {
        if (!interview.strategic_plan) return;
        setIsSavingEmail(true);
        try {
            const updatedPlan = {
                ...interview.strategic_plan,
                briefing_email_draft: editableEmail
            };
            await onSavePlan({ strategic_plan: updatedPlan }, interview.interview_id);
        } catch(e) {
            console.error("Failed to save email", e);
        } finally {
            setIsSavingEmail(false);
        }
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(editableEmail);
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 2000);
    };

    const canGenerate = hypothesis.problem && hypothesis.evidence && hypothesis.angle && hypothesis.outcome;
    const plan = interview.strategic_plan;

    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700 animate-fade-in">
            <header className="mb-6 flex justify-between items-start">
                <div>
                    <button onClick={onBack} className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 mb-2">
                        &larr; Back to Application
                    </button>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Consultative Close Strategy Studio</h2>
                    <p className="text-lg text-slate-600 dark:text-slate-300">
                        For: {interview.interview_type} with {company.company_name}
                    </p>
                </div>
            </header>
            
            {isLoading && !plan ? (
                <div className="flex flex-col items-center justify-center p-12">
                    <LoadingSpinner />
                    <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Generating your strategic plan...</p>
                </div>
            ) : plan ? (
                <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                            <PlanSection title="30-Day Plan" theme={plan.thirty_day_plan.theme} goals={plan.thirty_day_plan.goals} />
                            <PlanSection title="60-Day Plan" theme={plan.sixty_day_plan.theme} goals={plan.sixty_day_plan.goals} />
                            <PlanSection title="90-Day Plan" theme={plan.ninety_day_plan.theme} goals={plan.ninety_day_plan.goals} />
                        </div>
                        <div className="space-y-4">
                            <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
                                <h4 className="font-bold text-slate-800 dark:text-slate-200">Key Talking Points</h4>
                                <ul className="mt-2 list-disc pl-5 space-y-1 text-sm text-slate-600 dark:text-slate-300">
                                    {plan.key_talking_points.map((point, i) => <li key={i}>{point}</li>)}
                                </ul>
                            </div>
                             <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
                                <div className="flex justify-between items-center">
                                    <h4 className="font-bold text-slate-800 dark:text-slate-200">Pre-Interview Briefing Email</h4>
                                    <div className="flex items-center gap-x-2">
                                        <button onClick={handleSaveEmail} disabled={isSavingEmail} className="inline-flex items-center gap-x-1 rounded-md bg-white dark:bg-slate-700 px-2 py-1 text-xs font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600 disabled:opacity-50">
                                            {isSavingEmail ? <LoadingSpinner/> : 'Save Email'}
                                        </button>
                                        <button onClick={handleCopy} className="inline-flex items-center gap-x-1 rounded-md bg-white dark:bg-slate-700 px-2 py-1 text-xs font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600">
                                            {copySuccess ? <CheckIcon className="h-4 w-4 text-green-500" /> : <ClipboardDocumentCheckIcon className="h-4 w-4" />}
                                            {copySuccess ? 'Copied!' : 'Copy'}
                                        </button>
                                    </div>
                                </div>
                                <textarea
                                    value={editableEmail}
                                    onChange={(e) => setEditableEmail(e.target.value)}
                                    rows={8}
                                    className={`${textareaClass} mt-2 bg-white dark:bg-slate-800`}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-6">
                        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700/50">
                            <h3 className="font-semibold text-blue-800 dark:text-blue-200">Problem-Solving Framework</h3>
                            <p className="text-sm mt-1 text-blue-700 dark:text-blue-300">Articulate your hypothesis. The AI has provided a first draft based on its analysis.</p>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label htmlFor="problem" className={labelClass}>The Assumed Core Problem</label>
                                <textarea id="problem" value={hypothesis.problem} onChange={e => handleHypothesisChange('problem', e.target.value)} rows={3} className={textareaClass} placeholder="e.g., New user churn is high because the product's value is not realized in the first session." />
                            </div>
                            <div>
                                <label htmlFor="evidence" className={labelClass}>Key Evidence (from JD/Research)</label>
                                <textarea id="evidence" value={hypothesis.evidence} onChange={e => handleHypothesisChange('evidence', e.target.value)} rows={3} className={textareaClass} placeholder="e.g., JD mentions 'improving onboarding' 3 times."/>
                            </div>
                            <div>
                                <label htmlFor="angle" className={labelClass}>My Unique Angle (Your Differentiator)</label>
                                <textarea id="angle" value={hypothesis.angle} onChange={e => handleHypothesisChange('angle', e.target.value)} rows={3} className={textareaClass} placeholder={`e.g., My mastery is in '${activeNarrative.signature_capability}'. I can apply this by...`}/>
                            </div>
                            <div>
                                <label htmlFor="outcome" className={labelClass}>The "Hot Lead" (The Desired Outcome)</label>
                                <textarea id="outcome" value={hypothesis.outcome} onChange={e => handleHypothesisChange('outcome', e.target.value)} rows={3} className={textareaClass} placeholder="e.g., My goal is to deliver a measurable 15% reduction in 30-day churn within the first 90 days."/>
                            </div>
                        </div>
                        <div className="flex justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
                            <button onClick={handleGenerate} disabled={isLoading || !canGenerate} className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed">
                                {isLoading ? <LoadingSpinner/> : <SparklesIcon className="h-5 w-5" />}
                                Generate 30-60-90 Day Plan
                            </button>
                        </div>
                    </div>
                    <div className="lg:col-span-1">
                        <div className="sticky top-8 space-y-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
                             <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Intelligence Dossier</h3>
                             <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
                                 <div>
                                     <p className="font-bold text-slate-500 dark:text-slate-400">Core Problem</p>
                                     <p className="mt-1">{application.job_problem_analysis_result?.core_problem_analysis.core_problem || 'N/A'}</p>
                                 </div>
                                  <div>
                                     <p className="font-bold text-slate-500 dark:text-slate-400">Key Success Metrics</p>
                                     <ul className="list-disc pl-4 mt-1">{(application.job_problem_analysis_result?.key_success_metrics || []).map((m,i)=><li key={i}>{m}</li>)}</ul>
                                 </div>
                                  <div>
                                     <p className="font-bold text-slate-500 dark:text-slate-400">Company Mission</p>
                                     <p className="mt-1">{company.mission?.text || 'N/A'}</p>
                                 </div>
                                 <div>
                                     <p className="font-bold text-slate-500 dark:text-slate-400">Company Stated Goals</p>
                                     <p className="mt-1">{company.goals?.text || 'N/A'}</p>
                                 </div>
                                  <div>
                                     <p className="font-bold text-slate-500 dark:text-slate-400">Company Challenges</p>
                                     <p className="mt-1">{company.issues?.text || 'N/A'}</p>
                                 </div>
                             </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};