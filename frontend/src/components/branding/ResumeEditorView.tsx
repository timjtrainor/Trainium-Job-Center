import React, { useState, useEffect, useRef, useLayoutEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { BaseResume, Resume, WorkExperience, Education, Certification, SkillSection, ResumeAccomplishment, DateInfo, StrategicNarrative, Prompt, CombinedAchievementSuggestion, KeywordDetail, PromptContext, ResumeTailoringData, SkillOptions } from '../../types';
import { LoadingSpinner, PlusCircleIcon, TrashIcon, SparklesIcon, GripVerticalIcon, ArrowDownTrayIcon, CheckIcon } from '../shared/ui/IconComponents';
import { AchievementRefinementPanel } from './AchievementRefinementPanel';
import { SummaryRefinementPanel } from '../SummaryRefinementPanel';
import { CombineAchievementsModal } from './CombineAchievementsModal';
import * as geminiService from '../../services/geminiService';
import { ensureUniqueAchievementIds } from '../../utils/resume';
import { DownloadResumeStep } from './DownloadResumeStep';

interface ResumeEditorViewProps {
    resume: BaseResume | null;
    activeNarrative: StrategicNarrative | null;
    onSave: (resume: BaseResume) => Promise<void>;
    onCancel: () => void;
    onAutoSave: (resume: BaseResume) => Promise<void>;
    isLoading: boolean;
    prompts: Prompt[];
    commonKeywords: string[];
    onSetDefault: (resumeId: string) => void;
}

const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";
const textareaClass = `${inputClass} font-sans`;

const FormSection = ({ title, children, onAdd, addLabel }: { title: string, children: React.ReactNode, onAdd?: () => void, addLabel?: string }) => (
    <div className="space-y-4 pt-6 border-t border-slate-200 dark:border-slate-700 first:pt-0 first:border-t-0">
        <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">{title}</h3>
            {onAdd && addLabel && (
                <button type="button" onClick={onAdd} className="inline-flex items-center gap-x-1.5 rounded-md bg-blue-600 px-2.5 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600">
                    <PlusCircleIcon className="-ml-0.5 h-5 w-5" />
                    {addLabel}
                </button>
            )}
        </div>
        <div className="space-y-4">{children}</div>
    </div>
);

const ArrayItemWrapper = ({ onRemove, children, title }: { onRemove: () => void, children: React.ReactNode, title?: string }) => (
    <div className="relative p-4 border border-slate-300 dark:border-slate-600 rounded-lg bg-slate-50 dark:bg-slate-800/50">
        <div className="absolute top-2 right-2 flex items-center gap-2">
            {title && <span className="text-xs font-semibold text-slate-500">{title}</span>}
            <button type="button" onClick={onRemove} className="p-1 text-slate-400 hover:text-red-500 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700">
                <TrashIcon className="h-5 w-5" />
            </button>
        </div>
        {children}
    </div>
);

// Helper functions to prevent rendering objects in value props
const safeGetString = (val: unknown): string => (typeof val === 'string' ? val : '');
const safeGetNumber = (val: unknown): number | '' => (typeof val === 'number' ? val : '');


export const ResumeEditorView = ({ resume, activeNarrative, onSave, onCancel, onAutoSave, isLoading, prompts, commonKeywords, onSetDefault }: ResumeEditorViewProps): React.ReactNode => {
    const [editableResume, setEditableResume] = useState<BaseResume | null>(null);
    const [editingAchievement, setEditingAchievement] = useState<{ achievement: ResumeAccomplishment, expIndex: number, accIndex: number } | null>(null);
    const [isSummaryPanelOpen, setIsSummaryPanelOpen] = useState(false);
    const [isCombineModalOpen, setIsCombineModalOpen] = useState(false);
    const [combineSuggestions, setCombineSuggestions] = useState<CombinedAchievementSuggestion[]>([]);
    const [editingExperienceIndex, setEditingExperienceIndex] = useState<number | null>(null);
    const [isCombining, setIsCombining] = useState(false);
    const [draggedItem, setDraggedItem] = useState<{ expIdx: number; accIdx: number } | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [showFloatingSave, setShowFloatingSave] = useState(false);

    // State for preview functionality
    const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
    const [isPreviewReady, setIsPreviewReady] = useState(false);
    const [previewJobTitle, setPreviewJobTitle] = useState('');
    const [previewCompanyName, setPreviewCompanyName] = useState('');
    const [previewResume, setPreviewResume] = useState<Resume | null>(null);
    const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            if (window.scrollY > 300) {
                setShowFloatingSave(true);
            } else {
                setShowFloatingSave(false);
            }
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    useEffect(() => {
        if (resume) {
            const deepCopy = JSON.parse(JSON.stringify(resume));
            if (!deepCopy.content) deepCopy.content = {};
            if (!deepCopy.content.work_experience) deepCopy.content.work_experience = [];

            deepCopy.content = ensureUniqueAchievementIds(deepCopy.content);

            (deepCopy.content.work_experience || []).forEach((exp: WorkExperience) => {
                (exp.accomplishments || []).forEach((acc: ResumeAccomplishment, index: number) => {
                    if (acc.original_description === undefined) acc.original_description = acc.description;
                    if (acc.order_index === undefined) acc.order_index = index;
                });
                // Ensure accomplishments are sorted by order_index
                exp.accomplishments.sort((a, b) => a.order_index - b.order_index);
            });
            setEditableResume(deepCopy);
        } else {
            setEditableResume(null);
        }
    }, [resume]);

    // --- State Update Handlers ---

    const handleResumeChange = (updater: (draft: BaseResume) => void) => {
        setEditableResume(prev => {
            if (!prev) return null;
            const newResume = JSON.parse(JSON.stringify(prev));
            updater(newResume);
            return newResume;
        });
    };

    const handleSaveAchievement = (updatedAchievement: ResumeAccomplishment) => {
        if (!editingAchievement) return;
        const { expIndex, accIndex } = editingAchievement;
        handleResumeChange(draft => {
            if (draft.content)
                draft.content.work_experience[expIndex].accomplishments[accIndex] = updatedAchievement;
        });
        setEditingAchievement(null);
    };

    const handleSaveSummary = (newSummary: string) => {
        handleResumeChange(draft => {
            if (draft.content?.summary)
                draft.content.summary.paragraph = newSummary;
        });
    };

    const handleOpenRefinementPanel = (achievement: ResumeAccomplishment, expIndex: number, accIndex: number) => {
        setEditingAchievement({ achievement, expIndex, accIndex });
    };

    const handleSave = async (andExit: boolean = false) => {
        if (!editableResume) return;
        setIsSaving(true);
        setSaveSuccess(false);
        try {
            await onSave(editableResume);
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 2000);
            if (andExit) {
                onCancel(); // Use the onCancel prop to navigate back
            }
        } catch (e) {
            console.error("Save failed", e);
            // Optionally, set an error state to show on the button
        } finally {
            setIsSaving(false);
        }
    };

    // Drag and Drop handlers
    const handleDragStart = (e: React.DragEvent, expIdx: number, accIdx: number) => {
        setDraggedItem({ expIdx, accIdx });
        e.dataTransfer.effectAllowed = 'move';
    };

    const handleDragOver = (e: React.DragEvent) => e.preventDefault();

    const handleDrop = (e: React.DragEvent, targetExpIdx: number, targetAccIdx: number) => {
        e.preventDefault();
        if (!draggedItem || draggedItem.expIdx !== targetExpIdx) {
            setDraggedItem(null);
            return;
        }

        handleResumeChange(draft => {
            const expToUpdate = draft.content?.work_experience[targetExpIdx];
            if (!expToUpdate) return;
            const [removedItem] = expToUpdate.accomplishments.splice(draggedItem.accIdx, 1);
            expToUpdate.accomplishments.splice(targetAccIdx, 0, removedItem);
            // Re-assign order_index after drop
            expToUpdate.accomplishments.forEach((acc, index) => {
                acc.order_index = index;
            });
        });
        setDraggedItem(null);
    };

    const handleCombineClick = async (expIndex: number) => {
        if (!editableResume?.content) return;
        const experience = editableResume.content.work_experience[expIndex];
        if (!experience || experience.accomplishments.length < 2) return;

        setIsCombining(true);
        setEditingExperienceIndex(expIndex);

        try {
            const prompt = prompts.find(p => p.id === 'COMBINE_SIMILAR_ACHIEVEMENTS');
            if (!prompt) throw new Error("Combine achievements prompt not found.");

            const context = {
                ACCOMPLISHMENT_LIST: JSON.stringify(experience.accomplishments.map(a => a.description))
            };
            const result = await geminiService.findAndCombineAchievements(context, prompt.content);
            setCombineSuggestions(result.combinations);
            setIsCombineModalOpen(true);
        } catch (error) {
            console.error("Failed to get combine suggestions", error);
        } finally {
            setIsCombining(false);
        }
    };

    const handleApplyCombinedSuggestion = (suggestionGroup: CombinedAchievementSuggestion, chosenSuggestion: string) => {
        if (editingExperienceIndex === null) return;

        handleResumeChange(draft => {
            const experienceToUpdate = draft.content?.work_experience[editingExperienceIndex];
            if (!experienceToUpdate) return;

            const newAccomplishment: ResumeAccomplishment = {
                achievement_id: uuidv4(),
                description: chosenSuggestion,
                original_description: chosenSuggestion,
                always_include: false,
                order_index: experienceToUpdate.accomplishments.length // Will be re-ordered later
            };
            // Remove old items in reverse index order to avoid shifting
            suggestionGroup.original_indices.sort((a, b) => b - a).forEach(indexToRemove => {
                experienceToUpdate.accomplishments.splice(indexToRemove, 1);
            });
            // Add the new combined one and re-index
            experienceToUpdate.accomplishments.push(newAccomplishment);
            experienceToUpdate.accomplishments.forEach((acc, index) => acc.order_index = index);
        });

        setIsCombineModalOpen(false);
        setCombineSuggestions([]);
        setEditingExperienceIndex(null);
    };

    const handleGeneratePreview = async () => {
        if (!editableResume?.content || !previewJobTitle || !previewCompanyName) {
            // Can set an error state for the modal here
            return;
        }
        setIsGeneratingPreview(true);

        try {
            // Create a direct "what you see is what you get" preview. No AI re-writing.
            const previewContent: Resume = {
                ...editableResume.content,
                header: {
                    ...editableResume.content.header,
                    job_title: previewJobTitle, // Use the sample job title for the header
                },
            };

            setPreviewResume(previewContent);
            setIsPreviewModalOpen(false); // Close the input modal
            setIsPreviewReady(true); // Open the download modal
        } catch (e) {
            console.error("Failed to generate preview:", e);
            alert("Failed to generate preview. Please check console for details.");
        } finally {
            setIsGeneratingPreview(false);
        }
    };

    const commonKeywordsAsResult: KeywordDetail[] = commonKeywords.map(kw => ({
        keyword: kw,
        frequency: 1,
        emphasis: true,
        reason: 'Common from recent applications',
        is_required: false,
        match_strength: 0.8,
        resume_boost: true
    }));

    if (!editableResume || !editableResume.content) {
        return (
            <div className="flex items-center justify-center h-[50vh]">
                <LoadingSpinner />
                <span className="ml-4">Loading resume details...</span>
            </div>
        );
    }

    const isDefault = editableResume?.resume_id === activeNarrative?.default_resume_id;

    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700 animate-fade-in">
            {editingAchievement && (
                <AchievementRefinementPanel
                    isOpen={!!editingAchievement}
                    onClose={() => setEditingAchievement(null)}
                    achievement={editingAchievement.achievement}
                    activeNarrative={activeNarrative}
                    onSave={handleSaveAchievement}
                    prompts={prompts}
                    jobContext={{
                        jobTitle: 'Various Roles',
                        companyName: 'Various Companies',
                        keywords: {
                            hard_keywords: commonKeywordsAsResult,
                            soft_keywords: []
                        }
                    }}
                />
            )}
            {showFloatingSave && (
                <div className="fixed bottom-6 right-6 z-40">
                    <button
                        type="button"
                        onClick={() => handleSave(false)}
                        disabled={isSaving}
                        className={`flex items-center justify-center w-36 h-12 rounded-full shadow-lg transition-colors duration-300 ease-in-out text-white font-semibold focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-900
                            ${saveSuccess ? 'bg-green-600 focus:ring-green-500' : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'}
                            ${isSaving ? 'cursor-not-allowed bg-blue-400' : ''}
                        `}
                        title="Save changes"
                    >
                        {isSaving ? (
                            <>
                                <LoadingSpinner />
                                <span className="ml-2">Saving...</span>
                            </>
                        ) : saveSuccess ? (
                            <>
                                <CheckIcon className="h-6 w-6 text-white" />
                                <span className="ml-2">Saved!</span>
                            </>
                        ) : (
                            <>
                                <ArrowDownTrayIcon className="h-6 w-6" />
                                <span className="ml-2">Save</span>
                            </>
                        )}
                    </button>
                </div>
            )}
            <header className="mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <button onClick={onCancel} className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 mb-2">
                        &larr; Back to Application Lab
                    </button>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Resume Editor</h2>
                </div>
                <div className="flex items-center gap-4">
                    <button
                        type="button"
                        onClick={() => setIsPreviewModalOpen(true)}
                        className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none"
                    >
                        Generate Download Preview
                    </button>
                </div>
            </header>

            <form onSubmit={(e) => { e.preventDefault(); handleSave(true); }}>
                <div className="space-y-6">
                    <FormSection title="Resume Details">
                        <div className="flex items-center gap-4">
                            <div className="flex-grow">
                                <label htmlFor="resume_name" className={labelClass}>Resume Name</label>
                                <input type="text" id="resume_name" value={safeGetString(editableResume.resume_name)} onChange={e => handleResumeChange(draft => { draft.resume_name = e.target.value; })} className={inputClass} />
                            </div>
                            <div className="pt-6">
                                <button
                                    type="button"
                                    onClick={() => editableResume && onSetDefault(editableResume.resume_id)}
                                    disabled={isDefault || isLoading}
                                    className={`inline-flex items-center gap-x-1.5 rounded-md px-3 py-2 text-sm font-semibold shadow-sm ring-1 ring-inset disabled:cursor-not-allowed disabled:opacity-50
                                        ${isDefault
                                            ? 'bg-green-100 text-green-700 ring-green-300 dark:bg-green-900/50 dark:text-green-300 dark:ring-green-700'
                                            : 'bg-white text-gray-900 ring-gray-300 hover:bg-gray-50 dark:bg-slate-700 dark:text-white dark:ring-slate-600 dark:hover:bg-slate-600'}`}
                                >
                                    {isDefault && <CheckIcon className="h-5 w-5 -ml-1" />}
                                    {isDefault ? 'Default' : `Set as Default for ${activeNarrative?.narrative_name}`}
                                </button>
                            </div>
                        </div>
                    </FormSection>

                    <FormSection title="Header Info">
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                            <div><label htmlFor="first_name" className={labelClass}>First Name</label><input type="text" id="first_name" value={safeGetString(editableResume.content.header?.first_name)} onChange={e => handleResumeChange(draft => { if (draft.content?.header) draft.content.header.first_name = e.target.value })} className={inputClass} /></div>
                            <div><label htmlFor="last_name" className={labelClass}>Last Name</label><input type="text" id="last_name" value={safeGetString(editableResume.content.header?.last_name)} onChange={e => handleResumeChange(draft => { if (draft.content?.header) draft.content.header.last_name = e.target.value })} className={inputClass} /></div>
                            <div><label htmlFor="email" className={labelClass}>Email</label><input type="email" id="email" value={safeGetString(editableResume.content.header?.email)} onChange={e => handleResumeChange(draft => { if (draft.content?.header) draft.content.header.email = e.target.value })} className={inputClass} /></div>
                            <div><label htmlFor="phone_number" className={labelClass}>Phone</label><input type="tel" id="phone_number" value={safeGetString(editableResume.content.header?.phone_number)} onChange={e => handleResumeChange(draft => { if (draft.content?.header) draft.content.header.phone_number = e.target.value })} className={inputClass} /></div>
                            <div><label htmlFor="city" className={labelClass}>City</label><input type="text" id="city" value={safeGetString(editableResume.content.header?.city)} onChange={e => handleResumeChange(draft => { if (draft.content?.header) draft.content.header.city = e.target.value })} className={inputClass} /></div>
                            <div><label htmlFor="state" className={labelClass}>State</label><input type="text" id="state" value={safeGetString(editableResume.content.header?.state)} onChange={e => handleResumeChange(draft => { if (draft.content?.header) draft.content.header.state = e.target.value })} className={inputClass} /></div>
                            <div className="sm:col-span-2"><label htmlFor="links" className={labelClass}>Links (one per line)</label><textarea id="links" rows={3} value={(Array.isArray(editableResume.content.header?.links) ? editableResume.content.header.links.filter(l => typeof l === 'string') : []).join('\n')} onChange={e => handleResumeChange(draft => { if (draft.content?.header) draft.content.header.links = e.target.value.split('\n') })} className={textareaClass} /></div>
                        </div>
                    </FormSection>

                    <FormSection title="Summary">
                        <div className="flex justify-between items-center"><label htmlFor="summary" className={labelClass}>Summary Paragraph</label><button type="button" onClick={() => setIsSummaryPanelOpen(true)} className="p-1 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200" title="Refine with AI"><SparklesIcon className="w-5 h-5" /></button></div>
                        <textarea id="summary" rows={4} value={safeGetString(editableResume.content.summary?.paragraph)} onChange={e => handleSaveSummary(e.target.value)} className={textareaClass} />
                    </FormSection>

                    <FormSection title="Work Experience" onAdd={() => handleResumeChange(draft => draft.content?.work_experience.push({ company_name: '', job_title: '', location: '', start_date: { month: 1, year: 2024 }, end_date: { month: 1, year: 2024 }, is_current: false, filter_accomplishment_count: 3, accomplishments: [] }))} addLabel="Add Experience">
                        {(Array.isArray(editableResume.content.work_experience) ? editableResume.content.work_experience : []).map((exp, expIdx) => {
                            if (typeof exp !== 'object' || !exp) return null;
                            return (
                                <ArrayItemWrapper key={expIdx} onRemove={() => handleResumeChange(draft => { draft.content?.work_experience.splice(expIdx, 1) })}>
                                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-6">
                                        <div className="sm:col-span-3"><label className={labelClass}>Company</label><input type="text" value={safeGetString(exp.company_name)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.work_experience[expIdx].company_name = e.target.value })} className={inputClass} /></div>
                                        <div className="sm:col-span-3"><label className={labelClass}>Job Title</label><input type="text" value={safeGetString(exp.job_title)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.work_experience[expIdx].job_title = e.target.value })} className={inputClass} /></div>
                                        <div className="sm:col-span-2"><label className={labelClass}>Location</label><input type="text" value={safeGetString(exp.location)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.work_experience[expIdx].location = e.target.value })} className={inputClass} /></div>
                                        <div className="sm:col-span-2"><label className={labelClass}>Accomplishments to Show</label><input type="number" value={safeGetNumber(exp.filter_accomplishment_count)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.work_experience[expIdx].filter_accomplishment_count = parseInt(e.target.value, 10) || 0 })} className={inputClass} /></div>
                                        <div className="sm:col-span-2 flex items-end pb-1"><div className="relative flex items-start"><div className="flex h-6 items-center"><input id={`current-${expIdx}`} type="checkbox" checked={exp.is_current} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.work_experience[expIdx].is_current = e.target.checked })} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" /></div><div className="ml-3 text-sm leading-6"><label htmlFor={`current-${expIdx}`} className={labelClass}>Current</label></div></div></div>
                                        <div className="sm:col-span-3 grid grid-cols-2 gap-2"><label className={`${labelClass} col-span-2`}>Start Date</label><input type="number" placeholder="MM" value={safeGetNumber(exp.start_date?.month)} onChange={e => handleResumeChange(draft => { if (draft.content?.work_experience[expIdx].start_date) draft.content.work_experience[expIdx].start_date.month = parseInt(e.target.value) })} className={inputClass} /><input type="number" placeholder="YYYY" value={safeGetNumber(exp.start_date?.year)} onChange={e => handleResumeChange(draft => { if (draft.content?.work_experience[expIdx].start_date) draft.content.work_experience[expIdx].start_date.year = parseInt(e.target.value) })} className={inputClass} /></div>
                                        <div className="sm:col-span-3 grid grid-cols-2 gap-2"><label className={`${labelClass} col-span-2`}>End Date</label><input type="number" placeholder="MM" disabled={exp.is_current} value={safeGetNumber(exp.end_date?.month)} onChange={e => handleResumeChange(draft => { if (draft.content?.work_experience[expIdx].end_date) draft.content.work_experience[expIdx].end_date.month = parseInt(e.target.value) })} className={`${inputClass} disabled:bg-slate-100 dark:disabled:bg-slate-700`} /><input type="number" placeholder="YYYY" disabled={exp.is_current} value={safeGetNumber(exp.end_date?.year)} onChange={e => handleResumeChange(draft => { if (draft.content?.work_experience[expIdx].end_date) draft.content.work_experience[expIdx].end_date.year = parseInt(e.target.value) })} className={`${inputClass} disabled:bg-slate-100 dark:disabled:bg-slate-700`} /></div>

                                        <div className="sm:col-span-6">
                                            <FormSection title="Accomplishments">
                                                <div className="flex justify-end -mt-12 mb-2"><button type="button" onClick={() => handleCombineClick(expIdx)} disabled={isCombining || (exp.accomplishments || []).length < 2} className="inline-flex items-center gap-x-1.5 rounded-md bg-indigo-50 dark:bg-indigo-500/10 px-2.5 py-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 ring-1 ring-inset ring-indigo-200 dark:ring-indigo-500/30 hover:bg-indigo-100 dark:hover:bg-indigo-500/20 disabled:opacity-50">{isCombining ? <LoadingSpinner /> : <SparklesIcon className="h-4 w-4" />} Combine Similar</button></div>
                                                <div className="space-y-2">
                                                    {(Array.isArray(exp.accomplishments) ? exp.accomplishments : []).map((acc, accIdx) => {
                                                        if (typeof acc !== 'object' || !acc) return null;
                                                        return (
                                                            <div key={acc.achievement_id} draggable onDragStart={(e) => handleDragStart(e, expIdx, accIdx)} onDragEnd={() => setDraggedItem(null)} onDragOver={handleDragOver} onDrop={(e) => handleDrop(e, expIdx, accIdx)} className={`flex items-start gap-2 rounded-lg transition-opacity ${draggedItem?.expIdx === expIdx && draggedItem?.accIdx === accIdx ? 'opacity-50' : ''}`}>
                                                                <div className="cursor-grab text-slate-400 pt-5"><GripVerticalIcon className="w-5 h-5" /></div>
                                                                <div className="flex-grow"><ArrayItemWrapper onRemove={() => handleResumeChange(draft => { draft.content?.work_experience[expIdx].accomplishments.splice(accIdx, 1) })} >
                                                                    <div className="space-y-2"><label className={labelClass}>Description</label><textarea rows={3} value={safeGetString(acc.description)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.work_experience[expIdx].accomplishments[accIdx].description = e.target.value })} className={textareaClass} />
                                                                        {acc.score && typeof acc.score.overall_score === 'number' && (<div className="flex items-center gap-x-4 text-xs text-slate-500 dark:text-slate-400 p-2 bg-slate-100 dark:bg-slate-900/50 rounded-md"><strong className="text-slate-600 dark:text-slate-300">AI Score:</strong><span>Overall: <span className="font-semibold">{acc.score.overall_score.toFixed(1)}</span></span><span>Clarity: <span className="font-semibold">{acc.score.clarity.toFixed(1)}</span></span><span>Drama: <span className="font-semibold">{acc.score.drama.toFixed(1)}</span></span></div>)}
                                                                        <div className="flex justify-between items-center"><div className="flex gap-4">
                                                                            <div className="relative flex items-start"><div className="flex h-6 items-center"><input id={`always-${expIdx}-${accIdx}`} type="checkbox" checked={acc.always_include} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.work_experience[expIdx].accomplishments[accIdx].always_include = e.target.checked })} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" /></div><div className="ml-3 text-sm leading-6"><label htmlFor={`always-${expIdx}-${accIdx}`} className={labelClass}>Always Include</label></div></div>
                                                                        </div><button type="button" onClick={() => handleOpenRefinementPanel(acc, expIdx, accIdx)} className="inline-flex items-center gap-x-1 text-sm font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-500"><SparklesIcon className="h-4 w-4" />Refine</button></div>
                                                                    </div>
                                                                </ArrayItemWrapper></div>
                                                            </div>
                                                        )
                                                    })}
                                                </div>
                                                <div className="mt-4 flex justify-center"><button type="button" onClick={() => handleResumeChange(draft => draft.content?.work_experience[expIdx].accomplishments.push({ achievement_id: uuidv4(), description: '', always_include: false, order_index: (draft.content?.work_experience[expIdx].accomplishments.length || 0) }))} className="inline-flex items-center gap-x-1.5 rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600"><PlusCircleIcon className="-ml-0.5 h-5 w-5" /> Add Accomplishment</button></div>
                                            </FormSection>
                                        </div>
                                    </div>
                                </ArrayItemWrapper>
                            );
                        })}
                    </FormSection>

                    <FormSection title="Education" onAdd={() => handleResumeChange(draft => draft.content?.education.push({ school: '', location: '', degree: '', major: [], minor: [], start_month: 1, start_year: 2024, end_month: 1, end_year: 2024 }))} addLabel="Add Education">
                        {(Array.isArray(editableResume.content.education) ? editableResume.content.education : []).map((edu, idx) => {
                            if (typeof edu !== 'object' || !edu) return null;
                            return (
                                <ArrayItemWrapper key={idx} onRemove={() => handleResumeChange(draft => { draft.content?.education.splice(idx, 1) })}><div className="grid grid-cols-1 gap-4 sm:grid-cols-6">
                                    <div className="sm:col-span-3"><label className={labelClass}>School</label><input type="text" value={safeGetString(edu.school)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.education[idx].school = e.target.value })} className={inputClass} /></div>
                                    <div className="sm:col-span-3"><label className={labelClass}>Location</label><input type="text" value={safeGetString(edu.location)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.education[idx].location = e.target.value })} className={inputClass} /></div>
                                    <div className="sm:col-span-6"><label className={labelClass}>Degree</label><input type="text" value={safeGetString(edu.degree)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.education[idx].degree = e.target.value })} className={inputClass} /></div>
                                    <div className="sm:col-span-3"><label className={labelClass}>Major(s) (comma separated)</label><input type="text" value={(Array.isArray(edu.major) ? edu.major.filter(i => typeof i === 'string') : []).join(', ')} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.education[idx].major = e.target.value.split(',').map(s => s.trim()) })} className={inputClass} /></div>
                                    <div className="sm:col-span-3"><label className={labelClass}>Minor(s) (comma separated)</label><input type="text" value={(Array.isArray(edu.minor) ? edu.minor.filter(i => typeof i === 'string') : []).join(', ')} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.education[idx].minor = e.target.value.split(',').map(s => s.trim()) })} className={inputClass} /></div>
                                    <div className="sm:col-span-3 grid grid-cols-2 gap-2">
                                        <label className={`${labelClass} col-span-2`}>Start Date</label>
                                        <input type="number" placeholder="MM" value={safeGetNumber(edu.start_month)} onChange={e => handleResumeChange(draft => { if (draft.content?.education[idx]) draft.content.education[idx].start_month = parseInt(e.target.value, 10) })} className={inputClass} />
                                        <input type="number" placeholder="YYYY" value={safeGetNumber(edu.start_year)} onChange={e => handleResumeChange(draft => { if (draft.content?.education[idx]) draft.content.education[idx].start_year = parseInt(e.target.value, 10) })} className={inputClass} />
                                    </div>
                                    <div className="sm:col-span-3 grid grid-cols-2 gap-2">
                                        <label className={`${labelClass} col-span-2`}>End Date</label>
                                        <input type="number" placeholder="MM" value={safeGetNumber(edu.end_month)} onChange={e => handleResumeChange(draft => { if (draft.content?.education[idx]) draft.content.education[idx].end_month = parseInt(e.target.value, 10) })} className={inputClass} />
                                        <input type="number" placeholder="YYYY" value={safeGetNumber(edu.end_year)} onChange={e => handleResumeChange(draft => { if (draft.content?.education[idx]) draft.content.education[idx].end_year = parseInt(e.target.value, 10) })} className={inputClass} />
                                    </div>
                                </div></ArrayItemWrapper>
                            )
                        })}
                    </FormSection>

                    <FormSection title="Certifications" onAdd={() => handleResumeChange(draft => draft.content?.certifications.push({ name: '', organization: '', link: '', issued_date: '2024-01-01' }))} addLabel="Add Certification">
                        {(Array.isArray(editableResume.content.certifications) ? editableResume.content.certifications : []).map((cert, idx) => {
                            if (typeof cert !== 'object' || !cert) return null;
                            return (
                                <ArrayItemWrapper key={idx} onRemove={() => handleResumeChange(draft => { draft.content?.certifications.splice(idx, 1) })}><div className="grid grid-cols-1 gap-4 sm:grid-cols-6">
                                    <div className="sm:col-span-3"><label className={labelClass}>Name</label><input type="text" value={safeGetString(cert.name)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.certifications[idx].name = e.target.value })} className={inputClass} /></div>
                                    <div className="sm:col-span-3"><label className={labelClass}>Organization</label><input type="text" value={safeGetString(cert.organization)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.certifications[idx].organization = e.target.value })} className={inputClass} /></div>
                                    <div className="sm:col-span-3"><label className={labelClass}>Date Issued (YYYY-MM-DD)</label><input type="text" placeholder="YYYY-MM-DD" value={safeGetString(cert.issued_date)} onChange={e => handleResumeChange(draft => { if (draft.content?.certifications[idx]) draft.content.certifications[idx].issued_date = e.target.value })} className={inputClass} /></div>
                                    <div className="sm:col-span-3"><label className={labelClass}>Link</label><input type="url" value={safeGetString(cert.link)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.certifications[idx].link = e.target.value })} className={inputClass} /></div>
                                </div></ArrayItemWrapper>
                            )
                        })}
                    </FormSection>

                    <FormSection title="Skills" onAdd={() => handleResumeChange(draft => draft.content?.skills.push({ heading: '', items: [] }))} addLabel="Add Skill Section">
                        {(Array.isArray(editableResume.content.skills) ? editableResume.content.skills : []).map((skill, idx) => {
                            if (typeof skill !== 'object' || !skill) return null;
                            return (
                                <ArrayItemWrapper key={idx} onRemove={() => handleResumeChange(draft => { draft.content?.skills.splice(idx, 1) })}><div className="grid grid-cols-1 gap-4 sm:grid-cols-6">
                                    <div className="sm:col-span-6"><label className={labelClass}>Heading</label><input type="text" value={safeGetString(skill.heading)} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.skills[idx].heading = e.target.value })} className={inputClass} /></div>
                                    <div className="sm:col-span-6"><label className={labelClass}>Items (comma separated)</label><textarea rows={3} value={(Array.isArray(skill.items) ? skill.items.filter(i => typeof i === 'string') : []).join(', ')} onChange={e => handleResumeChange(draft => { if (draft.content) draft.content.skills[idx].items = e.target.value.split(',').map(s => s.trim()) })} className={textareaClass} /></div>
                                </div></ArrayItemWrapper>
                            )
                        })}
                    </FormSection>
                </div>
                <div className="mt-8 pt-6 border-t border-slate-200 dark:border-slate-700 flex justify-end items-center gap-4">
                    <button type="button" onClick={onCancel} className="px-4 py-2 text-sm font-medium rounded-lg text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 border border-slate-300 dark:border-slate-500 shadow-sm transition-colors">Cancel</button>
                    <button type="submit" className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">{isLoading || isSaving ? <LoadingSpinner /> : 'Save & Exit'}</button>
                </div>
            </form>
            {editableResume.content.summary && <SummaryRefinementPanel isOpen={isSummaryPanelOpen} onClose={() => setIsSummaryPanelOpen(false)} summary={safeGetString(editableResume.content.summary?.paragraph)} resume={editableResume.content} activeNarrative={activeNarrative} onSave={handleSaveSummary} prompts={prompts} />}
            {editingExperienceIndex !== null && (<CombineAchievementsModal isOpen={isCombineModalOpen} onClose={() => setIsCombineModalOpen(false)} suggestions={combineSuggestions} onApplySuggestion={handleApplyCombinedSuggestion} originalAccomplishments={((editableResume.content.work_experience[editingExperienceIndex] || {}).accomplishments || []).map(a => a.description)} />)}

            {isPreviewModalOpen && (
                <div className="relative z-[80]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
                    <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                        <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                            <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                                <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                                    <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">Generate Download Preview</h3>
                                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Enter a sample job title and company to generate a tailored resume preview.</p>
                                    <div className="mt-4 space-y-4">
                                        <div>
                                            <label htmlFor="preview-company" className={labelClass}>Company Name</label>
                                            <input type="text" id="preview-company" value={previewCompanyName} onChange={(e) => setPreviewCompanyName(e.target.value)} className={inputClass} />
                                        </div>
                                        <div>
                                            <label htmlFor="preview-title" className={labelClass}>Job Title</label>
                                            <input type="text" id="preview-title" value={previewJobTitle} onChange={(e) => setPreviewJobTitle(e.target.value)} className={inputClass} />
                                        </div>
                                    </div>
                                </div>
                                <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                                    <button type="button" onClick={handleGeneratePreview} disabled={isGeneratingPreview || !previewCompanyName || !previewJobTitle} className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 sm:ml-3 sm:w-auto disabled:opacity-50">
                                        {isGeneratingPreview ? <LoadingSpinner /> : 'Generate'}
                                    </button>
                                    <button type="button" onClick={() => setIsPreviewModalOpen(false)} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto">
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            {isPreviewReady && previewResume && (
                <div className="relative z-[80]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
                    <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                        <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                            <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl">
                                <div className="p-4 sm:p-6">
                                    <DownloadResumeStep
                                        finalResume={previewResume}
                                        companyName={previewCompanyName}
                                        isLoading={false}
                                        onClose={() => setIsPreviewReady(false)}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};