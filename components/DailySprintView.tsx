import React, { useState, useEffect, useMemo } from 'react';
import { Prompt, StrategicNarrative, Sprint, SprintAction, GoalType, GOAL_TYPES, CreateSprintPayload, SprintActionPayload, AiSprintAction, PromptContext, JobApplication, Contact, LinkedInPost, Message } from '../types';
import * as geminiService from '../services/geminiService';
import { LoadingSpinner, RocketLaunchIcon, SparklesIcon, CheckIcon, PlusCircleIcon, TrashIcon } from './IconComponents';
import { TagInput } from './TagInput';

interface DailySprintViewProps {
    prompts: Prompt[];
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
    activeNarrative: StrategicNarrative | null;
    sprint: Sprint | null;
    onCreateSprint: (payload: CreateSprintPayload) => Promise<void>;
    onUpdateSprint: (sprintId: string, payload: Partial<Sprint>) => Promise<void>;
    onUpdateAction: (actionId: string, payload: SprintActionPayload) => Promise<void>;
    onAddActions: (sprintId: string, actions: SprintActionPayload[]) => Promise<void>;
    applications: JobApplication[];
    contacts: Contact[];
    linkedInPosts: LinkedInPost[];
    allMessages: Message[];
}

const effortOptions = ["Low (<1h)", "Medium (1-3h)", "High (3h+)", "Quick Task"];

const SprintCreationView = ({ onCreateSprint, activeNarrative }: { onCreateSprint: DailySprintViewProps['onCreateSprint'], activeNarrative: StrategicNarrative | null }) => {
    const [theme, setTheme] = useState('');
    const [mode, setMode] = useState<'search' | 'career'>('search');
    const [goals, setGoals] = useState<Omit<SprintActionPayload, 'sprint_id'>[]>([
        { title: 'Applications Goal', is_completed: false, is_goal: true, goal_type: 'applications', goal_target: 50, order_index: 0 },
        { title: 'Contacts Goal', is_completed: false, is_goal: true, goal_type: 'contacts', goal_target: 100, order_index: 1 },
    ]);
    
    // New strategic fields state
    const [tags, setTags] = useState<string[]>([]);
    const [strategicScore, setStrategicScore] = useState<number>(7.5);

    const handleCreate = () => {
        const validGoals = goals.filter(g => g.goal_target && g.goal_target > 0);
        const payload: CreateSprintPayload = {
            theme,
            mode,
            actions: validGoals,
            tags,
            strategic_score: strategicScore,
        };
        onCreateSprint(payload);
    };

    const handleGoalChange = (index: number, field: 'goal_type' | 'goal_target', value: string | number) => {
        const newGoals = [...goals];
        if (field === 'goal_type') {
            newGoals[index].goal_type = value as GoalType;
        } else {
            newGoals[index].goal_target = Number(value) || 0;
        }
        setGoals(newGoals);
    };

    const addGoal = () => {
        setGoals([...goals, { title: 'New Goal', is_completed: false, is_goal: true, goal_type: 'posts', goal_target: 2, order_index: goals.length }]);
    };

    const removeGoal = (index: number) => {
        setGoals(goals.filter((_, i) => i !== index));
    };


    return (
        <div className="text-center py-10 max-w-2xl mx-auto">
            <RocketLaunchIcon className="mx-auto h-12 w-12 text-slate-400" />
            <h2 className="mt-2 text-xl font-bold text-slate-800 dark:text-slate-200">Start a New Weekly Sprint</h2>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Set your theme and goals to generate an action plan.</p>
            <div className="mt-6 text-left space-y-4">
                 <input type="text" value={theme} onChange={e => setTheme(e.target.value)} placeholder="Theme of the week (e.g., 'Targeted Outreach to Series B')" className="w-full p-2 rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700" />
                 <TagInput tags={tags} onTagsChange={setTags} label="Strategic Tags" />
                 <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Strategic Value Score: {strategicScore.toFixed(1)}</label>
                    <input type="range" min="0" max="10" step="0.5" value={strategicScore} onChange={e => setStrategicScore(parseFloat(e.target.value))} className="w-full" />
                 </div>
                 <div className="space-y-3 pt-4 border-t border-slate-200 dark:border-slate-700">
                    <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">Set Your Weekly Goals</h3>
                    {goals.map((goal, index) => (
                        <div key={index} className="flex items-center gap-2">
                            <select
                                value={goal.goal_type || ''}
                                onChange={e => handleGoalChange(index, 'goal_type', e.target.value)}
                                className="p-2 rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                            >
                                {GOAL_TYPES.map(type => <option key={type} value={type} className="capitalize">{type}</option>)}
                            </select>
                            <input
                                type="number"
                                value={goal.goal_target || ''}
                                onChange={e => handleGoalChange(index, 'goal_target', e.target.value)}
                                className="w-24 p-2 rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                                placeholder="Target"
                            />
                            <button type="button" onClick={() => removeGoal(index)} className="p-1 text-red-500 hover:text-red-400">
                                <TrashIcon className="h-5 w-5" />
                            </button>
                        </div>
                    ))}
                    <button type="button" onClick={addGoal} className="text-sm font-semibold text-blue-600 hover:underline flex items-center gap-1">
                        <PlusCircleIcon className="h-4 w-4" /> Add Goal
                    </button>
                 </div>
            </div>
            <button onClick={handleCreate} disabled={!theme && !goals.some(g => g.goal_target && g.goal_target > 0)} className="mt-6 inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400">
                Create Sprint
            </button>
        </div>
    );
};

