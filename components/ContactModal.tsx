import React, { useState, useEffect } from 'react';
import { Contact, Company, ContactPayload, BaseResume, Prompt, JobApplication, MessagePayload, PromptContext, Resume, DateInfo, ContactPersona, LinkedInPost, UserProfile, Education, Certification, StrategicNarrative, BrandVoiceAnalysis } from '../types';
import { LoadingSpinner, CheckIcon, SparklesIcon, TrashIcon } from './IconComponents';
import * as geminiService from '../services/geminiService';
import { CONTACT_PERSONAS } from '../constants';

interface ContactModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSaveContact: (contactData: Partial<Contact>) => Promise<Contact>;
    onCreateMessage: (messageData: MessagePayload) => Promise<void>;
    onAddNewCompany: () => void;
    contact: Partial<Contact> | null;
    companies: Company[];
    applications: JobApplication[];
    baseResumes: BaseResume[];
    linkedInPosts: LinkedInPost[];
    userProfile: UserProfile | null;
    strategicNarratives: StrategicNarrative[];
    activeNarrativeId: string | null;
    prompts: Prompt[];
    onDeleteContact?: (contactId: string) => Promise<void>;
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
}

const contactStatuses = ['To Contact', 'Initial Outreach', 'In Conversation', 'Follow-up Needed', 'Not a Fit', 'No Response'];

type ComposerGoal = 'Initial Connection' | 'Follow-up' | 'Reply to Interaction' | 'Comment on Post';
type CommentTone = 'Standard' | 'Expertise-Driven';

