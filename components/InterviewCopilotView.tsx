import React, { useState, useEffect, useMemo } from 'react';
import { JobApplication, Interview, StrategicNarrative, StorytellingFormat, StarBody, ScopeBody, WinsBody, SpotlightBody, InterviewPayload, Company, JobProblemAnalysisResult, InterviewPrepOutline, ImpactStory } from '../types';
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

const sanitizeListInput = (value: string): string[] =>
    value
        .split('\n')
        .map(item => item.trim())
        .filter(Boolean);

const buildPrepOutline = (
    analysis?: JobProblemAnalysisResult | null,
    stored?: InterviewPrepOutline | null
): InterviewPrepOutline => {
    const defaults: InterviewPrepOutline = {
        role_intelligence: {
            core_problem: analysis?.core_problem_analysis?.core_problem?.trim() || '',
            suggested_positioning: analysis?.suggested_positioning?.trim() || '',
            key_success_metrics: (analysis?.key_success_metrics || []).slice(),
            role_levers: (analysis?.role_levers || []).slice(),
            potential_blockers: (analysis?.potential_blockers || []).slice(),
        },
        jd_insights: {
            business_context: analysis?.core_problem_analysis?.business_context?.trim() || '',
            strategic_importance: analysis?.core_problem_analysis?.strategic_importance?.trim() || '',
            tags: (analysis?.tags || []).slice(),
        },
    };

    if (!stored) {
        return defaults;
    }

    return {
        role_intelligence: {
            core_problem: stored.role_intelligence?.core_problem ?? defaults.role_intelligence?.core_problem ?? '',
            suggested_positioning: stored.role_intelligence?.suggested_positioning ?? defaults.role_intelligence?.suggested_positioning ?? '',
            key_success_metrics: stored.role_intelligence?.key_success_metrics ?? defaults.role_intelligence?.key_success_metrics ?? [],
            role_levers: stored.role_intelligence?.role_levers ?? defaults.role_intelligence?.role_levers ?? [],
            potential_blockers: stored.role_intelligence?.potential_blockers ?? defaults.role_intelligence?.potential_blockers ?? [],
        },
        jd_insights: {
            business_context: stored.jd_insights?.business_context ?? defaults.jd_insights?.business_context ?? '',
            strategic_importance: stored.jd_insights?.strategic_importance ?? defaults.jd_insights?.strategic_importance ?? '',
            tags: stored.jd_insights?.tags ?? defaults.jd_insights?.tags ?? [],
        },
    };
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

interface PrepWorkspaceProps {
    interview: Interview;
    jobAnalysis?: JobProblemAnalysisResult | null;
    activeRole: string;
    availableRoles: string[];
    onRoleChange: (role: string) => void;
    onAddRole: () => void;
    onRemoveRole: (role: string) => void;
    newRoleName: string;
    onNewRoleNameChange: (value: string) => void;
    availableStories: ImpactStory[];
    storyToAdd: string;
    onStoryToAddChange: (value: string) => void;
    onAddStory: () => void;
    storyDeck: HydratedDeckItem[];
    onNoteChange: (storyId: string, field: string, value: string) => void;
    onDragStart: (storyId: string) => void;
    onDragEnter: (storyId: string) => void;
    onDragEnd: () => void;
    onRemoveStory: (storyId: string) => void;
    editableOpening: string;
    onChangeOpening: (value: string) => void;
    editableQuestions: string;
    onChangeQuestions: (value: string) => void;
    prepOutline: InterviewPrepOutline;
    onUpdateRoleIntelligence: (
        field: keyof NonNullable<InterviewPrepOutline['role_intelligence']>,
        value: string,
        isList?: boolean,
    ) => void;
    onUpdateJdInsights: (
        field: keyof NonNullable<InterviewPrepOutline['jd_insights']>,
        value: string,
        isList?: boolean,
    ) => void;
}

const PrepWorkspace = ({
    interview,
    jobAnalysis,
    activeRole,
    availableRoles,
    onRoleChange,
    onAddRole,
    onRemoveRole,
    newRoleName,
    onNewRoleNameChange,
    availableStories,
    storyToAdd,
    onStoryToAddChange,
    onAddStory,
    storyDeck,
    onNoteChange,
    onDragStart,
    onDragEnter,
    onDragEnd,
    onRemoveStory,
    editableOpening,
    onChangeOpening,
    editableQuestions,
    onChangeQuestions,
    prepOutline,
    onUpdateRoleIntelligence,
    onUpdateJdInsights,
}: PrepWorkspaceProps) => {
    const roleIntelligence = prepOutline.role_intelligence || {};
    const jdInsights = prepOutline.jd_insights || {};

    const keyMetricsValue = (roleIntelligence.key_success_metrics || []).join('\n');
    const leversValue = (roleIntelligence.role_levers || []).join('\n');
    const blockersValue = (roleIntelligence.potential_blockers || []).join('\n');
    const tagsValue = (jdInsights.tags || []).join('\n');

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 h-full">
            <div className="md:col-span-2 overflow-y-auto space-y-3 pr-0 md:pr-2">
                <CoPilotSection title="Strategic Opening Draft">
                    <textarea
                        value={editableOpening}
                        onChange={(e) => onChangeOpening(e.target.value)}
                        rows={5}
                        className="w-full mt-1 p-2 text-sm text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md"
                    />
                </CoPilotSection>
                <CoPilotSection title="Impact Story Drafting">
                    <div className="space-y-3">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                            <div className="flex flex-wrap items-center gap-2">
                                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Persona</span>
                                <select
                                    value={activeRole}
                                    onChange={(e) => onRoleChange(e.target.value)}
                                    className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-xs px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                >
                                    {availableRoles.map(role => (
                                        <option key={role} value={role}>{role}</option>
                                    ))}
                                </select>
                                {activeRole !== 'default' && (
                                    <button
                                        type="button"
                                        onClick={() => onRemoveRole(activeRole)}
                                        className="inline-flex items-center rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[10px] font-semibold text-red-600 dark:text-red-300 hover:bg-slate-200 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-red-500"
                                    >
                                        Remove Role
                                    </button>
                                )}
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                                <input
                                    type="text"
                                    value={newRoleName}
                                    onChange={(e) => onNewRoleNameChange(e.target.value)}
                                    placeholder="Add interviewer persona"
                                    className="w-48 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                />
                                <button
                                    type="button"
                                    onClick={onAddRole}
                                    disabled={!newRoleName.trim()}
                                    className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-1 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:bg-indigo-300"
                                >
                                    Add Role
                                </button>
                            </div>
                        </div>
                        {availableStories.length > 0 && (
                            <div className="flex flex-wrap items-center gap-2">
                                <select
                                    value={storyToAdd}
                                    onChange={(e) => onStoryToAddChange(e.target.value)}
                                    className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-xs px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                >
                                    <option value="">Add narrative story…</option>
                                    {availableStories.map(story => (
                                        <option key={story.story_id} value={story.story_id}>{story.story_title}</option>
                                    ))}
                                </select>
                                <button
                                    type="button"
                                    onClick={onAddStory}
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
                                        onAppendNotepad={() => undefined}
                                        isEditMode
                                        activeRole={activeRole}
                                        onNoteChange={onNoteChange}
                                        onDragStart={onDragStart}
                                        onDragEnter={onDragEnter}
                                        onDragEnd={onDragEnd}
                                        onRemove={onRemoveStory}
                                    />
                                ))
                            ) : (
                                <p className="text-xs text-slate-500 dark:text-slate-400 text-center">No impact stories defined.</p>
                            )}
                        </div>
                    </div>
                </CoPilotSection>
                <CoPilotSection title="Consultative Close Highlights">
                    <ul className="list-disc pl-4 text-sm space-y-1 text-slate-700 dark:text-slate-300">
                        {(interview.strategic_plan?.key_talking_points || []).map((point, i) => (
                            <li key={i}>{point}</li>
                        ))}
                    </ul>
                </CoPilotSection>
                <CoPilotSection title="Question Drafting">
                    <textarea
                        value={editableQuestions}
                        onChange={(e) => onChangeQuestions(e.target.value)}
                        rows={8}
                        className="w-full mt-1 p-2 text-sm text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md"
                    />
                </CoPilotSection>
            </div>
            <aside className="md:col-span-1 overflow-y-auto space-y-3 pl-0 md:pl-2">
                <CoPilotSection title="Role Intelligence Research">
                    <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
                        <div>
                            <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Core Problem</label>
                            <textarea
                                value={roleIntelligence.core_problem || ''}
                                onChange={(e) => onUpdateRoleIntelligence('core_problem', e.target.value)}
                                rows={3}
                                className="w-full mt-1 p-2 text-xs font-mono bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-md"
                            />
                        </div>
                        <div>
                            <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Suggested Positioning</label>
                            <textarea
                                value={roleIntelligence.suggested_positioning || ''}
                                onChange={(e) => onUpdateRoleIntelligence('suggested_positioning', e.target.value)}
                                rows={3}
                                className="w-full mt-1 p-2 text-xs font-mono bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-md"
                            />
                        </div>
                        <div>
                            <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Key Success Metrics</label>
                            <textarea
                                value={keyMetricsValue}
                                onChange={(e) => onUpdateRoleIntelligence('key_success_metrics', e.target.value, true)}
                                rows={4}
                                className="w-full mt-1 p-2 text-xs font-mono bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-md"
                                placeholder="One metric per line"
                            />
                        </div>
                        <div>
                            <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Role Levers</label>
                            <textarea
                                value={leversValue}
                                onChange={(e) => onUpdateRoleIntelligence('role_levers', e.target.value, true)}
                                rows={4}
                                className="w-full mt-1 p-2 text-xs font-mono bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-md"
                                placeholder="One lever per line"
                            />
                        </div>
                        <div>
                            <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Potential Blockers</label>
                            <textarea
                                value={blockersValue}
                                onChange={(e) => onUpdateRoleIntelligence('potential_blockers', e.target.value, true)}
                                rows={4}
                                className="w-full mt-1 p-2 text-xs font-mono bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-md"
                                placeholder="One blocker per line"
                            />
                        </div>
                    </div>
                </CoPilotSection>
                <CoPilotSection title="JD Insights">
                    <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
                        <div>
                            <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Business Context</label>
                            <textarea
                                value={jdInsights.business_context || ''}
                                onChange={(e) => onUpdateJdInsights('business_context', e.target.value)}
                                rows={3}
                                className="w-full mt-1 p-2 text-xs font-mono bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-md"
                            />
                        </div>
                        <div>
                            <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Strategic Importance</label>
                            <textarea
                                value={jdInsights.strategic_importance || ''}
                                onChange={(e) => onUpdateJdInsights('strategic_importance', e.target.value)}
                                rows={3}
                                className="w-full mt-1 p-2 text-xs font-mono bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-md"
                            />
                        </div>
                        <div>
                            <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Focus Tags</label>
                            <textarea
                                value={tagsValue}
                                onChange={(e) => onUpdateJdInsights('tags', e.target.value, true)}
                                rows={3}
                                className="w-full mt-1 p-2 text-xs font-mono bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-md"
                                placeholder="One tag per line"
                            />
                        </div>
                    </div>
                </CoPilotSection>
            </aside>
        </div>
    );
};

