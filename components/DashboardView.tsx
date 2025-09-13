import React, { useMemo, useState } from 'react';
import { JobApplication, Contact, Message, LinkedInPost, UserProfile, Prompt, StrategicNarrative, LinkedInEngagement, BaseResume, StrategicNarrativePayload, SkillGapAnalysisResult, NarrativeSynthesisResult, SkillTrendPayload, AiFocusItem, Sprint, SkillTrend, Company, PromptContext, SprintActionPayload } from '../types';
import * as geminiService from '../services/geminiService';
import { LoadingSpinner, CheckBadgeIcon, ClockIcon, StrategyIcon, RocketLaunchIcon, MagnifyingGlassPlusIcon, XCircleIcon, NetworkingIcon, SparklesIcon } from './IconComponents';
import { SkillGapAnalysisModal } from './SkillGapAnalysisModal';
import { CatalyzePathModal } from './CatalyzePathModal';

interface DashboardViewProps {
  applications: JobApplication[];
  contacts: Contact[];
  messages: Message[];
  linkedInPosts: LinkedInPost[];
  engagements: LinkedInEngagement[];
  pendingFollowUps: Message[];
  userProfile: UserProfile | null;
  activeNarrative: StrategicNarrative | null;
  strategicNarratives: StrategicNarrative[];
  onOpenContactModal: (contact: Partial<Contact>) => void;
  onScoutForOpportunities: () => void;
  onUpdateContactStatus: (contactId: string, status: string) => void;
  prompts: Prompt[];
  debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
  baseResumes: BaseResume[];
  onCreateSynthesizedNarrative: (payload: StrategicNarrativePayload) => Promise<void>;
  onSaveSkillTrends: (trends: SkillTrendPayload[]) => Promise<void>;
  sprint: Sprint | null;
  skillTrends: SkillTrend[];
  companies: Company[];
  weeklyProgress: string;
  onAddActions: (sprintId: string, actions: SprintActionPayload[]) => Promise<void>;
}

type DashboardViewType = 'A' | 'B' | 'Combined';

const DashboardViewSwitcher = ({ view, setView, narrativeA, narrativeB }: { view: DashboardViewType, setView: (view: DashboardViewType) => void, narrativeA: StrategicNarrative | null, narrativeB: StrategicNarrative | null }) => {
    if (!narrativeA || !narrativeB) return null;

    const buttonClass = (buttonView: DashboardViewType) => 
        `px-3 py-1.5 text-sm font-medium rounded-md transition-colors ` +
        (view === buttonView
            ? 'bg-white shadow-sm text-blue-600 dark:bg-slate-700 dark:text-white'
            : 'text-slate-500 hover:bg-slate-200/50 dark:text-slate-400 dark:hover:bg-slate-700/50');
    
    return (
        <div className="flex items-center space-x-1 rounded-lg bg-slate-100 dark:bg-slate-800 p-1 self-start">
            <button onClick={() => setView('A')} className={buttonClass('A')}>{narrativeA.narrative_name}</button>
            <button onClick={() => setView('B')} className={buttonClass('B')}>{narrativeB.narrative_name}</button>
            <button onClick={() => setView('Combined')} className={buttonClass('Combined')}>Combined View</button>
        </div>
    );
};

