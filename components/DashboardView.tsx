import React, { useMemo, useState } from 'react';
import { JobApplication, Contact, Message, LinkedInPost, UserProfile, Prompt, LinkedInEngagement, StrategicNarrativePayload, AiFocusItem, Sprint, PromptContext } from '../types';
import * as geminiService from '../services/geminiService';
import { LoadingSpinner, CheckBadgeIcon, ClockIcon, XCircleIcon, NetworkingIcon, SparklesIcon, ClipboardDocumentListIcon, ChatBubbleLeftRightIcon } from './IconComponents';

interface DashboardViewProps {
    applications: JobApplication[];
    contacts: Contact[];
    messages: Message[];
    linkedInPosts: LinkedInPost[];
    engagements: LinkedInEngagement[];
    pendingFollowUps: Message[];
    userProfile: UserProfile | null;
    prompts: Prompt[];
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
    onCreateSynthesizedNarrative: (payload: StrategicNarrativePayload) => Promise<void>;
    sprint: Sprint | null;
    weeklyProgress: string;
    onOpenContactModal: (contact: Partial<Contact>) => void;
    onUpdateContactStatus: (contactId: string, status: string) => void;
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

const TargetProgressCard = ({ label, current, target, unit, icon: Icon }: { label: string, current: number, target: number, unit: string, icon: React.ElementType }) => {
    const percentage = target > 0 ? Math.min(Math.round((current / target) * 100), 100) : 0;
    const isMet = current >= target && target > 0;

    return (
        <div className="bg-white dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="flex justify-between items-start mb-2">
                <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg text-slate-500 dark:text-slate-400">
                    <Icon className="h-5 w-5" />
                </div>
                {isMet ? (
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border border-green-200 dark:border-green-800">Target Met</span>
                ) : (
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 border border-blue-200 dark:border-blue-800">In Progress</span>
                )}
            </div>
            <h4 className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</h4>
            <div className="flex items-baseline gap-1 mt-1">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">{current}</span>
                <span className="text-sm text-slate-500 dark:text-slate-400">/ {target} {unit}</span>
            </div>
            <div className="mt-3 h-1.5 w-full bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                    className={`h-full transition-all duration-1000 ${isMet ? 'bg-green-500' : 'bg-blue-600'}`}
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
};

export const DashboardView = (props: DashboardViewProps): React.ReactNode => {
    const { applications, contacts, messages, linkedInPosts, engagements, userProfile, onOpenContactModal, onUpdateContactStatus, prompts, debugCallbacks, pendingFollowUps, sprint, weeklyProgress } = props;

    const [focusItems, setFocusItems] = useState<AiFocusItem[]>([]);
    const [isGeneratingFeed, setIsGeneratingFeed] = useState(false);
    const [feedError, setFeedError] = useState<string | null>(null);

    const weeklyStats = useMemo(() => {
        const today = new Date();
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - today.getDay());
        startOfWeek.setHours(0, 0, 0, 0);

        const appsThisWeek = applications.filter(a => new Date(a.date_applied) >= startOfWeek).length;
        const contactsThisWeek = contacts.filter(c => new Date(c.date_contacted) >= startOfWeek).length;
        const postsThisWeek = linkedInPosts.filter(p => new Date(p.created_at) >= startOfWeek).length;

        const goals = sprint?.actions.filter(a => a.is_goal) || [];
        const appGoal = goals.find(g => g.goal_type === 'applications')?.goal_target || 0;
        const contactGoal = goals.find(g => g.goal_type === 'contacts')?.goal_target || 0;
        const postGoal = goals.find(g => g.goal_type === 'posts')?.goal_target || 0;

        return {
            apps: appsThisWeek,
            appGoal,
            contacts: contactsThisWeek,
            contactGoal,
            posts: postsThisWeek,
            postGoal,
            totalEngagements: engagements.length,
            engagementGrowth: engagements.filter(e => new Date(e.created_at) >= startOfWeek).length
        };
    }, [applications, contacts, linkedInPosts, engagements, sprint]);

    const recentApplications = useMemo(() => {
        return [...applications]
            .sort((a, b) => new Date(b.date_applied).getTime() - new Date(a.date_applied).getTime())
            .slice(0, 5);
    }, [applications]);

    const overallPipelineAlignment = useMemo(() => {
        const scoredApps = applications.filter(app => typeof app.strategic_fit_score === 'number' && app.status?.status_name !== 'Bad Fit');
        if (scoredApps.length === 0) return 0;
        const totalScore = scoredApps.reduce((sum, app) => sum + (app.strategic_fit_score || 0), 0);
        return (totalScore / scoredApps.length);
    }, [applications]);

    const networkingFunnel = useMemo(() => {
        const contactIdsWithInterviews = new Set<string>();
        applications.forEach(app => {
            app.interviews?.forEach(interview => {
                interview.interview_contacts?.forEach(contact => {
                    contactIdsWithInterviews.add(contact.contact_id);
                });
            });
        });

        const contactsInFunnel = contacts.filter(c => !contactIdsWithInterviews.has(c.contact_id));

        return {
            toContact: contactsInFunnel.filter(c => c.status === 'To Contact'),
            initialOutreach: contactsInFunnel.filter(c => c.status === 'Initial Outreach'),
            inConversation: contactsInFunnel.filter(c => c.status === 'In Conversation'),
            followUpNeeded: contactsInFunnel.filter(c => c.status === 'Follow-up Needed'),
        };
    }, [contacts, applications]);

    const handleGenerateFocusFeed = async () => {
        setIsGeneratingFeed(true);
        setFeedError(null);
        setFocusItems([]);

        try {
            const prompt = prompts.find(p => p.id === 'GENERATE_DASHBOARD_FEED');
            if (!prompt) throw new Error("Dashboard feed prompt not found.");

            const context: PromptContext = {
                WEEKLY_APPLICATION_GOAL: weeklyStats.appGoal,
                WEEKLY_CONTACT_GOAL: weeklyStats.contactGoal,
                WEEKLY_POST_GOAL: weeklyStats.postGoal,
                WEEKLY_PROGRESS: weeklyProgress,
                PENDING_FOLLOW_UPS: JSON.stringify(pendingFollowUps.map(f => ({ contactName: `${f.contact?.first_name} ${f.contact?.last_name}`, dueDate: f.follow_up_due_date }))),
            };

            const result = await geminiService.generateDashboardFeed(context, prompt.id, debugCallbacks);
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
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Performance Dashboard</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">
                        Welcome back, {userProfile?.first_name || 'User'}. Tracking your core performance metrics.
                    </p>
                </div>
            </header>

            {/* Weekly Goal Progress */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <TargetProgressCard label="Resumes Submitted" current={weeklyStats.apps} target={weeklyStats.appGoal} unit="resumes" icon={ClipboardDocumentListIcon} />
                <TargetProgressCard label="New Connections" current={weeklyStats.contacts} target={weeklyStats.contactGoal} unit="contacts" icon={NetworkingIcon} />
                <TargetProgressCard label="LinkedIn Posts" current={weeklyStats.posts} target={weeklyStats.postGoal} unit="posts" icon={ChatBubbleLeftRightIcon} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <div className="lg:col-span-1">
                    <KpiCard title="Active Applications" value={applications.filter(a => !['Rejected', 'Bad Fit', 'Accepted'].includes(a.status?.status_name || '')).length} subtext="In pipeline" icon={ClipboardDocumentListIcon} />
                </div>
                <div className="lg:col-span-1">
                    <KpiCard title="Pipeline Alignment" value={overallPipelineAlignment.toFixed(1)} subtext="Avg. strategic fit score" icon={CheckBadgeIcon} colorClass="text-green-600 dark:text-green-400" />
                </div>
                <div className="lg:col-span-1">
                    <KpiCard title="Follow-ups Due" value={pendingFollowUps.length} subtext="Require action" icon={ClockIcon} colorClass="text-yellow-600 dark:text-yellow-400" />
                </div>
                <div className="lg:col-span-1">
                    <KpiCard title="Engagement Growth" value={weeklyStats.engagementGrowth} subtext="Interactions this week" icon={SparklesIcon} colorClass="text-purple-600 dark:text-purple-400" />
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column: AI Feed and Recent Submissions */}
                <div className="lg:col-span-1 space-y-6">
                    {/* AI Focus Feed */}
                    <div className="bg-white dark:bg-slate-800/80 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">AI Focus Feed</h3>
                            <button onClick={handleGenerateFocusFeed} disabled={isGeneratingFeed} className="p-1 rounded-full text-blue-600 dark:text-blue-400 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                                {isGeneratingFeed ? <LoadingSpinner /> : <SparklesIcon className="h-5 w-5" />}
                            </button>
                        </div>
                        <div className="space-y-3 max-h-60 overflow-y-auto pr-2">
                            {feedError && <p className="text-sm text-red-500">{feedError}</p>}
                            {focusItems.length > 0 ? focusItems.map((item, index) => (
                                <div key={index} className="p-3 bg-slate-100 dark:bg-slate-700/50 rounded-lg border-l-4 border-blue-500">
                                    <p className="font-semibold text-sm text-slate-800 dark:text-slate-200">{item.title}</p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">{item.suggestion}</p>
                                </div>
                            )) : !isGeneratingFeed && <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-8">Click the ✨ to generate today's focus items.</p>}
                        </div>
                    </div>

                    {/* Recent Submissions */}
                    <div className="bg-white dark:bg-slate-800/80 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Recent Resumes Submitted</h3>
                        <div className="space-y-3">
                            {recentApplications.length > 0 ? recentApplications.map((app, idx) => (
                                <div key={idx} className="flex justify-between items-center p-2 hover:bg-slate-50 dark:hover:bg-slate-700/30 rounded-lg transition-colors border border-transparent hover:border-slate-200 dark:hover:border-slate-600">
                                    <div className="min-w-0">
                                        <p className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate">{app.job_title}</p>
                                        <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{app.company_name || 'Unknown Company'}</p>
                                    </div>
                                    <span className="text-[10px] font-mono text-slate-400 bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 rounded flex-shrink-0 ml-2">
                                        {new Date(app.date_applied).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                    </span>
                                </div>
                            )) : (
                                <p className="text-sm text-slate-500 text-center py-4">No submissions yet.</p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Column: Networking Funnel */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white dark:bg-slate-800/80 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Networking Funnel</h3>
                            <span className="text-xs text-slate-400 font-medium">Build your network through engagement</span>
                        </div>
                        <div className="flex -mx-2 overflow-x-auto pb-4">
                            <FunnelColumn title="To Contact" count={networkingFunnel.toContact.length} contacts={networkingFunnel.toContact} onOpenContactModal={onOpenContactModal} onUpdateContactStatus={onUpdateContactStatus} />
                            <FunnelColumn title="Initial Outreach" count={networkingFunnel.initialOutreach.length} contacts={networkingFunnel.initialOutreach} onOpenContactModal={onOpenContactModal} onUpdateContactStatus={onUpdateContactStatus} />
                            <FunnelColumn title="In Conversation" count={networkingFunnel.inConversation.length} contacts={networkingFunnel.inConversation} onOpenContactModal={onOpenContactModal} onUpdateContactStatus={onUpdateContactStatus} />
                            <FunnelColumn title="Follow-up Needed" count={networkingFunnel.followUpNeeded.length} contacts={networkingFunnel.followUpNeeded} onOpenContactModal={onOpenContactModal} onUpdateContactStatus={onUpdateContactStatus} />
                        </div>
                    </div>

                    {/* Engagement / Thought Leadership */}
                    <div className="bg-white dark:bg-slate-800/80 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">LinkedIn Thought Leadership</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-4 bg-blue-50/50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-800/50 flex items-center gap-4">
                                <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                                    <ChatBubbleLeftRightIcon className="h-6 w-6" />
                                </div>
                                <div>
                                    <p className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">Posts Created</p>
                                    <p className="text-2xl font-bold text-slate-900 dark:text-white">{linkedInPosts.length}</p>
                                </div>
                            </div>
                            <div className="p-4 bg-purple-50/50 dark:bg-purple-900/10 rounded-xl border border-purple-100 dark:border-purple-800/50 flex items-center gap-4">
                                <div className="h-10 w-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400">
                                    <SparklesIcon className="h-6 w-6" />
                                </div>
                                <div>
                                    <p className="text-xs font-semibold text-purple-600 dark:text-purple-400 uppercase tracking-wider">Interactions</p>
                                    <p className="text-2xl font-bold text-slate-900 dark:text-white">{engagements.length}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