const GoalProgressDisplay = ({ goal, currentProgress, onUpdateAction }: { goal: SprintAction; currentProgress: number; onUpdateAction: (actionId: string, payload: SprintActionPayload) => Promise<void>; }) => {
    const [isEditingTarget, setIsEditingTarget] = useState(false);
    const [newTarget, setNewTarget] = useState(goal.goal_target);

    const handleTargetSave = () => {
        if (newTarget !== goal.goal_target) {
            onUpdateAction(goal.action_id, { goal_target: Number(newTarget) });
        }
        setIsEditingTarget(false);
    };

    const target = goal.goal_target || 0;
    const percentage = target > 0 ? (currentProgress / target) * 100 : 0;

    return (
        <div className="p-3 bg-slate-50 dark:bg-slate-800/80 rounded-lg">
            <div className="flex justify-between items-baseline">
                <p className="text-sm capitalize text-slate-500 dark:text-slate-400">{goal.goal_type}</p>
                <div className="text-sm font-semibold text-slate-800 dark:text-slate-200" onClick={() => setIsEditingTarget(true)}>
                    <span>{currentProgress}/</span>
                    {isEditingTarget ? (
                        <input
                            type="number"
                            value={newTarget || ''}
                            onChange={e => setNewTarget(Number(e.target.value))}
                            onBlur={handleTargetSave}
                            onKeyDown={e => e.key === 'Enter' && handleTargetSave()}
                            autoFocus
                            className="w-12 text-right bg-transparent p-0 border-0 border-b-2 border-blue-500 focus:ring-0 text-slate-800 dark:text-slate-200"
                        />
                    ) : (
                        <span className="cursor-pointer">{target}</span>
                    )}
                </div>
            </div>
            <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2.5 mt-2">
                <div className="bg-blue-600 h-2.5 rounded-full transition-all duration-500" style={{ width: `${Math.min(percentage, 100)}%` }}></div>
            </div>
        </div>
    );
};

