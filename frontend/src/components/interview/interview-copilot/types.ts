import type { Layouts } from 'react-grid-layout';
import type {
    ImpactStory,
    Interview,
    InterviewPrepOutline,
    JobApplication,
    JobProblemAnalysisResult,
    StrategicNarrative,
} from '../../../types';
import type { HydratedDeckItem } from '../../../utils/interviewDeck';

export type WidgetMode = 'prep' | 'live';

export interface WidgetRuntimeContext {
    appendToNotes?: (text: string) => void;
    jobAnalysis?: JobProblemAnalysisResult | null;
    interview: Interview;
    application: JobApplication;
    narrative: StrategicNarrative;
    availableStories: ImpactStory[];
}

export interface WidgetProps<TData> {
    id: string;
    mode: WidgetMode;
    data: TData;
    onChange: (value: TData) => void;
    lastUpdated?: string;
    editable: boolean;
    context: WidgetRuntimeContext;
}

export interface WidgetState<TData> {
    id: string;
    data: TData;
    lastUpdated?: string;
    collapsed?: boolean;
}

export interface WidgetConfig<TData> {
    id: WidgetId;
    title: string;
    component: (props: WidgetProps<TData>) => JSX.Element;
    defaultLayouts: Layouts;
    editableInModes?: WidgetMode[];
    allowCollapse?: boolean;
    getInitialState: (context: WidgetInitContext) => WidgetState<TData>;
    serialize?: (state: WidgetState<TData>, context: WidgetInitContext) => PartialWidgetPayload;
}

export interface WidgetInitContext {
    application: JobApplication;
    interview: Interview;
    narrative: StrategicNarrative;
    prepOutline: InterviewPrepOutline;
    storyDeck: HydratedDeckItem[];
    jobAnalysis?: JobProblemAnalysisResult | null;
}

export type PartialWidgetPayload = Partial<
    Pick<Interview, 'strategic_opening' | 'strategic_questions_to_ask' | 'live_notes' | 'prep_outline'>
> & {
    story_deck?: Interview['story_deck'];
};

export type WidgetId =
    | 'jobCheatSheet'
    | 'clarifyingPrompt'
    | 'topOfMind'
    | 'strategicOpening'
    | 'questionArsenal'
    | 'impactStories'
    | 'liveChecklist'
    | 'notes';

export interface JobCheatSheetData {
    coreProblem: string;
    suggestedPositioning: string;
    keySuccessMetrics: string[];
    roleLevers: string[];
    potentialBlockers: string[];
    businessContext: string;
    strategicImportance: string;
    focusTags: string[];
}

export interface ClarifyingPromptData {
    prompt: string;
}

export interface TopOfMindData {
    interviewerName?: string;
    interviewFormat: string;
}

export interface StrategicOpeningData {
    opening: string;
}

export interface QuestionArsenalData {
    questions: string[];
    asked: string[];
}

export interface ImpactStoriesData {
    storyDeck: HydratedDeckItem[];
    activeRole: string;
    newRoleName: string;
    storyToAdd: string;
}

export interface LiveChecklistData {
    metrics: string[];
    levers: string[];
    blockers: string[];
    covered: {
        metrics: string[];
        levers: string[];
        blockers: string[];
    };
}

export interface NotesData {
    content: string;
}

export type WidgetDataMap = {
    jobCheatSheet: JobCheatSheetData;
    clarifyingPrompt: ClarifyingPromptData;
    topOfMind: TopOfMindData;
    strategicOpening: StrategicOpeningData;
    questionArsenal: QuestionArsenalData;
    impactStories: ImpactStoriesData;
    liveChecklist: LiveChecklistData;
    notes: NotesData;
};

export type WidgetStateMap = { [K in WidgetId]: WidgetState<WidgetDataMap[K]> };