interface LiveRundownProps {
    interview: Interview;
    editableOpening: string;
    prepOutline: InterviewPrepOutline;
    questionList: string[];
    askedQuestions: Set<string>;
    onToggleQuestion: (question: string) => void;
    storyDeck: HydratedDeckItem[];
    activeRole: string;
    availableRoles: string[];
    onRoleChange: (role: string) => void;
    jobAnalysis?: JobProblemAnalysisResult | null;
    onQuickAdd: (text: string) => void;
    keyMetrics: string[];
    roleLevers: string[];
    potentialBlockers: string[];
    covered: CoverageState;
    toggleCoverage: (category: CoverageCategory, value: string) => void;
    resetCoverage: () => void;
    interviewer?: { first_name: string; last_name: string } | undefined;
    coveragePercent: number;
    roleTags: string[];
}

const LiveRundown = ({
    interview,
    editableOpening,
    prepOutline,
    questionList,
    askedQuestions,
    onToggleQuestion,
    storyDeck,
    activeRole,
    availableRoles,
    onRoleChange,
    jobAnalysis,
    onQuickAdd,
    keyMetrics,
    roleLevers,
    potentialBlockers,
    covered,
    toggleCoverage,
    resetCoverage,
    interviewer,
    coveragePercent,
    roleTags,
}: LiveRundownProps) => {
    const roleIntelligence = prepOutline.role_intelligence || {};
    const jdInsights = prepOutline.jd_insights || {};

    const cheatSheetItems = [
        roleIntelligence.core_problem
            ? { label: 'Core Problem', value: roleIntelligence.core_problem }
            : null,
        jdInsights.business_context
            ? { label: 'Business Context', value: jdInsights.business_context }
            : null,
        jdInsights.strategic_importance
            ? { label: 'Strategic Importance', value: jdInsights.strategic_importance }
            : null,
        roleIntelligence.suggested_positioning
            ? { label: 'Suggested Positioning', value: roleIntelligence.suggested_positioning }
            : null,
    ].filter(Boolean) as { label: string; value: string }[];

    const clarifyingLines = [
        'To make sure I tailor my answers, could we clarify:',
        roleIntelligence.core_problem
            ? `• Are we aligned that the core challenge is "${roleIntelligence.core_problem}"?`
            : null,
        (roleIntelligence.key_success_metrics || []).length
            ? `• Which success metrics matter most right now? (${roleIntelligence.key_success_metrics!.join(', ')})`
            : null,
        (roleIntelligence.role_levers || []).length
            ? `• Where do you need the most leverage today? (${roleIntelligence.role_levers!.join(', ')})`
            : null,
        (roleIntelligence.potential_blockers || []).length
            ? `• What blockers are slowing progress? (${roleIntelligence.potential_blockers!.join(', ')})`
            : null,
    ].filter(Boolean) as string[];

    const clarifyingPrompt = clarifyingLines.join('\n');

    const metricsList = keyMetrics.map((metric, index) => {
        const id = `metric-${index}`;
        const isCovered = covered.metrics.has(metric);
        return (
            <li key={id}>
                <button
                    type="button"
                    onClick={() => toggleCoverage('metrics', metric)}
                    className={`flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-sm transition ${isCovered ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-200' : 'hover:bg-slate-200 dark:hover:bg-slate-700/80 text-slate-700 dark:text-slate-200'}`}
                >
                    <span className={`flex h-4 w-4 items-center justify-center rounded border ${isCovered ? 'border-green-600 bg-green-600 text-white' : 'border-slate-400 text-transparent'}`}>
                        <CheckIcon className="h-3 w-3" />
                    </span>
                    <span className={isCovered ? 'line-through' : ''}>{metric}</span>
                </button>
            </li>
        );
    });

    const leversList = roleLevers.map((lever, index) => {
        const isCovered = covered.levers.has(lever);
        return (
            <li key={`lever-${index}`}>
                <button
                    type="button"
                    onClick={() => toggleCoverage('levers', lever)}
                    className={`flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-sm transition ${isCovered ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-200' : 'hover:bg-slate-200 dark:hover:bg-slate-700/80 text-slate-700 dark:text-slate-200'}`}
                >
                    <span className={`flex h-4 w-4 items-center justify-center rounded border ${isCovered ? 'border-green-600 bg-green-600 text-white' : 'border-slate-400 text-transparent'}`}>
                        <CheckIcon className="h-3 w-3" />
                    </span>
                    <span className={isCovered ? 'line-through' : ''}>{lever}</span>
                </button>
            </li>
        );
    });

    const blockersList = potentialBlockers.map((blocker, index) => {
        const isCovered = covered.blockers.has(blocker);
        return (
            <li key={`blocker-${index}`}>
                <button
                    type="button"
                    onClick={() => toggleCoverage('blockers', blocker)}
                    className={`flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-sm transition ${isCovered ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-200' : 'hover:bg-slate-200 dark:hover:bg-slate-700/80 text-slate-700 dark:text-slate-200'}`}
                >
                    <span className={`flex h-4 w-4 items-center justify-center rounded border ${isCovered ? 'border-green-600 bg-green-600 text-white' : 'border-slate-400 text-transparent'}`}>
                        <CheckIcon className="h-3 w-3" />
                    </span>
                    <span className={isCovered ? 'line-through' : ''}>{blocker}</span>
                </button>
            </li>
        );
    });

    return (
        <div className="md:col-span-2 overflow-y-auto space-y-3 pr-0 md:pr-2">
            <CoPilotSection title="Job Cheat Sheet">
                <div className="space-y-2 text-sm text-slate-700 dark:text-slate-200">
                    {cheatSheetItems.length > 0 ? (
                        cheatSheetItems.map(item => (
                            <div key={item.label}>
                                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{item.label}</p>
                                <p className="mt-1 whitespace-pre-wrap">{item.value}</p>
                            </div>
                        ))
                    ) : (
                        <p className="text-sm text-slate-500 dark:text-slate-400">Add research in prep mode to populate this cheat sheet.</p>
                    )}
                    {roleTags.length > 0 && (
                        <div>
                            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Focus Tags</p>
                            <p className="mt-1 text-sm">{roleTags.join(', ')}</p>
                        </div>
                    )}
                </div>
            </CoPilotSection>
            <CoPilotSection title="Clarifying Prompt Launcher">
                <div className="space-y-2">
                    <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 p-2 text-xs font-mono text-slate-700 dark:text-slate-200 whitespace-pre-wrap">
                        {clarifyingPrompt || 'Draft clarifying prompts in prep mode to launch them quickly during the interview.'}
                    </div>
                    {clarifyingPrompt && (
                        <button
                            type="button"
                            onClick={() => onQuickAdd(clarifyingPrompt)}
                            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700"
                        >
                            <SparklesIcon className="h-4 w-4" /> Send to Notes
                        </button>
                    )}
                </div>
            </CoPilotSection>
            <CoPilotSection title="Top of Mind">
                <div className="text-xs space-y-1 text-slate-600 dark:text-slate-300">
                    <p><strong>Interviewing with:</strong> {interviewer ? `${interviewer.first_name} ${interviewer.last_name}` : 'TBD'}</p>
                    <p><strong>Format:</strong> {interview.interview_type}</p>
                </div>
            </CoPilotSection>
            <CoPilotSection title="Strategic Opening">
                <p className="text-sm italic text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{editableOpening}</p>
            </CoPilotSection>
            <CoPilotSection title="Question Arsenal">
                <div className="space-y-2">
                    {questionList.length > 0 ? (
                        questionList.map((question, index) => {
                            const id = `live-question-${index}`;
                            return (
                                <div key={id} className="relative flex items-start">
                                    <div className="flex h-6 items-center">
                                        <input
                                            id={id}
                                            type="checkbox"
                                            checked={askedQuestions.has(question)}
                                            onChange={() => onToggleQuestion(question)}
                                            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                    </div>
                                    <div className="ml-3 text-sm leading-6">
                                        <label htmlFor={id} className={`text-slate-700 dark:text-slate-300 ${askedQuestions.has(question) ? 'line-through text-slate-400 dark:text-slate-500' : ''}`}>
                                            {question}
                                        </label>
                                    </div>
                                </div>
                            );
                        })
                    ) : (
                        <p className="text-sm text-slate-500 dark:text-slate-400">Add strategic questions in prep mode.</p>
                    )}
                </div>
            </CoPilotSection>
            <CoPilotSection title="Impact Story Triggers">
                <div className="space-y-3">
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Persona</span>
                        <select
                            value={activeRole}
                            onChange={(e) => onRoleChange(e.target.value)}
                            className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-xs px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        >
                            {availableRoles.map(role => (
                                <option key={role} value={role}>{role}</option>
                            ))}
                        </select>
                    </div>
                    <div className="space-y-2">
                        {storyDeck.length > 0 ? (
                            storyDeck.map(item => (
                                <ImpactStoryTrigger
                                    key={item.story_id}
                                    item={item}
                                    jobAnalysis={jobAnalysis}
                                    onAppendNotepad={onQuickAdd}
                                    isEditMode={false}
                                    activeRole={activeRole}
                                    onNoteChange={() => undefined}
                                />
                            ))
                        ) : (
                            <p className="text-xs text-slate-500 dark:text-slate-400 text-center">No impact stories defined.</p>
                        )}
                    </div>
                </div>
            </CoPilotSection>
            <CoPilotSection title="Live Checklist">
                <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                        <span>Coverage</span>
                        <span>{coveragePercent}% complete</span>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <div className="flex items-center justify-between">
                                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Key Success Metrics</p>
                                {keyMetrics.length > 0 && (
                                    <button
                                        type="button"
                                        onClick={() => onQuickAdd(`Key Success Metrics:\n${keyMetrics.map(metric => `• ${metric}`).join('\n')}`)}
                                        className="inline-flex items-center gap-1 rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[10px] font-semibold text-slate-600 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
                                    >
                                        <ClipboardDocumentCheckIcon className="h-4 w-4" /> Copy
                                    </button>
                                )}
                            </div>
                            <ul className="mt-2 space-y-1">{metricsList}</ul>
                        </div>
                        <div>
                            <div className="flex items-center justify-between">
                                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Levers</p>
                                {roleLevers.length > 0 && (
                                    <button
                                        type="button"
                                        onClick={() => onQuickAdd(`Levers:\n${roleLevers.map(lever => `• ${lever}`).join('\n')}`)}
                                        className="inline-flex items-center gap-1 rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[10px] font-semibold text-slate-600 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
                                    >
                                        <ClipboardDocumentCheckIcon className="h-4 w-4" /> Copy
                                    </button>
                                )}
                            </div>
                            <ul className="mt-2 space-y-1">{leversList}</ul>
                        </div>
                        <div>
                            <div className="flex items-center justify-between">
                                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Potential Blockers</p>
                                {potentialBlockers.length > 0 && (
                                    <button
                                        type="button"
                                        onClick={() => onQuickAdd(`Potential Blockers:\n${potentialBlockers.map(blocker => `• ${blocker}`).join('\n')}`)}
                                        className="inline-flex items-center gap-1 rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[10px] font-semibold text-slate-600 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
                                    >
                                        <ClipboardDocumentCheckIcon className="h-4 w-4" /> Copy
                                    </button>
                                )}
                            </div>
                            <ul className="mt-2 space-y-1">{blockersList}</ul>
                        </div>
                        <button
                            type="button"
                            onClick={resetCoverage}
                            className="inline-flex items-center gap-1 rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[10px] font-semibold text-slate-600 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
                        >
                            Reset Checklist
                        </button>
                    </div>
                </div>
            </CoPilotSection>
            <CoPilotSection title="Hot Leads (30-60-90 Plan)">
                <ul className="list-disc pl-4 text-sm space-y-1 text-slate-700 dark:text-slate-300">
                    {(interview.strategic_plan?.key_talking_points || []).map((point, i) => (
                        <li key={i}>{point}</li>
                    ))}
                </ul>
            </CoPilotSection>
        </div>
    );
};

