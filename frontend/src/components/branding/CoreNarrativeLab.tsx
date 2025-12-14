import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { StrategicNarrative, StrategicNarrativePayload, Prompt, ImpactStory, StorytellingFormat, StarBody, ScopeBody, WinsBody, SpotlightBody } from '../../types';
import * as geminiService from '../../services/geminiService';
import { LoadingSpinner, PlusCircleIcon, SparklesIcon, TrashIcon } from '../shared/ui/IconComponents';

interface CoreNarrativeLabProps {
    activeNarrative: StrategicNarrative;
    onSaveNarrative: (payload: StrategicNarrativePayload, narrativeId: string) => Promise<void>;
    prompts: Prompt[];
}

const STORY_FORMATS: {
    [key in StorytellingFormat]: {
        name: string;
        description: string;
        fields: { id: keyof (StarBody & ScopeBody & WinsBody & SpotlightBody); label: string; placeholder: string; rows: number }[];
    }
} = {
    STAR: {
        name: 'STAR',
        description: 'Classic, reliable, good for mid-level behavioral rounds.',
        fields: [
            { id: 'situation', label: 'Situation', placeholder: 'Set the scene. What was the context?', rows: 2 },
            { id: 'task', label: 'Task', placeholder: 'What was your specific goal or challenge?', rows: 2 },
            { id: 'action', label: 'Action', placeholder: 'What specific steps did YOU take?', rows: 4 },
            { id: 'result', label: 'Result', placeholder: 'What was the quantifiable outcome?', rows: 2 },
        ],
    },
    SCOPE: {
        name: 'SCOPE',
        description: 'Strategic stories with complexity and evolution.',
        fields: [
            { id: 'situation', label: 'Situation', placeholder: 'Set the scene. What was the business context and your role?', rows: 2 },
            { id: 'complication', label: 'Complication', placeholder: 'What unexpected challenge, problem, or change occurred?', rows: 2 },
            { id: 'opportunity', label: 'Opportunity', placeholder: 'What insight or opportunity did this complication reveal?', rows: 2 },
            { id: 'product_thinking', label: 'Product Thinking', placeholder: 'Describe your thought process. What frameworks, data, or principles did you use?', rows: 3 },
            { id: 'end_result', label: 'End Result', placeholder: 'What was the final, quantifiable outcome of your new approach?', rows: 2 },
        ],
    },
    WINS: {
        name: 'WINS',
        description: 'Tight stories that emphasize insight and adaptability.',
        fields: [
            { id: 'situation', label: 'Situation', placeholder: 'Briefly set the scene. What was the context?', rows: 2 },
            { id: 'what_i_did', label: 'What I Did', placeholder: 'Describe the specific actions you took.', rows: 4 },
            { id: 'impact', label: 'Impact', placeholder: 'What was the quantifiable result or outcome of your actions?', rows: 2 },
            { id: 'nuance', label: 'Nuance', placeholder: 'What was the subtle, non-obvious insight or learning?', rows: 3 },
        ],
    },
    SPOTLIGHT: {
        name: 'SPOTLIGHT',
        description: 'PM stories that center product judgment and trade-offs.',
        fields: [
            { id: 'situation', label: 'Situation', placeholder: 'Set the scene. What was the context?', rows: 2 },
            { id: 'positive_moment_or_goal', label: 'Positive Moment (Goal)', placeholder: 'What was the initial goal or positive event?', rows: 2 },
            { id: 'observation_opportunity', label: 'Observation/Opportunity', placeholder: 'What did you notice that others might have missed?', rows: 2 },
            { id: 'task_action', label: 'Task/Action', placeholder: 'What specific steps did you take based on your observation?', rows: 3 },
            { id: 'learnings_leverage', label: 'Learnings/Leverage', placeholder: 'What did you learn, and how did you apply it?', rows: 2 },
            { id: 'impact_results', label: 'Impact/Results', placeholder: 'What was the final quantifiable outcome?', rows: 2 },
            { id: 'growth_grit', label: 'Growth/Grit', placeholder: 'How did this experience shape your growth or demonstrate resilience?', rows: 2 },
            { id: 'highlights_key_trait', label: 'Highlights (Key Trait)', placeholder: "What core personal trait does this story highlight (e.g., 'curiosity', 'bias for action')?", rows: 1 },
            { id: 'takeaway_tie_in', label: 'Takeaway/Tie-in', placeholder: 'What is the key takeaway for the interviewer?', rows: 2 },
        ],
    },
};