export const DailySprintView = (props: DailySprintViewProps): React.ReactNode => {
    const { prompts, debugCallbacks, activeNarrative, sprint, onCreateSprint, onUpdateSprint, onUpdateAction, onAddActions, applications, contacts, linkedInPosts, allMessages } = props;
    const [expandedActionId, setExpandedActionId] = useState<string | null>(null);
    const [newActionTitle, setNewActionTitle] = useState('');
    const [newActionImpact, setNewActionImpact] = useState('');
    
    const progress = useMemo(() => {
        if (!sprint) return {};

        const startDate = new Date(sprint.start_date + 'T00:00:00Z');
        const endDate = new Date(startDate);
        endDate.setUTCDate(startDate.getUTCDate() + 7);

        const filterByDate = (dateStr: string) => {
            const itemDate = new Date(dateStr);
            return itemDate >= startDate && itemDate < endDate;
        };

        const appsThisWeek = applications.filter(a => filterByDate(a.date_applied)).length;
        const contactsThisWeek = contacts.filter(c => filterByDate(c.date_contacted)).length;
        const postsThisWeek = linkedInPosts.filter(p => filterByDate(p.created_at)).length;
        const followUpsThisWeek = allMessages.filter(m => m.message_type === 'Follow-up' && filterByDate(m.created_at)).length;

        return {
            applications: appsThisWeek,
            contacts: contactsThisWeek,
            posts: postsThisWeek,
            'follow-ups': followUpsThisWeek,
        };
    }, [sprint, applications, contacts, linkedInPosts, allMessages]);


    const handleUpdateActionField = (actionId: string, field: keyof SprintActionPayload, value: any) => {
        onUpdateAction(actionId, { [field]: value });
    };

    const handleAddNewAction = () => {
        if (!newActionTitle.trim() || !sprint) return;
        const newAction: SprintActionPayload = {
            title: newActionTitle,
            impact: newActionImpact,
            is_completed: false,
            is_goal: false,
            order_index: (sprint.actions.filter(a => !a.is_goal).length || 0),
        };
        onAddActions(sprint.sprint_id, [newAction]);
        setNewActionTitle('');
        setNewActionImpact('');
    };

    if (!sprint) {
        return <SprintCreationView onCreateSprint={onCreateSprint} activeNarrative={activeNarrative} />;
    }
    
    const goals = sprint.actions.filter(a => a.is_goal);
    const tasks = sprint.actions.filter(a => !a.is_goal);

    return (
        <div className="space-y-8 animate-fade-in">
            <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{sprint.theme || 'Weekly Sprint'}</h1>
                <div className="mt-2 flex items-center gap-4">
                    <div className="flex items-center gap-x-2">
                        <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">Strategic Score:</span>
                        <span className="font-bold text-lg text-blue-600 dark:text-blue-400">{sprint.strategic_score?.toFixed(1) || 'N/A'}</span>
                    </div>
                    <div className="flex items-center gap-x-2 flex-wrap">
                        {(sprint.tags || []).map(tag => (
                             <span key={tag} className="px-2 py-1 text-xs font-medium rounded-full bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300">{tag}</span>
                        ))}
                    </div>
                </div>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold text-lg text-slate-900 dark:text-white mb-4">Weekly Goals</h3>
                 <p className="text-xs text-slate-400 -mt-3 mb-4">Click on a number to edit a goal target.</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {goals.map(goal => (
                        <GoalProgressDisplay
                            key={goal.action_id}
                            goal={goal}
                            currentProgress={progress[goal.goal_type as GoalType] || 0}
                            onUpdateAction={onUpdateAction}
                        />
                    ))}
                </div>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold text-lg text-slate-900 dark:text-white mb-4">To-Do List</h3>
                 <ul className="space-y-3">
                    {tasks.map((action) => (
                        <li key={action.action_id} className="p-3 rounded-md bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
                            <div className="flex items-start">
                                <input
                                    type="checkbox"
                                    id={`action-${action.action_id}`}
                                    checked={action.is_completed}
                                    onChange={() => onUpdateAction(action.action_id, { is_completed: !action.is_completed })}
                                    className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 mt-0.5"
                                />
                                <div className="ml-3 text-sm flex-grow">
                                    <label htmlFor={`action-${action.action_id}`} className={`font-medium ${action.is_completed ? 'text-slate-400 line-through' : 'text-slate-700 dark:text-slate-300'}`}>
                                        {action.title}
                                    </label>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                        {(action.strategic_tags || []).map(tag => (
                                            <span key={tag} className="px-1.5 py-0.5 text-xs rounded bg-sky-100 text-sky-800 dark:bg-sky-900/50 dark:text-sky-300">{tag}</span>
                                        ))}
                                    </div>
                                </div>
                                <button onClick={() => setExpandedActionId(expandedActionId === action.action_id ? null : action.action_id)} className="text-xs font-semibold text-blue-600 hover:underline">
                                    {expandedActionId === action.action_id ? 'Hide' : 'Details'}
                                </button>
                            </div>
                            {expandedActionId === action.action_id && (
                                <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-600 space-y-3">
                                    <TagInput tags={action.strategic_tags || []} onTagsChange={(tags) => handleUpdateActionField(action.action_id, 'strategic_tags', tags)} label="Strategic Tags" />
                                    <div>
                                        <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Impact</label>
                                        <input type="text" defaultValue={action.impact || ''} onBlur={(e) => handleUpdateActionField(action.action_id, 'impact', e.target.value)} className="w-full p-1 text-sm mt-1 rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700" />
                                    </div>
                                     <div>
                                        <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Measurable Value</label>
                                        <input type="text" defaultValue={action.measurable_value || ''} onBlur={(e) => handleUpdateActionField(action.action_id, 'measurable_value', e.target.value)} className="w-full p-1 text-sm mt-1 rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700" />
                                    </div>
                                     <div>
                                        <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Effort Estimate</label>
                                        <select defaultValue={action.effort_estimate || ''} onBlur={(e) => handleUpdateActionField(action.action_id, 'effort_estimate', e.target.value)} className="w-full p-1 text-sm mt-1 rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700">
                                            <option value="">Select...</option>
                                            {effortOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                                        </select>
                                    </div>
                                </div>
                            )}
                        </li>
                    ))}
                </ul>
                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-600">
                    <h4 className="font-semibold text-slate-800 dark:text-slate-200">Add New Task</h4>
                    <div className="mt-2 space-y-2">
                        <input
                            type="text"
                            value={newActionTitle}
                            onChange={e => setNewActionTitle(e.target.value)}
                            placeholder="Task title..."
                            className="w-full p-2 rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                        />
                        <textarea
                            value={newActionImpact}
                            onChange={e => setNewActionImpact(e.target.value)}
                            placeholder="Details / Impact..."
                            rows={2}
                            className="w-full p-2 rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                        />
                        <div className="text-right">
                            <button
                                onClick={handleAddNewAction}
                                disabled={!newActionTitle.trim()}
                                className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-semibold rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                            >
                                <PlusCircleIcon className="h-4 w-4" /> Add Task
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
