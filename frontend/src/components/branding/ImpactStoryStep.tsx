import React, { useState } from 'react';
import { StrategicNarrative, Prompt } from '../../types';
import { StrategyAiAssistant } from '../StrategyAiAssistant';
import * as geminiService from '../../services/geminiService';
import { TagInput } from '../shared/ui/TagInput';
import { MarkdownPreview } from '../shared/ui/MarkdownPreview';
import { SparklesIcon } from '../shared/ui/IconComponents';

interface ImpactStoryStepProps {
    profile: Partial<StrategicNarrative>;
    onProfileChange: (field: keyof StrategicNarrative, value: any) => void;
    prompts: Prompt[];
}

const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";
const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
const textareaClass = `${inputClass} font-sans`;

export const ImpactStoryStep = ({ profile, onProfileChange, prompts }: ImpactStoryStepProps) => {
    const [showAi, setShowAi] = useState(false);
    const [aiResult, setAiResult] = useState<{ impact_story_title: string; impact_story_body: string; } | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [storyTab, setStoryTab] = useState<'edit' | 'preview'>('edit');
    
    const tabClass = (isActive: boolean) =>
        `px-3 py-1.5 text-sm font-medium rounded-md transition-colors ` +
        (isActive
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
            : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700/50');

    const handleGenerate = async () => {
        setIsGenerating(true);
        setAiResult(null);
        try {
            const prompt = prompts.find(p => p.id === 'GENERATE_IMPACT_STORY');
            if (!prompt) throw new Error("GENERATE_IMPACT_STORY prompt not found.");
            const result = await geminiService.generateImpactStory({
                STORY_DRAFT: profile.impact_story_body,
                STORY_METRICS: (profile.representative_metrics || []).join(', ')
            }, prompt.content);
            setAiResult(result);
        } catch (error) {
            console.error("AI generation failed", error);
        } finally {
            setIsGenerating(false);
        }
    };

    const useAiResult = (result: { impact_story_title: string; impact_story_body: string; } | null) => {
        if (!result) return;
        if (result.impact_story_title) onProfileChange('impact_story_title', result.impact_story_title);
        if (result.impact_story_body) onProfileChange('impact_story_body', result.impact_story_body);
        setShowAi(false);
    };

    return (
        <div className="space-y-6 animate-fade-in">
            <p className="text-slate-600 dark:text-slate-400">
                One story can define your brand. Share a moment where your contribution made a major difference — product impact, team transformation, or strategic success. We'll help you polish it and reuse it throughout your search.
            </p>
            <div className="space-y-4">
                <div>
                    <label htmlFor="impact_story_title" className={labelClass}>Impact Story Title</label>
                    <input
                        type="text"
                        id="impact_story_title"
                        value={profile.impact_story_title || ''}
                        onChange={e => onProfileChange('impact_story_title', e.target.value)}
                        className={inputClass}
                        placeholder="e.g., Turned around a failing launch in 6 weeks."
                    />
                </div>
                 <div>
                    <TagInput
                        label="Representative Metrics"
                        tags={profile.representative_metrics || []}
                        onTagsChange={(tags) => onProfileChange('representative_metrics', tags)}
                        placeholder="e.g., +200% ARR, cut churn 40%"
                    />
                </div>
                <div>
                    <div className="flex justify-between items-center mb-1">
                        <label htmlFor="impact_story_body" className={labelClass}>Impact Story Body (Markdown supported)</label>
                        <div className="flex items-center space-x-2">
                             <div className="flex items-center space-x-1 rounded-lg bg-slate-100 dark:bg-slate-800 p-1">
                                <button type="button" onClick={() => setStoryTab('edit')} className={tabClass(storyTab === 'edit')}>Edit</button>
                                <button type="button" onClick={() => setStoryTab('preview')} className={tabClass(storyTab === 'preview')}>Preview</button>
                            </div>
                            <button type="button" onClick={() => setShowAi(!showAi)} className="p-1 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200" title="Help me polish this story">
                                <SparklesIcon className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                    {storyTab === 'edit' ? (
                        <textarea
                            id="impact_story_body"
                            rows={8}
                            value={profile.impact_story_body || ''}
                            onChange={e => onProfileChange('impact_story_body', e.target.value)}
                            className={textareaClass}
                            placeholder="Use the STAR method: Situation, Task, Action, Result."
                        />
                    ) : (
                        <div className="w-full p-3 h-[210px] overflow-y-auto bg-slate-50 dark:bg-slate-700/50 border border-slate-300 dark:border-slate-600 rounded-lg">
                           <MarkdownPreview markdown={profile.impact_story_body || ''} />
                        </div>
                    )}
                </div>

                {showAi && (
                    <div className="p-4 bg-slate-100 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 mt-4 space-y-3">
                        <h4 className="text-md font-semibold text-slate-800 dark:text-slate-200">Story Polishing AI</h4>
                            <button
                            type="button"
                            onClick={handleGenerate}
                            disabled={isGenerating || !profile.impact_story_body}
                            className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400"
                        >
                            {isGenerating ? <div className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" /> : null}
                            Polish My Story
                        </button>
                        {aiResult && (
                                <div className="p-3 bg-white dark:bg-slate-700/50 rounded-md border border-slate-300 dark:border-slate-600 space-y-3">
                                <p className="text-sm font-semibold">AI Suggestion:</p>
                                <div className="text-xs whitespace-pre-wrap font-mono bg-slate-50 dark:bg-slate-900/50 p-2 rounded">
                                    <MarkdownPreview markdown={`**${(aiResult as any).impact_story_title}**\n\n${(aiResult as any).impact_story_body}`} />
                                </div>
                                <button
                                    type="button"
                                    onClick={() => useAiResult(aiResult)}
                                    className="px-3 py-1 text-xs font-semibold rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700"
                                >
                                    Use This Version
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};