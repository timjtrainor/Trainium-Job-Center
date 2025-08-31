import React, { useState, useEffect, useMemo, useRef } from 'react';
import { JobApplication, Interview, StrategicNarrative, ImpactStory, StorytellingFormat, StarBody, ScopeBody, WinsBody, SpotlightBody, InterviewPayload } from '../types';
import { CheckIcon, GripVerticalIcon, MicrophoneIcon, ClipboardDocumentCheckIcon } from './IconComponents';
import { Switch } from './Switch';

interface InterviewCopilotViewProps {
    application: JobApplication;
    interview: Interview;
    activeNarrative: StrategicNarrative;
    onBack: () => void;
    onSaveInterview: (payload: InterviewPayload, interviewId: string) => Promise<void>;
}

const STORY_FORMAT_FIELDS: { [key in StorytellingFormat]: (keyof (StarBody & ScopeBody & WinsBody & SpotlightBody))[] } = {
    STAR: ['situation', 'task', 'action', 'result'],
    SCOPE: ['situation', 'complication', 'opportunity', 'product_thinking', 'end_result'],
    WINS: ['situation', 'what_i_did', 'impact', 'nuance'],
    SPOTLIGHT: ['situation', 'positive_moment_or_goal', 'observation_opportunity', 'task_action', 'learnings_leverage', 'impact_results', 'growth_grit', 'highlights_key_trait', 'takeaway_tie_in'],
};

const STORY_FORMAT_COLORS: { [key in StorytellingFormat]: string } = {
    STAR: 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300',
    SCOPE: 'bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300',
    WINS: 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300',
    SPOTLIGHT: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300',
};


const CoPilotSection = ({ title, children, className = '' }: { title: string, children: React.ReactNode, className?: string }) => (
    <div className={`bg-white dark:bg-slate-800 p-3 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 ${className}`}>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">{title}</h3>
        <div className="space-y-2">
            {children}
        </div>
    </div>
);

const ImpactStoryTrigger = ({ story }: { story: ImpactStory }) => {
    const formatName = story.format || 'STAR';
    const badgeColor = STORY_FORMAT_COLORS[formatName];
    const orderedFields = STORY_FORMAT_FIELDS[formatName];

    return (
        <details className="p-2 rounded-md bg-slate-200 dark:bg-slate-700">
            <summary className="w-full text-left text-sm font-semibold text-slate-800 dark:text-slate-200 flex justify-between items-center cursor-pointer">
                <span className="truncate pr-2">{story.story_title}</span>
                <span className={`text-xs font-mono px-1.5 py-0.5 rounded flex-shrink-0 ${badgeColor}`}>{formatName}</span>
            </summary>
             <div className="mt-2 pt-2 border-t border-slate-300 dark:border-slate-600 text-xs text-slate-600 dark:text-slate-300 whitespace-pre-wrap font-mono">
                {story.speaker_notes && typeof story.speaker_notes === 'object' ? (
                    orderedFields.map(key => {
                        const value = (story.speaker_notes as any)[key];
                        // Create a more readable label from the key
                        const label = key.toString().replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        return value ? (
                            <p key={key as string} className="mb-1"><strong>{label}:</strong> {value}</p>
                        ) : null
                    })
                ) : <p>No speaker notes.</p>}
             </div>
        </details>
    )
}

