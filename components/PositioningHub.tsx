import React, { useState } from 'react';
import { BaseResume, Prompt, StrategicNarrative, StrategicNarrativePayload } from '../types';
import { CareerBrandDashboard } from './CareerBrandDashboard';
import { CoreNarrativeLab } from './CoreNarrativeLab';
import { StrategyIcon, RocketLaunchIcon } from './IconComponents';

interface PositioningHubProps {
    activeNarrative: StrategicNarrative | null;
    activeNarrativeId: string | null;
    onSaveNarrative: (payload: StrategicNarrativePayload, narrativeId: string) => Promise<void>;
    onUpdateNarrative: (updatedNarrative: StrategicNarrative) => void;
    prompts: Prompt[];
    baseResumes: BaseResume[];
}

type Tab = 'strategy' | 'roles' | 'narrative_lab';

const tabs: { id: Tab; name: string; icon: React.ElementType }[] = [
    { id: 'strategy', name: 'Define Your Strategy', icon: StrategyIcon },
    { id: 'narrative_lab', name: 'Core Narrative Lab', icon: RocketLaunchIcon },
];

export const PositioningHub = ({
    activeNarrative,
    activeNarrativeId,
    onSaveNarrative,
    onUpdateNarrative,
    prompts,
    baseResumes,
}: PositioningHubProps) => {
    const [activeTab, setActiveTab] = useState<Tab>('strategy');

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
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Positioning Hub</h1>
                <p className="mt-1 text-slate-600 dark:text-slate-400">Define your career strategy and manage the resume formulas that bring it to life.</p>
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

            <div className="mt-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700">
                {activeTab === 'strategy' && activeNarrative && (
                    <CareerBrandDashboard
                        activeNarrative={activeNarrative}
                        onUpdateNarrative={onUpdateNarrative}
                    />
                )}
                {activeTab === 'narrative_lab' && activeNarrative && (
                    <CoreNarrativeLab
                        activeNarrative={activeNarrative}
                        onSaveNarrative={onSaveNarrative}
                        prompts={prompts}
                    />
                )}
            </div>
        </div>
    );
};