const getInitialBodyForFormat = (format: StorytellingFormat): ImpactStory['story_body'] => {
    const fields = STORY_FORMATS[format].fields;
    const body: { [key: string]: string } = {};
    fields.forEach(field => {
        body[field.id as string] = '';
    });
    return body;
};

const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";
const textareaClass = `mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm font-sans`;

export const CoreNarrativeLab = ({ activeNarrative, onSaveNarrative, prompts }: CoreNarrativeLabProps) => {
    const [stories, setStories] = useState<ImpactStory[]>([]);
    const [selectedStoryId, setSelectedStoryId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isGenerating, setIsGenerating] = useState<string | null>(null); // e.g., 'storyId-fieldName' or 'storyId-all-notes'
    
    const [isPracticeModalOpen, setIsPracticeModalOpen] = useState(false);
    const [practiceStoryNotes, setPracticeStoryNotes] = useState<{ [key: string]: string }>({});
    const [isSavingNotes, setIsSavingNotes] = useState(false);

    useEffect(() => {
        const initialStories = activeNarrative.impact_stories?.map(s => ({
            ...s,
            story_id: s.story_id || uuidv4(),
            format: s.format || 'STAR',
            speaker_notes: s.speaker_notes || {},
            story_body: (typeof s.story_body === 'string' || !s.story_body)
                ? getInitialBodyForFormat(s.format || 'STAR')
                : s.story_body,
        })) || [];

        setStories(initialStories);
        
        if (!selectedStoryId) {
            setSelectedStoryId(initialStories[0]?.story_id || null);
        }
    }, [activeNarrative.impact_stories]);


    const handleSave = async () => {
        setIsLoading(true);
        try {
            await onSaveNarrative({ impact_stories: stories }, activeNarrative.narrative_id);
        } catch (e) { console.error(e); } finally { setIsLoading(false); }
    };

    const handleStoryChange = (updatedStory: ImpactStory) => {
        setStories(prev => prev.map(s => s.story_id === updatedStory.story_id ? updatedStory : s));
    };

    const handleFormatChange = (story: ImpactStory, newFormat: StorytellingFormat) => {
        const newBody = getInitialBodyForFormat(newFormat);
        // Attempt to map common fields
        if ('situation' in story.story_body && typeof (story.story_body as any).situation === 'string') {
            if ('situation' in newBody) {
                (newBody as any).situation = (story.story_body as any).situation;
            }
        }
        handleStoryChange({ ...story, format: newFormat, story_body: newBody, speaker_notes: {} });
    };

    const handleAddStory = () => {
        const newStory: ImpactStory = {
            story_id: uuidv4(),
            story_title: 'New Core Story',
            format: 'STAR',
            story_body: getInitialBodyForFormat('STAR'),
            target_questions: [],
            speaker_notes: {}
        };
        setStories([...stories, newStory]);
        setSelectedStoryId(newStory.story_id);
    };

    const handleRemoveStory = (storyIdToRemove: string) => {
        const originalIndex = stories.findIndex(s => s.story_id === storyIdToRemove);
        const newStories = stories.filter(s => s.story_id !== storyIdToRemove);
        setStories(newStories);
        if (selectedStoryId === storyIdToRemove) {
            setSelectedStoryId(newStories[Math.min(originalIndex, newStories.length - 1)]?.story_id || null);
        }
    };
    
    const handleAIPolishPart = async (story: ImpactStory, fieldName: string) => {
        const generationKey = `${story.story_id}-${fieldName}`;
        setIsGenerating(generationKey);
        try {
            const prompt = prompts.find(p => p.id === 'POLISH_IMPACT_STORY_PART');
            if (!prompt) throw new Error("POLISH_IMPACT_STORY_PART prompt not found.");
            
            const result = await geminiService.polishImpactStoryPart({
                STORY_FORMAT: story.format,
                STORY_PART: fieldName,
                DRAFT_TEXT: (story.story_body as any)[fieldName],
                FULL_STORY_CONTEXT: JSON.stringify(story.story_body)
            }, prompt.content);
            
            handleStoryChange({ ...story, story_body: { ...story.story_body, [fieldName]: result } });
        } catch (error) { console.error("AI polish failed", error); } finally { setIsGenerating(null); }
    };

    const handleGenerateAllSpeakerNotes = async () => {
        const story = stories.find(s => s.story_id === selectedStoryId);
        if (!story) return;

        const generationKey = `${story.story_id}-all-notes`;
        setIsGenerating(generationKey);
        try {
            const prompt = prompts.find(p => p.id === 'GENERATE_STRUCTURED_SPEAKER_NOTES');
            if (!prompt) throw new Error("GENERATE_STRUCTURED_SPEAKER_NOTES prompt not found.");
            
            const result = await geminiService.generateStructuredSpeakerNotes({
                STORY_FORMAT: story.format,
                FULL_STORY_JSON: JSON.stringify(story.story_body)
            }, prompt.content);
            setPracticeStoryNotes(result);
            handleStoryChange({ ...story, speaker_notes: result });
        } catch (error) {
            console.error("AI speaker notes generation failed", error);
        } finally {
            setIsGenerating(null);
        }
    };
    
    const handleSaveNotesFromPractice = async () => {
        const story = stories.find(s => s.story_id === selectedStoryId);
        if (!story) return;
        setIsSavingNotes(true);
        try {
            const newStories = stories.map(s =>
                s.story_id === selectedStoryId
                    ? { ...s, speaker_notes: practiceStoryNotes }
                    : s
            );
            setStories(newStories);
            await onSaveNarrative({ impact_stories: newStories }, activeNarrative.narrative_id);
            setIsPracticeModalOpen(false);
        } catch(e) {
            console.error("Failed to save notes:", e);
        } finally {
            setIsSavingNotes(false);
        }
    };

    
    const selectedStory = stories.find(s => s.story_id === selectedStoryId);
    const storyFormatData = selectedStory ? STORY_FORMATS[selectedStory.format] : null;

    return (
        <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-1">
                    <div className="flex justify-between items-center mb-2">
                        <h3 className="font-semibold">Core Story Library</h3>
                        <button onClick={handleAddStory} className="text-sm font-semibold text-blue-600 hover:underline">Add New</button>
                    </div>
                    <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-2">
                        {stories.map(story => (
                            <div key={story.story_id} onClick={() => setSelectedStoryId(story.story_id)}
                                className={`p-3 rounded-md cursor-pointer border ${selectedStoryId === story.story_id ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700' : 'bg-white dark:bg-slate-800/80 hover:bg-slate-50 dark:hover:bg-slate-700/50 border-slate-200 dark:border-slate-700'}`}>
                                <div className="flex justify-between items-center">
                                    <p className="font-semibold text-sm text-slate-800 dark:text-slate-200 truncate">{story.story_title}</p>
                                    <span className="text-xs font-mono bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 px-1.5 py-0.5 rounded">{story.format}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="md:col-span-2">
                    {selectedStory && storyFormatData ? (
                        <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 space-y-4">
                            <div className="flex justify-between items-center">
                                <h3 className="font-semibold text-lg">Story Editor</h3>
                                <div className="flex items-center gap-x-2">
                                    <button type="button" onClick={() => {
                                        setPracticeStoryNotes(selectedStory.speaker_notes || {});
                                        setIsPracticeModalOpen(true);
                                    }} className="text-sm font-semibold text-blue-600 hover:underline">Practice Story</button>
                                    <button type="button" onClick={() => handleRemoveStory(selectedStory.story_id)} className="p-1 text-slate-400 hover:text-red-500"><TrashIcon className="h-5 w-5" /></button>
                                </div>
                            </div>
                            <div>
                                <label htmlFor={`title-${selectedStory.story_id}`} className={labelClass}>Title</label>
                                <input id={`title-${selectedStory.story_id}`} type="text" value={selectedStory.story_title} onChange={e => handleStoryChange({ ...selectedStory, story_title: e.target.value })} className={`${textareaClass} font-semibold`} />
                            </div>
                            <div>
                                <label className={labelClass}>Story Format</label>
                                <div className="mt-2 flex rounded-md shadow-sm">
                                    {Object.values(STORY_FORMATS).map(formatInfo => (
                                        <button
                                            key={formatInfo.name}
                                            type="button"
                                            onClick={() => handleFormatChange(selectedStory, formatInfo.name as StorytellingFormat)}
                                            className={`-ml-px px-4 py-2 text-sm border border-slate-300 dark:border-slate-600 first:rounded-l-md last:rounded-r-md first:ml-0 ${selectedStory.format === formatInfo.name ? 'bg-blue-600 text-white z-10' : 'bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600'}`}
                                            title={formatInfo.description}
                                        >
                                            {formatInfo.name}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            
                            <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                                <div className="flex justify-between items-center">
                                    <h4 className="text-md font-semibold text-slate-700 dark:text-slate-300">Detailed Story</h4>
                                    <button type="button" onClick={handleGenerateAllSpeakerNotes} disabled={!!isGenerating} className="text-xs font-semibold text-blue-600 hover:underline inline-flex items-center gap-1">
                                        {isGenerating === `${selectedStory.story_id}-all-notes` ? <LoadingSpinner/> : <SparklesIcon className="h-4 w-4"/>} Generate All Speaker Notes
                                    </button>
                                </div>
                                {storyFormatData.fields.map(field => (
                                    <div key={field.id as string}>
                                        <div className="flex justify-between items-center">
                                            <label htmlFor={`${selectedStory.story_id}-${field.id as string}`} className={labelClass}>{field.label}</label>
                                            <button type="button" onClick={() => handleAIPolishPart(selectedStory, field.id as string)} disabled={!!isGenerating} className="text-xs font-semibold text-blue-600 hover:underline inline-flex items-center gap-1">
                                                {isGenerating === `${selectedStory.story_id}-${field.id as string}` ? <LoadingSpinner/> : <SparklesIcon className="h-4 w-4"/>} Polish
                                            </button>
                                        </div>
                                        <textarea id={`${selectedStory.story_id}-${field.id as string}`} rows={field.rows} value={(selectedStory.story_body as any)[field.id] || ''} onChange={e => handleStoryChange({ ...selectedStory, story_body: {...selectedStory.story_body, [field.id]: e.target.value }})} className={textareaClass} placeholder={field.placeholder}/>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="text-center p-12 bg-slate-50 dark:bg-slate-800/80 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-700">
                            <p>Select a story to edit or add a new one.</p>
                        </div>
                    )}
                    <div className="flex justify-end mt-6 pt-6 border-t border-slate-200 dark:border-slate-700">
                        <button type="button" onClick={handleSave} disabled={isLoading} className="rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-700 disabled:opacity-50">
                            {isLoading ? <LoadingSpinner/> : 'Save All Changes'}
                        </button>
                    </div>
                </div>
            </div>

            {isPracticeModalOpen && selectedStory && storyFormatData && (
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-[70]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                    <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                        <div className="flex min-h-full items-center justify-center p-4 text-center">
                            <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-6xl">
                                <div className="bg-white dark:bg-slate-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                                    <h3 className="text-xl font-bold leading-6 text-slate-900 dark:text-white" id="modal-title">Practice: {selectedStory.story_title}</h3>
                                    <div className="mt-4 max-h-[70vh] overflow-y-auto pr-4">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {/* Left Column: Full Story */}
                                            <div className="space-y-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-900/50">
                                                <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Full Story</h2>
                                                {storyFormatData.fields.map(field => (
                                                    <div key={field.id as string}>
                                                        <h3 className="font-semibold text-slate-600 dark:text-slate-300">{field.label}</h3>
                                                        <p className="text-sm text-slate-700 dark:text-slate-400 whitespace-pre-wrap">{(selectedStory.story_body as any)[field.id] || 'Not provided.'}</p>
                                                    </div>
                                                ))}
                                            </div>
                                            {/* Right Column: Editable Speaker Notes */}
                                            <div className="space-y-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-900/50">
                                                <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Editable Speaker Notes</h2>
                                                {storyFormatData.fields.map(field => (
                                                    <div key={field.id as string}>
                                                        <label htmlFor={`practice-${field.id as string}`} className="block text-sm font-medium text-slate-600 dark:text-slate-300">{field.label}</label>
                                                        <textarea
                                                            id={`practice-${field.id as string}`}
                                                            value={practiceStoryNotes[field.id as string] || ''}
                                                            onChange={e => setPracticeStoryNotes(prev => ({ ...prev, [field.id as string]: e.target.value }))}
                                                            rows={field.rows > 2 ? 3 : 2}
                                                            className={`${textareaClass} text-sm font-mono`}
                                                            placeholder={`Concise points for ${field.label}...`}
                                                        />
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                                    <button
                                        type="button"
                                        onClick={handleSaveNotesFromPractice}
                                        disabled={isSavingNotes}
                                        className="inline-flex w-full justify-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-700 sm:ml-3 sm:w-auto disabled:opacity-50"
                                    >
                                        {isSavingNotes ? <LoadingSpinner /> : 'Save Notes'}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setIsPracticeModalOpen(false)}
                                        className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto"
                                    >
                                        Close
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};