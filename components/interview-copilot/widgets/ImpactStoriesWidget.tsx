import React, { useEffect, useMemo, useState } from 'react';
import type { WidgetProps } from '../types';
import type { ImpactStoriesData } from '../types';
import { formatTimestamp } from '../utils';
import {
    ensureRoleOnDeck,
    removeRoleFromDeck,
    updateDeckOrder,
    upsertDeckStory,
} from '../../../utils/interviewDeck';
import type { HydratedDeckItem } from '../../../utils/interviewDeck';
import { GripVerticalIcon, SparklesIcon } from '../../../components/IconComponents';

const STORY_FORMAT_FIELDS: Record<string, string[]> = {
    STAR: ['situation', 'task', 'action', 'result'],
    SCOPE: ['situation', 'complication', 'opportunity', 'product_thinking', 'end_result'],
    WINS: ['situation', 'what_i_did', 'impact', 'nuance'],
    SPOTLIGHT: [
        'situation',
        'positive_moment_or_goal',
        'observation_opportunity',
        'task_action',
        'learnings_leverage',
        'impact_results',
        'growth_grit',
        'highlights_key_trait',
        'takeaway_tie_in',
    ],
};

const STORY_FORMAT_COLORS: Record<string, string> = {
    STAR: 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300',
    SCOPE: 'bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300',
    WINS: 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300',
    SPOTLIGHT: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300',
};

const readableLabel = (key: string) => key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

