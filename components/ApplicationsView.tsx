import React, { useState } from 'react';
import { JobApplication, Company, Status, BaseResume, UserProfile, StrategicNarrative, Offer } from '../types';
import { ApplicationsTable } from './ApplicationsTable';
import { PlusCircleIcon, ApplicationsIcon, ResumeIcon, CurrencyDollarIcon } from './IconComponents';
import { ResumeFormulasDashboard } from './ResumeFormulasDashboard';
import { OffersDashboard } from './OffersDashboard';

interface ApplicationsViewProps {
    applications: JobApplication[];
    companies: Company[];
    statuses: Status[];
    offers: Offer[];
    onViewApplication: (appId: string) => void;
    onViewCompany: (companyId: string) => void;
    onResumeApplication: (app: JobApplication) => void;
    onAddNew: () => void;
    onDeleteApplication: (appId: string) => void;
    onUpdateApplicationStatus: (appId: string, statusId: string) => Promise<void>;
    onDeleteOffer: (offerId: string) => void;
    resumes: BaseResume[];
    userProfile: UserProfile | null;
    onAddNewResume: () => void;
    onEditResume: (resume: BaseResume) => void;
    onDeleteResume: (resumeId: string) => void;
    onCopyResume: (resume: BaseResume) => void;
    onSetDefaultResume: (resumeId: string) => void;
    onToggleLock: (resumeId: string, isCurrentlyLocked: boolean) => void;
    isLoading: boolean;
    activeNarrative: StrategicNarrative | null;
    strategicNarratives: StrategicNarrative[];
}

type Tab = 'lab' | 'formulas' | 'offers';

const tabs: { id: Tab; name: string; icon: React.ElementType }[] = [
    { id: 'lab', name: 'Applications Lab', icon: ApplicationsIcon },
    { id: 'formulas', name: 'Resume Formulas', icon: ResumeIcon },
    { id: 'offers', name: 'Offers', icon: CurrencyDollarIcon },
];

export const ApplicationsView = ({
    applications, companies, statuses, offers, onViewApplication, onViewCompany, onResumeApplication, onAddNew, onDeleteApplication, onUpdateApplicationStatus, onDeleteOffer,
    resumes, userProfile, onAddNewResume, onEditResume, onDeleteResume, onCopyResume, onSetDefaultResume, onToggleLock, isLoading, activeNarrative, strategicNarratives
}: ApplicationsViewProps): React.ReactNode => {
    const [activeTab, setActiveTab] = useState<Tab>('lab');

    const handleAppClick = (appId: string) => {
        const app = applications.find(a => a.job_application_id === appId);
        if (!app) return;

        const finalStatuses = [
            'Step-4: Applied',
            'Step-5: Comment/DM created',
            'Step-6: Email sent waiting for follow-up',
            'Hold',
            'Waiting',
            'Interviewing',
            'Accepted',
            'Rejected',
            'Bad Fit'
        ];
        const isFinal = app.status && finalStatuses.includes(app.status.status_name);

        if (isFinal) {
            onViewApplication(appId);
        } else {
            onResumeApplication(app);
        }
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
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Application Lab</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">Catalyze your next career move by tracking every application.</p>
                </div>
                <button
                    onClick={onAddNew}
                    className="inline-flex items-center justify-center w-full md:w-auto px-5 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                    <PlusCircleIcon className="w-5 h-5 mr-2 -ml-1" />
                    Add New Application
                </button>
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

            {activeTab === 'lab' && (
                <ApplicationsTable
                    title="All Applications"
                    applications={applications}
                    companies={companies}
                    statuses={statuses}
                    onViewApplication={handleAppClick}
                    onViewCompany={onViewCompany}
                    onDeleteApplication={onDeleteApplication}
                    onUpdateApplicationStatus={onUpdateApplicationStatus}
                    strategicNarratives={strategicNarratives}
                />
            )}
            {activeTab === 'formulas' && activeNarrative && (
                <ResumeFormulasDashboard
                    activeNarrative={activeNarrative}
                />
            )}
            {activeTab === 'offers' && (
                <OffersDashboard
                    offers={offers}
                    applications={applications}
                    onDeleteOffer={onDeleteOffer}
                />
            )}
        </div>
    );
};
