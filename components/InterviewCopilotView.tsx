import React, { useState } from 'react';
import type { Interview, InterviewPayload, JobApplication, InterviewStrategyState, Company, StrategicNarrative } from '../types';
import {
    CheckIcon, LoadingSpinner, SparklesIcon,
    UserIcon, ChatBubbleBottomCenterTextIcon,
    BeakerIcon, ShieldCheckIcon, PresentationChartLineIcon,
    UsersIcon, LightBulbIcon, CloudArrowUpIcon, FlagIcon
} from './IconComponents';
import { InterviewStrategyView } from './interview-copilot/InterviewStrategyView';
import { TMAYView, StandardQuestionView } from './interview-copilot/CommandCenterViews';
import LiveNotesWidget from './interview-copilot/LiveNotesWidget';

// Default Initial State
const INITIAL_STRATEGY_STATE: InterviewStrategyState = {
    persona: {
        buyer_type: 'Recruiter',
        primary_anxiety: '',
        win_condition: '',
        functional_friction_point: ''
    },
    tmay: { hook: '', bridge: '', pivot: '' },
    questions: [],
    success_metrics: [],
    potential_blockers: [],
    power_vocabulary: {
        'Behavioral': ['Situation', 'Task', 'Action', 'Result', 'Impact', 'Learnings'],
        'Technical Depth': ['Architecture', 'Scalability', 'Trade-offs', 'Latency', 'Consistency'],
        'Strategy Case': ['Framework', 'MECE', 'Hypothesis', 'Validation', 'Recommendation']
    },
    discovery_questions: []
};

type TabId =
    | 'strategy'
    | 'tmay'
    | 'behavioral'
    | 'technical'
    | 'situational'
    | 'case'
    | 'leadership'
    | 'discovery';

interface InterviewCopilotViewProps {
    application: JobApplication;
    interview: Interview;
    company: Company;
    activeNarrative: StrategicNarrative;
    onBack: () => void;
    onSaveInterview: (payload: InterviewPayload, interviewId: string) => Promise<void>;
    onGenerateInterviewPrep: (app: JobApplication, interview: Interview) => Promise<void>;
    onGenerateRecruiterScreenPrep: (app: JobApplication, interview: Interview) => Promise<void>;
    onOpenDebriefStudio: (interview: Interview) => void;
}

