import React, { useState, useCallback, useRef, useLayoutEffect, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Resume, KeywordsResult, ResumeAccomplishment, Prompt, UserProfile, StrategicNarrative, KeywordDetail, SkillSection, AchievementScore } from '../types';
import { ArrowRightIcon, LoadingSpinner, SparklesIcon, XCircleIcon } from './IconComponents';
import * as geminiService from '../services/geminiService';

interface TailorResumeStepProps {
  finalResume: Resume;
  setFinalResume: React.Dispatch<React.SetStateAction<Resume | null>>;
  summaryParagraphOptions: string[];
  allSkillOptions: string[];
  keywords: KeywordsResult | null;
  missingKeywords: KeywordDetail[];
  setMissingKeywords: React.Dispatch<React.SetStateAction<KeywordDetail[]>>;
  onNext: () => void;
  isLoading: boolean;
  prompts: Prompt[];
  userProfile: UserProfile | null;
  activeNarrative: StrategicNarrative | null;
  jobTitle: string;
  companyName: string;
  debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
  resumeAlignmentScore: number | null;
  onRecalculateScore: () => Promise<void>;
}

const SectionCard = ({ title, children, subtitle }: { title: string, subtitle?: string, children: React.ReactNode }) => (
    <div className="bg-white dark:bg-slate-800/80 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{title}</h3>
        {subtitle && <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">{subtitle}</p>}
        <div className="space-y-4 mt-4">{children}</div>
    </div>
);

const AlignmentScore = ({ score, onRecalculate, isLoading }: { score: number | null, onRecalculate: () => void, isLoading: boolean }) => {
    const percentage = score ? score * 10 : 0;
    const radius = 45;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    const getScoreColor = () => {
        if (score === null) return 'text-slate-400';
        if (score >= 8) return 'text-green-500';
        if (score >= 6) return 'text-yellow-500';
        return 'text-red-500';
    };

    const scoreColor = getScoreColor();

    return (
        <SectionCard title="Resume Alignment Score">
            <div className="flex flex-col items-center gap-4">
                <div className="relative h-32 w-32">
                    <svg className="h-full w-full" viewBox="0 0 100 100">
                        <circle className="stroke-current text-slate-200 dark:text-slate-700" strokeWidth="10" cx="50" cy="50" r={radius} fill="transparent" />
                        <circle 
                            className={`stroke-current ${scoreColor} transition-all duration-1000 ease-in-out`}
                            strokeWidth="10" 
                            cx="50" 
                            cy="50" 
                            r={radius} 
                            fill="transparent" 
                            strokeLinecap="round" 
                            strokeDasharray={circumference} 
                            strokeDashoffset={strokeDashoffset} 
                            transform="rotate(-90 50 50)"
                        />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className={`text-3xl font-bold ${scoreColor}`}>
                            {score !== null ? score.toFixed(1) : '?'}
                        </span>
                    </div>
                </div>
                <button 
                    onClick={onRecalculate} 
                    disabled={isLoading}
                    className="inline-flex items-center justify-center gap-2 w-full px-4 py-2 text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400"
                >
                    {isLoading ? <LoadingSpinner/> : <SparklesIcon className="h-5 w-5"/>}
                    Recalculate Score
                </button>
                <p className="text-xs text-slate-500 dark:text-slate-400 text-center">Recalculate after making edits to see your updated score.</p>
            </div>
        </SectionCard>
    );
};

const AutoSizingTextarea = (props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    useLayoutEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = `${textarea.scrollHeight}px`;
        }
    }, [props.value]);
    return <textarea ref={textareaRef} {...props} rows={1} />;
};

