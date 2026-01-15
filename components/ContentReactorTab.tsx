import React, { useState } from 'react';
import {
    LinkedInPost,
    Contact,
    StrategicNarrative,
    Prompt,
    LinkedInPostPayload,
    LinkedInEngagement,
    LinkedInEngagementPayload,
    JobApplication,
    Message,
    BaseResume
} from '../types';
import { LinkedInPostStudioView } from './LinkedInPostStudioView';
import { PostEngagementTab } from './PostEngagementTab';
import { ManualEngagementForm } from './ManualEngagementForm';
import { LinkedInIcon, UsersIcon } from './IconComponents';

interface ContentReactorTabProps {
    posts: LinkedInPost[];
    engagements: LinkedInEngagement[];
    contacts: Contact[];
    applications: JobApplication[];
    allMessages: Message[];
    baseResumes: BaseResume[];
    onCreatePost: (payload: LinkedInPostPayload) => Promise<void>;
    onCreateLinkedInEngagement: (payload: LinkedInEngagementPayload) => Promise<void>;
    onOpenContactModal: (contact?: Partial<Contact> | null) => void;
    // prompts prop removed
    strategicNarratives: StrategicNarrative[];
    activeNarrative: StrategicNarrative | null;
    onScoreEngagement: (engagement: LinkedInEngagement) => void;
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
}

type Tab = 'studio' | 'engagements';

export const ContentReactorTab = (props: ContentReactorTabProps) => {
    const [activeTab, setActiveTab] = useState<Tab>('studio');
    const [isEngagementFormOpen, setIsEngagementFormOpen] = useState(false);

    const tabs: { id: Tab; name: string; icon: React.ElementType }[] = [
        { id: 'studio', name: 'Post Studio', icon: LinkedInIcon },
        { id: 'engagements', name: 'Engagement Tracking', icon: UsersIcon },
    ];

    const tabClass = (tabName: Tab) =>
        `group inline-flex items-center justify-center px-4 py-2.5 -mb-px border-b-2 font-medium text-sm focus:outline-none ` +
        (activeTab === tabName
            ? 'border-blue-500 text-blue-600 dark:text-blue-400'
            : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:border-slate-600');

    const iconClass = (tabName: Tab) =>
        `mr-2 h-5 w-5 ` +
        (activeTab === tabName
            ? 'text-blue-500'
            : 'text-slate-400 group-hover:text-slate-500 dark:group-hover:text-slate-300');

    return (
        <div className="space-y-6">
            <div className="border-b border-slate-200 dark:border-slate-700">
                <nav className="-mb-px flex space-x-6" aria-label="Tabs">
                    {tabs.map(tab => (
                        <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={tabClass(tab.id)}>
                            <tab.icon className={iconClass(tab.id)} />
                            <span>{tab.name}</span>
                        </button>
                    ))}
                </nav>
            </div>

            {activeTab === 'studio' && (
                <LinkedInPostStudioView
                    posts={props.posts}
                    // prompts prop removed
                    onCreatePost={props.onCreatePost}
                    strategicNarratives={props.strategicNarratives}
                    applications={props.applications}
                    debugCallbacks={props.debugCallbacks}
                />
            )}

            {activeTab === 'engagements' && (
                <PostEngagementTab
                    engagements={props.engagements}
                    contacts={props.contacts}
                    activeNarrative={props.activeNarrative}
                    onOpenContactModal={props.onOpenContactModal}
                    onAddEngagement={() => setIsEngagementFormOpen(true)}
                />
            )}

            <ManualEngagementForm
                isOpen={isEngagementFormOpen}
                onClose={() => setIsEngagementFormOpen(false)}
                onCreate={props.onCreateLinkedInEngagement}
                posts={props.posts}
            />
        </div>
    );
};