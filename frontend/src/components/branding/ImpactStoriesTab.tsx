import React, { useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { StrategicNarrative, StrategicNarrativePayload, Prompt, ImpactStory } from '../../types';
import * as geminiService from '../../services/geminiService';
import { LoadingSpinner, PlusCircleIcon, SparklesIcon, TrashIcon } from '../shared/ui/IconComponents';

interface ImpactStoriesTabProps {
    activeNarrative: StrategicNarrative;
    onSaveNarrative: (payload: StrategicNarrativePayload, narrativeId: string) => Promise<void>;
    prompts: Prompt[];
}

const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";
const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
const textareaClass = `${inputClass} font-sans`;

const storyBodyToString = (body: ImpactStory['story_body']): string => {
    if (typeof body === 'string') return body; // Should not happen based on type, but for safety
    if (!body) return '';
    return Object.entries(body)
        .map(([key, value]) => `**${key.charAt(0).toUpperCase() + key.slice(1)}:** ${value || ''}`)
        .join('\n\n');
};

const stringToStoryBody = (text: string): ImpactStory['story_body'] => {
    const body: { [key: string]: string } = {};
    const parts = text.split(/\n\s*\n/);
    parts.forEach(part => {
        const match = part.match(/^\*\*(.*?):\*\*\s*(.*)/s);
        if (match) {
            const key = match[1].toLowerCase().replace(/ /g, '_');
            body[key] = match[2];
        }
    });
    return body;
};

const speakerNotesToString = (notes: { [key: string]: string } | undefined): string => {
    if (!notes || typeof notes !== 'object') return '';
    return Object.entries(notes)
        .map(([key, value]) => `${key}: ${value || ''}`)
        .join('\n');
};

const stringToSpeakerNotes = (text: string): { [key: string]: string } => {
    const notes: { [key: string]: string } = {};
    if (!text) return notes;
    text.split('\n').forEach(line => {
        const separatorIndex = line.indexOf(':');
        if (separatorIndex > -1) {
            const key = line.substring(0, separatorIndex).trim();
            const value = line.substring(separatorIndex + 1).trim();
            if (key) {
                notes[key] = value;
            }
        }
    });
    return notes;
};

const StoryEditor = ({
    story,
    onStoryChange,
    onRemove,
    prompts,
}: {
    story: ImpactStory;
    onStoryChange: (updatedStory: ImpactStory) => void;
    onRemove: () => void;
    prompts: Prompt[];
}) => {
    const [isGenerating, setIsGenerating] = useState(false);

    const handleGenerate = async () => {
        setIsGenerating(true);
        try {
            const prompt = prompts.find(p => p.id === 'GENERATE_IMPACT_STORY');
            if (!prompt) throw new Error("GENERATE_IMPACT_STORY prompt not found.");
            const result = await geminiService.generateImpactStory({
                STORY_DRAFT: storyBodyToString(story.story_body),
                STORY_METRICS: "" // Assuming metrics are in the body for this context
            }, prompt.content);
            onStoryChange({
                ...story,
                story_title: result.impact_story_title,
                story_body: stringToStoryBody(result.impact_story_body)
            });
        } catch (error) {
            console.error("AI generation failed", error);
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 space-y-3 relative">
            <button
                type="button"
                onClick={onRemove}
                className="absolute top-2 right-2 p-1 text-slate-400 hover:text-red-500 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700"
            >
                <TrashIcon className="h-5 w-5" />
            </button>

            <div>
                <label htmlFor={`title-${story.story_id}`} className={labelClass}>Title</label>
                <input
                    id={`title-${story.story_id}`}
                    type="text"
                    value={story.story_title}
                    onChange={e => onStoryChange({ ...story, story_title: e.target.value })}
                    className={inputClass}
                />
            </div>
            <div>
                <label htmlFor={`body-${story.story_id}`} className={labelClass}>Body (STAR Method)</label>
                <textarea
                    id={`body-${story.story_id}`}
                    rows={6}
                    value={storyBodyToString(story.story_body)}
                    onChange={e => onStoryChange({ ...story, story_body: stringToStoryBody(e.target.value) })}
                    className={textareaClass}
                />
            </div>
             <div>
                <label htmlFor={`notes-${story.story_id}`} className={labelClass}>Speaker Notes</label>
                <textarea
                    id={`notes-${story.story_id}`}
                    rows={3}
                    value={speakerNotesToString(story.speaker_notes)}
                    onChange={e => onStoryChange({ ...story, speaker_notes: stringToSpeakerNotes(e.target.value) })}
                    className={`${textareaClass} font-mono text-xs`}
                    placeholder="Concise bullet points for the interview co-pilot..."
                />
            </div>
            <div className="flex justify-end">
                <button
                    type="button"
                    onClick={handleGenerate}
                    disabled={isGenerating}
                    className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                    {isGenerating ? <LoadingSpinner /> : <SparklesIcon className="h-4 w-4" />}
                    Polish with AI
                </button>
            </div>
        </div>
    );
};

export const ImpactStoriesTab = ({ activeNarrative, onSaveNarrative, prompts }: ImpactStoriesTabProps) => {
    const [stories, setStories] = useState<ImpactStory[]>(activeNarrative.impact_stories || []);

    const handleSave = () => {
        onSaveNarrative({ impact_stories: stories }, activeNarrative.narrative_id);
    };

    const handleStoryChange = (index: number, updatedStory: ImpactStory) => {
        const newStories = [...stories];
        newStories[index] = updatedStory;
        setStories(newStories);
    };

    const handleAddStory = () => {
        const newStory: ImpactStory = {
            story_id: uuidv4(),
            story_title: 'New Impact Story',
            format: 'STAR',
            story_body: { situation: '', task: '', action: '', result: '' },
            target_questions: [],
            speaker_notes: {}
        };
        setStories([...stories, newStory]);
    };

    const handleRemoveStory = (index: number) => {
        const newStories = stories.filter((_, i) => i !== index);
        setStories(newStories);
    };

    return (
        <div className="space-y-6">
            <p className="text-slate-600 dark:text-slate-400">
                Build your library of core impact stories. These are the powerful, reusable narratives that prove your value and will be used by the AI Co-pilot during interview prep.
            </p>

            <div className="space-y-4">
                {stories.map((story, index) => (
                    <StoryEditor
                        key={story.story_id}
                        story={story}
                        onStoryChange={(updated) => handleStoryChange(index, updated)}
                        onRemove={() => handleRemoveStory(index)}
                        prompts={prompts}
                    />
                ))}
            </div>

            <div className="flex justify-between items-center pt-6 border-t border-slate-200 dark:border-slate-700">
                <button
                    type="button"
                    onClick={handleAddStory}
                    className="inline-flex items-center gap-x-1.5 rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600"
                >
                    <PlusCircleIcon className="h-5 w-5" />
                    Add Story
                </button>
                <button
                    type="button"
                    onClick={handleSave}
                    className="rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-700"
                >
                    Save Stories
                </button>
            </div>
        </div>
    );
};