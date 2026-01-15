import React, { useState, useEffect, useCallback } from 'react';
import { Competency, TrackCompetencies } from '../types';
import {
    getTrackCompetencies,
    saveTrackCompetencies,
    getTracksWithApplications
} from '../services/apiService';
import {
    LoadingSpinner,
    PlusCircleIcon,
    TrashIcon,
    CheckBadgeIcon,
    SparklesIcon,
    ChevronDownIcon,
    ChevronUpIcon,
    TagIcon,
    InformationCircleIcon,
    PresentationChartLineIcon,
    ChatBubbleBottomCenterTextIcon
} from './IconComponents';
import { useToast } from '../hooks/useToast';

interface CompetencyArchitectureIntakeProps {
    tracks: string[];
    selectedTrack: string;
    onSelectTrack: (track: string) => void;
    competencies: Competency[];
    onUpdateCompetencies: (competencies: Competency[]) => void;
    trackId: string | null;
    isLoading: boolean;
    onSave: () => Promise<void>;
    isSaving: boolean;
}

export const CompetencyArchitectureIntake = ({
    tracks,
    selectedTrack,
    onSelectTrack,
    competencies,
    onUpdateCompetencies,
    trackId,
    isLoading,
    onSave,
    isSaving
}: CompetencyArchitectureIntakeProps) => {
    const [expandedBlocks, setExpandedBlocks] = useState<Record<number, boolean>>({});


    const handleAddBlock = () => {
        const newIndex = competencies.length;
        onUpdateCompetencies([...competencies, {
            title: '',
            strategies: [{ strategy_name: '', best_practices: '', tools: [], kpis: [], talking_points: [] }]
        }]);
        setExpandedBlocks(prev => ({ ...prev, [newIndex]: true }));
    };

    const handleRemoveBlock = (index: number) => {
        onUpdateCompetencies(competencies.filter((_, i) => i !== index));
    };

    const handleUpdateBlock = (index: number, updates: Partial<Competency>) => {
        const newCompetencies = [...competencies];
        newCompetencies[index] = { ...newCompetencies[index], ...updates };
        onUpdateCompetencies(newCompetencies);
    };

    const handleAddStrategy = (compIndex: number) => {
        const newCompetencies = [...competencies];
        newCompetencies[compIndex].strategies.push({
            strategy_name: '',
            best_practices: '',
            tools: [],
            kpis: [],
            talking_points: []
        });
        onUpdateCompetencies(newCompetencies);
    };

    const handleRemoveStrategy = (compIndex: number, stratIndex: number) => {
        const newCompetencies = [...competencies];
        newCompetencies[compIndex].strategies = newCompetencies[compIndex].strategies.filter((_, i) => i !== stratIndex);
        onUpdateCompetencies(newCompetencies);
    };

    const handleUpdateStrategy = (compIndex: number, stratIndex: number, updates: Partial<any>) => {
        const newCompetencies = [...competencies];
        newCompetencies[compIndex].strategies[stratIndex] = {
            ...newCompetencies[compIndex].strategies[stratIndex],
            ...updates
        };
        onUpdateCompetencies(newCompetencies);
    };

    const toggleExpand = (index: number) => {
        setExpandedBlocks(prev => ({ ...prev, [index]: !prev[index] }));
    };



    const handleToolInput = (compIndex: number, stratIndex: number, e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const value = e.currentTarget.value.trim().replace(/,$/, '');
            const currentTools = competencies[compIndex].strategies[stratIndex].tools || [];
            if (value && !currentTools.includes(value)) {
                handleUpdateStrategy(compIndex, stratIndex, { tools: [...currentTools, value] });
                e.currentTarget.value = '';
            }
        }
    };

    const removeTool = (compIndex: number, stratIndex: number, toolIndex: number) => {
        const currentTools = competencies[compIndex].strategies[stratIndex].tools || [];
        const newTools = currentTools.filter((_, i) => i !== toolIndex);
        handleUpdateStrategy(compIndex, stratIndex, { tools: newTools });
    };

    const handleKPIInput = (compIndex: number, stratIndex: number, e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const value = e.currentTarget.value.trim().replace(/,$/, '');
            const currentKPIs = competencies[compIndex].strategies[stratIndex].kpis || [];
            if (value && !currentKPIs.includes(value)) {
                handleUpdateStrategy(compIndex, stratIndex, { kpis: [...currentKPIs, value] });
                e.currentTarget.value = '';
            }
        }
    };

    const removeKPI = (compIndex: number, stratIndex: number, kpiIndex: number) => {
        const currentKPIs = competencies[compIndex].strategies[stratIndex].kpis || [];
        const newKPIs = currentKPIs.filter((_, i) => i !== kpiIndex);
        handleUpdateStrategy(compIndex, stratIndex, { kpis: newKPIs });
    };

    const handleTalkingPointInput = (compIndex: number, stratIndex: number, e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const value = e.currentTarget.value.trim().replace(/,$/, '');
            const currentPoints = competencies[compIndex].strategies[stratIndex].talking_points || [];
            if (value && !currentPoints.includes(value)) {
                handleUpdateStrategy(compIndex, stratIndex, { talking_points: [...currentPoints, value] });
                e.currentTarget.value = '';
            }
        }
    };

    const removeTalkingPoint = (compIndex: number, stratIndex: number, pointIndex: number) => {
        const currentPoints = competencies[compIndex].strategies[stratIndex].talking_points || [];
        const newPoints = currentPoints.filter((_, i) => i !== pointIndex);
        handleUpdateStrategy(compIndex, stratIndex, { talking_points: newPoints });
    };

    return (
        <div className="space-y-8 max-w-5xl mx-auto animate-fade-in">
            {/* Context Header */}
            <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-10">
                    <SparklesIcon className="w-32 h-32" />
                </div>
                <div className="relative z-10">
                    <h2 className="text-2xl font-bold mb-2">Source of Truth: Competency Hub</h2>
                    <p className="text-blue-100 max-w-2xl">
                        Transition from "Cowboy" experiences to structured leadership pillars.
                        Document layered strategies, best practices, and tools for each competency.
                    </p>
                </div>
            </div>

            {/* Track Selector & Global Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white/50 dark:bg-slate-800/50 backdrop-blur-md p-4 rounded-xl border border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-3 w-full sm:w-auto">
                    <label htmlFor="track-select" className="text-sm font-semibold text-slate-700 dark:text-slate-300 whitespace-nowrap">
                        Select Job Track:
                    </label>
                    <select
                        id="track-select"
                        value={selectedTrack}
                        onChange={(e) => onSelectTrack(e.target.value)}
                        className="block w-full sm:w-64 rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                        <option value="" disabled>Select a track...</option>
                        {tracks.map(t => (
                            <option key={t} value={t}>{t}</option>
                        ))}
                    </select>
                </div>
                <div className="flex items-center gap-3 w-full sm:w-auto">
                    <button
                        onClick={handleAddBlock}
                        className="flex-1 sm:flex-none inline-flex items-center justify-center px-4 py-2 border border-blue-500 text-blue-600 hover:bg-blue-500 hover:text-white dark:hover:bg-blue-600 transition-all rounded-lg text-sm font-medium"
                    >
                        <PlusCircleIcon className="w-4 h-4 mr-2" />
                        Add Competency
                    </button>
                    <button
                        onClick={onSave}
                        disabled={isSaving || !selectedTrack}
                        className="flex-1 sm:flex-none inline-flex items-center justify-center px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/30 disabled:opacity-50 transition-all rounded-lg text-sm font-bold"
                    >
                        {isSaving ? <LoadingSpinner className="w-4 h-4 mr-2" /> : <CheckBadgeIcon className="w-4 h-4 mr-2" />}
                        Save Framework
                    </button>
                </div>
            </div>

            {/* Competency Blocks */}
            <div className="space-y-4">
                {isLoading ? (
                    <div className="flex justify-center items-center p-12 text-slate-500">
                        <LoadingSpinner className="w-8 h-8 mr-3" />
                        <span>Architecting view...</span>
                    </div>
                ) : competencies.length === 0 ? (
                    <div className="text-center py-20 bg-slate-50 dark:bg-slate-800/30 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700">
                        <InformationCircleIcon className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-slate-900 dark:text-slate-200">No competency framework defined for {selectedTrack || 'this track'}</h3>
                        <p className="text-slate-500 dark:text-slate-400 mt-2 max-w-sm mx-auto">
                            Start building your source of truth by adding your first competency block.
                        </p>
                        <button
                            onClick={handleAddBlock}
                            className="mt-6 inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold"
                        >
                            <PlusCircleIcon className="w-5 h-5 mr-2" />
                            Initialize Framework
                        </button>
                    </div>
                ) : (
                    competencies.map((comp, index) => (
                        <div
                            key={index}
                            className="group bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm transition-all hover:shadow-md overflow-hidden"
                        >
                            {/* Block Header */}
                            <div
                                className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                                onClick={() => toggleExpand(index)}
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-xs">
                                        {index + 1}
                                    </div>
                                    <h4 className="font-bold text-slate-900 dark:text-white">
                                        {comp.title || <span className="text-slate-400 italic font-normal">Untitled Competency</span>}
                                    </h4>
                                </div>
                                <div className="flex items-center gap-4">
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleRemoveBlock(index); }}
                                        className="p-1.5 text-slate-400 hover:text-red-500 transition-colors"
                                        title="Remove block"
                                    >
                                        <TrashIcon className="w-4 h-4" />
                                    </button>
                                    {expandedBlocks[index] ? <ChevronUpIcon className="w-5 h-5 text-slate-400" /> : <ChevronDownIcon className="w-5 h-5 text-slate-400" />}
                                </div>
                            </div>

                            {/* Block Content */}
                            {expandedBlocks[index] && (
                                <div className="p-6 pt-4 border-t border-slate-100 dark:border-slate-700 space-y-8 animate-slide-down">
                                    {/* Competency Title */}
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">
                                            Competency Title
                                        </label>
                                        <input
                                            type="text"
                                            value={comp.title}
                                            onChange={(e) => handleUpdateBlock(index, { title: e.target.value })}
                                            placeholder="e.g., Strategic Product Discovery"
                                            className="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm focus:ring-blue-500 focus:border-blue-500"
                                        />
                                    </div>

                                    {/* Strategies List */}
                                    <div className="space-y-6 pl-4 border-l-2 border-slate-100 dark:border-slate-700">
                                        <div className="flex items-center justify-between">
                                            <h5 className="text-sm font-bold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                                                <SparklesIcon className="w-4 h-4 text-blue-500" />
                                                Strategies ({comp.strategies.length})
                                            </h5>
                                            <button
                                                onClick={() => handleAddStrategy(index)}
                                                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
                                            >
                                                <PlusCircleIcon className="w-3.5 h-3.5" />
                                                Add Strategy
                                            </button>
                                        </div>

                                        <div className="space-y-8">
                                            {comp.strategies.map((strat, sIndex) => (
                                                <div key={sIndex} className="relative bg-slate-50/50 dark:bg-slate-700/20 p-5 rounded-xl border border-slate-100 dark:border-slate-700/50">
                                                    <button
                                                        onClick={() => handleRemoveStrategy(index, sIndex)}
                                                        className="absolute -top-2 -right-2 p-1.5 bg-white dark:bg-slate-800 rounded-full border border-slate-200 dark:border-slate-700 text-slate-400 hover:text-red-500 shadow-sm transition-colors"
                                                        title="Remove strategy"
                                                    >
                                                        <TrashIcon className="w-3.5 h-3.5" />
                                                    </button>

                                                    <div className="space-y-6">
                                                        {/* Strategy Name */}
                                                        <div className="space-y-2">
                                                            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                                                Strategy Name
                                                            </label>
                                                            <input
                                                                type="text"
                                                                value={strat.strategy_name}
                                                                onChange={(e) => handleUpdateStrategy(index, sIndex, { strategy_name: e.target.value })}
                                                                placeholder="e.g., User Interview Masterclass"
                                                                className="w-full bg-transparent border-0 border-b border-slate-200 dark:border-slate-700 rounded-0 px-0 py-1 text-sm font-semibold focus:ring-0 focus:border-blue-500 placeholder:text-slate-400"
                                                            />
                                                        </div>

                                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                            {/* Best Practices */}
                                                            <div className="space-y-2">
                                                                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                                                    Best Practices
                                                                </label>
                                                                <textarea
                                                                    rows={8}
                                                                    value={strat.best_practices}
                                                                    onChange={(e) => handleUpdateStrategy(index, sIndex, { best_practices: e.target.value })}
                                                                    placeholder="Document best practices..."
                                                                    className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 text-sm focus:ring-blue-500 focus:border-blue-500"
                                                                />
                                                            </div>

                                                            {/* Tools & KPIs */}
                                                            <div className="space-y-8">
                                                                {/* Associated Tools */}
                                                                <div className="space-y-2">
                                                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1">
                                                                        <TagIcon className="w-3 h-3" /> Tools
                                                                    </label>
                                                                    <div className="space-y-3">
                                                                        <input
                                                                            type="text"
                                                                            onKeyDown={(e) => handleToolInput(index, sIndex, e)}
                                                                            placeholder="Add tools..."
                                                                            className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 text-sm focus:ring-blue-500 focus:border-blue-500"
                                                                        />
                                                                        <div className="flex flex-wrap gap-1.5">
                                                                            {strat.tools.map((tool: string, ti: number) => (
                                                                                <span
                                                                                    key={ti}
                                                                                    className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-white dark:bg-slate-800 text-[11px] font-medium text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                                                                                >
                                                                                    {tool}
                                                                                    <button
                                                                                        onClick={() => removeTool(index, sIndex, ti)}
                                                                                        className="text-slate-400 hover:text-red-500 transition-colors"
                                                                                    >
                                                                                        &times;
                                                                                    </button>
                                                                                </span>
                                                                            ))}
                                                                        </div>
                                                                    </div>
                                                                </div>

                                                                {/* KPIs */}
                                                                <div className="space-y-2">
                                                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1">
                                                                        <PresentationChartLineIcon className="w-3 h-3" /> Success Metrics (KPIs)
                                                                    </label>
                                                                    <div className="space-y-3">
                                                                        <input
                                                                            type="text"
                                                                            onKeyDown={(e) => handleKPIInput(index, sIndex, e)}
                                                                            placeholder="Add KPIs..."
                                                                            className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 text-sm focus:ring-blue-500 focus:border-blue-500"
                                                                        />
                                                                        <div className="flex flex-wrap gap-1.5">
                                                                            {(strat.kpis || []).map((kpi: string, ki: number) => (
                                                                                <span
                                                                                    key={ki}
                                                                                    className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-blue-50 dark:bg-blue-900/20 text-[11px] font-medium text-blue-600 dark:text-blue-300 border border-blue-100 dark:border-blue-800/50"
                                                                                >
                                                                                    {kpi}
                                                                                    <button
                                                                                        onClick={() => removeKPI(index, sIndex, ki)}
                                                                                        className="text-blue-400 hover:text-red-500 transition-colors"
                                                                                    >
                                                                                        &times;
                                                                                    </button>
                                                                                </span>
                                                                            ))}
                                                                        </div>
                                                                    </div>
                                                                </div>

                                                                {/* Talking Points */}
                                                                <div className="space-y-2">
                                                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1">
                                                                        <ChatBubbleBottomCenterTextIcon className="w-3 h-3" /> Key Talking Points (Focus Area)
                                                                    </label>
                                                                    <div className="space-y-3">
                                                                        <input
                                                                            type="text"
                                                                            onKeyDown={(e) => handleTalkingPointInput(index, sIndex, e)}
                                                                            placeholder="Add key talking points..."
                                                                            className="w-full rounded-lg border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 text-sm focus:ring-blue-500 focus:border-blue-500"
                                                                        />
                                                                        <div className="flex flex-wrap gap-1.5">
                                                                            {(strat.talking_points || []).map((point: string, pi: number) => (
                                                                                <span
                                                                                    key={pi}
                                                                                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 text-[12px] font-semibold text-indigo-700 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-800/50 shadow-sm"
                                                                                >
                                                                                    {point}
                                                                                    <button
                                                                                        onClick={() => removeTalkingPoint(index, sIndex, pi)}
                                                                                        className="text-indigo-400 hover:text-red-500 transition-colors"
                                                                                    >
                                                                                        &times;
                                                                                    </button>
                                                                                </span>
                                                                            ))}
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Bottom Add Link */}
            {!isLoading && competencies.length > 0 && (
                <div className="flex justify-center pb-8">
                    <button
                        onClick={handleAddBlock}
                        className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-blue-600 transition-colors"
                    >
                        <PlusCircleIcon className="w-5 h-5" />
                        Add another competency block
                    </button>
                </div>
            )}
        </div>
    );
};

