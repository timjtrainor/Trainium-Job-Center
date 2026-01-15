import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { StrategicNarrative, StrategicNarrativePayload, Prompt, ImpactStory, BaseResume, Competency, UploadedDocument } from '../types';
import * as geminiService from '../services/geminiService';
import * as apiService from '../services/apiService';
import { LoadingSpinner, SparklesIcon, TrashIcon, ChevronDownIcon, ChevronUpIcon, CheckIcon, PlusCircleIcon, BuildingOfficeIcon } from './IconComponents';

interface CoreNarrativeLabProps {
    activeNarrative: StrategicNarrative;
    onSaveNarrative: (payload: StrategicNarrativePayload, narrativeId: string) => Promise<void>;
    prompts: Prompt[];
    competencies: Competency[];
    proofPoints: UploadedDocument[];
}

const FRAMEWORKS = ['DIGS', 'STAR', 'PAR', 'SCQA'] as const;

export const CoreNarrativeLab = ({ activeNarrative, onSaveNarrative, prompts, competencies, proofPoints }: CoreNarrativeLabProps) => {
    // State for Wizard Selection
    const [selectedFramework, setSelectedFramework] = useState<typeof FRAMEWORKS[number]>('DIGS');

    // Strategy Selection (Now linked to Competency Hub)
    const [selectedStrategyId, setSelectedStrategyId] = useState<string>('');
    const [selectedexperienceKey, setSelectedExperienceKey] = useState<string>('');

    const [isGenerating, setIsGenerating] = useState(false);
    const [stories, setStories] = useState<ImpactStory[]>(activeNarrative.impact_stories || []);
    const [selectedStoryId, setSelectedStoryId] = useState<string | null>(null);

    // Sync stories
    useEffect(() => {
        setStories(activeNarrative.impact_stories || []);
    }, [activeNarrative.impact_stories]);

    const handleSave = async (updatedStories: ImpactStory[]) => {
        setStories(updatedStories);
        await onSaveNarrative({ impact_stories: updatedStories }, activeNarrative.narrative_id);
    };

    // Helpers to find strategy details
    const getStrategyDetails = (id: string) => {
        for (const comp of competencies) {
            const strat = comp.strategies.find((s: any) => (s.strategy_name === id || s.strategy_name === id.split('::')[1])); // Fuzzy or exact
            // Better: Let's assume we construct ID as compIndex::stratIndex or similar? 
            // Actually, let's just use the name for now as the ID isn't stable in the simple type.
            // Or better, let's look it up.
        }
        return null;
    };

    // Flatten strategies for dropdown
    const availableStrategies = React.useMemo(() => competencies.flatMap(c =>
        c.strategies.map(s => ({
            label: `${c.title} > ${s.strategy_name}`,
            value: s.strategy_name,
            details: s,
            competency: c.title
        }))
    ), [competencies]);

    // Group Proof Points by Company|Role (Same as ResumeFormulasDashboard)
    const groupedExperiences = React.useMemo(() => {
        const groups: Record<string, UploadedDocument[]> = {};
        proofPoints.forEach(doc => {
            const company = doc.metadata?.company || 'Unknown Company';
            const role = doc.metadata?.role_title || 'Unknown Role';
            const key = `${company}|${role}`;
            if (!groups[key]) groups[key] = [];
            groups[key].push(doc);
        });

        return Object.entries(groups).map(([key, docs]) => {
            const sorted = docs.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
            return {
                key,
                latest: sorted[0],
                label: `${sorted[0].metadata?.company} - ${sorted[0].metadata?.role_title}`
            };
        }).sort((a, b) => a.label.localeCompare(b.label));
    }, [proofPoints]);

    const handleGenerate = async () => {
        if (!selectedStrategyId || !selectedexperienceKey) {
            alert("Please select a Strategy and a Proof Point (Experience).");
            return;
        }

        const strategyObj = availableStrategies.find(s => s.value === selectedStrategyId);
        const experience = groupedExperiences.find(e => e.key === selectedexperienceKey);

        setIsGenerating(true);
        try {
            // 1. Fetch full high-fidelity content if it's a Chroma proof point
            let experienceContext = experience?.latest.content || experience?.latest.metadata?.description || "No specific experience content available.";

            if (experience?.latest.id && experience?.latest.collection_name) {
                try {
                    const detail = await apiService.getDocumentDetail(experience.latest.collection_name, experience.latest.id);
                    if (detail.content) {
                        experienceContext = detail.content;
                    }
                } catch (err) {
                    console.warn("Failed to fetch full document detail, falling back to snippet:", err);
                }
            }

            // 2. Construct Strategy Context
            const strategyContext = strategyObj ? JSON.stringify({
                competency: strategyObj.competency,
                name: strategyObj.details.strategy_name,
                best_practices: strategyObj.details.best_practices,
                kpis: strategyObj.details.kpis,
                talking_points: strategyObj.details.talking_points
            }) : selectedStrategyId;

            // 3. Generate structured narrative
            console.log("Generating Narrative with context:", {
                framework: selectedFramework,
                strategy: strategyObj?.details.strategy_name,
                experience: experience?.latest.metadata?.company || 'Unknown'
            });

            const result = await geminiService.generateStructuredNarrative({
                strategy_name: strategyObj?.details.strategy_name || selectedStrategyId,
                strategy_definition: strategyContext,
                competency_name: strategyObj?.competency || "General",
                experience_context: experienceContext,
                framework: selectedFramework
            }, 'GENERATE_STRUCTURED_NARRATIVE');

            console.log("Narrative Generation Result:", result);

            const storyData: Partial<ImpactStory> = {
                story_title: `${strategyObj?.details.strategy_name || selectedStrategyId} - ${experience?.latest.metadata?.company || 'Unknown'}`,
                format: selectedFramework,
                story_body: {}, // Legacy
                hero_kpi: result.hero_kpi,
                visual_anchor: result.visual_anchor,
                narrative_steps: result.narrative_steps,
                thinned_bullets: result.thinned_bullets,
                associated_experience_index: -1, // No longer using legacy index
                associated_strategy_id: selectedStrategyId,
                target_questions: []
            };

            // Check if a story already exists for this Strategy + Experience combo
            const existingStoryIndex = stories.findIndex(s =>
                s.associated_strategy_id === selectedStrategyId &&
                s.story_title.includes(experience?.latest.metadata?.company as string || '___')
            );

            let updatedStories: ImpactStory[];
            let finalStoryId: string;

            if (existingStoryIndex !== -1) {
                // Update existing
                const existingStory = stories[existingStoryIndex];
                finalStoryId = existingStory.story_id;
                updatedStories = [...stories];
                updatedStories[existingStoryIndex] = {
                    ...existingStory,
                    ...storyData,
                    story_id: finalStoryId // Keep same ID
                };
            } else {
                // Create new
                finalStoryId = uuidv4();
                const newStory: ImpactStory = {
                    ...storyData as ImpactStory,
                    story_id: finalStoryId
                };
                updatedStories = [...stories, newStory];
            }

            await handleSave(updatedStories);
            setSelectedStoryId(finalStoryId);

        } catch (e) {
            console.error(e);
            alert("Failed to generate narrative. See console.");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleRemoveStory = async (id: string) => {
        const updated = stories.filter(s => s.story_id !== id);
        await handleSave(updated);
        if (selectedStoryId === id) setSelectedStoryId(null);
    };

    const handleUpdateStory = async (updatedStory: ImpactStory) => {
        const updated = stories.map(s => s.story_id === updatedStory.story_id ? updatedStory : s);
        await handleSave(updated);
    };

    const selectedStory = stories.find(s => s.story_id === selectedStoryId);

    // Framework Step Definitions
    const FRAMEWORK_STEPS: Record<string, string[]> = {
        'STAR': ['Situation', 'Task', 'Action', 'Result'],
        'DIGS': ['Dramatize', 'Indicate', 'Go', 'Synergize'],
        'PAR': ['Problem', 'Action', 'Result'],
        'SCQA': ['Situation', 'Complication', 'Question', 'Answer']
    };

    // Helpers for rendering the structured view
    const renderSteps = (story: ImpactStory) => {
        if (!story.narrative_steps) return <p className="text-slate-500 italic">No structured steps available.</p>;

        // Determine order based on story format
        const order = FRAMEWORK_STEPS[story.format] || [];

        // Sort keys: If key is in order array, use index. If not, put at end.
        const sortedKeys = Object.keys(story.narrative_steps).sort((a, b) => {
            const indexA = order.indexOf(a);
            const indexB = order.indexOf(b);

            if (indexA !== -1 && indexB !== -1) return indexA - indexB;
            if (indexA !== -1) return -1;
            if (indexB !== -1) return 1;
            return 0;
        });

        return order.map((label) => {
            // Try to find a matching key in narrative_steps
            // In case the AI returned lowercase or slightly different keys
            const keys = Object.keys(story.narrative_steps!);
            const matchKey = keys.find(k =>
                k.toLowerCase() === label.toLowerCase() ||
                k.toLowerCase().includes(label.toLowerCase())
            );

            const value = matchKey ? story.narrative_steps![matchKey] : "Step content not available.";

            return (
                <div key={label} className="mb-3">
                    <span className="text-xs font-bold uppercase text-slate-400 block mb-1">{label}</span>
                    <textarea
                        className="w-full text-sm p-3 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-serif leading-relaxed"
                        rows={4}
                        value={value}
                        onChange={(e) => {
                            const actualKey = matchKey || label;
                            const newSteps = { ...story.narrative_steps, [actualKey]: e.target.value };
                            handleUpdateStory({ ...story, narrative_steps: newSteps as any });
                        }}
                    />
                </div>
            );
        });
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* LEFT PANEL: Library & Wizard */}
            <div className="lg:col-span-4 space-y-6">

                {/* 1. Story Library (Top for Access) */}
                <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-4">
                    <div className="flex justify-between items-center mb-3">
                        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider">Strategy Library</h3>
                        <span className="text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded-full font-medium">
                            {stories.length}
                        </span>
                    </div>

                    <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                        {stories.map(story => (
                            <div
                                key={story.story_id}
                                onClick={() => setSelectedStoryId(story.story_id)}
                                className={`p-3 rounded-lg border cursor-pointer transition-all relative group ${selectedStoryId === story.story_id
                                    ? 'bg-blue-50 border-blue-400 dark:bg-blue-900/20 dark:border-blue-500 shadow-sm ring-1 ring-blue-400 dark:ring-blue-500'
                                    : 'bg-white border-slate-200 hover:border-blue-300 hover:shadow-sm dark:bg-slate-700/50 dark:border-slate-700 dark:hover:border-slate-600'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <div className="pr-6">
                                        <h4 className={`font-bold text-sm leading-tight mb-1 ${selectedStoryId === story.story_id ? 'text-blue-700 dark:text-blue-300' : 'text-slate-800 dark:text-slate-200'}`}>
                                            {story.story_title}
                                        </h4>
                                        <div className="flex items-center gap-2">
                                            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 uppercase border border-slate-200">
                                                {story.format}
                                            </span>
                                            {story.hero_kpi && (
                                                <span className="text-[10px] text-green-600 font-bold truncate max-w-[150px]">
                                                    {story.hero_kpi}
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleRemoveStory(story.story_id); }}
                                        className="text-slate-300 hover:text-red-500 absolute top-3 right-3 p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                                        title="Delete Story"
                                    >
                                        <TrashIcon className="h-4 w-4" />
                                    </button>
                                </div>
                                {selectedStoryId === story.story_id && (
                                    <div className="absolute right-3 bottom-3">
                                        <span className="text-[10px] font-bold text-blue-500 flex items-center bg-blue-50 dark:bg-blue-900/40 px-2 py-0.5 rounded-full">
                                            Editing <ChevronDownIcon className="w-3 h-3 ml-1 -rotate-90" />
                                        </span>
                                    </div>
                                )}
                            </div>
                        ))}
                        {stories.length === 0 && (
                            <div className="text-center py-8 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-dashed border-slate-200 dark:border-slate-700">
                                <p className="text-sm text-slate-400 font-medium">No saved strategies yet.</p>
                                <p className="text-xs text-slate-400 mt-1">Use the generator below.</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* 2. Wizard Input Panel */}
                <div className="bg-slate-50 dark:bg-slate-900/50 p-6 border border-slate-200 dark:border-slate-700 rounded-xl">
                    <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                        <SparklesIcon className="w-4 h-4" />
                        New Generator
                    </h2>
                    <div className="space-y-5">

                        {/* 1. Strategic Anchor */}
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                                1. Strategic Anchor
                            </label>
                            <select
                                value={selectedStrategyId}
                                onChange={(e) => setSelectedStrategyId(e.target.value)}
                                className="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="">Select Defined Strategy...</option>
                                {availableStrategies.map((opt, i) => (
                                    <option key={i} value={opt.value}>{opt.label}</option>
                                ))}
                            </select>
                            <p className="text-[10px] text-slate-500">Source: Competency Hub</p>
                        </div>

                        {/* 2. Proof Point */}
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                                2. Proof Point (Vector Formula)
                            </label>
                            <select
                                value={selectedexperienceKey}
                                onChange={(e) => setSelectedExperienceKey(e.target.value)}
                                className="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="">Select High-Fidelity Experience...</option>
                                {groupedExperiences.map((exp, i) => (
                                    <option key={i} value={exp.key}>
                                        {exp.label}
                                    </option>
                                ))}
                            </select>
                            <p className="text-[10px] text-slate-500">Source: Resume Formulas (Chroma)</p>
                        </div>

                        {/* 3. Framework */}
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
                                3. Framework
                            </label>
                            <div className="flex bg-white dark:bg-slate-700 rounded-lg border border-slate-300 dark:border-slate-600 p-1">
                                {FRAMEWORKS.map(f => (
                                    <button
                                        key={f}
                                        onClick={() => setSelectedFramework(f)}
                                        className={`flex-1 text-xs font-bold py-1.5 rounded-md transition-all ${selectedFramework === f
                                            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 shadow-sm'
                                            : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                                            }`}
                                    >
                                        {f}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={handleGenerate}
                            disabled={isGenerating || !selectedStrategyId || !selectedexperienceKey}
                            className="w-full flex items-center justify-center px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg shadow hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all font-bold text-sm mt-4"
                        >
                            {isGenerating ? <LoadingSpinner className="w-5 h-5 mr-2" /> : <SparklesIcon className="w-5 h-5 mr-2" />}
                            Synthesize Narrative
                        </button>
                    </div>
                </div>
            </div>

            {/* RIGHT PANEL: Review & Edit (The Tweak) */}
            <div className="lg:col-span-8">
                {selectedStory ? (
                    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md border border-slate-200 dark:border-slate-700 overflow-hidden">
                        {/* Header */}
                        <div className="border-b border-slate-200 dark:border-slate-700 p-6 bg-slate-50 dark:bg-slate-900/50 flex justify-between items-start">
                            <div>
                                <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">
                                    {selectedStory.story_title}
                                </h2>
                                <p className="text-sm text-slate-500">
                                    Framework: <span className="font-bold">{selectedStory.format}</span> •
                                    Strategy: <span className="font-bold">{availableStrategies.find(s => s.value === selectedStory.associated_strategy_id)?.label || selectedStory.associated_strategy_id}</span>
                                </p>
                            </div>
                            <div className="flex flex-col items-end">
                                <label className="text-xs font-bold uppercase text-slate-400 mb-1">Hero KPI</label>
                                <input
                                    type="text"
                                    className="text-right font-bold text-green-600 text-xl border-none bg-transparent focus:ring-0 p-0 placeholder-green-600/50"
                                    value={selectedStory.hero_kpi || ''}
                                    placeholder="+40% Efficiency"
                                    onChange={(e) => handleUpdateStory({ ...selectedStory, hero_kpi: e.target.value })}
                                />
                            </div>
                        </div>

                        <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Column 1: The Narrative Steps (Deep Context) */}
                            <div>
                                <h3 className="text-md font-bold text-slate-900 dark:text-white mb-4 flex items-center">
                                    <span className="w-6 h-6 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center text-xs mr-2">1</span>
                                    Core Narrative
                                </h3>
                                <div className="space-y-4">
                                    {renderSteps(selectedStory)}
                                </div>
                            </div>

                            {/* Column 2: The Signal (Thinned Bullets) */}
                            <div>
                                <h3 className="text-md font-bold text-slate-900 dark:text-white mb-4 flex items-center">
                                    <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs mr-2">2</span>
                                    The Signal (War Room View)
                                </h3>
                                <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-5 border border-slate-200 dark:border-slate-700">
                                    <p className="text-xs text-slate-400 mb-3 uppercase tracking-wider font-bold">Thinned Bullets (Max 7 words)</p>
                                    <ul className="space-y-3">
                                        {(selectedStory.thinned_bullets || []).map((bullet, idx) => (
                                            <li key={idx} className="flex bg-white dark:bg-slate-800 p-2 rounded shadow-sm border border-slate-100 dark:border-slate-700">
                                                <span className="text-blue-500 font-bold mr-2">•</span>
                                                <input
                                                    type="text"
                                                    className="w-full text-sm border-none focus:ring-0 p-0 bg-transparent text-slate-700 dark:text-slate-200 font-medium"
                                                    value={bullet}
                                                    onChange={(e) => {
                                                        const newBullets = [...(selectedStory.thinned_bullets || [])];
                                                        newBullets[idx] = e.target.value;
                                                        handleUpdateStory({ ...selectedStory, thinned_bullets: newBullets });
                                                    }}
                                                />
                                                <button
                                                    onClick={() => {
                                                        const newBullets = (selectedStory.thinned_bullets || []).filter((_, i) => i !== idx);
                                                        handleUpdateStory({ ...selectedStory, thinned_bullets: newBullets });
                                                    }}
                                                    className="ml-2 text-slate-300 hover:text-red-400"
                                                >
                                                    &times;
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                    <button
                                        onClick={() => handleUpdateStory({ ...selectedStory, thinned_bullets: [...(selectedStory.thinned_bullets || []), "New bullet point"] })}
                                        className="mt-3 text-xs font-semibold text-blue-600 flex items-center hover:underline"
                                    >
                                        <PlusCircleIcon className="w-4 h-4 mr-1" /> Add Signal Bullet
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-800/50 rounded-xl border-2 border-dashed border-slate-200 dark:border-slate-700 p-12 text-slate-400">
                        <SparklesIcon className="h-12 w-12 mb-4 opacity-50" />
                        <p className="font-semibold text-lg">Select or Generate a Story</p>
                        <p className="text-sm">Use the wizard on the left to cook up a new narrative.</p>
                    </div>
                )}
            </div>
        </div>
    );
};