export const InterviewCopilotView = ({
    application,
    interview,
    company,
    activeNarrative,
    onBack,
    onSaveInterview,
    onOpenDebriefStudio
}: InterviewCopilotViewProps) => {
    // --- State ---
    const [activeTab, setActiveTab] = useState<TabId>('strategy');
    const [strategyState, setStrategyState] = useState<InterviewStrategyState>(() => {
        if (interview.interview_strategy_state && typeof interview.interview_strategy_state === 'object' && Object.keys(interview.interview_strategy_state).length > 0) {
            return interview.interview_strategy_state as InterviewStrategyState;
        }
        return INITIAL_STRATEGY_STATE;
    });
    const [liveNotes, setLiveNotes] = useState(interview.live_notes || '');
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);

    // Derived state for saving strategy vs interview root fields
    const handleSave = async (silent = false) => {
        if (!silent) setIsSaving(true);
        try {
            const payload: InterviewPayload = {
                interview_strategy_state: strategyState,
                live_notes: liveNotes
            };
            await onSaveInterview(payload, interview.interview_id);
            if (!silent) {
                setSaveSuccess(true);
                setTimeout(() => setSaveSuccess(false), 2000);
            }
        } catch (error) {
            console.error('[InterviewCopilotView] Failed to save:', error);
        } finally {
            if (!silent) setIsSaving(false);
        }
    };

    const handleEndInterview = async () => {
        setIsSaving(true);
        try {
            await handleSave(true); // Silent save first
            onOpenDebriefStudio(interview);
        } catch (error) {
            console.error(error);
        } finally {
            setIsSaving(false);
        }
    };

    // --- Navigation ---
    const MENU_ITEMS: { id: TabId; label: string; icon: React.ElementType }[] = [
        { id: 'strategy', label: 'Interview Strategy', icon: PresentationChartLineIcon },
        { id: 'tmay', label: 'TMAY', icon: UserIcon },
        { id: 'behavioral', label: 'Behavioral', icon: ChatBubbleBottomCenterTextIcon },
        { id: 'technical', label: 'Technical Depth', icon: BeakerIcon },
        { id: 'situational', label: 'Situational', icon: LightBulbIcon },
        { id: 'case', label: 'Strategy Case', icon: ShieldCheckIcon },
        { id: 'leadership', label: 'Leadership', icon: UsersIcon },
        { id: 'discovery', label: 'Discovery (Ask Them)', icon: SparklesIcon },
    ];

    // --- Render Content ---
    const renderContent = () => {
        switch (activeTab) {
            case 'strategy':
                return <InterviewStrategyView strategy={strategyState} application={application} onChange={setStrategyState} />;
            case 'tmay':
                return <TMAYView strategy={strategyState} />;
            case 'behavioral':
                return <StandardQuestionView strategy={strategyState} type="Behavioral" vocabularyKey="Behavioral" />;
            case 'technical':
                return <StandardQuestionView strategy={strategyState} type="Technical Depth" vocabularyKey="Technical Depth" />;
            case 'situational':
                return <StandardQuestionView strategy={strategyState} type="Situational" vocabularyKey="Situational" />;
            case 'case':
                return <StandardQuestionView strategy={strategyState} type="Strategy Case" vocabularyKey="Strategy Case" />;
            case 'leadership':
                return <StandardQuestionView strategy={strategyState} type="Leadership" vocabularyKey="Leadership" />;
            case 'discovery':
                return <StandardQuestionView strategy={strategyState} type="Discovery" vocabularyKey="Discovery" />;
            default:
                return <div>Select a tab</div>;
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex bg-slate-100 dark:bg-slate-900">
            {/* Left Sidebar - Command Center */}
            <div className="w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col">
                <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                    <h2 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-2">Command Center</h2>
                    <h1 className="font-bold text-slate-900 dark:text-white truncate">{company.company_name}</h1>
                    <div className="text-xs text-slate-500 truncate">{application.job_title}</div>
                </div>

                <nav className="flex-1 overflow-y-auto p-2 space-y-1">
                    {MENU_ITEMS.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === item.id
                                ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300'
                                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50'
                                }`}
                        >
                            <item.icon className={`w-5 h-5 ${activeTab === item.id ? 'text-indigo-600' : 'text-slate-400'}`} />
                            {item.label}
                        </button>
                    ))}
                </nav>

                <div className="p-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 space-y-2">
                    <button
                        onClick={() => handleSave()}
                        disabled={isSaving}
                        className={`w-full flex items-center justify-center gap-2 py-2 text-sm font-bold rounded-lg transition-all shadow-sm border ${saveSuccess
                            ? 'bg-emerald-500 text-white border-emerald-500'
                            : 'bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700'
                            } disabled:opacity-50`}
                    >
                        {isSaving ? <LoadingSpinner className="w-4 h-4" /> : saveSuccess ? <CheckIcon className="w-4 h-4" /> : <CloudArrowUpIcon className="w-4 h-4" />}
                        {saveSuccess ? 'Changes Saved' : 'Save All Changes'}
                    </button>

                    <button
                        onClick={handleEndInterview}
                        className="w-full flex items-center justify-center gap-2 py-2 text-sm font-bold text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-all"
                    >
                        <FlagIcon className="w-4 h-4 text-slate-400" />
                        End Interview
                    </button>

                    <button
                        onClick={onBack}
                        className="w-full flex items-center justify-center gap-2 py-2 text-xs font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-300 transition-colors"
                    >
                        &larr; Exit Co-Pilot
                    </button>
                </div>
            </div>

            {/* Main Area */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Header */}
                <div className="h-16 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-6 shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-widest ${activeTab === 'strategy' ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-600'
                            }`}>
                            Current View: {MENU_ITEMS.find(m => m.id === activeTab)?.label}
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        {isSaving && <span className="text-[10px] text-slate-400 animate-pulse">Saving changes...</span>}
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-900/50 relative">
                    {renderContent()}
                </div>
            </div>

            {/* Right Pane - Live Notes (Always Visible) */}
            <div className="w-80 bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-700 flex flex-col h-full shadow-lg z-10">
                <LiveNotesWidget
                    notes={liveNotes}
                    onChange={setLiveNotes}
                    className="h-full border-none"
                    onSave={() => handleSave()}
                />
            </div>
        </div>
    );
};

export default InterviewCopilotView;