export const TailorResumeStep = (props: TailorResumeStepProps) => {
    const {
        finalResume, setFinalResume,
        summaryParagraphOptions,
        allSkillOptions, keywords, 
        missingKeywords, setMissingKeywords,
        onNext, isLoading,
        prompts,
        userProfile,
        activeNarrative,
        jobTitle,
        companyName,
        debugCallbacks,
        resumeAlignmentScore,
        onRecalculateScore
    } = props;

    const [selectedKeywords, setSelectedKeywords] = useState<string[]>([]);
    const [customKeywords, setCustomKeywords] = useState<string[]>([]);
    const [newKeywordInput, setNewKeywordInput] = useState('');
    const [refiningId, setRefiningId] = useState<string | null>(null);
    const [isRecalculating, setIsRecalculating] = useState(false);
    
    useEffect(() => {
        // This effect is critical to ensure every accomplishment has a stable, unique ID.
        // The bug where editing one bullet updates others is caused by missing or non-unique IDs,
        // which makes it impossible for React and the update handlers to track items correctly.
        // This runs once when the component receives the resume data.
        if (finalResume) {
            let needsUpdate = false;
            const updatedWorkExperience = finalResume.work_experience.map(exp => {
                const updatedAccomplishments = exp.accomplishments.map((acc, index) => {
                    // If an accomplishment lacks a unique ID, we assign one.
                    if (!acc.achievement_id) {
                        needsUpdate = true;
                        return { ...acc, achievement_id: uuidv4(), order_index: index };
                    }
                    // Also ensure order_index is set for sorting.
                    if (acc.order_index === undefined) {
                         needsUpdate = true;
                         return { ...acc, order_index: index };
                    }
                    return acc;
                });
                updatedAccomplishments.sort((a,b) => (a.order_index || 0) - (b.order_index || 0));
                return { ...exp, accomplishments: updatedAccomplishments };
            });

            if (needsUpdate) {
                setFinalResume(prev => prev ? { ...prev, work_experience: updatedWorkExperience } : null);
            }
        }
    }, [finalResume, setFinalResume]);


    const handleSummaryParagraphChange = useCallback((newParagraph: string) => {
        setFinalResume(prev => prev ? { ...prev, summary: { ...prev.summary, paragraph: newParagraph, bullets: [] } } : null);
    }, [setFinalResume]);

    
    const handleSkillChange = useCallback((skill: string, isChecked: boolean) => {
        setFinalResume(prev => {
            if (!prev) return null;
            const skillSection: SkillSection = (prev.skills && prev.skills[0]) ? { ...prev.skills[0] } : { heading: 'Core Competencies', items: [] };
            let currentItems = skillSection.items || [];
    
            if (isChecked) {
                if (currentItems.length < 9 && !currentItems.includes(skill)) {
                    skillSection.items = [...currentItems, skill];
                }
            } else {
                skillSection.items = currentItems.filter(s => s !== skill);
            }
            return { ...prev, skills: [skillSection] };
        });
    }, [setFinalResume]);

    const handleAccomplishmentChange = useCallback((achievementId: string, newDescription: string) => {
        setFinalResume(prev => {
            if (!prev) return null;
            const newWorkExperience = prev.work_experience.map(job => ({
                ...job,
                accomplishments: job.accomplishments.map(acc =>
                    acc.achievement_id === achievementId
                        ? { ...acc, description: newDescription }
                        : acc
                )
            }));
            return { ...prev, work_experience: newWorkExperience };
        });
    }, [setFinalResume]);
    
    const handleRefineWithKeywords = useCallback(async (achievementId: string) => {
        const keywordsToUse = [...selectedKeywords];
        if (keywordsToUse.length === 0 || !finalResume) return;

        setRefiningId(achievementId);
        
        let achievementToRefine: ResumeAccomplishment | null = null;
        for (const job of finalResume.work_experience) {
            const found = job.accomplishments.find(acc => acc.achievement_id === achievementId);
            if (found) {
                achievementToRefine = found;
                break;
            }
        }

        if (!achievementToRefine) {
            console.error("Could not find achievement to refine with ID:", achievementId);
            setRefiningId(null);
            return;
        }
        
        try {
            const prompt = prompts.find(p => p.id === 'REFINE_ACHIEVEMENT_WITH_KEYWORDS');
            if (!prompt) throw new Error("Refine with keywords prompt not found.");
            
            const context = {
                ACHIEVEMENT_TO_REFINE: achievementToRefine.description,
                KEYWORDS_TO_INCLUDE: keywordsToUse.join(', '),
            };
            const result = await geminiService.refineAchievementWithKeywords(context, prompt.content, debugCallbacks);
            
            handleAccomplishmentChange(achievementId, result);
            
            setMissingKeywords(prev => prev.filter(kw => !keywordsToUse.includes(kw.keyword)));
            setCustomKeywords(prev => prev.filter(kw => !keywordsToUse.includes(kw)));
            setSelectedKeywords([]);

        } catch (err) {
            console.error(err);
        } finally {
            setRefiningId(null);
        }
    }, [selectedKeywords, finalResume, prompts, debugCallbacks, handleAccomplishmentChange, setMissingKeywords, setCustomKeywords]);

    const handleKeywordToggle = useCallback((keyword: string) => {
        setSelectedKeywords(prev => 
            prev.includes(keyword)
                ? prev.filter(k => k !== keyword)
                : [...prev, keyword]
        );
    }, []);
    
    const handleAddCustomKeyword = () => {
        const newKeyword = newKeywordInput.trim();
        if (newKeyword && !customKeywords.includes(newKeyword) && !missingKeywords.some(kw => kw.keyword === newKeyword)) {
            setCustomKeywords(prev => [...prev, newKeyword]);
            setNewKeywordInput('');
        }
    };

    const handleRemoveCustomKeyword = (keywordToRemove: string) => {
        setCustomKeywords(prev => prev.filter(k => k !== keywordToRemove));
        setSelectedKeywords(prev => prev.filter(k => k !== keywordToRemove));
    };

    const handleRecalculate = async () => {
        setIsRecalculating(true);
        await onRecalculateScore();
        setIsRecalculating(false);
    };

    if (!finalResume) return <div className="text-center p-8">Loading resume data...</div>;
    
    const selectedSkills = finalResume.skills[0]?.items || [];

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Tailor Your Resume</h2>
                <p className="mt-1 text-slate-600 dark:text-slate-400">Refine the AI's suggestions to create the perfect resume for this role.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                    <SectionCard title="Professional Summary" subtitle="Choose your preferred summary paragraph. Your original summary is selected by default.">
                        {summaryParagraphOptions.map((option, index) => (
                            <div key={index} className="flex items-start">
                                <input id={`summary-${index}`} type="radio" name="summary-paragraph" value={option} checked={finalResume.summary.paragraph === option} onChange={(e) => handleSummaryParagraphChange(e.target.value)} className="h-4 w-4 border-slate-300 text-blue-600 focus:ring-blue-500 mt-1"/>
                                <label htmlFor={`summary-${index}`} className="ml-3 block text-sm text-slate-700 dark:text-slate-300">{option}</label>
                            </div>
                        ))}
                    </SectionCard>

                    <SectionCard title="Core Competencies" subtitle={`Select exactly 9 of the most relevant skills. (${selectedSkills.length}/9)`}>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                            {allSkillOptions.map(skill => {
                                const isChecked = selectedSkills.includes(skill);
                                const isDisabled = selectedSkills.length >= 9 && !isChecked;
                                return (
                                    <div key={skill} className="relative flex items-start">
                                        <div className="flex h-6 items-center"><input id={`skill-${skill}`} type="checkbox" value={skill} checked={isChecked} onChange={(e) => handleSkillChange(skill, e.target.checked)} disabled={isDisabled} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50"/></div>
                                        <div className="ml-3 text-sm leading-6"><label htmlFor={`skill-${skill}`} className={`font-medium ${isDisabled ? 'text-slate-400 dark:text-slate-500' : 'text-slate-700 dark:text-slate-300'}`}>{skill}</label></div>
                                    </div>
                                );
                            })}
                        </div>
                    </SectionCard>
                    
                    <SectionCard title="Work Experience" subtitle="Review and edit the AI-tailored accomplishments.">
                        <div className="pr-2 space-y-4">
                            {finalResume.work_experience.map((job) => {
                                const allAccomplishments = [...(job.accomplishments || [])].sort((a,b) => (a.order_index || 0) - (b.order_index || 0));
                                const alwaysInclude = allAccomplishments.filter(a => a.always_include);
                                const others = allAccomplishments.filter(a => !a.always_include);
                                
                                others.sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0));

                                const countToShow = job.filter_accomplishment_count || 3;
                                const remainingCount = Math.max(0, countToShow - alwaysInclude.length);

                                const visibleAccomplishments = [...alwaysInclude, ...others.slice(0, remainingCount)]
                                    .sort((a, b) => (a.order_index || 0) - (b.order_index || 0));

                                const visibleIds = new Set(visibleAccomplishments.map(a => a.achievement_id));
                                const hiddenAccomplishments = allAccomplishments
                                    .filter(a => !visibleIds.has(a.achievement_id))
                                    .sort((a, b) => (a.order_index || 0) - (b.order_index || 0));
                                
                                const renderAccomplishmentEditor = (acc: ResumeAccomplishment, isVisible: boolean) => (
                                    <div key={acc.achievement_id} className={`p-4 mb-4 border rounded-md transition-opacity ${isVisible ? 'border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/80' : 'border-dashed border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800/40 opacity-70'}`}>
                                        <AutoSizingTextarea value={acc.description} onChange={(e) => handleAccomplishmentChange(acc.achievement_id, e.target.value)} className="block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm resize-none overflow-hidden"/>
                                        <div className="flex justify-between items-center mt-2">
                                            <div className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                                                AI Relevance Score: {acc.relevance_score ? acc.relevance_score.toFixed(1) : 'N/A'}
                                            </div>
                                            <button type="button" onClick={() => handleRefineWithKeywords(acc.achievement_id)} disabled={selectedKeywords.length === 0 || !!refiningId} className="text-xs font-semibold text-blue-600 hover:text-blue-500 inline-flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed">
                                                {refiningId === acc.achievement_id ? <LoadingSpinner /> : <SparklesIcon className="h-4 w-4" />}
                                                Refine with Keyword
                                            </button>
                                        </div>
                                    </div>
                                );

                                return (
                                    <div key={job.company_name} className="p-4 border-t border-slate-200 dark:border-slate-700 first:border-t-0">
                                        <h4 className="font-bold text-md text-slate-800 dark:text-slate-200 mb-3">{job.job_title} at {job.company_name}</h4>
                                        {visibleAccomplishments.map(acc => renderAccomplishmentEditor(acc, true))}
                                        {hiddenAccomplishments.length > 0 && (
                                            <>
                                                <div className="relative my-4 text-center">
                                                    <div className="absolute inset-0 flex items-center" aria-hidden="true">
                                                        <div className="w-full border-t border-dashed border-slate-300 dark:border-slate-600"></div>
                                                    </div>
                                                    <div className="relative flex justify-center">
                                                        <span className="bg-white dark:bg-slate-800/80 px-3 text-xs font-medium text-slate-500 dark:text-slate-400">
                                                            Not included in this version ({hiddenAccomplishments.length} hidden)
                                                        </span>
                                                    </div>
                                                </div>
                                                {hiddenAccomplishments.map(acc => renderAccomplishmentEditor(acc, false))}
                                            </>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </SectionCard>
                </div>

                 <div className="lg:col-span-1">
                    <div className="sticky top-8 space-y-4">
                        <AlignmentScore 
                            score={resumeAlignmentScore} 
                            onRecalculate={handleRecalculate} 
                            isLoading={isRecalculating}
                        />
                         <SectionCard title="AI Co-pilot">
                             <div className="space-y-3">
                                <h4 className="text-sm font-semibold">Missing Keywords</h4>
                                <p className="text-xs text-slate-500 dark:text-slate-400">Select keywords, then click "Refine with Keyword" on a relevant accomplishment.</p>
                                <div className="space-y-2 max-h-40 overflow-y-auto pr-2">
                                    {missingKeywords.map(kw => (
                                        <div key={kw.keyword} className="relative flex items-start">
                                            <div className="flex h-5 items-center"><input id={`keyword-${kw.keyword}`} type="checkbox" checked={selectedKeywords.includes(kw.keyword)} onChange={() => handleKeywordToggle(kw.keyword)} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"/></div>
                                            <div className="ml-3 text-sm"><label htmlFor={`keyword-${kw.keyword}`} className="font-medium text-slate-700 dark:text-slate-300">{kw.keyword}</label><p className="text-xs text-slate-500 dark:text-slate-400">{kw.reason}</p></div>
                                        </div>
                                    ))}
                                </div>
                             </div>
                             <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
                                <h4 className="text-sm font-semibold">My Keywords</h4>
                                <p className="text-xs text-slate-500 dark:text-slate-400">Add and select your own keywords to weave into your resume.</p>
                                <div className="mt-2 flex gap-2">
                                    <input
                                        type="text"
                                        value={newKeywordInput}
                                        onChange={e => setNewKeywordInput(e.target.value)}
                                        onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddCustomKeyword(); } }}
                                        placeholder="Add a keyword..."
                                        className="w-full p-2 text-sm bg-white dark:bg-slate-700 rounded-md border-slate-300 dark:border-slate-600 focus:ring-blue-500 focus:border-blue-500"
                                    />
                                    <button
                                        type="button"
                                        onClick={handleAddCustomKeyword}
                                        className="px-3 py-1 rounded-md text-sm font-semibold bg-slate-200 dark:bg-slate-600 hover:bg-slate-300 dark:hover:bg-slate-500"
                                    >
                                        Add
                                    </button>
                                </div>
                                <div className="mt-2 space-y-2 max-h-40 overflow-y-auto pr-2">
                                    {customKeywords.map(kw => (
                                        <div key={kw} className="relative flex items-start group">
                                            <div className="flex h-5 items-center">
                                                <input
                                                    id={`custom-keyword-${kw}`}
                                                    type="checkbox"
                                                    checked={selectedKeywords.includes(kw)}
                                                    onChange={() => handleKeywordToggle(kw)}
                                                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                />
                                            </div>
                                            <div className="ml-3 text-sm">
                                                <label htmlFor={`custom-keyword-${kw}`} className="font-medium text-slate-700 dark:text-slate-300">{kw}</label>
                                            </div>
                                            <button 
                                                onClick={() => handleRemoveCustomKeyword(kw)} 
                                                className="absolute right-0 top-0.5 p-0.5 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                                            >
                                                <XCircleIcon className="h-4 w-4" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                         </SectionCard>
                    </div>
                </div>
            </div>

            <div className="flex items-center justify-end space-x-4 pt-6 border-t border-slate-200 dark:border-slate-700">
                 <button type="button" onClick={onNext} disabled={isLoading || selectedSkills.length !== 9} className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-green-400 disabled:cursor-not-allowed transition-colors" title={selectedSkills.length !== 9 ? 'Please select exactly 9 skills to continue' : ''}>
                    {isLoading ? <LoadingSpinner /> : 'Save & Continue'}
                    {!isLoading && <ArrowRightIcon />}
                </button>
            </div>
        </div>
    );
};