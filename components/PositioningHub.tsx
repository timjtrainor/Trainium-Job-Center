import React, { useState, useEffect, useCallback } from 'react';
import { BaseResume, Prompt, StrategicNarrative, StrategicNarrativePayload, Competency, UploadedDocument } from '../types';
import { CareerBrandDashboard } from './CareerBrandDashboard';
import { CoreNarrativeLab } from './CoreNarrativeLab';
import { CompetencyArchitectureIntake } from './CompetencyArchitectureIntake';
import { StrategyIcon, RocketLaunchIcon, CheckBadgeIcon } from './IconComponents';
import { getTracksWithApplications, getTrackCompetencies, saveTrackCompetencies, getCollectionDocuments } from '../services/apiService';
import { useToast } from '../hooks/useToast';

interface PositioningHubProps {
    activeNarrative: StrategicNarrative | null;
    activeNarrativeId: string | null;
    onSaveNarrative: (payload: StrategicNarrativePayload, narrativeId: string) => Promise<void>;
    onUpdateNarrative: (updatedNarrative: StrategicNarrative) => void;
    prompts: Prompt[];
    baseResumes: BaseResume[];
}

type Tab = 'competencies' | 'strategy' | 'narrative_lab';

const tabs: { id: Tab; name: string; icon: React.ElementType }[] = [
    { id: 'competencies', name: 'Competency Hub', icon: CheckBadgeIcon },
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
    const [activeTab, setActiveTab] = useState<Tab>('competencies');

    // Lifted State for Competency Architecture
    const [tracks, setTracks] = useState<string[]>([]);
    const [selectedTrack, setSelectedTrack] = useState<string>('');
    const [competencies, setCompetencies] = useState<Competency[]>([]);
    const [trackId, setTrackId] = useState<string | null>(null);
    const [isLoadingCompetencies, setIsLoadingCompetencies] = useState(false);
    const [isSavingCompetencies, setIsSavingCompetencies] = useState(false);
    const [proofPoints, setProofPoints] = useState<UploadedDocument[]>([]);
    const [isLoadingProofPoints, setIsLoadingProofPoints] = useState(false);
    const { addToast } = useToast();

    const fetchTracks = useCallback(async () => {
        try {
            const data = await getTracksWithApplications();
            setTracks(data);
            if (data.length > 0 && !selectedTrack) {
                setSelectedTrack(data[0]);
            }
        } catch (err) {
            console.error('Failed to fetch tracks:', err);
            addToast('Failed to load job tracks', 'error');
        }
    }, [selectedTrack, addToast]);

    useEffect(() => {
        fetchTracks();
    }, [fetchTracks]);

    // Fetch Proof Points (ChromaDB)
    const fetchProofPoints = useCallback(async () => {
        setIsLoadingProofPoints(true);
        try {
            const docs = await getCollectionDocuments('proof_points');
            setProofPoints(docs);
        } catch (error) {
            console.error('Failed to load proof points:', error);
        } finally {
            setIsLoadingProofPoints(false);
        }
    }, []);

    useEffect(() => {
        fetchProofPoints();
    }, [fetchProofPoints]);

    // Fetch Competencies when Track Changes
    const fetchCompetencies = useCallback(async (trackName: string) => {
        if (!trackName) return;
        setIsLoadingCompetencies(true);
        try {
            const data = await getTrackCompetencies(trackName);
            if (data) {
                setTrackId(data.track_competency_id);
                // Migrate old data structure if needed (Safety Check)
                const migrated = (data.competencies || []).map((comp: any) => {
                    if (comp.strategies) {
                        return {
                            ...comp,
                            strategies: comp.strategies.map((s: any) => ({
                                ...s,
                                tools: s.tools || [],
                                kpis: s.kpis || [],
                                talking_points: s.talking_points || []
                            }))
                        };
                    }
                    return {
                        title: comp.title,
                        strategies: [{
                            strategy_name: 'Core Strategy',
                            best_practices: comp.best_practices || '',
                            tools: comp.tools || [],
                            kpis: [],
                            talking_points: []
                        }]
                    };
                });
                setCompetencies(migrated);
            } else {
                setTrackId(null);
                setCompetencies([]);
            }
        } catch (err) {
            console.error('Failed to fetch competencies:', err);
            addToast('Failed to load competencies', 'error');
        } finally {
            setIsLoadingCompetencies(false);
        }
    }, [addToast]);

    useEffect(() => {
        if (selectedTrack) {
            fetchCompetencies(selectedTrack);
        }
    }, [selectedTrack, fetchCompetencies]);

    const handleSaveCompetencies = async () => {
        if (!selectedTrack) return;
        setIsSavingCompetencies(true);
        try {
            await saveTrackCompetencies({
                track_competency_id: trackId || undefined,
                track_name: selectedTrack,
                competencies
            });
            addToast('Competencies saved successfully', 'success');
            fetchCompetencies(selectedTrack); // Refresh to get the ID if it was new
        } catch (err) {
            console.error('Failed to save competencies:', err);
            addToast('Failed to save competencies', 'error');
        } finally {
            setIsSavingCompetencies(false);
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
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Positioning Hub</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">Define your career strategy and manage the resume formulas that bring it to life.</p>
                </div>
                {/* Global Context Selector */}
                <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-2 rounded-lg border border-slate-200 dark:border-slate-700">
                    <span className="text-xs font-bold uppercase text-slate-500 ml-2">Context:</span>
                    <select
                        value={selectedTrack}
                        onChange={(e) => setSelectedTrack(e.target.value)}
                        className="bg-white dark:bg-slate-900 border-none rounded text-sm font-semibold focus:ring-0 py-1 pl-2 pr-8"
                    >
                        <option value="" disabled>Select Job Track...</option>
                        {tracks.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                </div>
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
                {activeTab === 'competencies' && (
                    <CompetencyArchitectureIntake
                        tracks={tracks}
                        selectedTrack={selectedTrack}
                        onSelectTrack={setSelectedTrack}
                        competencies={competencies}
                        onUpdateCompetencies={setCompetencies}
                        trackId={trackId}
                        isLoading={isLoadingCompetencies}
                        onSave={handleSaveCompetencies}
                        isSaving={isSavingCompetencies}
                    />
                )}
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
                        competencies={competencies}
                        proofPoints={proofPoints}
                    />
                )}
            </div>
        </div>
    );
};
