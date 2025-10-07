import React, { useState, useEffect, useMemo } from 'react';
import { JobApplication, Interview, StrategicNarrative, StorytellingFormat, StarBody, ScopeBody, WinsBody, SpotlightBody, InterviewPayload, Company, JobProblemAnalysisResult } from '../types';
import { CheckIcon, GripVerticalIcon, ClipboardDocumentCheckIcon, SparklesIcon, LoadingSpinner } from './IconComponents';
import { Switch } from './Switch';
import { HydratedDeckItem, buildHydratedDeck, ensureRoleOnDeck, removeRoleFromDeck, serializeDeck, updateDeckOrder, upsertDeckStory } from '../utils/interviewDeck';

interface InterviewCopilotViewProps {
    application: JobApplication;
    interview: Interview;
    company: Company;
    activeNarrative: StrategicNarrative;
    onBack: () => void;
    onSaveInterview: (payload: InterviewPayload, interviewId: string) => Promise<void>;
    onGenerateInterviewPrep: (app: JobApplication, interview: Interview) => Promise<void>;
    onGenerateRecruiterScreenPrep: (app: JobApplication, interview: Interview) => Promise<void>;
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


const appendUnique = (existing: string, addition: string) => {
    const trimmedAddition = addition.trim();
    if (!trimmedAddition) return existing;

    if (!existing.trim()) {
        return trimmedAddition;
    }

    if (existing.includes(trimmedAddition)) {
        return existing;
    }

    return `${existing.trimEnd()}\n\n${trimmedAddition}`;
};

const CoPilotSection = ({ title, children, className = '' }: { title: string, children: React.ReactNode, className?: string }) => (
    <div className={`bg-white dark:bg-slate-800 p-3 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 ${className}`}>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">{title}</h3>
        <div className="space-y-2">
            {children}
        </div>
    </div>
);

type CoverageState = { metrics: Set<string>; levers: Set<string>; blockers: Set<string>; };
type CoverageCategory = keyof CoverageState;

const createEmptyCoverageState = (): CoverageState => ({
    metrics: new Set<string>(),
    levers: new Set<string>(),
    blockers: new Set<string>(),
});

const pruneCoverageSelections = (
    state: CoverageState,
    metrics: string[],
    levers: string[],
    blockers: string[],
): CoverageState => ({
    metrics: new Set(metrics.filter(metric => state.metrics.has(metric))),
    levers: new Set(levers.filter(lever => state.levers.has(lever))),
    blockers: new Set(blockers.filter(blocker => state.blockers.has(blocker))),
});

const ImpactStoryTrigger = ({
    item,
    jobAnalysis,
    onAppendNotepad,
    isEditMode,
    activeRole,
    onNoteChange,
    onDragStart,
    onDragEnter,
    onDragEnd,
    onRemove,
}: {
    item: HydratedDeckItem;
    jobAnalysis?: JobProblemAnalysisResult;
    onAppendNotepad: (text: string) => void;
    isEditMode: boolean;
    activeRole: string;
    onNoteChange: (storyId: string, field: string, value: string) => void;
    onDragStart?: (storyId: string) => void;
    onDragEnter?: (storyId: string) => void;
    onDragEnd?: () => void;
    onRemove?: (storyId: string) => void;
}) => {
    const story = item.story;
    const formatName = (story?.format || 'STAR') as StorytellingFormat;
    const badgeColor = STORY_FORMAT_COLORS[formatName];
    const orderedFields = STORY_FORMAT_FIELDS[formatName] || [];
    const defaultNotes = item.custom_notes.default || {};
    const roleNotes = item.custom_notes[activeRole] || {};

    const cues = jobAnalysis
        ? [
              ...(jobAnalysis.key_success_metrics || []).map((value) => ({
                  label: 'Success Metric',
                  value,
              })),
              ...(jobAnalysis.role_levers || []).map((value) => ({
                  label: 'Lever',
                  value,
              })),
              ...(jobAnalysis.potential_blockers || []).map((value) => ({
                  label: 'Blocker',
                  value,
              })),
          ].slice(0, 3)
        : [];

    const readableLabel = (key: string) => key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

    if (isEditMode) {
        const dragHandlers = {
            draggable: true,
            onDragStart: (event: React.DragEvent<HTMLDivElement>) => {
                event.dataTransfer.effectAllowed = 'move';
                onDragStart?.(item.story_id);
            },
            onDragOver: (event: React.DragEvent<HTMLDivElement>) => {
                event.preventDefault();
                onDragEnter?.(item.story_id);
            },
            onDrop: (event: React.DragEvent<HTMLDivElement>) => {
                event.preventDefault();
                onDragEnd?.();
            },
            onDragEnd: () => onDragEnd?.(),
        };

        return (
            <div
                className="p-3 rounded-md bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 space-y-3"
                {...dragHandlers}
            >
                <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                        <span className="text-slate-400 cursor-grab" aria-hidden="true">
                            <GripVerticalIcon className="w-4 h-4" />
                        </span>
                        <div>
                            <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                                {story ? story.story_title : 'Story unavailable'}
                            </p>
                            <span className={`inline-flex text-xs font-mono px-1.5 py-0.5 rounded ${badgeColor}`}>
                                {formatName}
                            </span>
                        </div>
                    </div>
                    {onRemove && (
                        <button
                            type="button"
                            onClick={() => onRemove(item.story_id)}
                            className="text-xs font-semibold text-red-600 hover:text-red-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-red-500 rounded"
                        >
                            Remove
                        </button>
                    )}
                </div>
                {story ? (
                    <div className="space-y-2">
                        {orderedFields.map(field => {
                            const key = field as keyof (StarBody & ScopeBody & WinsBody & SpotlightBody);
                            const fieldName = key as unknown as string;
                            const placeholder = defaultNotes[fieldName] || '';
                            const value = roleNotes[fieldName] || '';
                            return (
                                <div key={fieldName}>
                                    <label className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                        {readableLabel(fieldName)}
                                    </label>
                                    <textarea
                                        rows={2}
                                        value={value}
                                        placeholder={placeholder}
                                        onChange={(e) => onNoteChange(item.story_id, fieldName, e.target.value)}
                                        className="w-full mt-1 p-2 text-xs font-mono bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    />
                                    {activeRole !== 'default' && placeholder && (
                                        <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">Default: {placeholder}</p>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <p className="text-xs text-amber-600">
                        This story is no longer part of the strategic narrative. Add it back to the narrative or remove it from this deck.
                    </p>
                )}
            </div>
        );
    }

    const noteParagraphs = orderedFields
        .map(field => {
            const key = field as keyof (StarBody & ScopeBody & WinsBody & SpotlightBody);
            const fieldName = key as unknown as string;
            const value = roleNotes[fieldName] ?? defaultNotes[fieldName];
            if (!value) {
                return null;
            }
            return (
                <p key={fieldName} className="mb-1">
                    <strong>{readableLabel(fieldName)}:</strong> {value}
                </p>
            );
        })
        .filter(Boolean);

    return (
        <details className="p-2 rounded-md bg-slate-200 dark:bg-slate-700">
            <summary className="w-full text-left text-sm font-semibold text-slate-800 dark:text-slate-200 flex justify-between items-center cursor-pointer">
                <span className="truncate pr-2">{story ? story.story_title : 'Story unavailable'}</span>
                <span className={`text-xs font-mono px-1.5 py-0.5 rounded flex-shrink-0 ${badgeColor}`}>{formatName}</span>
            </summary>
            <div className="mt-2 pt-2 border-t border-slate-300 dark:border-slate-600 text-xs text-slate-600 dark:text-slate-300 whitespace-pre-wrap font-mono">
                {noteParagraphs.length > 0 ? noteParagraphs : <p className="italic">No speaker notes for this role yet.</p>}
            </div>
            {cues.length > 0 && (
                <div className="mt-3 rounded-md border border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-800/70 p-2 text-xs text-slate-600 dark:text-slate-300">
                    <p className="font-semibold uppercase tracking-wide text-[10px] text-slate-500 dark:text-slate-400">Align this story to…</p>
                    <ul className="mt-2 space-y-2">
                        {cues.map(({ label, value }, index) => {
                            const prompt = `Emphasize how you solved ${value}.`;
                            const stub = `Emphasize how I solved ${value} by `;
                            return (
                                <li key={`${label}-${index}`} className="flex items-start justify-between gap-2">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                            <span className="inline-flex h-1.5 w-1.5 rounded-full bg-indigo-500" aria-hidden="true" />
                                            {label}
                                        </div>
                                        <p className="text-[11px] font-medium text-slate-700 dark:text-slate-200">{prompt}</p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => onAppendNotepad(stub)}
                                        className="flex-shrink-0 inline-flex items-center rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[10px] font-semibold text-indigo-600 dark:text-indigo-300 hover:bg-slate-200 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500"
                                    >
                                        Add stub
                                    </button>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            )}
        </details>
    );
};

export const InterviewCopilotView = ({ application, interview, company, activeNarrative, onBack, onSaveInterview, onGenerateInterviewPrep, onGenerateRecruiterScreenPrep }: InterviewCopilotViewProps) => {
    const [isEditMode, setIsEditMode] = useState(false);
    const [editableOpening, setEditableOpening] = useState('');
    const [editableQuestions, setEditableQuestions] = useState('');
    const [notepadContent, setNotepadContent] = useState('');
    const [askedQuestions, setAskedQuestions] = useState<Set<string>>(new Set());
    const [storyDeck, setStoryDeck] = useState<HydratedDeckItem[]>(() => buildHydratedDeck(interview, activeNarrative));
    const [activeRole, setActiveRole] = useState('default');
    const [draggingStoryId, setDraggingStoryId] = useState<string | null>(null);
    const [newRoleName, setNewRoleName] = useState('');
    const [storyToAdd, setStoryToAdd] = useState('');
    const [covered, setCovered] = useState<CoverageState>(createEmptyCoverageState);

    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [isSavingNotes, setIsSavingNotes] = useState(false);
    const [notesSuccess, setNotesSuccess] = useState(false);
    const [isGeneratingPrep, setIsGeneratingPrep] = useState(false);

    const jobAnalysis = useMemo(() => application.job_problem_analysis_result, [application]);

    useEffect(() => {
        setStoryDeck(buildHydratedDeck(interview, activeNarrative));
    }, [interview, activeNarrative]);

    useEffect(() => {
        const opening = interview.strategic_opening || `"I'm a product leader who excels at ${activeNarrative.positioning_statement}. My understanding is the core challenge here is ${application.job_problem_analysis_result?.core_problem_analysis.core_problem}. That's a problem I'm familiar with from my time when I ${activeNarrative.impact_story_title}."`;
        setEditableOpening(opening);
        setEditableQuestions((interview.strategic_questions_to_ask || []).join('\n'));
        setNotepadContent(interview.notes || '');
    }, [interview, activeNarrative, application]);

    const availableRoles = useMemo(() => {
        const roles = new Set<string>();
        storyDeck.forEach(item => {
            Object.keys(item.custom_notes).forEach(role => roles.add(role));
        });
        if (roles.size === 0) {
            roles.add('default');
        }
        return Array.from(roles);
    }, [storyDeck]);

    const questionList = useMemo(
        () => editableQuestions.split('\n').map(question => question.trim()).filter(Boolean),
        [editableQuestions]
    );

    useEffect(() => {
        setAskedQuestions(prev => {
            const next = new Set<string>();
            questionList.forEach(question => {
                if (prev.has(question)) {
                    next.add(question);
                }
            });
            return next;
        });
    }, [questionList]);

    useEffect(() => {
        if (!availableRoles.includes(activeRole)) {
            setActiveRole(availableRoles[0] || 'default');
        }
    }, [availableRoles, activeRole]);

    useEffect(() => {
        if (!activeRole) {
            return;
        }
        setStoryDeck(prev => {
            if (prev.length === 0) {
                return prev;
            }
            const needsRole = prev.some(item => !item.custom_notes[activeRole]);
            return needsRole ? ensureRoleOnDeck(prev, activeRole) : prev;
        });
    }, [activeRole]);

    const availableStories = useMemo(() => {
        const selectedIds = new Set(storyDeck.map(item => item.story_id));
        return (activeNarrative.impact_stories || []).filter(story => !selectedIds.has(story.story_id));
    }, [storyDeck, activeNarrative]);

    const toggleCoverage = (category: CoverageCategory, value: string) => {
        setCovered(prev => {
            const nextSet = new Set(prev[category]);
            if (nextSet.has(value)) {
                nextSet.delete(value);
            } else {
                nextSet.add(value);
            }
            return {
                ...prev,
                [category]: nextSet,
            };
        });
    };

    const resetCoverage = () => {
        setCovered(createEmptyCoverageState());
    };

    const handleAddRole = () => {
        const trimmed = newRoleName.trim();
        if (!trimmed) {
            return;
        }
        const existingRole = availableRoles.find(role => role.toLowerCase() === trimmed.toLowerCase());
        if (existingRole) {
            setActiveRole(existingRole);
            setNewRoleName('');
            return;
        }
        setStoryDeck(prev => ensureRoleOnDeck(prev, trimmed));
        setActiveRole(trimmed);
        setNewRoleName('');
    };

    const handleRemoveRole = (role: string) => {
        if (role === 'default') {
            return;
        }
        setStoryDeck(prev => removeRoleFromDeck(prev, role));
    };

    const handleNoteChange = (storyId: string, field: string, value: string) => {
        setStoryDeck(prev => prev.map(item => {
            if (item.story_id !== storyId) {
                return item;
            }
            const roleNotes = item.custom_notes[activeRole] || {};
            return {
                ...item,
                custom_notes: {
                    ...item.custom_notes,
                    [activeRole]: {
                        ...roleNotes,
                        [field]: value,
                    },
                },
            };
        }));
    };

    const handleDragStart = (storyId: string) => {
        setDraggingStoryId(storyId);
    };

    const handleDragEnter = (storyId: string) => {
        if (!draggingStoryId || draggingStoryId === storyId) {
            return;
        }
        setStoryDeck(prev => updateDeckOrder(prev, draggingStoryId, storyId));
    };

    const handleDragEnd = () => {
        setDraggingStoryId(null);
    };

    const handleAddStory = () => {
        if (!storyToAdd) {
            return;
        }
        const story = (activeNarrative.impact_stories || []).find(s => s.story_id === storyToAdd);
        if (!story) {
            return;
        }
        setStoryDeck(prev => upsertDeckStory(prev, story));
        setStoryToAdd('');
    };

    const handleRemoveStory = (storyId: string) => {
        setStoryDeck(prev => prev
            .filter(item => item.story_id !== storyId)
            .map((item, index) => ({ ...item, order_index: index }))
        );
    };

    const handleSave = async () => {
        setIsSaving(true);
        setSaveSuccess(false);
        try {
            const payload: InterviewPayload = {
                strategic_opening: editableOpening,
                strategic_questions_to_ask: questionList,
                story_deck: serializeDeck(storyDeck),
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

    const handleRerunAI = async () => {
        setIsGeneratingPrep(true);
        try {
            const isRecruiterScreen = interview.interview_type === "Step 6.1: Recruiter Screen";
            if (isRecruiterScreen) {
                await onGenerateRecruiterScreenPrep(application, interview);
            } else {
                await onGenerateInterviewPrep(application, interview);
            }
        } catch (error) {
            console.error("Failed to rerun AI prep", error);
        } finally {
            setIsGeneratingPrep(false);
        }
    };

    const interviewer = interview.interview_contacts?.[0];

    const coreProblem = jobAnalysis?.core_problem_analysis?.core_problem?.trim();
    const keyMetrics = jobAnalysis?.key_success_metrics || [];
    const roleLevers = jobAnalysis?.role_levers || [];
    const potentialBlockers = jobAnalysis?.potential_blockers || [];
    const roleTags = jobAnalysis?.tags || [];

    useEffect(() => {
        setCovered(createEmptyCoverageState());
    }, [interview.interview_id, jobAnalysis]);

    useEffect(() => {
        setCovered(prev => pruneCoverageSelections(prev, keyMetrics, roleLevers, potentialBlockers));
    }, [keyMetrics, roleLevers, potentialBlockers]);

    const totalCoverageItems = keyMetrics.length + roleLevers.length + potentialBlockers.length;
    const coveredCount = covered.metrics.size + covered.levers.size + covered.blockers.size;
    const coveragePercent = totalCoverageItems === 0 ? 0 : Math.round((coveredCount / totalCoverageItems) * 100);

    const handleQuickAdd = (text: string) => {
        setNotepadContent(prev => appendUnique(prev, text));
    };

    return (
        <div className="fixed inset-0 z-50 bg-slate-900 bg-opacity-75 flex items-center justify-center p-4">
            <div className="bg-slate-100 dark:bg-slate-900 rounded-xl shadow-2xl flex flex-col h-full w-full">
                <header className="p-3 border-b border-slate-300 dark:border-slate-700 flex justify-between items-center flex-shrink-0">
                    <div>
                        <h2 className="text-base font-bold text-slate-900 dark:text-white">Interview Co-pilot</h2>
                        <p className="text-xs text-slate-500 dark:text-slate-400">{application.job_title} at {company.company_name}</p>
                    </div>
                    <div className="flex items-center gap-4">
                         <div className="flex items-center space-x-2">
                             <span className="text-xs font-medium text-slate-500 dark:text-slate-400">View Mode</span>
                            <Switch enabled={isEditMode} onChange={setIsEditMode} />
                            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Edit Mode</span>
                        </div>
                        {isEditMode ? (
                            <button onClick={handleSave} disabled={isSaving} className={`px-3 py-1.5 text-xs font-semibold rounded-md shadow-sm transition-colors ${saveSuccess ? 'bg-green-600 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white disabled:bg-blue-400'}`}>
                                {isSaving ? 'Saving...' : saveSuccess ? 'Saved!' : 'Save Changes'}
                            </button>
                        ) : (
                             <button onClick={handleRerunAI} disabled={isGeneratingPrep} className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-md shadow-sm transition-colors bg-indigo-600 hover:bg-indigo-700 text-white disabled:bg-indigo-400">
                                {isGeneratingPrep ? <LoadingSpinner/> : <SparklesIcon className="h-4 w-4"/>}
                                Rerun AI Prep
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
                        {jobAnalysis && (
                            <CoPilotSection title="Role Intelligence">
                                <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
                                    <div className="space-y-1">
                                        <div className="flex items-start justify-between gap-2">
                                            <div>
                                                <p className="font-bold text-slate-500 dark:text-slate-400">Core Problem</p>
                                                <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">{coreProblem || 'N/A'}</p>
                                            </div>
                                            {coreProblem && (
                                                <button
                                                    onClick={() => handleQuickAdd(`Core Problem: ${coreProblem}`)}
                                                    className="inline-flex items-center gap-1 rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[11px] font-semibold text-slate-600 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500"
                                                >
                                                    <ClipboardDocumentCheckIcon className="h-4 w-4" />
                                                    Copy to Notepad
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <div className="flex items-start justify-between gap-2">
                                            <div>
                                                <p className="font-bold text-slate-500 dark:text-slate-400">Key Success Metrics</p>
                                                {keyMetrics.length > 0 && (
                                                    <p className="text-[11px] text-slate-500 dark:text-slate-400">{covered.metrics.size}/{keyMetrics.length} covered</p>
                                                )}
                                            </div>
                                            {keyMetrics.length > 0 && (
                                                <button
                                                    onClick={() => handleQuickAdd(`Key Success Metrics:\n${keyMetrics.map(metric => `• ${metric}`).join('\n')}`)}
                                                    className="inline-flex items-center gap-1 rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[11px] font-semibold text-slate-600 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500"
                                                >
                                                    <ClipboardDocumentCheckIcon className="h-4 w-4" />
                                                    Copy to Notepad
                                                </button>
                                            )}
                                        </div>
                                        {keyMetrics.length > 0 ? (
                                            <ul className="mt-1 space-y-1 text-sm text-slate-700 dark:text-slate-200">
                                                {keyMetrics.map((metric, index) => {
                                                    const isCovered = covered.metrics.has(metric);
                                                    return (
                                                        <li key={index}>
                                                            <button
                                                                type="button"
                                                                onClick={() => toggleCoverage('metrics', metric)}
                                                                className={`flex w-full items-center gap-2 rounded-md px-2 py-1 text-left transition ${isCovered ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-200' : 'hover:bg-slate-200 dark:hover:bg-slate-700/80'}`}
                                                            >
                                                                <span className={`flex h-4 w-4 items-center justify-center rounded border ${isCovered ? 'border-green-600 bg-green-600 text-white' : 'border-slate-400 text-transparent'}`}>
                                                                    <CheckIcon className="h-3 w-3" />
                                                                </span>
                                                                <span className={isCovered ? 'line-through' : ''}>{metric}</span>
                                                            </button>
                                                        </li>
                                                    );
                                                })}
                                            </ul>
                                        ) : (
                                            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">N/A</p>
                                        )}
                                    </div>
                                    <div className="space-y-1">
                                        <div className="flex items-start justify-between gap-2">
                                            <div>
                                                <p className="font-bold text-slate-500 dark:text-slate-400">Levers</p>
                                                {roleLevers.length > 0 && (
                                                    <p className="text-[11px] text-slate-500 dark:text-slate-400">{covered.levers.size}/{roleLevers.length} covered</p>
                                                )}
                                            </div>
                                            {roleLevers.length > 0 && (
                                                <button
                                                    onClick={() => handleQuickAdd(`Levers:\n${roleLevers.map(lever => `• ${lever}`).join('\n')}`)}
                                                    className="inline-flex items-center gap-1 rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[11px] font-semibold text-slate-600 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500"
                                                >
                                                    <ClipboardDocumentCheckIcon className="h-4 w-4" />
                                                    Copy to Notepad
                                                </button>
                                            )}
                                        </div>
                                        {roleLevers.length > 0 ? (
                                            <ul className="mt-1 space-y-1 text-sm text-slate-700 dark:text-slate-200">
                                                {roleLevers.map((lever, index) => {
                                                    const isCovered = covered.levers.has(lever);
                                                    return (
                                                        <li key={index}>
                                                            <button
                                                                type="button"
                                                                onClick={() => toggleCoverage('levers', lever)}
                                                                className={`flex w-full items-center gap-2 rounded-md px-2 py-1 text-left transition ${isCovered ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-200' : 'hover:bg-slate-200 dark:hover:bg-slate-700/80'}`}
                                                            >
                                                                <span className={`flex h-4 w-4 items-center justify-center rounded border ${isCovered ? 'border-green-600 bg-green-600 text-white' : 'border-slate-400 text-transparent'}`}>
                                                                    <CheckIcon className="h-3 w-3" />
                                                                </span>
                                                                <span className={isCovered ? 'line-through' : ''}>{lever}</span>
                                                            </button>
                                                        </li>
                                                    );
                                                })}
                                            </ul>
                                        ) : (
                                            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">N/A</p>
                                        )}
                                    </div>
                                    <div className="space-y-1">
                                        <div className="flex items-start justify-between gap-2">
                                            <div>
                                                <p className="font-bold text-slate-500 dark:text-slate-400">Potential Blockers</p>
                                                {potentialBlockers.length > 0 && (
                                                    <p className="text-[11px] text-slate-500 dark:text-slate-400">{covered.blockers.size}/{potentialBlockers.length} covered</p>
                                                )}
                                            </div>
                                            {potentialBlockers.length > 0 && (
                                                <button
                                                    onClick={() => handleQuickAdd(`Potential Blockers:\n${potentialBlockers.map(blocker => `• ${blocker}`).join('\n')}`)}
                                                    className="inline-flex items-center gap-1 rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[11px] font-semibold text-slate-600 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500"
                                                >
                                                    <ClipboardDocumentCheckIcon className="h-4 w-4" />
                                                    Copy to Notepad
                                                </button>
                                            )}
                                        </div>
                                        {potentialBlockers.length > 0 ? (
                                            <ul className="mt-1 space-y-1 text-sm text-slate-700 dark:text-slate-200">
                                                {potentialBlockers.map((blocker, index) => {
                                                    const isCovered = covered.blockers.has(blocker);
                                                    return (
                                                        <li key={index}>
                                                            <button
                                                                type="button"
                                                                onClick={() => toggleCoverage('blockers', blocker)}
                                                                className={`flex w-full items-center gap-2 rounded-md px-2 py-1 text-left transition ${isCovered ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-200' : 'hover:bg-slate-200 dark:hover:bg-slate-700/80'}`}
                                                            >
                                                                <span className={`flex h-4 w-4 items-center justify-center rounded border ${isCovered ? 'border-green-600 bg-green-600 text-white' : 'border-slate-400 text-transparent'}`}>
                                                                    <CheckIcon className="h-3 w-3" />
                                                                </span>
                                                                <span className={isCovered ? 'line-through' : ''}>{blocker}</span>
                                                            </button>
                                                        </li>
                                                    );
                                                })}
                                            </ul>
                                        ) : (
                                            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">N/A</p>
                                        )}
                                    </div>
                                    <div className="space-y-1">
                                        <div className="flex items-start justify-between gap-2">
                                            <p className="font-bold text-slate-500 dark:text-slate-400">Tags</p>
                                            {roleTags.length > 0 && (
                                                <button
                                                    onClick={() => handleQuickAdd(`Tags: ${roleTags.map(tag => `#${tag}`).join(' ')}`)}
                                                    className="inline-flex items-center gap-1 rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[11px] font-semibold text-slate-600 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500"
                                                >
                                                    <ClipboardDocumentCheckIcon className="h-4 w-4" />
                                                    Copy to Notepad
                                                </button>
                                            )}
                                        </div>
                                        {roleTags.length > 0 ? (
                                            <div className="mt-1 flex flex-wrap gap-1">
                                                {roleTags.map((tag, index) => (
                                                    <span key={index} className="inline-flex items-center rounded-full bg-slate-200 dark:bg-slate-700 px-2 py-0.5 text-[11px] font-semibold text-slate-700 dark:text-slate-200">#{tag}</span>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">N/A</p>
                                        )}
                                    </div>
                                </div>
                            </CoPilotSection>
                        )}
                        {jobAnalysis && totalCoverageItems > 0 && (
                            <CoPilotSection title="Interview Coverage Tracker">
                                <div className="space-y-3">
                                    <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                        <span aria-live="polite">Covered {coveredCount} of {totalCoverageItems} ({coveragePercent}%)</span>
                                        <button
                                            type="button"
                                            onClick={resetCoverage}
                                            className="text-xs font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-300 dark:hover:text-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 rounded"
                                        >
                                            Reset
                                        </button>
                                    </div>
                                    <div className="h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden" role="progressbar" aria-valuenow={coveragePercent} aria-valuemin={0} aria-valuemax={100} aria-label="Coverage progress">
                                        <div className="h-full bg-indigo-500 transition-all duration-300" style={{ width: `${coveragePercent}%` }} />
                                    </div>
                                    <div className="space-y-3">
                                        {keyMetrics.length > 0 && (
                                            <fieldset>
                                                <legend className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Key Success Metrics</legend>
                                                <div className="mt-2 space-y-2">
                                                    {keyMetrics.map((metric, index) => {
                                                        const id = `metric-${index}`;
                                                        const isChecked = covered.metrics.has(metric);
                                                        return (
                                                            <div key={`${metric}-${index}`} className="flex items-start gap-2">
                                                                <input
                                                                    id={id}
                                                                    type="checkbox"
                                                                    checked={isChecked}
                                                                    onChange={() => toggleCoverage('metrics', metric)}
                                                                    className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                                                                />
                                                                <label htmlFor={id} className={`text-sm leading-tight text-slate-700 dark:text-slate-200 ${isChecked ? 'line-through text-slate-400 dark:text-slate-500' : ''}`}>
                                                                    {metric}
                                                                </label>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </fieldset>
                                        )}
                                        {roleLevers.length > 0 && (
                                            <fieldset>
                                                <legend className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Levers</legend>
                                                <div className="mt-2 space-y-2">
                                                    {roleLevers.map((lever, index) => {
                                                        const id = `lever-${index}`;
                                                        const isChecked = covered.levers.has(lever);
                                                        return (
                                                            <div key={`${lever}-${index}`} className="flex items-start gap-2">
                                                                <input
                                                                    id={id}
                                                                    type="checkbox"
                                                                    checked={isChecked}
                                                                    onChange={() => toggleCoverage('levers', lever)}
                                                                    className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                                                                />
                                                                <label htmlFor={id} className={`text-sm leading-tight text-slate-700 dark:text-slate-200 ${isChecked ? 'line-through text-slate-400 dark:text-slate-500' : ''}`}>
                                                                    {lever}
                                                                </label>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </fieldset>
                                        )}
                                        {potentialBlockers.length > 0 && (
                                            <fieldset>
                                                <legend className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Potential Blockers</legend>
                                                <div className="mt-2 space-y-2">
                                                    {potentialBlockers.map((blocker, index) => {
                                                        const id = `blocker-${index}`;
                                                        const isChecked = covered.blockers.has(blocker);
                                                        return (
                                                            <div key={`${blocker}-${index}`} className="flex items-start gap-2">
                                                                <input
                                                                    id={id}
                                                                    type="checkbox"
                                                                    checked={isChecked}
                                                                    onChange={() => toggleCoverage('blockers', blocker)}
                                                                    className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                                                                />
                                                                <label htmlFor={id} className={`text-sm leading-tight text-slate-700 dark:text-slate-200 ${isChecked ? 'line-through text-slate-400 dark:text-slate-500' : ''}`}>
                                                                    {blocker}
                                                                </label>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </fieldset>
                                        )}
                                    </div>
                                </div>
                            </CoPilotSection>
                        )}
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
                            <div className="space-y-2">
                                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                                    <div className="flex flex-wrap items-center gap-2">
                                        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Persona</span>
                                        <select
                                            value={activeRole}
                                            onChange={(e) => setActiveRole(e.target.value)}
                                            className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-xs px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        >
                                            {availableRoles.map(role => (
                                                <option key={role} value={role}>{role}</option>
                                            ))}
                                        </select>
                                        {isEditMode && activeRole !== 'default' && (
                                            <button
                                                type="button"
                                                onClick={() => handleRemoveRole(activeRole)}
                                                className="inline-flex items-center rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[10px] font-semibold text-red-600 dark:text-red-300 hover:bg-slate-200 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-red-500"
                                            >
                                                Remove Role
                                            </button>
                                        )}
                                    </div>
                                    {isEditMode && (
                                        <div className="flex flex-wrap items-center gap-2">
                                            <input
                                                type="text"
                                                value={newRoleName}
                                                onChange={(e) => setNewRoleName(e.target.value)}
                                                placeholder="Add interviewer persona"
                                                className="w-48 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                            />
                                            <button
                                                type="button"
                                                onClick={handleAddRole}
                                                disabled={!newRoleName.trim()}
                                                className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-1 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:bg-indigo-300"
                                            >
                                                Add Role
                                            </button>
                                        </div>
                                    )}
                                </div>
                                {isEditMode && availableStories.length > 0 && (
                                    <div className="flex flex-wrap items-center gap-2">
                                        <select
                                            value={storyToAdd}
                                            onChange={(e) => setStoryToAdd(e.target.value)}
                                            className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-xs px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        >
                                            <option value="">Add narrative story…</option>
                                            {availableStories.map(story => (
                                                <option key={story.story_id} value={story.story_id}>{story.story_title}</option>
                                            ))}
                                        </select>
                                        <button
                                            type="button"
                                            onClick={handleAddStory}
                                            disabled={!storyToAdd}
                                            className="inline-flex items-center rounded-md bg-green-600 px-3 py-1 text-xs font-semibold text-white shadow-sm hover:bg-green-700 disabled:bg-green-300"
                                        >
                                            Add Story
                                        </button>
                                    </div>
                                )}
                                <div className="space-y-2">
                                    {storyDeck.length > 0 ? (
                                        storyDeck.map(item => (
                                            <ImpactStoryTrigger
                                                key={item.story_id}
                                                item={item}
                                                jobAnalysis={jobAnalysis}
                                                onAppendNotepad={handleQuickAdd}
                                                isEditMode={isEditMode}
                                                activeRole={activeRole}
                                                onNoteChange={handleNoteChange}
                                                onDragStart={isEditMode ? handleDragStart : undefined}
                                                onDragEnter={isEditMode ? handleDragEnter : undefined}
                                                onDragEnd={isEditMode ? handleDragEnd : undefined}
                                                onRemove={isEditMode ? handleRemoveStory : undefined}
                                            />
                                        ))
                                    ) : (
                                        <p className="text-xs text-slate-500 dark:text-slate-400 text-center">No impact stories defined.</p>
                                    )}
                                </div>
                            </div>
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
                                    {questionList.map((question, i) => (
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