export const InterviewCopilotView = ({ application, interview, company, activeNarrative, onBack, onSaveInterview, onGenerateInterviewPrep, onGenerateRecruiterScreenPrep }: InterviewCopilotViewProps) => {
    const [isEditMode, setIsEditMode] = useState(false);
    const [editableOpening, setEditableOpening] = useState('');
    const [editableQuestions, setEditableQuestions] = useState('');
    const [liveNotes, setLiveNotes] = useState('');
    const [askedQuestions, setAskedQuestions] = useState<Set<string>>(new Set());
    const [storyDeck, setStoryDeck] = useState<HydratedDeckItem[]>(() => buildHydratedDeck(interview, activeNarrative));
    const [activeRole, setActiveRole] = useState('default');
    const [draggingStoryId, setDraggingStoryId] = useState<string | null>(null);
    const [newRoleName, setNewRoleName] = useState('');
    const [storyToAdd, setStoryToAdd] = useState('');
    const [covered, setCovered] = useState<CoverageState>(createEmptyCoverageState);
    const [prepOutline, setPrepOutline] = useState<InterviewPrepOutline>(() =>
        buildPrepOutline(application.job_problem_analysis_result, interview.prep_outline)
    );

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
        setLiveNotes(interview.live_notes || '');
        setPrepOutline(buildPrepOutline(application.job_problem_analysis_result, interview.prep_outline));
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

    const updateRoleIntelligence = (
        field: keyof NonNullable<InterviewPrepOutline['role_intelligence']>,
        value: string,
        isList: boolean = false,
    ) => {
        setPrepOutline(prev => {
            const current = { ...(prev.role_intelligence || {}) } as Record<string, unknown>;
            current[field as string] = isList ? sanitizeListInput(value) : value;
            return {
                ...prev,
                role_intelligence: current as InterviewPrepOutline['role_intelligence'],
            };
        });
    };

    const updateJdInsights = (
        field: keyof NonNullable<InterviewPrepOutline['jd_insights']>,
        value: string,
        isList: boolean = false,
    ) => {
        setPrepOutline(prev => {
            const current = { ...(prev.jd_insights || {}) } as Record<string, unknown>;
            current[field as string] = isList ? sanitizeListInput(value) : value;
            return {
                ...prev,
                jd_insights: current as InterviewPrepOutline['jd_insights'],
            };
        });
    };

    const handleSave = async () => {
        setIsSaving(true);
        setSaveSuccess(false);
        try {
            const payload: InterviewPayload = {
                strategic_opening: editableOpening,
                strategic_questions_to_ask: questionList,
                story_deck: serializeDeck(storyDeck),
                prep_outline: prepOutline,
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
            await onSaveInterview({ live_notes: liveNotes }, interview.interview_id);
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
        setLiveNotes(prev => appendUnique(prev, text));
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
                             <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Live Mode</span>
                            <Switch enabled={isEditMode} onChange={setIsEditMode} />
                            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Prep Mode</span>
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

                <main className="flex-1 overflow-hidden p-3">
                    {isEditMode ? (
                        <PrepWorkspace
                            interview={interview}
                            jobAnalysis={jobAnalysis}
                            activeRole={activeRole}
                            availableRoles={availableRoles}
                            onRoleChange={setActiveRole}
                            onAddRole={handleAddRole}
                            onRemoveRole={handleRemoveRole}
                            newRoleName={newRoleName}
                            onNewRoleNameChange={setNewRoleName}
                            availableStories={availableStories}
                            storyToAdd={storyToAdd}
                            onStoryToAddChange={setStoryToAdd}
                            onAddStory={handleAddStory}
                            storyDeck={storyDeck}
                            onNoteChange={handleNoteChange}
                            onDragStart={handleDragStart}
                            onDragEnter={handleDragEnter}
                            onDragEnd={handleDragEnd}
                            onRemoveStory={handleRemoveStory}
                            editableOpening={editableOpening}
                            onChangeOpening={setEditableOpening}
                            editableQuestions={editableQuestions}
                            onChangeQuestions={setEditableQuestions}
                            prepOutline={prepOutline}
                            onUpdateRoleIntelligence={updateRoleIntelligence}
                            onUpdateJdInsights={updateJdInsights}
                        />
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 h-full">
                            <LiveRundown
                                interview={interview}
                                editableOpening={editableOpening}
                                prepOutline={prepOutline}
                                questionList={questionList}
                                askedQuestions={askedQuestions}
                                onToggleQuestion={handleQuestionToggle}
                                storyDeck={storyDeck}
                                activeRole={activeRole}
                                availableRoles={availableRoles}
                                onRoleChange={setActiveRole}
                                jobAnalysis={jobAnalysis}
                                onQuickAdd={handleQuickAdd}
                                keyMetrics={keyMetrics}
                                roleLevers={roleLevers}
                                potentialBlockers={potentialBlockers}
                                covered={covered}
                                toggleCoverage={toggleCoverage}
                                resetCoverage={resetCoverage}
                                interviewer={interviewer}
                                coveragePercent={coveragePercent}
                                roleTags={roleTags}
                            />
                            <aside className="md:col-span-1 overflow-y-auto h-full flex flex-col">
                                <CoPilotSection title="Live Notes" className="flex-grow flex flex-col">
                                    <div className="flex items-center justify-between mb-2">
                                        <p className="text-[11px] text-slate-500 dark:text-slate-400">Captured during the conversation</p>
                                        <button
                                            onClick={handleSaveNotes}
                                            disabled={isSavingNotes}
                                            className={`inline-flex items-center justify-center gap-1 rounded-md px-3 py-1.5 text-xs font-semibold shadow-sm transition-colors ${
                                                notesSuccess ? 'bg-green-600 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white disabled:bg-blue-400'
                                            }`}
                                        >
                                            {isSavingNotes ? (
                                                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                                            ) : notesSuccess ? (
                                                <CheckIcon className="h-4 w-4" />
                                            ) : (
                                                'Save Notes'
                                            )}
                                        </button>
                                    </div>
                                    <textarea
                                        value={liveNotes}
                                        onChange={(e) => setLiveNotes(e.target.value)}
                                        className="w-full flex-grow p-2 text-sm bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md"
                                        placeholder="Capture wins, fumbles, and new intelligence in real time…"
                                    />
                                </CoPilotSection>
                            </aside>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};