export const ContactModal = (props: ContactModalProps): React.ReactNode => {
    const { 
        isOpen, onClose, onSaveContact, onCreateMessage, onAddNewCompany, contact, 
        companies, applications, userProfile, prompts, debugCallbacks, onDeleteContact,
        strategicNarratives, activeNarrativeId
    } = props;
    
    const activeNarrative = strategicNarratives.find(n => n.narrative_id === activeNarrativeId);

    const [editableContact, setEditableContact] = useState<Partial<Contact>>({});
    
    // AI Composer State
    const [isGenerating, setIsGenerating] = useState(false);
    const [generationError, setGenerationError] = useState<string | null>(null);
    const [generatedMessages, setGeneratedMessages] = useState<string[]>([]);
    
    // Composer Context State
    const [composerGoal, setComposerGoal] = useState<ComposerGoal>('Initial Connection');
    const [commentTone, setCommentTone] = useState<CommentTone>('Standard');
    const [includeMission, setIncludeMission] = useState(false);
    const [includeValues, setIncludeValues] = useState(false);
    const [includeProblem, setIncludeProblem] = useState(true);
    const [interactionDetails, setInteractionDetails] = useState('');
    const [userNotes, setUserNotes] = useState('');

    // Message Composer State
    const [composerText, setComposerText] = useState('');
    const [messageType, setMessageType] = useState<'Connection' | 'Follow-up' | 'Comment' | 'Note'>('Note');
    const [followUpDate, setFollowUpDate] = useState('');
    const [isSending, setIsSending] = useState(false);

    // Form submission state
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [isCalculatingFit, setIsCalculatingFit] = useState(false);
    
    // Brand Voice Analysis State
    const [brandVoiceAnalysis, setBrandVoiceAnalysis] = useState<BrandVoiceAnalysis | null>(null);
    const [isAnalyzingVoice, setIsAnalyzingVoice] = useState(false);


    useEffect(() => {
        if (isOpen) {
            const defaults = {
                first_name: '', last_name: '', job_title: '', status: 'To Contact',
                date_contacted: new Date().toISOString().split('T')[0], is_referral: false, messages: [],
                narrative_ids: activeNarrativeId ? [activeNarrativeId] : [],
            };
             const contactNarrativeIds = contact?.strategic_narratives?.map(n => n.narrative_id) || [];
            
            setEditableContact(contact ? { ...defaults, ...contact, narrative_ids: contactNarrativeIds } : defaults);
            
            // Reset all states on open
            setSaveError(null);
            setIsSaving(false);
            setSaveSuccess(false);
            setIsSending(false);
            setComposerText('');
            setFollowUpDate('');
            setMessageType('Note');
            setGeneratedMessages([]);
            setGenerationError(null);
            setIsGenerating(false);
            setComposerGoal('Initial Connection');
            setCommentTone('Standard');
            setIncludeMission(false);
            setIncludeValues(false);
            setIncludeProblem(true);
            setInteractionDetails('');
            setUserNotes('');
            setBrandVoiceAnalysis(null);
            setIsAnalyzingVoice(false);
        }
    }, [isOpen, contact, activeNarrativeId]);

    if (!isOpen) return null;
    
    const handleGenerate = async () => {
        setIsGenerating(true);
        setGenerationError(null);
        setGeneratedMessages([]);
        
        try {
            if (composerGoal === 'Comment on Post') {
                const promptId = commentTone === 'Expertise-Driven' ? 'GENERATE_EXPERT_COMMENT' : 'GENERATE_STRATEGIC_COMMENT';
                const prompt = prompts.find(p => p.id === promptId);
                if (!prompt || !activeNarrative) {
                    throw new Error(`Prompt '${promptId}' or active narrative is not available.`);
                }
                const context: PromptContext = {
                    POST_TEXT: interactionDetails,
                    NORTH_STAR: activeNarrative.positioning_statement,
                    MASTERY: activeNarrative.signature_capability,
                };
                const comments = await geminiService.generateStrategicComment(context, prompt.content, debugCallbacks);
                setGeneratedMessages(comments);

            } else {
                const prompt = prompts.find(p => p.id === 'GENERATE_STRATEGIC_MESSAGE');
                if (!prompt || !activeNarrative) {
                    throw new Error('Strategic messaging prompt or active narrative is not available.');
                }

                const contactCompany = companies.find(c => c.company_id === editableContact.company_id);
                const linkedApp = applications.find(app => app.job_application_id === editableContact.job_application_id);

                const context: PromptContext = {
                    GOAL: composerGoal,
                    MY_SUMMARY: activeNarrative.positioning_statement || activeNarrative.impact_story_body,
                    COMPANY_NAME: contactCompany?.company_name,
                    CONTACT_PERSONA: editableContact.persona,
                    CONTACT_FIRST_NAME: editableContact.first_name,
                    CONTACT_LINKEDIN_ABOUT: editableContact.linkedin_about,
                    MISSION: includeMission ? contactCompany?.mission?.text : undefined,
                    VALUES: includeValues ? contactCompany?.values?.text : undefined,
                    COMPANY_PROBLEM: includeProblem ? (linkedApp?.job_problem_analysis_result?.core_problem_analysis.core_problem || contactCompany?.issues?.text) : undefined,
                    INTERACTION_DETAILS: composerGoal === 'Reply to Interaction' ? interactionDetails : undefined,
                    USER_NOTES: userNotes,
                    // Strategic Context
                    NORTH_STAR: activeNarrative?.positioning_statement,
                    MASTERY: activeNarrative?.signature_capability,
                    NARRATIVE: activeNarrative?.impact_story_body,
                };
                
                const messages = await geminiService.generateStrategicMessage(context, prompt.content, debugCallbacks);
                setGeneratedMessages(messages);
            }
        } catch (e) {
            setGenerationError(e instanceof Error ? e.message : "Failed to generate content.");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCalculateFit = async () => {
        const selectedNarrativeIds = editableContact.narrative_ids || [];

        if (selectedNarrativeIds.length !== 1) {
            setSaveError("Please select exactly one narrative to calculate a fit score against.");
            return;
        }

        const narrativeForFit = strategicNarratives.find(n => n.narrative_id === selectedNarrativeIds[0]);
        const prompt = prompts.find(p => p.id === 'SCORE_CONTACT_FIT');

        if (!prompt || !narrativeForFit) {
            setSaveError("Cannot calculate fit: Active narrative or required prompt is missing.");
            return;
        }

        setIsCalculatingFit(true);
        setSaveError(null);
        try {
             const context: PromptContext = {
                POSITIONING_STATEMENT: narrativeForFit.positioning_statement,
                MASTERY: narrativeForFit.signature_capability,
                CONTACT_JOB_TITLE: editableContact.job_title,
                CONTACT_PERSONA: editableContact.persona,
                COMPANY_NAME: companies.find(c => c.company_id === editableContact.company_id)?.company_name,
                CONTACT_LINKEDIN_ABOUT: editableContact.linkedin_about,
            };
            const result = await geminiService.scoreContactFit(context, prompt.content, debugCallbacks);
            setEditableContact(prev => ({...prev, strategic_alignment_score: result.strategic_fit_score ? Math.round(result.strategic_fit_score) : undefined }));
        } catch(err) {
            setSaveError(err instanceof Error ? err.message : 'Failed to calculate fit score.');
        } finally {
            setIsCalculatingFit(false);
        }
    };

    const handleAnalyzeBrandVoice = async () => {
        if (!composerText.trim() || !activeNarrative) {
            setGenerationError("Please write a message draft and ensure your positioning profile is complete.");
            return;
        }
        const prompt = prompts.find(p => p.id === 'ANALYZE_BRAND_VOICE');
        if (!prompt) {
            setGenerationError("Brand voice analysis prompt is not available.");
            return;
        }
        setIsAnalyzingVoice(true);
        setGenerationError(null);
        setBrandVoiceAnalysis(null);

        try {
            const context: PromptContext = {
                POSITIONING_STATEMENT: activeNarrative.positioning_statement,
                MASTERY: activeNarrative.signature_capability,
                MESSAGE_DRAFT: composerText,
            };
            const result = await geminiService.analyzeBrandVoice(context, prompt.content, debugCallbacks);
            setBrandVoiceAnalysis(result);
        } catch(err) {
            setGenerationError(err instanceof Error ? err.message : 'Failed to analyze brand voice.');
        } finally {
            setIsAnalyzingVoice(false);
        }
    };


    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        const isCheckbox = type === 'checkbox';
        setSaveSuccess(false); // Reset save success on any change
        setEditableContact(prev => ({ 
            ...prev, 
            [name]: isCheckbox ? (e.target as HTMLInputElement).checked : (value || undefined)
        }));
    };

    const handleNarrativeChange = (narrativeId: string, isChecked: boolean) => {
        setEditableContact(prev => {
            const currentIds = prev.narrative_ids || [];
            if (isChecked) {
                return { ...prev, narrative_ids: [...currentIds, narrativeId] };
            } else {
                return { ...prev, narrative_ids: currentIds.filter(id => id !== narrativeId) };
            }
        });
    };

    const handleSaveDetails = async (closeOnSuccess: boolean) => {
        if (!editableContact.first_name || !editableContact.last_name) {
            setSaveError('First and last name are required.');
            return;
        }
        setIsSaving(true);
        setSaveError(null);
        setSaveSuccess(false);
        try {
            const payload = { ...editableContact };
            if (payload.company_id === '') payload.company_id = undefined;
            if (payload.job_application_id === '') payload.job_application_id = undefined;

            const savedContact = await onSaveContact(payload);
            // This is the crucial fix: update the local state with the full object
            // returned from the API, which now includes the contact_id.
            setEditableContact(savedContact);
            
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 3000);
            if(closeOnSuccess) onClose();

        } catch (err) {
            setSaveError(err instanceof Error ? err.message : 'Failed to save contact.');
        } finally {
            setIsSaving(false);
        }
    };
    
    const handleSendMessage = async () => {
        if (!composerText.trim()) return;
        setIsSending(true);
        try {
            await onCreateMessage({
                contact_id: editableContact?.contact_id,
                company_id: editableContact.company_id,
                job_application_id: editableContact.job_application_id,
                content: composerText,
                message_type: messageType,
                is_user_sent: messageType !== 'Note',
                follow_up_due_date: messageType === 'Follow-up' ? followUpDate : undefined,
            });
            // Reset composer state
            setComposerText('');
            setGeneratedMessages([]);
            setFollowUpDate('');
            setMessageType('Note');
            setBrandVoiceAnalysis(null);
        } catch (e) {
            setSaveError("Failed to save message.");
        } finally {
            setIsSending(false);
        }
    };
    
    const handleDelete = async () => {
        if (onDeleteContact && editableContact.contact_id) {
            if(window.confirm("Are you sure you want to permanently delete this contact and all their messages? This action cannot be undone.")) {
                try {
                    setIsSaving(true);
                    setSaveError(null);
                    await onDeleteContact(editableContact.contact_id);
                    onClose();
                } catch(err) {
                    setSaveError(err instanceof Error ? err.message : "Failed to delete contact.");
                } finally {
                    setIsSaving(false);
                }
            }
        }
    };

    const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
    const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                {contact?.contact_id ? 'Edit Contact & Engage' : 'Add New Contact & Engage'}
                            </h3>
                            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-6 max-h-[80vh] overflow-y-auto p-1">
                               {/* Left: Details Form */}
                               <div className="space-y-4 pr-4 border-r-0 md:border-r border-slate-200 dark:border-slate-700">
                                    <form onSubmit={(e) => { e.preventDefault(); handleSaveDetails(false); }} className="space-y-4">
                                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                                            <div><label htmlFor="first_name" className={labelClass}>First Name *</label><input type="text" name="first_name" id="first_name" value={editableContact.first_name || ''} onChange={handleChange} className={inputClass} required /></div>
                                            <div><label htmlFor="last_name" className={labelClass}>Last Name *</label><input type="text" name="last_name" id="last_name" value={editableContact.last_name || ''} onChange={handleChange} className={inputClass} required /></div>
                                        </div>
                                        <div><label htmlFor="job_title" className={labelClass}>Job Title</label><input type="text" name="job_title" id="job_title" value={editableContact.job_title || ''} onChange={handleChange} className={inputClass} /></div>
                                        <div><label htmlFor="linkedin_url" className={labelClass}>LinkedIn Profile URL</label><input type="url" name="linkedin_url" id="linkedin_url" value={editableContact.linkedin_url || ''} onChange={handleChange} className={inputClass} /></div>
                                        <div><label htmlFor="linkedin_about" className={labelClass}>LinkedIn About Section (Optional)</label><textarea name="linkedin_about" id="linkedin_about" value={editableContact.linkedin_about || ''} onChange={handleChange} rows={2} className={inputClass} placeholder="Paste their 'About' section for more personalized AI generation." /></div>
                                        <div>
                                            <label htmlFor="persona" className={labelClass}>Contact Persona</label>
                                            <select name="persona" id="persona" value={editableContact.persona || ''} onChange={handleChange} className={inputClass}><option value="">-- Select --</option>{CONTACT_PERSONAS.map(p => <option key={p.type} value={p.type}>{p.type}</option>)}</select>
                                        </div>
                                         <div>
                                            <div className="flex justify-between items-center"><label htmlFor="company_id" className={labelClass}>Company</label><button type="button" onClick={onAddNewCompany} className="text-xs font-semibold text-blue-600 hover:text-blue-500">Add New</button></div>
                                            <select name="company_id" id="company_id" value={editableContact.company_id || ''} onChange={handleChange} className={inputClass}><option value="">-- Select --</option>{companies.map(c => <option key={c.company_id} value={c.company_id}>{c.company_name}</option>)}</select>
                                        </div>
                                        <div>
                                            <label htmlFor="job_application_id" className={labelClass}>Related Job Application</label>
                                            <select name="job_application_id" id="job_application_id" value={editableContact.job_application_id || ''} onChange={handleChange} className={inputClass}>
                                                <option value="">-- None --</option>
                                                {applications.map(app => <option key={app.job_application_id} value={app.job_application_id}>{companies.find(c => c.company_id === app.company_id)?.company_name} - {app.job_title}</option>)}
                                            </select>
                                        </div>
                                         <div className="space-y-2">
                                            <label className={labelClass}>Strategic Narratives</label>
                                            <div className="flex flex-col sm:flex-row gap-4">
                                                {strategicNarratives.map(n => (
                                                    <div key={n.narrative_id} className="relative flex items-start">
                                                        <div className="flex h-6 items-center">
                                                            <input
                                                                id={`narrative-${n.narrative_id}`}
                                                                type="checkbox"
                                                                checked={editableContact.narrative_ids?.includes(n.narrative_id) || false}
                                                                onChange={(e) => handleNarrativeChange(n.narrative_id, e.target.checked)}
                                                                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                            />
                                                        </div>
                                                        <div className="ml-3 text-sm leading-6">
                                                            <label htmlFor={`narrative-${n.narrative_id}`} className="font-medium text-slate-700 dark:text-slate-300">
                                                                {n.narrative_name}
                                                            </label>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700 space-y-2">
                                            <label className={labelClass}>Strategic Fit</label>
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center">
                                                    <div className="w-24 bg-slate-200 dark:bg-slate-700 rounded-full h-2.5">
                                                        <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${(editableContact.strategic_alignment_score || 0) * 10}%` }}></div>
                                                    </div>
                                                    <span className="ml-3 font-bold text-lg text-slate-800 dark:text-slate-200">{(editableContact.strategic_alignment_score || 0).toFixed(1)}</span>
                                                </div>
                                                <button type="button" onClick={handleCalculateFit} disabled={isCalculatingFit} className="inline-flex items-center gap-x-1.5 rounded-md bg-blue-50 dark:bg-blue-500/10 px-2.5 py-1.5 text-xs font-semibold text-blue-600 dark:text-blue-400 ring-1 ring-inset ring-blue-200 dark:ring-blue-500/30 hover:bg-blue-100 dark:hover:bg-blue-500/20 disabled:opacity-50">
                                                    {isCalculatingFit ? <LoadingSpinner/> : <SparklesIcon className="h-4 w-4" />}
                                                    Calculate Fit with AI
                                                </button>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                            <div><label htmlFor="status" className={labelClass}>Status</label><select name="status" id="status" value={editableContact.status || ''} onChange={handleChange} className={inputClass}>{contactStatuses.map(s => <option key={s} value={s}>{s}</option>)}</select></div>
                                            <div className="flex items-end pb-1"><div className="flex items-center"><input id="is_referral" name="is_referral" type="checkbox" checked={editableContact.is_referral || false} onChange={handleChange} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" /><label htmlFor="is_referral" className={`${labelClass} ml-2`}>Referral</label></div></div>
                                        </div>
                                        <div><label htmlFor="notes" className={labelClass}>Notes</label><textarea name="notes" id="notes" value={editableContact.notes || ''} onChange={handleChange} rows={2} className={inputClass}></textarea></div>
                                        
                                        <div className="flex justify-end pt-2">
                                            <button type="submit" disabled={isSaving || saveSuccess} className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md text-white shadow-sm transition-colors bg-green-600 hover:bg-green-700 disabled:bg-green-400">
                                                {isSaving ? <LoadingSpinner/> : saveSuccess ? <CheckIcon className="h-5 w-5"/> : null}
                                                <span className="ml-2">{saveSuccess ? 'Saved!' : 'Save Details'}</span>
                                            </button>
                                        </div>
                                        {saveError && <p className="text-red-500 text-sm">{saveError}</p>}
                                    </form>
                                    <div className="mt-6 space-y-3 pt-4 border-t border-slate-200 dark:border-slate-700">
                                        <h4 className="font-semibold text-slate-800 dark:text-slate-200">Message History</h4>
                                        <div className="max-h-48 overflow-y-auto space-y-2 pr-2">
                                            {editableContact?.messages && editableContact.messages.length > 0 ? (
                                                editableContact.messages.sort((a,b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).map(msg => (
                                                    <div key={msg.message_id} className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg group relative">
                                                        <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">{msg.message_type} on {new Date(msg.created_at).toLocaleDateString()}</p>
                                                        <p className="mt-1 text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{msg.content}</p>
                                                    </div>
                                                ))
                                            ) : <p className="text-sm text-slate-500 dark:text-slate-400">No messages yet.</p>}
                                        </div>
                                    </div>
                               </div>

                                {/* Right: AI Composer */}
                                <div className="space-y-4">
                                    <h4 className="font-semibold text-slate-800 dark:text-slate-200">AI Composer</h4>
                                    <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg space-y-3 border border-slate-200 dark:border-slate-700">
                                        <div><label className="text-sm font-medium text-slate-600 dark:text-slate-400">Goal</label><select value={composerGoal} onChange={(e) => setComposerGoal(e.target.value as ComposerGoal)} className={`${inputClass} mt-1`}><option>Initial Connection</option><option>Follow-up</option><option>Reply to Interaction</option><option>Comment on Post</option></select></div>
                                        {(composerGoal === 'Reply to Interaction' || composerGoal === 'Comment on Post') && <div><label className={labelClass}>Their Post/Comment Text</label><textarea value={interactionDetails} onChange={(e) => setInteractionDetails(e.target.value)} rows={2} className={`${inputClass} mt-1`} placeholder="Paste text of their post or comment..."/></div>}
                                        {composerGoal !== 'Comment on Post' && <div><label className={labelClass}>Include Context:</label><div className="flex flex-wrap gap-x-4 gap-y-2 mt-1">{[{label:'Mission', state:includeMission, setter:setIncludeMission}, {label:'Values',state:includeValues,setter:setIncludeValues}, {label:'Problem',state:includeProblem,setter:setIncludeProblem}].map(item => (<div key={item.label} className="flex items-center"><input id={item.label} type="checkbox" checked={item.state} onChange={(e) => item.setter(e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"/><label htmlFor={item.label} className="ml-2 text-sm text-slate-700 dark:text-slate-300">{item.label}</label></div>))}</div></div>}
                                        {composerGoal !== 'Comment on Post' && <div><label className={labelClass}>Your Notes (optional)</label><textarea value={userNotes} onChange={(e) => setUserNotes(e.target.value)} rows={2} className={`${inputClass} mt-1`} placeholder="Guide the AI's tone or angle..."/></div>}
                                        <button type="button" onClick={handleGenerate} disabled={isGenerating} className="w-full px-4 py-2 text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400">{isGenerating ? <LoadingSpinner/> : "Generate Messages"}</button>
                                    </div>
                                    <div className="space-y-2">
                                        {generatedMessages.map((msg, idx) => (<div key={idx} className="p-2 rounded-md border border-slate-200 dark:border-slate-700 flex justify-between items-center gap-2"><p className="text-sm flex-grow">{msg}</p><button onClick={() => setComposerText(msg)} className="text-xs font-semibold text-blue-600 hover:underline flex-shrink-0">Use this</button></div>))}
                                    </div>
                                    <div>
                                        <h4 className="font-semibold text-slate-800 dark:text-slate-200">New Message / Note Composer</h4>
                                        <select value={messageType} onChange={(e) => setMessageType(e.target.value as any)} className={`${inputClass} max-w-xs mt-2`}>
                                            <option value="Note">Note</option>
                                            <option value="Connection">Connection Message</option>
                                            <option value="Follow-up">Follow-up</option>
                                            <option value="Comment">Comment</option>
                                        </select>
                                        <div className="relative">
                                            <textarea value={composerText} onChange={e => {setComposerText(e.target.value); setBrandVoiceAnalysis(null);}} rows={4} className={`${inputClass} mt-2`} placeholder="Compose your message or generate one..."/>
                                            <button onClick={handleAnalyzeBrandVoice} disabled={isAnalyzingVoice || !composerText.trim()} title="Analyze Brand Voice" className="absolute top-3 right-2 p-1.5 rounded-full bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-blue-600 dark:text-blue-400 disabled:opacity-50">
                                                {isAnalyzingVoice ? <div className="animate-spin h-5 w-5"/> : <SparklesIcon className="h-5 w-5" />}
                                            </button>
                                        </div>
                                        {brandVoiceAnalysis && (
                                            <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-700 text-xs space-y-2">
                                                <p><strong className="font-semibold text-blue-800 dark:text-blue-200">Alignment Score: {brandVoiceAnalysis.alignment_score.toFixed(1)}/10</strong> - {brandVoiceAnalysis.tone_feedback}</p>
                                                <p><strong className="font-semibold text-blue-800 dark:text-blue-200">Suggestion:</strong> {brandVoiceAnalysis.suggestion}</p>
                                            </div>
                                        )}
                                        {messageType === 'Follow-up' && (
                                            <div className="mt-2">
                                                <label htmlFor="follow_up_due_date" className={labelClass}>Schedule Follow-up Date</label>
                                                <input type="date" id="follow_up_due_date" value={followUpDate} onChange={e => setFollowUpDate(e.target.value)} className={inputClass} />
                                            </div>
                                        )}
                                        <div className="flex justify-end mt-2">
                                            <button type="button" onClick={handleSendMessage} disabled={isSending || !composerText.trim()} className="px-4 py-2 text-sm rounded-md bg-green-600 text-white hover:bg-green-700 disabled:bg-green-400">
                                                {isSending ? <LoadingSpinner/> : 'Save Message'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            <button type="button" onClick={() => handleSaveDetails(true)} disabled={isSaving || isSending || isGenerating} className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 sm:ml-3 sm:w-auto disabled:opacity-50">
                                Save & Close
                            </button>
                            <button type="button" onClick={onClose} disabled={isSaving || isSending || isGenerating} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto">
                                Cancel
                            </button>
                             {contact?.contact_id && onDeleteContact && (
                                <div className="sm:flex-1">
                                    <button 
                                        type="button" 
                                        onClick={handleDelete} 
                                        disabled={isSaving || isSending || isGenerating} 
                                        className="mt-3 inline-flex w-full justify-center rounded-md bg-red-100 dark:bg-red-900/40 px-3 py-2 text-sm font-semibold text-red-700 dark:text-red-400 shadow-sm ring-1 ring-inset ring-red-200 dark:ring-red-700 hover:bg-red-200 dark:hover:bg-red-900/60 sm:mt-0 sm:mr-auto disabled:opacity-50"
                                    >
                                        <TrashIcon className="h-5 w-5 mr-2" />
                                        Delete Contact
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};