const ImpactStoryTrigger = ({
    item,
    activeRole,
    onNoteChange,
    isPrep,
}: {
    item: HydratedDeckItem;
    activeRole: string;
    onNoteChange: (storyId: string, field: string, value: string) => void;
    isPrep: boolean;
}) => {
    const story = item.story;
    if (!story) {
        return null;
    }
    const formatName = (story.format || 'STAR').toUpperCase();
    const badgeColor = STORY_FORMAT_COLORS[formatName] || STORY_FORMAT_COLORS.STAR;
    const orderedFields = STORY_FORMAT_FIELDS[formatName] || [];
    const roleNotes = item.custom_notes[activeRole] || item.custom_notes.default || {};

    return (
        <div className="space-y-3 rounded-md border border-slate-300 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <div className="flex items-center justify-between gap-3">
                <div>
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{story.story_title}</h4>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{story.context_summary}</p>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${badgeColor}`}>{story.format}</span>
            </div>
            <div className="space-y-2">
                {orderedFields.map((field) => {
                    const label = readableLabel(field);
                    const defaultValue = story.speaker_notes?.[field] || '';
                    const value = roleNotes?.[field] ?? defaultValue;
                    if (!isPrep && !value) {
                        return null;
                    }
                    return (
                        <div key={field}>
                            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</p>
                            {isPrep ? (
                                <textarea
                                    value={value}
                                    onChange={(event) => onNoteChange(item.story_id, field, event.target.value)}
                                    rows={2}
                                    className="mt-1 w-full rounded-md border border-slate-300 bg-white p-2 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                                />
                            ) : (
                                <p className="mt-1 whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200">{value || defaultValue}</p>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export const ImpactStoriesWidget = ({
    data,
    onChange,
    editable,
    mode,
    lastUpdated,
    context,
}: WidgetProps<ImpactStoriesData>) => {
    const [draggingStoryId, setDraggingStoryId] = useState<string | null>(null);
    const availableStories = context.availableStories || [];
    const hasAvailableStories = availableStories.length > 0;

    const availableRoles = useMemo(() => {
        const roles = new Set<string>(['default']);
        data.storyDeck.forEach((item) => {
            Object.keys(item.custom_notes).forEach((role) => roles.add(role));
        });
        return Array.from(roles);
    }, [data.storyDeck]);

    useEffect(() => {
        if (!availableRoles.includes(data.activeRole)) {
            onChange({ ...data, activeRole: availableRoles[0] || 'default' });
        }
    }, [availableRoles, data.activeRole, onChange, data]);

    const handleRoleChange = (role: string) => {
        const updatedDeck = ensureRoleOnDeck(data.storyDeck, role);
        onChange({ ...data, activeRole: role, storyDeck: updatedDeck });
    };

    const handleAddRole = () => {
        const trimmed = data.newRoleName.trim();
        if (!trimmed || availableRoles.includes(trimmed)) {
            return;
        }
        const updatedDeck = ensureRoleOnDeck(data.storyDeck, trimmed);
        onChange({ ...data, activeRole: trimmed, newRoleName: '', storyDeck: updatedDeck });
    };

    const handleRemoveRole = (role: string) => {
        if (role === 'default') {
            return;
        }
        const updatedDeck = removeRoleFromDeck(data.storyDeck, role);
        const remainingRoles = availableRoles.filter((value) => value !== role);
        onChange({
            ...data,
            activeRole: remainingRoles[0] || 'default',
            storyDeck: updatedDeck,
        });
    };

    const handleNoteChange = (storyId: string, field: string, value: string) => {
        const updatedDeck = data.storyDeck.map((item) => {
            if (item.story_id !== storyId) {
                return item;
            }
            const current = item.custom_notes[data.activeRole] || {};
            return {
                ...item,
                custom_notes: {
                    ...item.custom_notes,
                    [data.activeRole]: {
                        ...current,
                        [field]: value,
                    },
                },
            };
        });
        onChange({ ...data, storyDeck: updatedDeck });
    };

    const handleDragEnter = (storyId: string) => {
        if (!draggingStoryId || draggingStoryId === storyId) {
            return;
        }
        const updated = updateDeckOrder(data.storyDeck, draggingStoryId, storyId);
        onChange({ ...data, storyDeck: updated });
    };

    const handleAddStory = () => {
        const targetStory = availableStories.find((story) => story.story_id === data.storyToAdd);
        if (!targetStory) {
            return;
        }
        const updatedDeck = upsertDeckStory(data.storyDeck, targetStory);
        onChange({ ...data, storyDeck: updatedDeck, storyToAdd: '' });
    };

    const handleRemoveStory = (storyId: string) => {
        const updatedDeck = data.storyDeck.filter((item) => item.story_id !== storyId);
        const reindexed = updatedDeck.map((item, index) => ({ ...item, order_index: index }));
        onChange({ ...data, storyDeck: reindexed });
    };

    const liveView = (
        <div className="space-y-3">
            <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Persona</span>
                <select
                    value={data.activeRole}
                    onChange={(event) => handleRoleChange(event.target.value)}
                    className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs dark:border-slate-600 dark:bg-slate-800"
                >
                    {availableRoles.map((role) => (
                        <option key={role} value={role}>
                            {role}
                        </option>
                    ))}
                </select>
            </div>
            <div className="space-y-2">
                {data.storyDeck.length > 0 ? (
                    data.storyDeck.map((item) => (
                        <ImpactStoryTrigger key={item.story_id} item={item} activeRole={data.activeRole} onNoteChange={handleNoteChange} isPrep={false} />
                    ))
                ) : (
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        {hasAvailableStories
                            ? 'Add stories in prep mode to surface them here.'
                            : 'No stories available yet. Add impact stories to your narrative to populate this section.'}
                    </p>
                )}
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
        </div>
    );

    if (!editable || mode === 'live') {
        return liveView;
    }

    const availableStoryOptions = availableStories.filter((story) => !data.storyDeck.some((item) => item.story_id === story.story_id));

    return (
        <div className="space-y-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Persona</span>
                    <select
                        value={data.activeRole}
                        onChange={(event) => handleRoleChange(event.target.value)}
                        className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800"
                    >
                        {availableRoles.map((role) => (
                            <option key={role} value={role}>
                                {role}
                            </option>
                        ))}
                    </select>
                    {data.activeRole !== 'default' && (
                        <button
                            type="button"
                            onClick={() => handleRemoveRole(data.activeRole)}
                            className="inline-flex items-center rounded-md border border-slate-300 px-2 py-1 text-[10px] font-semibold text-red-600 shadow-sm hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-red-500 dark:border-slate-600 dark:text-red-300 dark:hover:bg-slate-700"
                        >
                            Remove Role
                        </button>
                    )}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                    <input
                        type="text"
                        value={data.newRoleName}
                        onChange={(event) => onChange({ ...data, newRoleName: event.target.value })}
                        placeholder="Add new persona"
                        className="w-full max-w-xs rounded-md border border-slate-300 bg-white px-2 py-1 text-xs shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800"
                    />
                    <button
                        type="button"
                        onClick={handleAddRole}
                        className="inline-flex items-center rounded-md bg-indigo-600 px-2 py-1 text-[10px] font-semibold text-white shadow-sm hover:bg-indigo-700"
                    >
                        Add Persona
                    </button>
                </div>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <select
                    value={data.storyToAdd}
                    onChange={(event) => onChange({ ...data, storyToAdd: event.target.value })}
                    disabled={!hasAvailableStories}
                    className="w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-xs shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800"
                >
                    <option value="">Select story to add</option>
                    {availableStoryOptions.map((story) => (
                        <option key={story.story_id} value={story.story_id}>
                            {story.story_title}
                        </option>
                    ))}
                </select>
                <button
                    type="button"
                    onClick={handleAddStory}
                    disabled={!hasAvailableStories || !data.storyToAdd}
                    className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
                >
                    <SparklesIcon className="h-4 w-4" /> Add Story
                </button>
            </div>
            {!hasAvailableStories && (
                <p className="text-xs text-slate-500 dark:text-slate-400">
                    Add impact stories to your narrative in the Positioning Hub to enable this widget.
                </p>
            )}
            <div className="space-y-3">
                {data.storyDeck.length > 0 ? (
                    data.storyDeck.map((item) => (
                        <div
                            key={item.story_id}
                            className="cursor-grab rounded-md border border-dashed border-slate-300 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-slate-800"
                            draggable
                            onDragStart={() => setDraggingStoryId(item.story_id)}
                            onDragOver={(event) => {
                                event.preventDefault();
                                handleDragEnter(item.story_id);
                            }}
                            onDragEnd={() => setDraggingStoryId(null)}
                        >
                            <div className="flex items-center justify-between gap-2">
                                <div className="flex items-center gap-2">
                                    <GripVerticalIcon className="h-4 w-4 text-slate-400" />
                                    <div>
                                        <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{item.story?.story_title || 'Untitled Story'}</p>
                                        <p className="text-xs text-slate-500 dark:text-slate-400">{item.story?.context_summary}</p>
                                    </div>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => handleRemoveStory(item.story_id)}
                                    className="rounded-md border border-slate-300 px-2 py-1 text-[10px] font-semibold text-red-600 hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-red-500 dark:border-slate-600 dark:text-red-300 dark:hover:bg-slate-700"
                                >
                                    Remove
                                </button>
                            </div>
                            <div className="mt-3">
                                <ImpactStoryTrigger item={item} activeRole={data.activeRole} onNoteChange={handleNoteChange} isPrep />
                            </div>
                        </div>
                    ))
                ) : (
                    <p className="text-sm text-slate-500 dark:text-slate-400">Add stories from your narrative to craft tailored talking points.</p>
                )}
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
        </div>
    );
};

export default ImpactStoriesWidget;
