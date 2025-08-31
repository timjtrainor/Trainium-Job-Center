import React, { useState } from 'react';
import { Contact, StrategicNarrative, LinkedInEngagement, PostResponse, PostResponsePayload, Prompt, LinkedInPost, LinkedInEngagementPayload, Message, JobApplication, LinkedInPostPayload, Company, BaseResume, UserProfile } from '../types';
import { CompaniesView } from './CompaniesView';
import { TargetedContactsTab } from './TargetedContactsTab';
import { ContentReactorTab } from './ContentReactorTab';
import { ConversationCatalystTab } from './ConversationCatalystTab';
import { MessageInsightsTab } from './MessageInsightsTab';
import { MessageDetailModal } from './MessageDetailModal';
import { UsersIcon, LinkedInIcon, ChatBubbleLeftRightIcon, ArrowTrendingUpIcon, CompanyIcon } from './IconComponents';

interface EngagementHubProps {
    contacts: Contact[];
    posts: LinkedInPost[];
    engagements: LinkedInEngagement[];
    postResponses: PostResponse[];
    applications: JobApplication[];
    allMessages: Message[];
    userProfile: UserProfile | null;
    onOpenContactModal: (contact?: Partial<Contact> | null) => void;
    onCreatePostResponse: (payload: PostResponsePayload) => Promise<void>;
    onUpdatePostResponse: (commentId: string, payload: PostResponsePayload) => Promise<void>;
    onCreateLinkedInEngagement: (payload: LinkedInEngagementPayload) => Promise<void>;
    onCreatePost: (payload: LinkedInPostPayload) => Promise<void>;
    onImportContacts: (fileContent: string) => Promise<void>;
    prompts: Prompt[];
    onDeleteContact: (contactId: string) => void;
    companies: Company[];
    onViewCompany: (companyId: string) => void;
    onAddNewCompany: () => void;
    baseResumes: BaseResume[];
    strategicNarratives: StrategicNarrative[];
    activeNarrative: StrategicNarrative | null;
    onScoreEngagement: (engagement: LinkedInEngagement) => void;
}

type Tab = 'insights' | 'companies' | 'contacts' | 'content' | 'conversations';

const tabs: { id: Tab; name: string; icon: React.ElementType }[] = [
    { id: 'insights', name: 'Message Insights', icon: ArrowTrendingUpIcon },
    { id: 'companies', name: 'Companies', icon: CompanyIcon },
    { id: 'contacts', name: 'Targeted Contacts', icon: UsersIcon },
    { id: 'content', name: 'Content Reactor', icon: LinkedInIcon },
    { id: 'conversations', name: 'Conversation Catalyst', icon: ChatBubbleLeftRightIcon },
];

export const EngagementHub = (props: EngagementHubProps) => {
    const [activeTab, setActiveTab] = useState<Tab>('insights');
    const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);

    const handleViewMessage = (message: Message) => {
        setSelectedMessage(message);
    };

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
        <div className="space-y-8 animate-fade-in">
            <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Engagement Hub</h1>
                <p className="mt-1 text-slate-600 dark:text-slate-400">Manage your networking, content, and strategic communications.</p>
            </div>

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
            
            <div className="mt-6">
                {activeTab === 'insights' && (
                    <MessageInsightsTab 
                        messages={props.allMessages} 
                        contacts={props.contacts}
                        onViewMessage={handleViewMessage}
                    />
                )}
                 {activeTab === 'companies' && (
                    <CompaniesView 
                        companies={props.companies}
                        applications={props.applications}
                        onViewCompany={props.onViewCompany}
                        onAddNewCompany={props.onAddNewCompany}
                    />
                )}
                {activeTab === 'contacts' && (
                    <TargetedContactsTab 
                        contacts={props.contacts} 
                        activeNarrative={props.activeNarrative} 
                        onOpenContactModal={props.onOpenContactModal} 
                        onImportContacts={props.onImportContacts}
                        onDeleteContact={props.onDeleteContact}
                    />
                )}
                {activeTab === 'content' && (
                    <ContentReactorTab
                        posts={props.posts}
                        engagements={props.engagements}
                        contacts={props.contacts}
                        applications={props.applications}
                        allMessages={props.allMessages}
                        baseResumes={props.baseResumes}
                        onCreatePost={props.onCreatePost}
                        onCreateLinkedInEngagement={props.onCreateLinkedInEngagement}
                        onOpenContactModal={props.onOpenContactModal}
                        prompts={props.prompts}
                        strategicNarratives={props.strategicNarratives}
                        activeNarrative={props.activeNarrative}
                        onScoreEngagement={props.onScoreEngagement}
                    />
                )}
                {activeTab === 'conversations' && (
                    <ConversationCatalystTab 
                        postResponses={props.postResponses}
                        onCreatePostResponse={props.onCreatePostResponse}
                        onUpdatePostResponse={props.onUpdatePostResponse}
                        activeNarrative={props.activeNarrative}
                        prompts={props.prompts}
                    />
                )}
            </div>

            {selectedMessage && <MessageDetailModal isOpen={!!selectedMessage} onClose={() => setSelectedMessage(null)} message={selectedMessage} />}
        </div>
    );
};