import React, { useState, useEffect, useMemo } from 'react';
import { JobApplication, Interview, Company, StrategicNarrative } from '../types';
import { LoadingSpinner, SparklesIcon } from './IconComponents';

interface PostInterviewDebriefStudioProps {
    application: JobApplication;
    interview: Interview;
    company: Company;
    activeNarrative: StrategicNarrative;
    onBack: () => void;
    onGenerate: (interview: Interview, notes: { wins: string, fumbles: string, new_intelligence: string }) => Promise<void>;
    isLoading: boolean;
}

const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";
const textareaClass = "mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm font-sans";

export const PostInterviewDebriefStudio = (props: PostInterviewDebriefStudioProps) => {
    const { application, interview, company, activeNarrative, onBack, onGenerate, isLoading } = props;

    const [notes, setNotes] = useState({
        wins: '',
        fumbles: '',
        new_intelligence: ''
    });

    useEffect(() => {
        // Pre-fill the "new_intelligence" field from the copilot notes for this interview.
        // The user can then organize these thoughts into wins/fumbles.
        if (interview.notes) {
            setNotes(prev => ({
                ...prev,
                new_intelligence: interview.notes || ''
            }));
        }
    }, [interview]);

    const previousInterviewContext = useMemo(() => {
        if (!application.interviews || application.interviews.length <= 1) {
            return null;
        }

        const previousInterviews = application.interviews
            .filter(i => i.interview_id !== interview.interview_id && i.interview_date && interview.interview_date && i.interview_date < interview.interview_date)
            .sort((a, b) => new Date(a.interview_date!).getTime() - new Date(b.interview_date!).getTime());
        
        if (previousInterviews.length === 0) return null;

        return previousInterviews.map(i => {
            const debrief = i.post_interview_debrief;
            const interviewerNames = i.interview_contacts?.map(c => `${c.first_name} ${c.last_name}`).join(', ') || 'Interview';
            let summary = `Context from ${i.interview_type} with ${interviewerNames}:\n`;
            if (debrief) {
                summary += `  - Wins: ${debrief.performance_analysis.wins.join(', ')}\n`;
                summary += `  - Fumbles: ${debrief.performance_analysis.areas_for_improvement.join(', ')}\n`;
            }
            if (i.notes) {
                summary += `  - Raw Notes/Intelligence: ${i.notes.substring(0, 150)}...\n`;
            }
            return summary;
        }).join('\n');
    }, [application.interviews, interview.interview_id]);


    const handleNoteChange = (field: keyof typeof notes, value: string) => {
        setNotes(prev => ({ ...prev, [field]: value }));
    };

    const handleGenerate = () => {
        onGenerate(interview, notes);
    };

    const debrief = interview.post_interview_debrief;
    const canGenerate = notes.wins.trim() && notes.fumbles.trim() && notes.new_intelligence.trim();

    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700 animate-fade-in">
            <header className="mb-6 flex justify-between items-start">
                <div>
                    <button onClick={onBack} className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 mb-2">
                        &larr; Back to Application
                    </button>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Post-Interview Debrief Studio</h2>
                    <p className="text-lg text-slate-600 dark:text-slate-300">
                        For: {interview.interview_type} with {company.company_name}
                    </p>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left: User Input (Brain Dump) */}
                <div className="space-y-6">
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700/50">
                        <h3 className="font-semibold text-blue-800 dark:text-blue-200">Guided Brain Dump</h3>
                        <p className="text-sm mt-1 text-blue-700 dark:text-blue-300">While the conversation is fresh, capture your key takeaways. The AI will use this to generate your follow-up.</p>
                    </div>
                    {previousInterviewContext && (
                        <div>
                            <label className={labelClass}>Context from Previous Interviews</label>
                            <textarea
                                readOnly
                                value={previousInterviewContext}
                                rows={4}
                                className={`${textareaClass} bg-slate-100 dark:bg-slate-700/50 text-slate-500 dark:text-slate-400 text-xs`}
                            />
                        </div>
                    )}
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="new_intelligence" className={labelClass}>New Intelligence (What did I learn?)</label>
                            <textarea id="new_intelligence" value={notes.new_intelligence} onChange={e => handleNoteChange('new_intelligence', e.target.value)} rows={4} className={textareaClass} placeholder="e.g., The hiring manager mentioned that their biggest unexpected problem is retaining users after the initial 90-day onboarding."/>
                        </div>
                        <div>
                            <label htmlFor="wins" className={labelClass}>My "Wins" (What resonated well?)</label>
                            <textarea id="wins" value={notes.wins} onChange={e => handleNoteChange('wins', e.target.value)} rows={4} className={textareaClass} placeholder="e.g., My story about reducing churn by 40% really landed well. They asked two follow-up questions about the data." />
                        </div>
                        <div>
                            <label htmlFor="fumbles" className={labelClass}>My "Fumbles" (Where could I have been stronger?)</label>
                            <textarea id="fumbles" value={notes.fumbles} onChange={e => handleNoteChange('fumbles', e.target.value)} rows={4} className={textareaClass} placeholder="e.g., I struggled to give a crisp answer when they asked about pricing strategy." />
                        </div>
                    </div>
                    <div className="flex justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
                        <button onClick={handleGenerate} disabled={isLoading || !canGenerate} className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed">
                            {isLoading ? <LoadingSpinner/> : <SparklesIcon className="h-5 w-5" />}
                            Synthesize & Generate Counter
                        </button>
                    </div>
                </div>

                {/* Right: AI Output */}
                <div className="space-y-6">
                     <div className="p-4 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700 h-full">
                        <h3 className="font-semibold text-lg text-slate-800 dark:text-slate-200">AI-Generated Counter-Punch</h3>
                        {isLoading && !debrief ? (
                             <div className="flex flex-col items-center justify-center p-12">
                                <LoadingSpinner />
                                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Analyzing your notes...</p>
                            </div>
                        ) : debrief ? (
                            <div className="space-y-4 mt-2">
                                <div>
                                    <h4 className="font-semibold text-sm text-slate-700 dark:text-slate-300">Strategic Thank-You Note Draft</h4>
                                    <textarea readOnly value={debrief.thank_you_note_draft.replace(/\\n/g, '\n')} rows={5} className={`${textareaClass} mt-1 bg-white dark:bg-slate-800`} />
                                </div>
                                 <div>
                                    <h4 className="font-semibold text-sm text-slate-700 dark:text-slate-300">Performance Analysis</h4>
                                    <div className="mt-1 text-xs space-y-2 text-slate-600 dark:text-slate-300">
                                        <p><strong>Wins:</strong> <ul className="list-disc pl-5">{(debrief.performance_analysis.wins || []).map((w,i)=><li key={i}>{w}</li>)}</ul></p>
                                        <p><strong>Areas for Improvement:</strong> <ul className="list-disc pl-5">{(debrief.performance_analysis.areas_for_improvement || []).map((a,i)=><li key={i}>{a}</li>)}</ul></p>
                                    </div>
                                </div>
                                <div>
                                    <h4 className="font-semibold text-sm text-slate-700 dark:text-slate-300">Coaching Recommendations for Next Round</h4>
                                    <ul className="list-disc pl-5 text-xs space-y-1 mt-1 text-slate-600 dark:text-slate-300">
                                        {(debrief.coaching_recommendations || []).map((r,i)=><li key={i}>{r}</li>)}
                                    </ul>
                                </div>
                            </div>
                        ) : (
                            <p className="text-center text-sm text-slate-500 dark:text-slate-400 py-20">Your strategic follow-up will appear here after you provide your notes and run the AI synthesis.</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};