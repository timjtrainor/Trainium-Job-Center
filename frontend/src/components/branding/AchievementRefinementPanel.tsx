import React, { useState, useEffect, useMemo } from 'react';
import { ResumeAccomplishment, StrategicNarrative, Prompt, PromptContext, KeywordsResult, AchievementScore, KeywordDetail } from '../../types';
import * as geminiService from '../../services/geminiService';
import { LoadingSpinner, SparklesIcon, XCircleIcon } from '../shared/ui/IconComponents';

interface AchievementRefinementPanelProps {
    isOpen: boolean;
    onClose: () => void;
    achievement: ResumeAccomplishment;
    activeNarrative: StrategicNarrative | null;
    onSave: (achievement: ResumeAccomplishment) => void;
    prompts: Prompt[];
    jobContext: {
        jobTitle: string;
        companyName: string;
        keywords: KeywordsResult | null;
    }
}

const KeywordPill = ({ keyword, isSelected, onToggle }: { keyword: string; isSelected: boolean; onToggle: (keyword: string) => void; }) => (
    <button
        type="button"
        onClick={() => onToggle(keyword)}
        className={`px-2.5 py-1 text-xs font-medium rounded-full border transition-colors ${
            isSelected
                ? 'bg-blue-600 border-blue-600 text-white'
                : 'bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600'
        }`}
    >
        {keyword}
    </button>
);


