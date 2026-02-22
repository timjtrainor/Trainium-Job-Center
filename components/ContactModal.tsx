import React, { useState, useEffect } from 'react';
import { Contact, Company, ContactPayload, BaseResume, Prompt, JobApplication, MessagePayload, PromptContext, Resume, DateInfo, ContactPersona, LinkedInPost, UserProfile, Education, Certification, StrategicNarrative, StrategicMessage, StrategicMessageResult } from '../types';
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
    const [generatedMessages, setGeneratedMessages] = useState<StrategicMessage[]>([]);
    const [generationReasoning, setGenerationReasoning] = useState<string | null>(null);

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


    // Smart Fill State
    const [rawLinkedInText, setRawLinkedInText] = useState('');
    const [isParsing, setIsParsing] = useState(false);


    useEffect(() => {
        if (isOpen) {
            const defaults = {
                first_name: '', last_name: '', job_title: '', status: 'To Contact',
                date_contacted: new Date().toISOString().split('T')[0], is_referral: false, messages: [],
            };
            setEditableContact(contact ? { ...defaults, ...contact } : defaults);

            // Reset all states on open
            setSaveError(null);
            setIsSaving(false);
            setSaveSuccess(false);
            setIsSending(false);
            setComposerText('');
            setFollowUpDate('');
            setMessageType('Note');
            setGeneratedMessages([]);
            setGenerationReasoning(null);
            setGenerationError(null);
            setIsGenerating(false);
            setComposerGoal('Initial Connection');
            setCommentTone('Standard');
            setIncludeMission(false);
            setIncludeValues(false);
            setIncludeProblem(true);
            setInteractionDetails('');
            setUserNotes('');
            setRawLinkedInText('');
            setIsParsing(false);
        }
    }, [isOpen, contact, activeNarrativeId]);

    if (!isOpen) return null;

    const handleGenerate = async () => {
        setIsGenerating(true);
        setGenerationError(null);
        setGeneratedMessages([]);

        try {
            if (composerGoal === 'Comment on Post') {
                const promptId = commentTone === 'Expertise-Driven' ? 'networking/expert-comment-gen' : 'networking/strategic-comment-gen';
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
                setGeneratedMessages(comments.map(c => ({ body: c, type: 'Comment', word_count: c.split(' ').length })));
                setGenerationReasoning(null);

            } else {
                const promptId = 'networking/strategic-message-gen';
                const prompt = prompts.find(p => p.id === promptId);
                if (!prompt) {
                    throw new Error('Strategic messaging prompt is not available.');
                }

                const contactCompany = companies.find(c => c.company_id === editableContact.company_id);
                const linkedApp = applications.find(app => app.job_application_id === editableContact.job_application_id);

                const context: PromptContext = {
                    alignment_strategy: linkedApp?.alignment_strategy ? JSON.stringify(linkedApp.alignment_strategy, null, 2) : "{}",
                    job_problem_analysis: linkedApp?.job_problem_analysis_result ? JSON.stringify(linkedApp.job_problem_analysis_result, null, 2) : "{}",
                    CONTACT_ROLE: editableContact.job_title || "Unknown Title",
                    CONTACT_INTEL: editableContact.linkedin_about || editableContact.notes || "Not provided",
                    USER_NOTES: userNotes || "No specific steer provided",
                    CONTACT_FIRST_NAME: editableContact.first_name || "there",
                    COMPANY_NAME: contactCompany?.company_name || linkedApp?.job_title || "Target Company",
                    GOAL: composerGoal,
                };

                const result = await geminiService.generateStrategicMessage(context, prompt.id, debugCallbacks);
                setGeneratedMessages(result.messages);
                setGenerationReasoning(result.internal_reasoning);
            }
        } catch (e) {
            setGenerationError(e instanceof Error ? e.message : "Failed to generate content.");
        } finally {
            setIsGenerating(false);
        }
    };


    const handleSmartFill = async () => {
        if (!rawLinkedInText.trim()) return;

        setIsParsing(true);
        setSaveError(null);
        try {
            const result = await geminiService.parseLinkedinContact(rawLinkedInText);

            if (result.error) {
                setSaveError(`Parsing Error: ${result.error}`);
            } else {
                setEditableContact(prev => ({
                    ...prev,
                    first_name: result.first_name || prev.first_name,
                    last_name: result.last_name || prev.last_name,
                    job_title: result.job_title || prev.job_title,
                    linkedin_url: result.linkedin_url || prev.linkedin_url,
                    linkedin_about: result.linkedin_about || prev.linkedin_about,
                    persona: result.persona_suggestion || prev.persona,
                    notes: result.notes || prev.notes,
                }));
                setSaveSuccess(false);
                setRawLinkedInText(''); // Clear on success
            }
        } catch (err) {
            setSaveError(err instanceof Error ? err.message : 'Failed to parse LinkedIn text.');
        } finally {
            setIsParsing(false);
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
            if (closeOnSuccess) onClose();

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
        } catch (e) {
            setSaveError("Failed to save message.");
        } finally {
            setIsSending(false);
        }
    };

    const handleDelete = async () => {
        if (onDeleteContact && editableContact.contact_id) {
            if (window.confirm("Are you sure you want to permanently delete this contact and all their messages? This action cannot be undone.")) {
                try {
                    setIsSaving(true);
                    setSaveError(null);
                    await onDeleteContact(editableContact.contact_id);
                    onClose();
                } catch (err) {
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
                                    {/* Smart Fill Section */}
                                    <div className="p-3 bg-blue-50/50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800/50 space-y-2">
                                        <div className="flex items-center justify-between">
                                            <label className="text-xs font-bold uppercase tracking-wider text-blue-700 dark:text-blue-400">Smart Fill (from LinkedIn)</label>
                                            <span className="text-[10px] text-blue-600/70 dark:text-blue-400/50 italic">Paste text from a profile page</span>
                                        </div>
                                        <div className="relative">
                                            <textarea
                                                rows={2}
                                                className="block w-full rounded-md border-0 py-1.5 text-slate-900 dark:text-white bg-white dark:bg-slate-800/50 ring-1 ring-inset ring-blue-300 dark:ring-blue-800 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
                                                placeholder="Paste any LinkedIn profile text here..."
                                                value={rawLinkedInText}
                                                onChange={(e) => setRawLinkedInText(e.target.value)}
                                            />
                                            <button
                                                type="button"
                                                onClick={handleSmartFill}
                                                disabled={isParsing || !rawLinkedInText.trim()}
                                                className="absolute bottom-1.5 right-1.5 inline-flex items-center gap-x-1 rounded bg-blue-600 px-2 py-1 text-xs font-semibold text-white shadow-sm hover:bg-blue-500 disabled:opacity-50"
                                            >
                                                {isParsing ? <LoadingSpinner /> : <SparklesIcon className="h-3 w-3" />}
                                                Fill Form
                                            </button>
                                        </div>
                                    </div>

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
                                                {applications
                                                    .filter(app => !editableContact.company_id || app.company_id === editableContact.company_id)
                                                    .sort((a, b) => {
                                                        const compA = companies.find(c => c.company_id === a.company_id)?.company_name || '';
                                                        const compB = companies.find(c => c.company_id === b.company_id)?.company_name || '';
                                                        return `${compA} - ${a.job_title}`.localeCompare(`${compB} - ${b.job_title}`);
                                                    })
                                                    .map(app => (
                                                        <option key={app.job_application_id} value={app.job_application_id}>
                                                            {companies.find(c => c.company_id === app.company_id)?.company_name} - {app.job_title}
                                                        </option>
                                                    ))}
                                            </select>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                            <div><label htmlFor="status" className={labelClass}>Status</label><select name="status" id="status" value={editableContact.status || ''} onChange={handleChange} className={inputClass}>{contactStatuses.map(s => <option key={s} value={s}>{s}</option>)}</select></div>
                                            <div className="flex items-end pb-1"><div className="flex items-center"><input id="is_referral" name="is_referral" type="checkbox" checked={editableContact.is_referral || false} onChange={handleChange} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" /><label htmlFor="is_referral" className={`${labelClass} ml-2`}>Referral</label></div></div>
                                        </div>
                                        <div><label htmlFor="notes" className={labelClass}>Notes</label><textarea name="notes" id="notes" value={editableContact.notes || ''} onChange={handleChange} rows={2} className={inputClass}></textarea></div>

                                        <div className="flex justify-end pt-2">
                                            <button type="submit" disabled={isSaving || saveSuccess} className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md text-white shadow-sm transition-colors bg-green-600 hover:bg-green-700 disabled:bg-green-400">
                                                {isSaving ? <LoadingSpinner /> : saveSuccess ? <CheckIcon className="h-5 w-5" /> : null}
                                                <span className="ml-2">{saveSuccess ? 'Saved!' : 'Save Details'}</span>
                                            </button>
                                        </div>
                                        {saveError && <p className="text-red-500 text-sm">{saveError}</p>}
                                    </form>
                                    <div className="mt-6 space-y-3 pt-4 border-t border-slate-200 dark:border-slate-700">
                                        <h4 className="font-semibold text-slate-800 dark:text-slate-200">Message History</h4>
                                        <div className="max-h-48 overflow-y-auto space-y-2 pr-2">
                                            {editableContact?.messages && editableContact.messages.length > 0 ? (
                                                editableContact.messages.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).map(msg => (
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
                                        {(composerGoal === 'Reply to Interaction' || composerGoal === 'Comment on Post') && <div><label className={labelClass}>Their Post/Comment Text</label><textarea value={interactionDetails} onChange={(e) => setInteractionDetails(e.target.value)} rows={2} className={`${inputClass} mt-1`} placeholder="Paste text of their post or comment..." /></div>}
                                        {composerGoal !== 'Comment on Post' && <div><label className={labelClass}>Your Notes (optional)</label><textarea value={userNotes} onChange={(e) => setUserNotes(e.target.value)} rows={2} className={`${inputClass} mt-1`} placeholder="Guide the AI's tone or angle..." /></div>}
                                        <button type="button" onClick={handleGenerate} disabled={isGenerating} className="w-full px-4 py-2 text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400">
                                            {isGenerating ? <div className="flex items-center justify-center gap-2"><LoadingSpinner /><span>Generating...</span></div> : "Generate Messages"}
                                        </button>
                                        {generationError && <p className="text-xs text-red-500 mt-1">{generationError}</p>}
                                    </div>
                                    {generationReasoning && (
                                        <div className="p-3 bg-indigo-50 dark:bg-indigo-900/30 rounded-lg border border-indigo-200 dark:border-indigo-700 text-xs italic text-slate-700 dark:text-slate-300">
                                            <strong className="font-semibold block mb-1">Diagnostic Logic:</strong>
                                            {generationReasoning}
                                        </div>
                                    )}
                                    <div className="space-y-2">
                                        {generatedMessages.map((msg, idx) => (
                                            <div key={idx} className="p-3 rounded-md border border-slate-200 dark:border-slate-700 flex flex-col gap-2 bg-white dark:bg-slate-800 shadow-sm transition-shadow hover:shadow-md">
                                                <div className="flex justify-between items-center">
                                                    <span className="px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/50 text-[10px] font-bold text-blue-700 dark:text-blue-300 uppercase tracking-wider border border-blue-200 dark:border-blue-800">
                                                        {msg.type}
                                                    </span>
                                                    <button onClick={() => setComposerText(msg.body)} className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex-shrink-0">
                                                        Use message
                                                    </button>
                                                </div>
                                                <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">{msg.body}</p>
                                                <div className="text-[10px] text-slate-400 dark:text-slate-500 flex justify-end italic">
                                                    {msg.word_count} words
                                                </div>
                                            </div>
                                        ))}
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
                                            <textarea value={composerText} onChange={e => setComposerText(e.target.value)} rows={4} className={`${inputClass} mt-2`} placeholder="Compose your message or generate one..." />
                                        </div>
                                        {messageType === 'Follow-up' && (
                                            <div className="mt-2">
                                                <label htmlFor="follow_up_due_date" className={labelClass}>Schedule Follow-up Date</label>
                                                <input type="date" id="follow_up_due_date" value={followUpDate} onChange={e => setFollowUpDate(e.target.value)} className={inputClass} />
                                            </div>
                                        )}
                                        <div className="flex justify-end mt-2">
                                            <button type="button" onClick={handleSendMessage} disabled={isSending || !composerText.trim()} className="px-4 py-2 text-sm rounded-md bg-green-600 text-white hover:bg-green-700 disabled:bg-green-400">
                                                {isSending ? <LoadingSpinner /> : 'Save Message'}
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