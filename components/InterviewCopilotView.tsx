import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import type { Layouts, Layout } from 'react-grid-layout';
import { componentRegistry } from './interview-copilot/componentRegistry';
import type {
    JobCheatSheetData,
    WidgetId,
    WidgetMode,
    WidgetState,
    WidgetRuntimeContext,
} from './interview-copilot/types';
import type {
    JobApplication,
    Interview,
    StrategicNarrative,
    InterviewPayload,
    Company,
    JobProblemAnalysisResult,
    InterviewPrepOutline,
} from '../types';
import { buildHydratedDeck } from '../utils/interviewDeck';
import { Switch } from './Switch';
import { CheckIcon, LoadingSpinner, SparklesIcon } from './IconComponents';
import { appendUnique, formatTimestamp } from './interview-copilot/utils';

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

const ResponsiveGridLayout = WidthProvider(Responsive);

const buildPrepOutline = (
    analysis?: JobProblemAnalysisResult | null,
    stored?: InterviewPrepOutline | null,
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
            suggested_positioning:
                stored.role_intelligence?.suggested_positioning ?? defaults.role_intelligence?.suggested_positioning ?? '',
            key_success_metrics:
                stored.role_intelligence?.key_success_metrics ?? defaults.role_intelligence?.key_success_metrics ?? [],
            role_levers: stored.role_intelligence?.role_levers ?? defaults.role_intelligence?.role_levers ?? [],
            potential_blockers:
                stored.role_intelligence?.potential_blockers ?? defaults.role_intelligence?.potential_blockers ?? [],
        },
        jd_insights: {
            business_context: stored.jd_insights?.business_context ?? defaults.jd_insights?.business_context ?? '',
            strategic_importance: stored.jd_insights?.strategic_importance ?? defaults.jd_insights?.strategic_importance ?? '',
            tags: stored.jd_insights?.tags ?? defaults.jd_insights?.tags ?? [],
        },
    };
};

const mergeLayouts = (registryLayouts: Layouts[]): Layouts => {
    const result: Layouts = { lg: [], md: [], sm: [] };
    registryLayouts.forEach((layoutSet) => {
        (Object.keys(layoutSet) as (keyof Layouts)[]).forEach((breakpoint) => {
            const layouts = layoutSet[breakpoint] || [];
            result[breakpoint] = result[breakpoint] || [];
            result[breakpoint]!.push(...layouts.map((layout) => ({ ...layout })));
        });
    });
    return result;
};

const buildDefaultLayouts = (): Layouts =>
    mergeLayouts(componentRegistry.map((config) => config.defaultLayouts));

const buildDefaultHeights = (): Record<string, Record<WidgetId, number>> => {
    const heights: Record<string, Record<WidgetId, number>> = { lg: {}, md: {}, sm: {} };
    componentRegistry.forEach((config) => {
        (Object.keys(config.defaultLayouts) as (keyof Layouts)[]).forEach((breakpoint) => {
            const layout = config.defaultLayouts[breakpoint]?.find((item) => item.i === config.id);
            if (layout) {
                heights[breakpoint] = heights[breakpoint] || {};
                heights[breakpoint]![config.id] = layout.h;
            }
        });
    });
    return heights;
};

const pruneCoverage = (values: string[], covered: string[]): string[] => {
    const set = new Set(values);
    return covered.filter((value) => set.has(value));
};

