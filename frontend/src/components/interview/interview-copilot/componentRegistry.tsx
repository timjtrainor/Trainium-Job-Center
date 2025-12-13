import type { Layouts } from 'react-grid-layout';
import { JobCheatSheetWidget } from './widgets/JobCheatSheetWidget';
import { ClarifyingPromptWidget } from './widgets/ClarifyingPromptWidget';
import { TopOfMindWidget } from './widgets/TopOfMindWidget';
import { StrategicOpeningWidget } from './widgets/StrategicOpeningWidget';
import { QuestionArsenalWidget } from './widgets/QuestionArsenalWidget';
import { ImpactStoriesWidget } from './widgets/ImpactStoriesWidget';
import { LiveChecklistWidget } from './widgets/LiveChecklistWidget';
import { NotesWidget } from './widgets/NotesWidget';
import type {
    ClarifyingPromptData,
    ImpactStoriesData,
    JobCheatSheetData,
    LiveChecklistData,
    NotesData,
    QuestionArsenalData,
    StrategicOpeningData,
    TopOfMindData,
    WidgetConfig,
    WidgetDataMap,
    WidgetInitContext,
    WidgetState,
    WidgetId,
} from '../../../types';
import { serializeDeck } from '../../../utils/interviewDeck';

const createLayouts = (config: {
    lg: { x: number; y: number; w: number; h: number };
    md: { x: number; y: number; w: number; h: number };
    sm: { x: number; y: number; w: number; h: number };
    id: WidgetId;
}): Layouts => ({
    lg: [{ i: config.id, ...config.lg }],
    md: [{ i: config.id, ...config.md }],
    sm: [{ i: config.id, ...config.sm }],
});

const jobCheatSheetInitialState = ({ prepOutline }: WidgetInitContext): WidgetState<JobCheatSheetData> => ({
    id: 'jobCheatSheet',
    data: {
        coreProblem: prepOutline.role_intelligence?.core_problem || '',
        suggestedPositioning: prepOutline.role_intelligence?.suggested_positioning || '',
        keySuccessMetrics: prepOutline.role_intelligence?.key_success_metrics || [],
        roleLevers: prepOutline.role_intelligence?.role_levers || [],
        potentialBlockers: prepOutline.role_intelligence?.potential_blockers || [],
        businessContext: prepOutline.jd_insights?.business_context || '',
        strategicImportance: prepOutline.jd_insights?.strategic_importance || '',
        focusTags: prepOutline.jd_insights?.tags || [],
    },
});

const clarifyInitialState = ({ prepOutline }: WidgetInitContext): WidgetState<ClarifyingPromptData> => {
    const roleIntelligence = prepOutline.role_intelligence || {};
    const lines = [
        'To make sure I tailor my answers, could we clarify:',
        roleIntelligence.core_problem ? `• Are we aligned that the core challenge is "${roleIntelligence.core_problem}"?` : null,
        roleIntelligence.key_success_metrics?.length
            ? `• Which success metrics matter most right now? (${roleIntelligence.key_success_metrics.join(', ')})`
            : null,
        roleIntelligence.role_levers?.length
            ? `• Where do you need the most leverage today? (${roleIntelligence.role_levers.join(', ')})`
            : null,
        roleIntelligence.potential_blockers?.length
            ? `• What blockers are slowing progress? (${roleIntelligence.potential_blockers.join(', ')})`
            : null,
    ].filter(Boolean);
    return {
        id: 'clarifyingPrompt',
        data: { prompt: lines.join('\n') },
    };
};

const topOfMindInitialState = ({ interview }: WidgetInitContext): WidgetState<TopOfMindData> => ({
    id: 'topOfMind',
    data: {
        interviewerName: interview.interview_contacts?.[0]
            ? `${interview.interview_contacts[0].first_name} ${interview.interview_contacts[0].last_name}`
            : undefined,
        interviewFormat: interview.interview_type,
    },
});

const openingInitialState = ({ interview, narrative, application }: WidgetInitContext): WidgetState<StrategicOpeningData> => {
    const savedOpening = interview.strategic_opening?.trim();
    if (savedOpening) {
        return {
            id: 'strategicOpening',
            data: { opening: savedOpening },
        };
    }

    const positioning = narrative.positioning_statement?.trim();
    const coreProblem = application.job_problem_analysis_result?.core_problem_analysis?.core_problem?.trim();
    const storyTitle = narrative.impact_story_title?.trim();

    const intro = positioning
        ? `"I'm a product leader who excels at ${positioning}."`
        : '"I appreciate the chance to connect today."';
    const problemStatement = coreProblem ? `My understanding is the core challenge here is ${coreProblem}.` : null;
    const credibility = storyTitle ? `That's a problem I'm familiar with from my time when I ${storyTitle}.` : null;

    const opening = [intro, problemStatement, credibility].filter(Boolean).join(' ');

    return {
        id: 'strategicOpening',
        data: {
            opening: opening ||
                'Use this space to craft an opening that connects your background to their priorities.',
        },
    };
};

const questionsInitialState = ({ interview }: WidgetInitContext): WidgetState<QuestionArsenalData> => ({
    id: 'questionArsenal',
    data: {
        questions: interview.strategic_questions_to_ask || [],
        asked: [],
    },
});

const storiesInitialState = ({ storyDeck }: WidgetInitContext): WidgetState<ImpactStoriesData> => ({
    id: 'impactStories',
    data: {
        storyDeck,
        activeRole: 'default',
        newRoleName: '',
        storyToAdd: '',
    },
});