const NarrativeTractionWidget = ({ narrativeA, narrativeB, applications, contacts, linkedInPosts, engagements }: { narrativeA: StrategicNarrative | null, narrativeB: StrategicNarrative | null, applications: JobApplication[], contacts: Contact[], linkedInPosts: LinkedInPost[], engagements: LinkedInEngagement[] }) => {
    const calculateMetrics = (narrative: StrategicNarrative | null) => {
        if (!narrative) return { appCount: 0, avgFitScore: 0, inConversationCount: 0, avgEngagementScore: 0 };
        
        const narrativeApps = applications.filter(app => app.narrative_id === narrative.narrative_id);
        const appCount = narrativeApps.length;
        
        const scoredApps = narrativeApps.filter(app => typeof app.strategic_fit_score === 'number');
        const totalScore = scoredApps.reduce((sum, app) => sum + (app.strategic_fit_score || 0), 0);
        const avgFitScore = scoredApps.length > 0 ? totalScore / scoredApps.length : 0;

        const inConversationCount = contacts.filter(c => 
            c.status === 'In Conversation' && 
            c.strategic_narratives?.some(n => n.narrative_id === narrative.narrative_id)
        ).length;
        
        const narrativePostIds = new Set(linkedInPosts.filter(p => p.narrative_id === narrative.narrative_id).map(p => p.post_id));
        const narrativeEngagements = engagements.filter(e => e.post_id && narrativePostIds.has(e.post_id) && typeof e.strategic_score === 'number');
        const totalEngagementScore = narrativeEngagements.reduce((sum, e) => sum + (e.strategic_score || 0), 0);
        const avgEngagementScore = narrativeEngagements.length > 0 ? totalEngagementScore / narrativeEngagements.length : 0;


        return { appCount, avgFitScore, inConversationCount, avgEngagementScore };
    };

    const metricsA = calculateMetrics(narrativeA);
    const metricsB = calculateMetrics(narrativeB);

    const MetricRow = ({ label, valueA, valueB }: { label: string, valueA: string | number, valueB: string | number }) => (
        <div className="grid grid-cols-3 items-center text-center py-3 border-b border-slate-200 dark:border-slate-700 last:border-b-0">
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400 text-left">{label}</p>
            <p className="text-2xl font-bold text-slate-800 dark:text-slate-200">{valueA}</p>
            <p className="text-2xl font-bold text-slate-800 dark:text-slate-200">{valueB}</p>
        </div>
    );

    return (
         <div className="bg-white dark:bg-slate-800/80 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm col-span-1 lg:col-span-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Narrative Traction (A/B Test)</h3>
            <div className="grid grid-cols-3 text-center border-b border-slate-200 dark:border-slate-700 pb-2">
                <p className="text-sm font-semibold text-slate-600 dark:text-slate-300 text-left">Metric</p>
                <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">{narrativeA?.narrative_name}</p>
                <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">{narrativeB?.narrative_name}</p>
            </div>
            <div>
                <MetricRow label="Applications Submitted" valueA={metricsA.appCount} valueB={metricsB.appCount} />
                <MetricRow label="Avg. Strategic Fit" valueA={metricsA.avgFitScore.toFixed(1)} valueB={metricsB.avgFitScore.toFixed(1)} />
                <MetricRow label="Contacts 'In Conversation'" valueA={metricsA.inConversationCount} valueB={metricsB.inConversationCount} />
                <MetricRow label="Strategic Engagement Score" valueA={metricsA.avgEngagementScore.toFixed(1)} valueB={metricsB.avgEngagementScore.toFixed(1)} />
            </div>
         </div>
    )
}

const KpiCard = ({ title, value, subtext, icon: Icon, colorClass = 'text-blue-600 dark:text-blue-400' }: { title: string, value: string | number, subtext: string, icon: React.ElementType, colorClass?: string }) => (
    <div className="bg-white dark:bg-slate-800/80 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex items-start">
        <div className="flex-shrink-0 bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 rounded-lg p-3">
            <Icon className="h-6 w-6" />
        </div>
        <div className="ml-4">
            <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</h3>
            <p className={`text-3xl font-bold ${colorClass}`}>{value}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">{subtext}</p>
        </div>
    </div>
);

const FunnelColumn = ({ title, count, contacts, onOpenContactModal, onUpdateContactStatus }: { title: string, count: number, contacts: Contact[], onOpenContactModal: (contact: Partial<Contact>) => void, onUpdateContactStatus: (contactId: string, status: string) => void }) => (
    <div className="flex-1 min-w-0 px-2">
        <h4 className="font-semibold text-slate-700 dark:text-slate-300 text-sm mb-3">
            {title} <span className="text-xs font-mono bg-slate-200 dark:bg-slate-700 rounded-full px-2 py-0.5">{count}</span>
        </h4>
        <div className="space-y-2 h-64 overflow-y-auto pr-2">
            {contacts.map(c => (
                <div key={c.contact_id} onClick={() => onOpenContactModal(c)} className="group relative p-2.5 bg-white dark:bg-slate-800 rounded-md border border-slate-200 dark:border-slate-700 shadow-sm cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50">
                    <button
                        type="button"
                        onClick={(e) => {
                            e.stopPropagation();
                            onUpdateContactStatus(c.contact_id, 'No Response');
                        }}
                        className="absolute top-1 right-1 p-0.5 rounded-full text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 hover:text-slate-600 dark:hover:text-slate-200 opacity-0 group-hover:opacity-100 transition-opacity"
                        aria-label="Archive contact"
                        title="Mark as 'No Response' and remove from funnel"
                    >
                        <XCircleIcon className="h-4 w-4" />
                    </button>
                    <p className="font-semibold text-sm text-slate-800 dark:text-slate-200 truncate">{c.first_name} {c.last_name}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{c.job_title}</p>
                </div>
            ))}
        </div>
    </div>
);