export const AchievementRefinementPanel = ({ isOpen, onClose, achievement, activeNarrative, onSave, prompts, jobContext }: AchievementRefinementPanelProps) => {
    const [originalText, setOriginalText] = useState('');
    const [currentDraft, setCurrentDraft] = useState('');
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [selectedTone, setSelectedTone] = useState<string>('Metric-Focused');
    const [scores, setScores] = useState<{ original_score: AchievementScore; edited_score: AchievementScore } | null>(null);
    const [customKeywords, setCustomKeywords] = useState<string[]>([]);
    const [newKeyword, setNewKeyword] = useState('');
    
    const [isLoading, setIsLoading] = useState(false);
    const [loadingAction, setLoadingAction] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    
    // State for chat refinement flow
    const [refiningDraft, setRefiningDraft] = useState<string | null>(null);
    const [refinementHistory, setRefinementHistory] = useState<{ author: 'user' | 'ai', text: string }[]>([]);
    const [chatInput, setChatInput] = useState('');
    const [selectedFramework, setSelectedFramework] = useState<'PAR' | 'APR' | 'Result First'>('PAR');


    const storyTones = ["Metric-Focused", "Struggle-to-Triumph", "Efficiency Gain", "Innovation", "Leadership"];
    
    const suggestedKeywords = useMemo(() => {
        if (!jobContext.keywords) return [];
        return [...jobContext.keywords.hard_keywords, ...jobContext.keywords.soft_keywords]
            .filter(kw => kw.resume_boost)
            .map(kw => kw.keyword)
            .slice(0, 10);
    }, [jobContext.keywords]);

    const [selectedKeywords, setSelectedKeywords] = useState<string[]>([]);

    useEffect(() => {
        if (isOpen) {
            // Set the "original" text for scoring to the true original from the base resume.
            setOriginalText(achievement.original_description || achievement.description);
            setCurrentDraft(achievement.description);
            setSelectedTone('Metric-Focused');
            setSelectedFramework('PAR');
            setSuggestions([]);
            setError(null);
            setScores(null);
            setCustomKeywords([]);
            setNewKeyword('');
            setSelectedKeywords([]);
            setRefiningDraft(null);
            setRefinementHistory([]);
            setChatInput('');
        }
    }, [isOpen, achievement]);

    const handleAction = async (action: () => Promise<void>, actionName: string) => {
        setLoadingAction(actionName);
        setIsLoading(true);
        setError(null);
        try {
            await action();
        } catch (e) {
            setError(e instanceof Error ? e.message : `Failed to ${actionName}.`);
        } finally {
            setIsLoading(false);
            setLoadingAction(null);
        }
    };
    
    const handleGenerate = async () => {
        await handleAction(async () => {
            setSuggestions([]);
            const prompt = prompts.find(p => p.id === 'REFINE_ACHIEVEMENT_WITH_CONTEXT');
            if (!prompt) throw new Error("Refinement prompt not found.");

            const jobContextString = jobContext.jobTitle ? JSON.stringify({ title: jobContext.jobTitle, company: jobContext.companyName, keywords: jobContext.keywords }) : '';
            const allKeywords = [...selectedKeywords, ...customKeywords];

            const context: PromptContext = {
                RAW_TEXT: originalText,
                POSITIONING_STATEMENT: activeNarrative?.positioning_statement || '',
                MASTERY: activeNarrative?.signature_capability || '',
                STORY_TONE: selectedTone,
                BULLET_FRAMEWORK: selectedFramework,
                KEYWORDS_TO_INCLUDE: allKeywords.join(', '),
                JOB_CONTEXT_JSON: jobContextString,
            };

            const result = await geminiService.refineAchievementWithContext(context, prompt.content);
            setSuggestions(result);
            if(result.length > 0) {
                setCurrentDraft(result[0]);
            }
        }, 'generate');
    };

    const handleScore = async () => {
        await handleAction(async () => {
            const prompt = prompts.find(p => p.id === 'SCORE_DUAL_ACHIEVEMENTS');
            if (!prompt || !activeNarrative) throw new Error("Scoring prompt or active narrative not found.");

            const jobContextString = jobContext.jobTitle ? JSON.stringify({ title: jobContext.jobTitle, company: jobContext.companyName, keywords: jobContext.keywords }) : '';

            const context: PromptContext = {
                ORIGINAL_ACHIEVEMENT_TO_SCORE: originalText,
                EDITED_ACHIEVEMENT_TO_SCORE: currentDraft,
                POSITIONING_STATEMENT: activeNarrative.positioning_statement,
                MASTERY: activeNarrative.signature_capability,
                JOB_CONTEXT_JSON: jobContextString,
            };
            
            const result = await geminiService.scoreDualAccomplishments(context, prompt.content);
            setScores(result);
        }, 'score');
    };
    
    const handleStartRefinement = (suggestion: string) => {
        setRefiningDraft(suggestion);
        setRefinementHistory([]);
    };
    
    const handleRefinementChat = async () => {
        if (!chatInput.trim() || !refiningDraft) return;
        
        const userMessage = { author: 'user' as const, text: chatInput };
        const newHistory = [...refinementHistory, userMessage];
        setRefinementHistory(newHistory);
        setChatInput('');

        await handleAction(async () => {
            const prompt = prompts.find(p => p.id === 'REFINE_ACHIEVEMENT_CHAT');
            if (!prompt) throw new Error("Chat refinement prompt not found.");
            
            const context: PromptContext = {
                ORIGINAL_ACHIEVEMENT: originalText,
                ACHIEVEMENT_TO_REFINE: refiningDraft,
                USER_FEEDBACK: chatInput,
                BULLET_FRAMEWORK: selectedFramework,
                CONVERSATION_HISTORY: newHistory.map(m => `${m.author}: ${m.text}`).join('\n'),
            };

            const result = await geminiService.chatToRefineAchievement(context, prompt.content);
            setRefiningDraft(result);
            setRefinementHistory(prev => [...prev, { author: 'ai', text: result }]);
        }, 'chat');
    };

    const handleUseRefined = () => {
        if (refiningDraft) {
            setCurrentDraft(refiningDraft);
        }
        setRefiningDraft(null);
    };

    const handleSave = () => {
        const updatedAchievement = { ...achievement, description: currentDraft, score: scores?.edited_score };
        onSave(updatedAchievement);
        onClose();
    };

    const handleKeywordToggle = (keyword: string) => {
        setSelectedKeywords(prev => 
            prev.includes(keyword)
                ? prev.filter(k => k !== keyword)
                : [...prev, keyword]
        );
    };

    const handleAddCustomKeyword = () => {
        if(newKeyword.trim() && !customKeywords.includes(newKeyword.trim())) {
            setCustomKeywords(prev => [...prev, newKeyword.trim()]);
            setNewKeyword('');
        }
    };

    if (!isOpen) return null;

    return (
        <div className="relative z-[70]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-5xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">Achievement Refinement Studio</h3>
                            {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
                            <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-6 max-h-[75vh] overflow-y-auto p-1">
                                {/* Left: Control Panel & Suggestions/Chat */}
                                <div className="space-y-4">
                                    {refiningDraft === null ? (
                                        <>
                                            <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
                                                <h4 className="font-semibold text-slate-800 dark:text-slate-200">Creative Direction</h4>
                                                <div className="mt-2 space-y-3">
                                                    <div><label htmlFor="story-tone" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Drama Tone</label><select id="story-tone" value={selectedTone} onChange={(e) => setSelectedTone(e.target.value)} disabled={isLoading} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm">{storyTones.map(tone => <option key={tone} value={tone}>{tone}</option>)}</select></div>
                                                    <div>
                                                        <label htmlFor="bullet-framework" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Bullet Framework</label>
                                                        <select
                                                            id="bullet-framework"
                                                            value={selectedFramework}
                                                            onChange={(e) => setSelectedFramework(e.target.value as any)}
                                                            disabled={isLoading}
                                                            className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm"
                                                        >
                                                            <option value="PAR">PAR (Problem, Action, Result)</option>
                                                            <option value="APR">APR (Action, Problem, Result)</option>
                                                            <option value="Result First">Result First</option>
                                                        </select>
                                                    </div>
                                                    <div><label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Keywords</label><div className="mt-2 flex flex-wrap gap-2">{suggestedKeywords.map(kw => <KeywordPill key={kw} keyword={kw} isSelected={selectedKeywords.includes(kw)} onToggle={handleKeywordToggle} />)}</div><div className="mt-2 flex flex-wrap gap-2">{customKeywords.map(kw => (<span key={kw} className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-800 dark:text-indigo-300">{kw} <button onClick={() => setCustomKeywords(prev => prev.filter(k => k !== kw))}><XCircleIcon className="h-4 w-4"/></button></span>))}</div><div className="mt-2 flex gap-2"><input value={newKeyword} onChange={e => setNewKeyword(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleAddCustomKeyword()} placeholder="Add custom keyword..." className="w-full p-2 text-sm bg-white dark:bg-slate-700 rounded-md border-slate-300 dark:border-slate-600"/> <button type="button" onClick={handleAddCustomKeyword} className="px-3 py-1 rounded-md text-sm font-semibold bg-slate-200 dark:bg-slate-600 hover:bg-slate-300 dark:hover:bg-slate-500">Add</button></div></div>
                                                </div>
                                            </div>
                                            <button onClick={handleGenerate} disabled={isLoading} className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400">{isLoading && loadingAction === 'generate' ? <LoadingSpinner/> : <SparklesIcon className="h-5 w-5"/>}Generate Suggestions</button>
                                            <div className="space-y-2"><h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Suggestions</h4><div className="space-y-2 max-h-60 overflow-y-auto pr-2">{suggestions.length === 0 && <p className="text-sm text-center text-slate-500 py-4">Suggestions will appear here.</p>}{suggestions.map((sugg, i) => (<div key={i} className="p-2 rounded-md bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 flex justify-between items-center"><p className="text-sm flex-grow text-left">{sugg}</p><div className="flex-shrink-0 ml-2 flex gap-2"><button onClick={() => setCurrentDraft(sugg)} className="text-xs font-semibold text-green-600 hover:underline">Use</button><button onClick={() => handleStartRefinement(sugg)} className="text-xs font-semibold text-blue-600 hover:underline">Refine</button></div></div>))}</div></div>
                                        </>
                                    ) : (
                                        <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700 space-y-3"><div className="flex justify-between items-center"><h4 className="font-semibold text-slate-800 dark:text-slate-200">Refinement Chat</h4><button onClick={() => setRefiningDraft(null)} className="text-xs font-semibold text-blue-600 hover:underline">Back to Suggestions</button></div><div className="space-y-3 p-2 border rounded-lg border-slate-200 dark:border-slate-700 h-48 overflow-y-auto flex flex-col">{refinementHistory.map((message, index) => (<div key={index} className={`flex ${message.author === 'user' ? 'justify-end' : 'justify-start'}`}><div className={`max-w-md p-2 rounded-lg ${message.author === 'user' ? 'bg-blue-100 dark:bg-blue-900/50' : 'bg-slate-100 dark:bg-slate-700'}`}><p className="text-sm text-slate-800 dark:text-slate-200 whitespace-pre-wrap">{message.text}</p></div></div>))}{isLoading && loadingAction === 'chat' && <div className="flex justify-start"><div className="max-w-md p-2 rounded-lg bg-slate-100 dark:bg-slate-700"><LoadingSpinner/></div></div>}</div><div className="flex gap-2"><input value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && !isLoading && handleRefinementChat()} disabled={isLoading} placeholder="Your instruction..." className="w-full p-2 text-sm bg-white dark:bg-slate-700 rounded-md border-slate-300 dark:border-slate-600"/><button onClick={handleRefinementChat} disabled={isLoading || !chatInput} className="px-4 py-2 text-sm rounded-md bg-blue-600 text-white font-semibold disabled:bg-blue-400">Send</button></div><div><label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Latest Refined Draft</label><textarea value={refiningDraft} onChange={e => setRefiningDraft(e.target.value)} rows={4} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm" /></div><div className="text-right"><button onClick={handleUseRefined} className="px-3 py-1 text-sm font-semibold text-white bg-green-600 hover:bg-green-700 rounded-md">Use this Refined Version</button></div></div>
                                    )}
                                </div>
                                {/* Right: Editor and Scoring */}
                                <div className="space-y-4"><div><label className="block text-sm font-medium text-slate-500 dark:text-slate-400">Original (from resume)</label><p className="mt-1 text-sm p-2 rounded-md bg-slate-100 dark:bg-slate-700/80 text-slate-600 dark:text-slate-300">{originalText}</p></div><div><label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Current Draft</label><textarea value={currentDraft} onChange={e => setCurrentDraft(e.target.value)} rows={5} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm" /></div><div className="p-4 bg-slate-100 dark:bg-slate-900/50 rounded-lg"><div className="flex justify-between items-center"><h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">AI Scorecard (Original vs. Draft)</h4><button onClick={handleScore} disabled={isLoading} className="inline-flex items-center justify-center px-3 py-1 text-xs font-semibold rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400">{loadingAction === 'score' ? <LoadingSpinner/> : "Score Draft"}</button></div>{scores ? (<div className="mt-2 text-sm"><table className="w-full"><thead><tr><th className="font-medium">Metric</th><th className="font-medium">Original</th><th className="font-medium">Draft</th><th className="font-medium">Change</th></tr></thead><tbody>{['overall_score', 'clarity', 'drama', 'alignment_with_mastery', 'alignment_with_job'].map(key => {const originalVal = scores.original_score[key as keyof AchievementScore] || 0;const editedVal = scores.edited_score[key as keyof AchievementScore] || 0;if (key === 'alignment_with_job' && !scores.original_score.alignment_with_job) return null;const diff = editedVal - originalVal;const diffColor = diff > 0.1 ? 'text-green-600 dark:text-green-400' : diff < -0.1 ? 'text-red-600 dark:text-red-400' : '';return (<tr key={key} className="text-center"><td className="text-left capitalize text-xs text-slate-500 dark:text-slate-400">{key.replace('_',' ')}</td><td>{originalVal.toFixed(1)}</td><td>{editedVal.toFixed(1)}</td><td className={diffColor}>{diff > 0 ? '+' : ''}{diff.toFixed(1)}</td></tr>)})}</tbody></table></div>) : (<p className="text-xs text-slate-500 mt-2">Score your draft to see how it compares to the original.</p>)}</div></div>
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6"><button type="button" onClick={handleSave} disabled={isLoading} className="inline-flex w-full justify-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-700 sm:ml-3 sm:w-auto disabled:opacity-50">Save & Close</button><button type="button" onClick={onClose} disabled={isLoading} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto">Cancel</button></div>
                    </div>
                </div>
            </div>
        </div>
    );
};