export const InterviewCopilotView = ({
    application,
    interview,
    company,
    activeNarrative,
    onBack,
    onSaveInterview,
    onGenerateInterviewPrep,
    onGenerateRecruiterScreenPrep,
}: InterviewCopilotViewProps) => {
    const [mode, setMode] = useState<WidgetMode>('live');
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [isSavingNotes, setIsSavingNotes] = useState(false);
    const [notesSuccess, setNotesSuccess] = useState(false);
    const [isGeneratingPrep, setIsGeneratingPrep] = useState(false);

    const jobAnalysis = useMemo(() => application.job_problem_analysis_result, [application]);
    const prepOutline = useMemo(
        () => buildPrepOutline(jobAnalysis, interview.prep_outline),
        [jobAnalysis, interview.prep_outline],
    );
    const storyDeck = useMemo(
        () => buildHydratedDeck(interview, activeNarrative),
        [interview, activeNarrative],
    );

    const defaultLayouts = useMemo(() => buildDefaultLayouts(), []);
    const defaultHeights = useMemo(() => buildDefaultHeights(), []);

    const initialWidgetStates = useMemo(() => {
        const context = {
            application,
            interview,
            narrative: activeNarrative,
            prepOutline,
            storyDeck,
            jobAnalysis,
        };
        return componentRegistry.reduce<Record<WidgetId, WidgetState<any>>>((acc, config) => {
            acc[config.id] = { ...config.getInitialState(context), lastUpdated: interview.interview_date || undefined };
            return acc;
        }, {} as Record<WidgetId, WidgetState<any>>);
    }, [application, interview, activeNarrative, prepOutline, storyDeck, jobAnalysis]);

    const [widgetStates, setWidgetStates] = useState<Record<WidgetId, WidgetState<any>>>(initialWidgetStates);
    const [layouts, setLayouts] = useState<Layouts>(defaultLayouts);

    useEffect(() => {
        setWidgetStates(initialWidgetStates);
        setLayouts(buildDefaultLayouts());
    }, [initialWidgetStates]);

    const updateWidgetData = useCallback(
        (id: WidgetId, value: unknown) => {
            setWidgetStates((prev) => {
                const current = prev[id];
                if (!current) {
                    return prev;
                }
                const timestamp = new Date().toISOString();
                const nextState: Record<WidgetId, WidgetState<any>> = {
                    ...prev,
                    [id]: {
                        ...current,
                        data: value,
                        lastUpdated: timestamp,
                    },
                };

                if (id === 'jobCheatSheet') {
                    const cheatSheet = value as JobCheatSheetData;
                    const checklist = prev.liveChecklist;
                    if (checklist) {
                        const updatedChecklist = {
                            ...checklist,
                            data: {
                                ...checklist.data,
                                metrics: cheatSheet.keySuccessMetrics,
                                levers: cheatSheet.roleLevers,
                                blockers: cheatSheet.potentialBlockers,
                                covered: {
                                    metrics: pruneCoverage(cheatSheet.keySuccessMetrics, checklist.data.covered.metrics),
                                    levers: pruneCoverage(cheatSheet.roleLevers, checklist.data.covered.levers),
                                    blockers: pruneCoverage(cheatSheet.potentialBlockers, checklist.data.covered.blockers),
                                },
                            },
                            lastUpdated: timestamp,
                        };
                        nextState.liveChecklist = updatedChecklist;
                    }
                }

                return nextState;
            });
        },
        [],
    );

    const toggleCollapse = useCallback(
        (id: WidgetId) => {
            const isCurrentlyCollapsed = Boolean(widgetStates[id]?.collapsed);
            const nextCollapsed = !isCurrentlyCollapsed;
            setWidgetStates((prev) => {
                const current = prev[id];
                if (!current) {
                    return prev;
                }
                return {
                    ...prev,
                    [id]: {
                        ...current,
                        collapsed: nextCollapsed,
                    },
                };
            });
            setLayouts((prev) => {
                const adjustHeight = (items: Layout[] | undefined, breakpoint: keyof Layouts) =>
                    (items || []).map((item) => {
                        if (item.i !== id) {
                            return { ...item };
                        }
                        const defaultHeight = defaultHeights[breakpoint]?.[id] ?? item.h;
                        return { ...item, h: nextCollapsed ? 2 : defaultHeight };
                    });
                return {
                    lg: adjustHeight(prev.lg, 'lg'),
                    md: adjustHeight(prev.md, 'md'),
                    sm: adjustHeight(prev.sm, 'sm'),
                };
            });
        },
        [defaultHeights, widgetStates],
    );

    const handleLayoutsChange = useCallback((_: Layout[], allLayouts: Layouts) => {
        setLayouts(allLayouts);
    }, []);

    const appendToNotes = useCallback(
        (text: string) => {
            setWidgetStates((prev) => {
                const notes = prev.notes;
                if (!notes) {
                    return prev;
                }
                const nextContent = appendUnique(notes.data.content, text);
                return {
                    ...prev,
                    notes: {
                        ...notes,
                        data: {
                            ...notes.data,
                            content: nextContent,
                        },
                        lastUpdated: new Date().toISOString(),
                    },
                };
            });
        },
        [],
    );

    const widgetContext = useMemo<WidgetRuntimeContext>(
        () => ({
            appendToNotes,
            jobAnalysis,
            interview,
            application,
            narrative: activeNarrative,
            availableStories: activeNarrative.impact_stories || [],
        }),
        [appendToNotes, jobAnalysis, interview, application, activeNarrative],
    );

    const handleSave = useCallback(async () => {
        setIsSaving(true);
        setSaveSuccess(false);
        try {
            const context = {
                application,
                interview,
                narrative: activeNarrative,
                prepOutline,
                storyDeck,
                jobAnalysis,
            };
            const payload = componentRegistry.reduce<InterviewPayload>((acc, config) => {
                const state = widgetStates[config.id];
                if (state && config.serialize) {
                    const partial = config.serialize(state, context);
                    if (partial) {
                        if (partial.prep_outline) {
                            acc.prep_outline = {
                                ...(acc.prep_outline || {}),
                                ...partial.prep_outline,
                            };
                            delete partial.prep_outline;
                        }
                        Object.assign(acc, partial);
                    }
                }
                return acc;
            }, {} as InterviewPayload);
            await onSaveInterview(payload, interview.interview_id);
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 2000);
        } catch (error) {
            console.error('Failed to save Interview Co-pilot data', error);
        } finally {
            setIsSaving(false);
        }
    }, [
        application,
        interview,
        activeNarrative,
        prepOutline,
        storyDeck,
        jobAnalysis,
        widgetStates,
        onSaveInterview,
    ]);

    const handleSaveNotes = useCallback(async () => {
        const notesState = widgetStates.notes;
        if (!notesState) {
            return;
        }
        setIsSavingNotes(true);
        setNotesSuccess(false);
        try {
            await onSaveInterview({ live_notes: notesState.data.content }, interview.interview_id);
            setNotesSuccess(true);
            setTimeout(() => setNotesSuccess(false), 2000);
        } catch (error) {
            console.error('Failed to save notes', error);
        } finally {
            setIsSavingNotes(false);
        }
    }, [widgetStates, interview, onSaveInterview]);

    const handleRerunAI = useCallback(async () => {
        setIsGeneratingPrep(true);
        try {
            const isRecruiterScreen = interview.interview_type === 'Step 6.1: Recruiter Screen';
            if (isRecruiterScreen) {
                await onGenerateRecruiterScreenPrep(application, interview);
            } else {
                await onGenerateInterviewPrep(application, interview);
            }
        } catch (error) {
            console.error('Failed to rerun AI prep', error);
        } finally {
            setIsGeneratingPrep(false);
        }
    }, [application, interview, onGenerateInterviewPrep, onGenerateRecruiterScreenPrep]);

    const interviewer = interview.interview_contacts?.[0];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/75 p-4">
            <div className="flex h-full w-full flex-col rounded-xl bg-slate-100 shadow-2xl dark:bg-slate-900">
                <header className="flex items-center justify-between border-b border-slate-300 p-3 dark:border-slate-700">
                    <div>
                        <h2 className="text-base font-bold text-slate-900 dark:text-white">Interview Co-pilot</h2>
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                            {application.job_title} at {company.company_name}
                        </p>
                        {interviewer && (
                            <p className="text-[11px] text-slate-500 dark:text-slate-400">
                                Interviewing with {interviewer.first_name} {interviewer.last_name}
                            </p>
                        )}
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center space-x-2">
                            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Live Mode</span>
                            <Switch enabled={mode === 'prep'} onChange={(value) => setMode(value ? 'prep' : 'live')} />
                            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Prep Mode</span>
                        </div>
                        {mode === 'prep' ? (
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className={`rounded-md px-3 py-1.5 text-xs font-semibold shadow-sm transition-colors ${
                                    saveSuccess
                                        ? 'bg-green-600 text-white'
                                        : 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400'
                                }`}
                            >
                                {isSaving ? 'Saving…' : saveSuccess ? 'Saved!' : 'Save Changes'}
                            </button>
                        ) : (
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={handleRerunAI}
                                    disabled={isGeneratingPrep}
                                    className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:bg-indigo-400"
                                >
                                    {isGeneratingPrep ? <LoadingSpinner /> : <SparklesIcon className="h-4 w-4" />}
                                    Rerun AI Prep
                                </button>
                                <button
                                    onClick={handleSaveNotes}
                                    disabled={isSavingNotes}
                                    className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-semibold shadow-sm transition-colors ${
                                        notesSuccess
                                            ? 'bg-green-600 text-white'
                                            : 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400'
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
                        )}
                        <button
                            onClick={onBack}
                            className="text-xs font-semibold text-blue-600 hover:underline dark:text-blue-400"
                        >
                            Close
                        </button>
                    </div>
                </header>

                <main className="flex-1 overflow-hidden p-3">
                    <ResponsiveGridLayout
                        className="layout"
                        layouts={layouts}
                        cols={{ lg: 12, md: 8, sm: 1 }}
                        breakpoints={{ lg: 1200, md: 996, sm: 480 }}
                        rowHeight={32}
                        margin={[12, 12]}
                        onLayoutChange={handleLayoutsChange}
                        draggableHandle=".widget-header"
                    >
                        {componentRegistry.map((config) => {
                            const state = widgetStates[config.id];
                            if (!state) {
                                return null;
                            }
                            const editable = config.editableInModes ? config.editableInModes.includes(mode) : false;
                            const isCollapsed = state.collapsed;
                            const lastUpdated = state.lastUpdated;
                            const titleTimestamp = lastUpdated ? formatTimestamp(lastUpdated) : undefined;
                            const handleChange = (value: unknown) => updateWidgetData(config.id, value);
                            const content = isCollapsed ? null : (
                                <div className="flex-1 overflow-y-auto p-3">
                                    <config.component
                                        id={config.id}
                                        mode={mode}
                                        data={state.data}
                                        onChange={handleChange}
                                        lastUpdated={lastUpdated}
                                        editable={editable}
                                        context={widgetContext}
                                    />
                                </div>
                            );
                            return (
                                <div key={config.id} className="flex h-full flex-col rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
                                    <div className="widget-header flex items-center justify-between border-b border-slate-200 px-3 py-2 dark:border-slate-700">
                                        <div>
                                            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-300">
                                                {config.title}
                                            </h3>
                                            {titleTimestamp && (
                                                <p className="text-[10px] text-slate-400 dark:text-slate-500">Updated {titleTimestamp}</p>
                                            )}
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => toggleCollapse(config.id)}
                                            className="rounded-md border border-slate-300 px-2 py-1 text-[10px] font-semibold text-slate-600 hover:bg-slate-200 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
                                        >
                                            {isCollapsed ? 'Expand' : 'Collapse'}
                                        </button>
                                    </div>
                                    {content}
                                </div>
                            );
                        })}
                    </ResponsiveGridLayout>
                </main>
            </div>
        </div>
    );
};

export default InterviewCopilotView;