export const DashboardView = (props: DashboardViewProps): React.ReactNode => {
    const { applications, contacts, messages, linkedInPosts, engagements, userProfile, activeNarrative, strategicNarratives, onOpenContactModal, onScoutForOpportunities, onUpdateContactStatus, prompts, debugCallbacks, pendingFollowUps, baseResumes, onCreateSynthesizedNarrative, onSaveSkillTrends, sprint, skillTrends, companies, weeklyProgress, onAddActions } = props;

    const [dashboardView, setDashboardView] = useState<DashboardViewType>('Combined');
    
    // State for Co-Pilot Features
    const [isSkillGapModalOpen, setIsSkillGapModalOpen] = useState(false);
    const [skillGapResult, setSkillGapResult] = useState<SkillGapAnalysisResult | null>(null);
    const [isAnalyzingSkillGap, setIsAnalyzingSkillGap] = useState(false);
    const [skillGapError, setSkillGapError] = useState<string | null>(null);

    const [isCatalyzeModalOpen, setIsCatalyzeModalOpen] = useState(false);
    const [catalyzeResult, setCatalyzeResult] = useState<NarrativeSynthesisResult | null>(null);
    const [isCatalyzing, setIsCatalyzing] = useState(false);
    const [catalyzeError, setCatalyzeError] = useState<string | null>(null);
    
    const [focusItems, setFocusItems] = useState<AiFocusItem[]>([]);
    const [isGeneratingFeed, setIsGeneratingFeed] = useState(false);
    const [feedError, setFeedError] = useState<string | null>(null);


    const narrativeA = strategicNarratives.length > 0 ? strategicNarratives[0] : null;
    const narrativeB = strategicNarratives.length > 1 ? strategicNarratives[1] : null;

    const displayedData = useMemo(() => {
        let narrativeId: string | null = null;
        if (dashboardView === 'A' && narrativeA) narrativeId = narrativeA.narrative_id;
        else if (dashboardView === 'B' && narrativeB) narrativeId = narrativeB.narrative_id;

        if (narrativeId) {
            const filteredApplications = applications.filter(app => app.narrative_id === narrativeId);
            const filteredContacts = contacts.filter(c => c.strategic_narratives?.some(n => n.narrative_id === narrativeId));
            const filteredContactIds = new Set(filteredContacts.map(c => c.contact_id));
            const filteredApplicationIds = new Set(filteredApplications.map(a => a.job_application_id));
            const filteredMessages = messages.filter(m => (m.contact_id && filteredContactIds.has(m.contact_id)) || (m.job_application_id && filteredApplicationIds.has(m.job_application_id)));
            const filteredLinkedInPosts = linkedInPosts.filter(p => p.narrative_id === narrativeId);
            const filteredPendingFollowUps = pendingFollowUps.filter(f => f.contact_id && filteredContactIds.has(f.contact_id));
            
            return { applications: filteredApplications, contacts: filteredContacts, messages: filteredMessages, linkedInPosts: filteredLinkedInPosts, pendingFollowUps: filteredPendingFollowUps };
        }
        
        return { applications, contacts, messages, linkedInPosts, pendingFollowUps };
    }, [dashboardView, narrativeA, narrativeB, applications, contacts, messages, linkedInPosts, pendingFollowUps]);
    
    const overallPipelineAlignment = useMemo(() => {
        const scoredApps = displayedData.applications.filter(app => typeof app.strategic_fit_score === 'number' && app.status?.status_name !== 'Bad Fit');
        if (scoredApps.length === 0) return 0;
        const totalScore = scoredApps.reduce((sum, app) => sum + (app.strategic_fit_score || 0), 0);
        return (totalScore / scoredApps.length);
    }, [displayedData.applications]);

    const networkingFunnel = useMemo(() => {
        const contactIdsWithInterviews = new Set<string>();
        // Using `applications` from props directly to get a complete list of interviewees
        applications.forEach(app => {
            app.interviews?.forEach(interview => {
                interview.interview_contacts?.forEach(contact => {
                    contactIdsWithInterviews.add(contact.contact_id);
                });
            });
        });

        // Filter out contacts with interviews from the contacts to be displayed in the funnel
        const contactsInFunnel = displayedData.contacts.filter(c => !contactIdsWithInterviews.has(c.contact_id));

        return {
            toContact: contactsInFunnel.filter(c => c.status === 'To Contact'),
            initialOutreach: contactsInFunnel.filter(c => c.status === 'Initial Outreach'),
            inConversation: contactsInFunnel.filter(c => c.status === 'In Conversation'),
            followUpNeeded: contactsInFunnel.filter(c => c.status === 'Follow-up Needed'),
        };
    }, [displayedData.contacts, applications]);

    const handleGenerateFocusFeed = async () => {
        setIsGeneratingFeed(true);
        setFeedError(null);
        setFocusItems([]);

        try {
            const prompt = prompts.find(p => p.id === 'GENERATE_DASHBOARD_FEED');
            if (!prompt) throw new Error("Dashboard feed prompt not found.");

            const weeklyGoals = sprint?.actions.filter(a => a.is_goal) || [];
            const weeklyApplicationGoal = weeklyGoals.find(g => g.goal_type === 'applications')?.goal_target || 0;
            const weeklyContactGoal = weeklyGoals.find(g => g.goal_type === 'contacts')?.goal_target || 0;
            const weeklyPostGoal = weeklyGoals.find(g => g.goal_type === 'posts')?.goal_target || 0;
            
            const context: PromptContext = {
                WEEKLY_APPLICATION_GOAL: weeklyApplicationGoal,
                WEEKLY_CONTACT_GOAL: weeklyContactGoal,
                WEEKLY_POST_GOAL: weeklyPostGoal,
                WEEKLY_PROGRESS: weeklyProgress,
                PENDING_FOLLOW_UPS: JSON.stringify(pendingFollowUps.map(f => ({ contactName: `${f.contact?.first_name} ${f.contact?.last_name}`, dueDate: f.follow_up_due_date }))),
                POSITIONING_STATEMENT: activeNarrative?.positioning_statement,
                MASTERY: activeNarrative?.signature_capability,
                DESIRED_TITLE: activeNarrative?.desired_title,
            };

            const result = await geminiService.generateDashboardFeed(context, prompt.content, debugCallbacks);
            setFocusItems(result);

        } catch (err) {
            setFeedError(err instanceof Error ? err.message : 'Failed to generate focus feed.');
        } finally {
            setIsGeneratingFeed(false);
        }
    };
    
    return (
        <div className="space-y-6">
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Dashboard</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">
                        Welcome back, {userProfile?.first_name || 'User'}. Here's your strategic overview.
                    </p>
                </div>
                {narrativeA && narrativeB && (
                    <DashboardViewSwitcher
                        view={dashboardView}
                        setView={setDashboardView}
                        narrativeA={narrativeA}
                        narrativeB={narrativeB}
                    />
                )}
            </header>

            {narrativeA && narrativeB && dashboardView === 'Combined' && (
                <NarrativeTractionWidget
                    narrativeA={narrativeA}
                    narrativeB={narrativeB}
                    applications={applications}
                    contacts={contacts}
                    linkedInPosts={linkedInPosts}
                    engagements={engagements}
                />
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                 <KpiCard title="Active Applications" value={displayedData.applications.filter(a => !['Rejected', 'Bad Fit', 'Accepted'].includes(a.status?.status_name || '')).length} subtext="In pipeline" icon={StrategyIcon} />
                <KpiCard title="Pipeline Alignment" value={overallPipelineAlignment.toFixed(1)} subtext="Avg. strategic fit score" icon={CheckBadgeIcon} colorClass="text-green-600 dark:text-green-400" />
                <KpiCard title="Follow-ups Due" value={displayedData.pendingFollowUps.length} subtext="Require action" icon={ClockIcon} colorClass="text-yellow-600 dark:text-yellow-400" />
                <KpiCard title="Networking Funnel" value={networkingFunnel.inConversation.length} subtext="'In Conversation' contacts" icon={NetworkingIcon} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* AI Co-Pilot */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-white dark:bg-slate-800/80 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Strategic Co-pilot</h3>
                        <div className="space-y-3">
                             <button onClick={() => {}} className="w-full text-left p-3 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-700/50 dark:hover:bg-slate-700 transition-colors">
                                <p className="font-semibold text-sm flex items-center gap-2"><MagnifyingGlassPlusIcon className="h-5 w-5 text-blue-500"/> Opportunity Scout</p>
                                <p className="text-xs text-slate-500 dark:text-slate-400">Find new high-fit roles based on your narrative.</p>
                            </button>
                             <button onClick={() => setIsSkillGapModalOpen(true)} className="w-full text-left p-3 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-700/50 dark:hover:bg-slate-700 transition-colors">
                                <p className="font-semibold text-sm flex items-center gap-2"><StrategyIcon className="h-5 w-5 text-green-500"/> Growth Pathways</p>
                                <p className="text-xs text-slate-500 dark:text-slate-400">Analyze skill gaps between your resume and market trends.</p>
                            </button>
                             <button onClick={() => setIsCatalyzeModalOpen(true)} className="w-full text-left p-3 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-700/50 dark:hover:bg-slate-700 transition-colors">
                                <p className="font-semibold text-sm flex items-center gap-2"><RocketLaunchIcon className="h-5 w-5 text-purple-500"/> Catalyze New Path</p>
                                <p className="text-xs text-slate-500 dark:text-slate-400">Synthesize your narratives to find new career angles.</p>
                            </button>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-slate-800/80 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">AI Focus Feed</h3>
                            <button onClick={handleGenerateFocusFeed} disabled={isGeneratingFeed} className="p-1 rounded-full text-blue-600 dark:text-blue-400 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                                {isGeneratingFeed ? <LoadingSpinner/> : <SparklesIcon className="h-5 w-5" />}
                            </button>
                        </div>
                        <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                            {feedError && <p className="text-sm text-red-500">{feedError}</p>}
                            {focusItems.length > 0 ? focusItems.map((item, index) => (
                                <div key={index} className="p-3 bg-slate-100 dark:bg-slate-700/50 rounded-lg">
                                    <p className="font-semibold text-sm text-slate-800 dark:text-slate-200">{item.title}</p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">{item.suggestion}</p>
                                </div>
                            )) : !isGeneratingFeed && <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-8">Click the ✨ to generate today's focus items.</p>}
                        </div>
                    </div>
                </div>

                {/* Networking Funnel */}
                <div className="lg:col-span-2 bg-white dark:bg-slate-800/80 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Networking Funnel</h3>
                    <div className="flex -mx-2">
                        <FunnelColumn title="To Contact" count={networkingFunnel.toContact.length} contacts={networkingFunnel.toContact} onOpenContactModal={onOpenContactModal} onUpdateContactStatus={onUpdateContactStatus}/>
                        <FunnelColumn title="Initial Outreach" count={networkingFunnel.initialOutreach.length} contacts={networkingFunnel.initialOutreach} onOpenContactModal={onOpenContactModal} onUpdateContactStatus={onUpdateContactStatus}/>
                        <FunnelColumn title="In Conversation" count={networkingFunnel.inConversation.length} contacts={networkingFunnel.inConversation} onOpenContactModal={onOpenContactModal} onUpdateContactStatus={onUpdateContactStatus}/>
                         <FunnelColumn title="Follow-up Needed" count={networkingFunnel.followUpNeeded.length} contacts={networkingFunnel.followUpNeeded} onOpenContactModal={onOpenContactModal} onUpdateContactStatus={onUpdateContactStatus}/>
                    </div>
                </div>
            </div>

             {/* Modals */}
             <SkillGapAnalysisModal 
                isOpen={isSkillGapModalOpen} 
                onClose={() => setIsSkillGapModalOpen(false)}
                isLoading={isAnalyzingSkillGap}
                result={skillGapResult}
                error={skillGapError}
            />

            <CatalyzePathModal
                isOpen={isCatalyzeModalOpen}
                onClose={() => setIsCatalyzeModalOpen(false)}
                isLoading={isCatalyzing}
                result={catalyzeResult}
                error={catalyzeError}
                onCreateNarrative={onCreateSynthesizedNarrative}
            />
        </div>
    );
};