const checklistInitialState = ({ prepOutline }: WidgetInitContext): WidgetState<LiveChecklistData> => ({
    id: 'liveChecklist',
    data: {
        metrics: prepOutline.role_intelligence?.key_success_metrics || [],
        levers: prepOutline.role_intelligence?.role_levers || [],
        blockers: prepOutline.role_intelligence?.potential_blockers || [],
        covered: { metrics: [], levers: [], blockers: [] },
    },
});

const notesInitialState = ({ interview }: WidgetInitContext): WidgetState<NotesData> => ({
    id: 'notes',
    data: {
        content: interview.live_notes || '',
    },
});

export const componentRegistry: WidgetConfig<any>[] = [
    {
        id: 'jobCheatSheet',
        title: 'Job Cheat Sheet',
        component: JobCheatSheetWidget,
        defaultLayouts: createLayouts({
            id: 'jobCheatSheet',
            lg: { x: 0, y: 0, w: 6, h: 8 },
            md: { x: 0, y: 0, w: 4, h: 8 },
            sm: { x: 0, y: 0, w: 1, h: 8 },
        }),
        editableInModes: ['prep'],
        getInitialState: jobCheatSheetInitialState,
        serialize: ({ data }) => ({
            prep_outline: {
                role_intelligence: {
                    core_problem: data.coreProblem,
                    suggested_positioning: data.suggestedPositioning,
                    key_success_metrics: data.keySuccessMetrics,
                    role_levers: data.roleLevers,
                    potential_blockers: data.potentialBlockers,
                },
                jd_insights: {
                    business_context: data.businessContext,
                    strategic_importance: data.strategicImportance,
                    tags: data.focusTags,
                },
            },
        }),
    },
    {
        id: 'clarifyingPrompt',
        title: 'Clarifying Prompt Launcher',
        component: ClarifyingPromptWidget,
        defaultLayouts: createLayouts({
            id: 'clarifyingPrompt',
            lg: { x: 6, y: 0, w: 3, h: 6 },
            md: { x: 4, y: 0, w: 4, h: 6 },
            sm: { x: 0, y: 8, w: 1, h: 6 },
        }),
        editableInModes: ['prep'],
        getInitialState: clarifyInitialState,
    },
    {
        id: 'topOfMind',
        title: 'Top of Mind',
        component: TopOfMindWidget,
        defaultLayouts: createLayouts({
            id: 'topOfMind',
            lg: { x: 9, y: 0, w: 3, h: 3 },
            md: { x: 4, y: 6, w: 4, h: 3 },
            sm: { x: 0, y: 14, w: 1, h: 3 },
        }),
        editableInModes: ['prep'],
        getInitialState: topOfMindInitialState,
    },
    {
        id: 'strategicOpening',
        title: 'Strategic Opening',
        component: StrategicOpeningWidget,
        defaultLayouts: createLayouts({
            id: 'strategicOpening',
            lg: { x: 6, y: 6, w: 6, h: 6 },
            md: { x: 0, y: 8, w: 4, h: 6 },
            sm: { x: 0, y: 17, w: 1, h: 6 },
        }),
        editableInModes: ['prep'],
        getInitialState: openingInitialState,
        serialize: ({ data }) => ({ strategic_opening: data.opening }),
    },
    {
        id: 'questionArsenal',
        title: 'Question Arsenal',
        component: QuestionArsenalWidget,
        defaultLayouts: createLayouts({
            id: 'questionArsenal',
            lg: { x: 0, y: 8, w: 6, h: 7 },
            md: { x: 0, y: 14, w: 4, h: 7 },
            sm: { x: 0, y: 23, w: 1, h: 7 },
        }),
        editableInModes: ['prep'],
        getInitialState: questionsInitialState,
        serialize: ({ data }) => ({ strategic_questions_to_ask: data.questions }),
    },
    {
        id: 'impactStories',
        title: 'Impact Stories',
        component: ImpactStoriesWidget,
        defaultLayouts: createLayouts({
            id: 'impactStories',
            lg: { x: 6, y: 12, w: 6, h: 12 },
            md: { x: 4, y: 11, w: 4, h: 12 },
            sm: { x: 0, y: 30, w: 1, h: 12 },
        }),
        editableInModes: ['prep'],
        getInitialState: storiesInitialState,
        serialize: ({ data }) => ({ story_deck: serializeDeck(data.storyDeck) }),
    },
    {
        id: 'liveChecklist',
        title: 'Live Checklist',
        component: LiveChecklistWidget,
        defaultLayouts: createLayouts({
            id: 'liveChecklist',
            lg: { x: 0, y: 15, w: 6, h: 8 },
            md: { x: 0, y: 21, w: 4, h: 8 },
            sm: { x: 0, y: 42, w: 1, h: 8 },
        }),
        getInitialState: checklistInitialState,
    },
    {
        id: 'notes',
        title: 'Live Notes',
        component: NotesWidget,
        defaultLayouts: createLayouts({
            id: 'notes',
            lg: { x: 0, y: 23, w: 12, h: 10 },
            md: { x: 0, y: 29, w: 8, h: 10 },
            sm: { x: 0, y: 50, w: 1, h: 10 },
        }),
        editableInModes: ['live'],
        getInitialState: notesInitialState,
        serialize: ({ data }) => ({ live_notes: data.content }),
    },
];

export const widgetMap = new Map(componentRegistry.map((config) => [config.id, config]));
