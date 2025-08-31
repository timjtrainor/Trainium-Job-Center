import React, { useState } from 'react';
import { LinkedInPost, Prompt, LinkedInPostPayload, PromptContext, StrategicNarrative, JobApplication } from '../types';
import * as geminiService from '../services/geminiService';
import { LoadingSpinner, PlusCircleIcon, LinkedInIcon, SparklesIcon } from './IconComponents';

interface LinkedInPostStudioViewProps {
    posts: LinkedInPost[];
    prompts: Prompt[];
    onCreatePost: (payload: LinkedInPostPayload) => Promise<void>;
    strategicNarratives: StrategicNarrative[];
    applications: JobApplication[];
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
}

type PostType = 'narrative' | 'journey';
type Step = 'idle' | 'themes' | 'post';

export const LinkedInPostStudioView = ({ posts, prompts, onCreatePost, strategicNarratives, applications, debugCallbacks }: LinkedInPostStudioViewProps): React.ReactNode => {
    // State for AI generator
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [step, setStep] = useState<Step>('idle');
    const [postType, setPostType] = useState<PostType>('narrative');
    const [selectedNarrativeId, setSelectedNarrativeId] = useState<string>(strategicNarratives[0]?.narrative_id || '');
    const [generatedThemes, setGeneratedThemes] = useState<string[]>([]);
    const [selectedTheme, setSelectedTheme] = useState<string>('');
    const [generatedPost, setGeneratedPost] = useState<string>('');
    const [isSaving, setIsSaving] = useState(false);

    // State for manual post tracker
    const [manualContent, setManualContent] = useState('');
    const [manualTheme, setManualTheme] = useState('');
    const [manualNarrativeId, setManualNarrativeId] = useState<string>(strategicNarratives[0]?.narrative_id || '');
    const [isSavingManual, setIsSavingManual] = useState(false);

    // Handlers for AI Generator
    const handleGenerateThemes = async () => {
        setIsLoading(true);
        setError(null);
        setGeneratedThemes([]);
        
        const selectedNarrative = strategicNarratives.find(n => n.narrative_id === selectedNarrativeId);
        if (!selectedNarrative) {
            setError("Please select a valid narrative.");
            setIsLoading(false);
            return;
        }

        try {
            if (postType === 'narrative') {
                const themesPrompt = prompts.find(p => p.id === 'GENERATE_LINKEDIN_THEMES');
                if (!themesPrompt) throw new Error("LinkedIn themes prompt not found.");

                const narrativeApps = applications.filter(app => app.narrative_id === selectedNarrativeId).slice(0, 5);
                const appSummaries = narrativeApps.map(app => `Applied for ${app.job_title}`).join(', ');

                const context: PromptContext = {
                    NORTH_STAR: selectedNarrative.positioning_statement,
                    MASTERY: selectedNarrative.signature_capability,
                    RECENT_APPLICATIONS: appSummaries || "various senior product roles",
                };
                
                const themes = await geminiService.generateLinkedInThemes(context, themesPrompt.content, debugCallbacks);
                setGeneratedThemes(themes);
                setStep('themes');
            } else if (postType === 'journey') {
                await handleGenerateJourneyPost();
            }

        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to generate content.");
        } finally {
            setIsLoading(false);
        }
    };
    
    const handleGeneratePostFromTheme = async (theme: string) => {
        setIsLoading(true);
        setError(null);
        setSelectedTheme(theme);
        
        const selectedNarrative = strategicNarratives.find(n => n.narrative_id === selectedNarrativeId);
        if (!selectedNarrative) {
            setError("Selected narrative not found.");
            setIsLoading(false);
            return;
        }

        try {
            const postPrompt = prompts.find(p => p.id === 'GENERATE_POSITIONED_LINKEDIN_POST');
            if (!postPrompt) throw new Error("LinkedIn post prompt not found.");
            
            const context: PromptContext = {
                THEME: theme,
                POSITIONING_STATEMENT: selectedNarrative.positioning_statement,
                NORTH_STAR: selectedNarrative.long_term_legacy,
                MASTERY: selectedNarrative.signature_capability,
            };
            
            const postContent = await geminiService.generatePositionedLinkedInPost(context, postPrompt.content, debugCallbacks);
            setGeneratedPost(postContent);
            setStep('post');

        } catch(e) {
            setError(e instanceof Error ? e.message : "Failed to generate post.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateJourneyPost = async () => {
        setIsLoading(true);
        setError(null);
        const narrativeA = strategicNarratives[0];
        const narrativeB = strategicNarratives[1];
        if (!narrativeA || !narrativeB) {
            setError("Two strategic narratives are required to generate a journey post.");
            setIsLoading(false);
            return;
        }
        
        try {
            const journeyPrompt = prompts.find(p => p.id === 'GENERATE_JOURNEY_POST');
            if (!journeyPrompt) throw new Error("Journey post prompt not found.");
            
            const context: PromptContext = {
                NARRATIVE_A_SUMMARY: `Title: ${narrativeA.desired_title}, Positioning: ${narrativeA.positioning_statement}`,
                NARRATIVE_B_SUMMARY: `Title: ${narrativeB.desired_title}, Positioning: ${narrativeB.positioning_statement}`,
            };
            
            const postContent = await geminiService.generatePositionedLinkedInPost(context, journeyPrompt.content, debugCallbacks);
            setGeneratedPost(postContent);
            setSelectedTheme("My Professional Journey");
            setStep('post');
        } catch(e) {
            setError(e instanceof Error ? e.message : "Failed to generate journey post.");
        } finally {
            setIsLoading(false);
        }
    };
    
    const handleSavePost = async () => {
        setIsSaving(true);
        setError(null);
        try {
            await onCreatePost({
                narrative_id: postType === 'narrative' ? selectedNarrativeId : null,
                theme: selectedTheme,
                content: generatedPost,
            });
            resetFlow();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to save post.");
        } finally {
            setIsSaving(false);
        }
    }

    const resetFlow = () => {
        setStep('idle');
        setError(null);
        setGeneratedThemes([]);
        setSelectedTheme('');
        setGeneratedPost('');
    }

    // Handlers for manual post tracker
    const handleSaveManualPost = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!manualContent || !manualTheme || !manualNarrativeId) {
            setError("Content, theme, and narrative are required for manual posts.");
            return;
        }
        setIsSavingManual(true);
        setError(null);
        try {
            await onCreatePost({
                narrative_id: manualNarrativeId,
                theme: manualTheme,
                content: manualContent,
            });
            setManualContent('');
            setManualTheme('');
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to save manual post.");
        } finally {
            setIsSavingManual(false);
        }
    };

    const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
    const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* AI Post Generator */}
                <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                    {step === 'idle' && (
                        <div className="space-y-4 text-center">
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Generate New Post with AI</h2>
                            <div className="max-w-md mx-auto text-left space-y-4">
                                <div>
                                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Choose Post Type</label>
                                    <div className="mt-2 flex rounded-md shadow-sm">
                                        <button onClick={() => setPostType('narrative')} className={`px-4 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-l-md ${postType === 'narrative' ? 'bg-blue-600 text-white z-10' : 'bg-white dark:bg-slate-700 hover:bg-slate-50'}`}>From Narrative</button>
                                        <button onClick={() => setPostType('journey')} className={`-ml-px px-4 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-r-md ${postType === 'journey' ? 'bg-blue-600 text-white z-10' : 'bg-white dark:bg-slate-700 hover:bg-slate-50'}`}>Journey Post</button>
                                    </div>
                                </div>
                                {postType === 'narrative' && (
                                    <div>
                                        <label htmlFor="narrative-select" className={labelClass}>Select Narrative</label>
                                        <select id="narrative-select" value={selectedNarrativeId} onChange={e => setSelectedNarrativeId(e.target.value)} className={inputClass}>
                                            {strategicNarratives.map(n => <option key={n.narrative_id} value={n.narrative_id}>{n.narrative_name}</option>)}
                                        </select>
                                    </div>
                                )}
                            </div>
                            <button onClick={handleGenerateThemes} disabled={isLoading} className="mt-4 inline-flex items-center justify-center px-5 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400">
                                {isLoading ? <LoadingSpinner/> : 'Generate Content Ideas'}
                            </button>
                        </div>
                    )}
                    {step !== 'idle' && (
                        <div className="space-y-6">
                            <button onClick={resetFlow} className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline">&larr; Start Over</button>
                            {step === 'themes' && (
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Step 1: Choose a Theme</h2>
                                    <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {generatedThemes.map((theme, index) => (
                                            <button key={index} onClick={() => handleGeneratePostFromTheme(theme)} disabled={isLoading} className="p-4 text-left rounded-lg border bg-slate-50 hover:bg-blue-50 dark:bg-slate-800/80 dark:hover:bg-blue-900/20 border-slate-300 dark:border-slate-600 hover:border-blue-400 dark:hover:border-blue-500 transition-colors disabled:opacity-50">
                                                <p className="font-semibold text-slate-800 dark:text-slate-200">{theme}</p>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {step === 'post' && (
                                <div className="space-y-4">
                                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Step 2: Refine Your Post</h2>
                                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">AI has drafted a post based on your theme: <span className="font-semibold">"{selectedTheme}"</span></p>
                                    <div>
                                        <label htmlFor="generated-post" className={labelClass}>Generated Post</label>
                                        {isLoading && <div className="text-center py-8">Generating post...</div>}
                                        <textarea id="generated-post" value={generatedPost} onChange={(e) => setGeneratedPost(e.target.value)} rows={10} className={`${inputClass} mt-1`} />
                                    </div>
                                    <div className="mt-4 flex justify-end">
                                        <button onClick={handleSavePost} disabled={isSaving} className="px-4 py-2 text-sm rounded-md bg-green-600 text-white hover:bg-green-700 disabled:bg-green-400">
                                            {isSaving ? <LoadingSpinner/> : 'Save Post'}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Manual Post Tracker */}
                <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Track an Existing Post</h2>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Paste in content you've already published to track its engagement.</p>
                    <form onSubmit={handleSaveManualPost} className="mt-4 space-y-4">
                        <div>
                            <label htmlFor="manualContent" className={labelClass}>Post Content *</label>
                            <textarea id="manualContent" value={manualContent} onChange={e => setManualContent(e.target.value)} rows={8} className={inputClass} required />
                        </div>
                        <div>
                            <label htmlFor="manualTheme" className={labelClass}>Theme *</label>
                            <input type="text" id="manualTheme" value={manualTheme} onChange={e => setManualTheme(e.target.value)} className={inputClass} required />
                        </div>
                        <div>
                            <label htmlFor="manualNarrativeId" className={labelClass}>Associated Narrative *</label>
                            <select id="manualNarrativeId" value={manualNarrativeId} onChange={e => setManualNarrativeId(e.target.value)} className={inputClass} required>
                                {strategicNarratives.map(n => <option key={n.narrative_id} value={n.narrative_id}>{n.narrative_name}</option>)}
                            </select>
                        </div>
                        <div className="text-right">
                            <button type="submit" disabled={isSavingManual} className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 disabled:bg-green-400">
                                {isSavingManual ? <LoadingSpinner /> : 'Save Post to History'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {error && <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4 text-sm font-medium text-red-700 dark:text-red-300">{error}</div>}
            
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Post History</h2>
                <div className="mt-4 space-y-4">
                    {posts.length > 0 ? posts.map(post => (
                        <div key={post.post_id} className="p-4 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700">
                            <p className="text-xs text-slate-500 dark:text-slate-400">Posted on: {new Date(post.created_at).toLocaleDateString()}</p>
                            <p className="mt-1 font-semibold text-slate-700 dark:text-slate-300">Theme: {post.theme}</p>
                            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap">{post.content}</p>
                        </div>
                    )) : (
                         <div className="text-center py-12 px-6 bg-slate-50 dark:bg-slate-800/50 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-700">
                            <LinkedInIcon className="mx-auto h-12 w-12 text-slate-400" />
                            <h3 className="mt-2 text-sm font-semibold text-gray-900 dark:text-white">No posts yet</h3>
                            <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">Get started by generating or tracking your first post.</p>
                         </div>
                    )}
                </div>
            </div>
        </div>
    );
};
