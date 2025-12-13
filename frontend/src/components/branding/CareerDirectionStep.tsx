import React, { useState } from 'react';
import { StrategicNarrative, Prompt } from '../../types';
import { StrategyAiAssistant } from '../StrategyAiAssistant';
import * as geminiService from '../../services/geminiService';
import { SparklesIcon } from '../shared/ui/IconComponents';

interface CareerDirectionStepProps {
    profile: Partial<StrategicNarrative>;
    onProfileChange: (field: keyof StrategicNarrative, value: any) => void;
    prompts: Prompt[];
}

const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";
const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
const textareaClass = `${inputClass} font-sans`;

export const CareerDirectionStep = ({ profile, onProfileChange, prompts }: CareerDirectionStepProps) => {
    const [editingField, setEditingField] = useState<'mission_alignment' | 'long_term_legacy' | null>(null);
    const [aiNotes, setAiNotes] = useState('');
    const [aiResult, setAiResult] = useState<any | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);

    const handleGenerate = async (notes: string) => {
        setIsGenerating(true);
        setAiResult(null);
        try {
            if (editingField === 'mission_alignment') {
                const prompt = prompts.find(p => p.id === 'DEFINE_MISSION_ALIGNMENT');
                if (!prompt) throw new Error("DEFINE_MISSION_ALIGNMENT prompt not found.");
                const result = await geminiService.defineMissionAlignment({ USER_NOTES: notes }, prompt.content);
                setAiResult(result);
            } else if (editingField === 'long_term_legacy') {
                const prompt = prompts.find(p => p.id === 'DEFINE_LONG_TERM_LEGACY');
                if (!prompt) throw new Error("DEFINE_LONG_TERM_LEGACY prompt not found.");
                const result = await geminiService.defineLongTermLegacy({ USER_NOTES: notes }, prompt.content);
                setAiResult(result);
            }
        } catch (error) {
            console.error("AI generation failed", error);
        } finally {
            setIsGenerating(false);
        }
    };

    const useAiResult = (result: any) => {
        if (result.suggestion && editingField) {
            onProfileChange(editingField, result.suggestion);
        }
        setEditingField(null);
        setAiResult(null);
        setAiNotes('');
    };
    
    const openAssistant = (field: 'mission_alignment' | 'long_term_legacy') => {
        if (editingField === field) {
            setEditingField(null); // Toggle off if already open
        } else {
            setEditingField(field);
            setAiNotes('');
            setAiResult(null);
        }
    };
    
    const renderAssistant = (field: 'mission_alignment' | 'long_term_legacy') => {
        if (editingField !== field) return null;

        const isMission = field === 'mission_alignment';
        const title = isMission ? "Mission Alignment AI" : "Long-term Legacy AI";
        const starterPrompt = isMission 
            ? "Help me articulate what kind of work energizes me..." 
            : "Help me figure out what I want to be known for...";

        return (
             <div className="pt-2">
                <StrategyAiAssistant
                    title={title}
                    starterPrompt={starterPrompt}
                    userNotes={aiNotes}
                    setUserNotes={setAiNotes}
                    onGenerate={handleGenerate}
                    generationResult={aiResult}
                    onUseResult={useAiResult}
                    isLoading={isGenerating}
                />
             </div>
        )
    }


    return (
        <div className="space-y-6 animate-fade-in">
            <p className="text-slate-600 dark:text-slate-400">
                Define where you're going and why. This will help us align your entire job search — resume, networking, and positioning — around your deeper goals.
            </p>
            <div className="space-y-4">
                <div>
                    <label htmlFor="desired_title" className={labelClass}>What is your target job title? *</label>
                    <input
                        type="text"
                        id="desired_title"
                        value={profile.desired_title || ''}
                        onChange={e => onProfileChange('desired_title', e.target.value)}
                        className={inputClass}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="desired_industry" className={labelClass}>Target industry (e.g., FinTech, HealthTech)</label>
                    <input
                        type="text"
                        id="desired_industry"
                        value={profile.desired_industry || ''}
                        onChange={e => onProfileChange('desired_industry', e.target.value)}
                        className={inputClass}
                    />
                </div>
                <div>
                    <label htmlFor="desired_company_stage" className={labelClass}>Ideal company stage</label>
                    <select
                        id="desired_company_stage"
                        value={profile.desired_company_stage || ''}
                        onChange={e => onProfileChange('desired_company_stage', e.target.value as 'early-stage' | 'growth' | 'enterprise')}
                        className={inputClass}
                    >
                        <option value="">Any</option>
                        <option value="early-stage">Early-stage (Seed, Series A/B)</option>
                        <option value="growth">Growth (Series C-E, high growth)</option>
                        <option value="enterprise">Enterprise (Public, large scale)</option>
                    </select>
                </div>
                <div>
                    <div className="flex justify-between items-center">
                        <label htmlFor="mission_alignment" className={labelClass}>What kind of work would energize you long-term?</label>
                         <button type="button" onClick={() => openAssistant('mission_alignment')} className="p-1 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200" title="Get AI help">
                            <SparklesIcon className="w-5 h-5" />
                        </button>
                    </div>
                    <textarea
                        id="mission_alignment"
                        rows={3}
                        value={profile.mission_alignment || ''}
                        onChange={e => onProfileChange('mission_alignment', e.target.value)}
                        className={textareaClass}
                    />
                    {renderAssistant('mission_alignment')}
                </div>
                <div>
                    <div className="flex justify-between items-center">
                        <label htmlFor="long_term_legacy" className={labelClass}>What do you want to be remembered for in your next role?</label>
                        <button type="button" onClick={() => openAssistant('long_term_legacy')} className="p-1 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200" title="Get AI help">
                            <SparklesIcon className="w-5 h-5" />
                        </button>
                    </div>
                    <textarea
                        id="long_term_legacy"
                        rows={3}
                        value={profile.long_term_legacy || ''}
                        onChange={e => onProfileChange('long_term_legacy', e.target.value)}
                        className={textareaClass}
                    />
                    {renderAssistant('long_term_legacy')}
                </div>
            </div>
        </div>
    );
};