export const InterviewCopilotView = ({ application, interview, activeNarrative, onBack, onSaveInterview }: InterviewCopilotViewProps) => {
    const [isEditMode, setIsEditMode] = useState(false);
    const [editableOpening, setEditableOpening] = useState('');
    const [editableQuestions, setEditableQuestions] = useState('');
    const [notepadContent, setNotepadContent] = useState('');
    const [askedQuestions, setAskedQuestions] = useState<Set<string>>(new Set());
    
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [isSavingNotes, setIsSavingNotes] = useState(false);
    const [notesSuccess, setNotesSuccess] = useState(false);

    useEffect(() => {
        const opening = interview.strategic_opening || `"I'm a product leader who excels at ${activeNarrative.positioning_statement}. My understanding is the core challenge here is ${application.job_problem_analysis_result?.core_problem_analysis.core_problem}. That's a problem I'm familiar with from my time when I ${activeNarrative.impact_story_title}."`;
        setEditableOpening(opening);
        setEditableQuestions((interview.strategic_questions_to_ask || []).join('\n'));
        setNotepadContent(interview.notes || '');
    }, [interview, activeNarrative, application]);

    const handleSave = async () => {
        setIsSaving(true);
        setSaveSuccess(false);
        try {
            const payload: InterviewPayload = {
                strategic_opening: editableOpening,
                strategic_questions_to_ask: editableQuestions.split('\n').filter(q => q.trim() !== '')
            };
            await onSaveInterview(payload, interview.interview_id);
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 2000);
        } catch (e) {
            console.error("Failed to save Co-pilot data:", e);
        } finally {
            setIsSaving(false);
        }
    };
    
    const handleSaveNotes = async () => {
        setIsSavingNotes(true);
        setNotesSuccess(false);
        try {
            await onSaveInterview({ notes: notepadContent }, interview.interview_id);
            setNotesSuccess(true);
            setTimeout(() => setNotesSuccess(false), 2000);
        } catch (e) {
            console.error("Failed to save notes:", e);
        } finally {
            setIsSavingNotes(false);
        }
    };
    
     const handleQuestionToggle = (question: string) => {
        setAskedQuestions(prev => {
            const newSet = new Set(prev);
            if (newSet.has(question)) {
                newSet.delete(question);
            } else {
                newSet.add(question);
            }
            return newSet;
        });
    };
    
    const interviewer = interview.interview_contacts?.[0];

    return (
        <div className="fixed inset-0 z-50 bg-slate-900 bg-opacity-75 flex items-center justify-center p-4">
            <div className="bg-slate-100 dark:bg-slate-900 rounded-xl shadow-2xl flex flex-col h-full w-full">
                <header className="p-3 border-b border-slate-300 dark:border-slate-700 flex justify-between items-center flex-shrink-0">
                    <div>
                        <h2 className="text-base font-bold text-slate-900 dark:text-white">Interview Co-pilot</h2>
                        <p className="text-xs text-slate-500 dark:text-slate-400">{application.job_title} at {application.company_id}</p>
                    </div>
                    <div className="flex items-center gap-4">
                         <div className="flex items-center space-x-2">
                             <span className="text-xs font-medium text-slate-500 dark:text-slate-400">View Mode</span>
                            <Switch enabled={isEditMode} onChange={setIsEditMode} />
                            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Edit Mode</span>
                        </div>
                        {isEditMode && (
                            <button onClick={handleSave} disabled={isSaving} className={`px-3 py-1.5 text-xs font-semibold rounded-md shadow-sm transition-colors ${saveSuccess ? 'bg-green-600 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white disabled:bg-blue-400'}`}>
                                {isSaving ? 'Saving...' : saveSuccess ? 'Saved!' : 'Save Changes'}
                            </button>
                        )}
                        <button onClick={onBack} className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline">
                            Close
                        </button>
                    </div>
                </header>

                <main className="flex-1 overflow-hidden grid grid-cols-1 md:grid-cols-3 gap-3 p-3">
                    {/* Left Column: Co-pilot Content */}
                    <div className="md:col-span-2 overflow-y-auto space-y-3 pr-2">
                         <CoPilotSection title="Top of Mind">
                            <div className="text-xs space-y-1">
                                <p><strong className="text-slate-600 dark:text-slate-300">Interviewing with:</strong> {interviewer ? `${interviewer.first_name} ${interviewer.last_name}` : 'N/A'}</p>
                                <p><strong className="text-slate-600 dark:text-slate-300">Role:</strong> {interview.interview_type}</p>
                            </div>
                        </CoPilotSection>
                        <CoPilotSection title="Strategic Opening">
                            {isEditMode ? (
                                <textarea
                                    value={editableOpening}
                                    onChange={(e) => setEditableOpening(e.target.value)}
                                    rows={5}
                                    className="w-full mt-1 p-2 text-sm text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md"
                                />
                            ) : (
                                <p className="text-sm italic text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{editableOpening}</p>
                            )}
                        </CoPilotSection>
                        <CoPilotSection title="Clarification Safety Net">
                            <p className="text-xs text-slate-500 dark:text-slate-400">If stuck, ask about:</p>
                            <p className="text-sm font-mono text-indigo-600 dark:text-indigo-400">Scope | Success Metrics | Constraints</p>
                        </CoPilotSection>
                        <CoPilotSection title="STAR Method Quick Reference">
                            <ul className="text-xs space-y-1 text-slate-600 dark:text-slate-400">
                                <li><strong className="text-slate-700 dark:text-slate-300">S (Situation):</strong> Set the scene. (1-2 sentences)</li>
                                <li><strong className="text-slate-700 dark:text-slate-300">T (Task):</strong> Describe your goal. (1 sentence)</li>
                                <li><strong className="text-slate-700 dark:text-slate-300">A (Action):</strong> What specific steps did YOU take? (2-3 sentences)</li>
                                <li><strong className="text-slate-700 dark:text-slate-300">R (Result):</strong> What was the quantifiable outcome? (1-2 sentences)</li>
                            </ul>
                        </CoPilotSection>
                        <CoPilotSection title="Impact Story Triggers">
                            {(activeNarrative.impact_stories || []).map(story => (
                               <ImpactStoryTrigger key={story.story_id} story={story} />
                            ))}
                             {(!activeNarrative.impact_stories || activeNarrative.impact_stories.length === 0) && (
                                <p className="text-xs text-slate-500 dark:text-slate-400 text-center">No impact stories defined.</p>
                             )}
                        </CoPilotSection>
                        <CoPilotSection title="Hot Leads (30-60-90 Plan)">
                            <ul className="list-disc pl-4 text-sm space-y-1 text-slate-700 dark:text-slate-300">
                                {(interview.strategic_plan?.key_talking_points || []).map((point, i) => <li key={i}>{point}</li>)}
                            </ul>
                        </CoPilotSection>
                         <CoPilotSection title="Question Arsenal">
                            {isEditMode ? (
                                <textarea
                                    value={editableQuestions}
                                    onChange={(e) => setEditableQuestions(e.target.value)}
                                    rows={8}
                                    className="w-full mt-1 p-2 text-sm text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md"
                                />
                            ) : (
                                 <div className="space-y-2">
                                    {editableQuestions.split('\n').filter(q => q.trim()).map((question, i) => (
                                         <div key={i} className="relative flex items-start">
                                            <div className="flex h-6 items-center">
                                                <input
                                                id={`q-${i}`}
                                                type="checkbox"
                                                checked={askedQuestions.has(question)}
                                                onChange={() => handleQuestionToggle(question)}
                                                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                />
                                            </div>
                                            <div className="ml-3 text-sm leading-6">
                                                <label htmlFor={`q-${i}`} className={`text-slate-700 dark:text-slate-300 ${askedQuestions.has(question) ? 'line-through text-slate-400 dark:text-slate-500' : ''}`}>
                                                    {question}
                                                </label>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CoPilotSection>
                    </div>

                    {/* Right Column: Notepad */}
                     <div className="md:col-span-1 overflow-y-auto h-full flex flex-col">
                        <CoPilotSection title="Notepad for Debrief" className="flex-grow flex flex-col">
                            <div className="flex justify-end mb-2">
                                <button
                                    onClick={handleSaveNotes}
                                    disabled={isSavingNotes}
                                    className={`inline-flex items-center justify-center w-24 px-2 py-1 text-xs font-semibold rounded-md shadow-sm transition-colors ${
                                        notesSuccess ? 'bg-green-600 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white disabled:bg-blue-400'
                                    }`}
                                >
                                    {isSavingNotes ? <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"/> : notesSuccess ? <CheckIcon className="h-4 w-4" /> : 'Save Notes'}
                                </button>
                            </div>
                            <textarea
                                value={notepadContent}
                                onChange={(e) => setNotepadContent(e.target.value)}
                                className="w-full flex-grow p-2 text-sm bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md"
                                placeholder="Jot down notes, new intelligence, wins, and fumbles here..."
                            />
                        </CoPilotSection>
                    </div>
                </main>
            </div>
        </div>
    );
};
