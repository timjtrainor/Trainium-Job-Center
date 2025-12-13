import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Company, JobApplication, InfoField, Message, MessagePayload, PromptContext, Prompt, Contact, CompanyPayload, StrategicNarrative } from '../../types';
import * as geminiService from '../../services/geminiService';
import { LoadingSpinner, PlusCircleIcon, TrashIcon, CheckBadgeIcon } from '../shared/ui/IconComponents';

interface CompanyDetailViewProps {
    company: Company;
    allCompanies: Company[];
    applications: JobApplication[];
    messages: Message[];
    contacts: Contact[];
    onBack: () => void;
    onUpdate: (payload: Partial<Company>) => void;
    onViewApplication: (appId: string) => void;
    onCreateMessage: (payload: MessagePayload) => Promise<void>;
    onOpenCreateCompanyModal: (initialData: Partial<CompanyPayload>) => void;
    onOpenContactModal: (contact?: Partial<Contact> | null) => void;
    onResearch: (details: { id: string; name: string, url?: string }) => Promise<void>;
    onDeleteContact: (contactId: string) => Promise<void>;
    prompts: Prompt[];
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
    activeNarrative: StrategicNarrative | null;
    autoResearch?: boolean;
}

type ViewTab = 'intelligence' | 'applications' | 'engagement';
type CommentTone = 'Standard' | 'Expertise-Driven';

const InfoFieldDisplay = ({ label, field, isEditing, onChange, children, type = 'text' }: { label: string, field?: InfoField | { text: string }, isEditing: boolean, onChange?: (newText: string) => void, children?: React.ReactNode, type?: 'text' | 'textarea' }) => {
    const textareaClass = "mt-1 w-full p-2 text-sm rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500";
    const text = field?.text || '';
    const source = (field as InfoField)?.source || '';

    if (children && !isEditing) {
         return (
             <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</dt>
                <dd className="mt-1 text-sm text-slate-900 dark:text-slate-100">{children}</dd>
            </div>
         )
    }

    if (isEditing) {
        return (
             <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</dt>
                <dd className="mt-1 text-sm text-slate-900 dark:text-slate-100">
                    {type === 'textarea' ? (
                        <textarea 
                            rows={3} 
                            className={textareaClass} 
                            value={text} 
                            onChange={e => onChange?.(e.target.value)} 
                        />
                    ) : (
                         <input 
                            type="text"
                            className={textareaClass} 
                            value={text} 
                            onChange={e => onChange?.(e.target.value)} 
                        />
                    )}
                </dd>
            </div>
        )
    }

    return (
        <div className="sm:col-span-1">
            <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</dt>
            <dd className="mt-1 text-sm text-slate-900 dark:text-slate-100">
                <p className="whitespace-pre-wrap">{text || 'N/A'}</p>
                 {source && (
                    <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                        Source: <a href={source} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline truncate inline-block max-w-full align-bottom">{source}</a>
                    </div>
                )}
            </dd>
        </div>
    );
};

export const CompanyDetailView = ({ company, allCompanies, applications, messages, contacts, onBack, onUpdate, onViewApplication, onCreateMessage, onOpenCreateCompanyModal, onOpenContactModal, onResearch, onDeleteContact, prompts, debugCallbacks, activeNarrative, autoResearch = false }: CompanyDetailViewProps): React.ReactNode => {
    const [activeTab, setActiveTab] = useState<ViewTab>('intelligence');
    const [isEditing, setIsEditing] = useState(false);
    const [editableCompany, setEditableCompany] = useState<Company>(company);
    
    // Engagement Tab State
    const [postText, setPostText] = useState('');
    const [generatedComments, setGeneratedComments] = useState<string[]>([]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState('');
    const [commentTone, setCommentTone] = useState<CommentTone>('Standard');

    
    // AI Research State
    const [isResearching, setIsResearching] = useState(false);

     useEffect(() => {
        setEditableCompany(company);
        // If we received new research data for the company, enter editing mode to show it.
        if (company.mission?.text && !isEditing) {
            const hasData = Object.values(company).some(val => (val as InfoField)?.text);
            if(hasData) {
                // Heuristic: if we have mission text but weren't editing, it's probably new research.
                // This is imperfect but avoids a more complex state-passing prop chain.
            }
        }
    }, [company]);

    const autoResearchTriggeredRef = useRef(false);

    const handleSave = () => {
        onUpdate(editableCompany);
        setIsEditing(false);
    };

    const handleCancel = () => {
        setEditableCompany(company);
        setIsEditing(false);
    };
    
    const handleFieldChange = (fieldName: keyof Company, value: string) => {
        setEditableCompany(prev => {
            const currentField = prev[fieldName] as InfoField | undefined;
            return {
                ...prev,
                [fieldName]: {
                    text: value,
                    source: currentField?.source || ''
                }
            };
        });
    };
    
    const handleResearchClick = useCallback(async () => {
        setIsResearching(true);
        setError('');
        try {
            await onResearch({
                id: company.company_id,
                name: editableCompany.company_name,
                url: editableCompany.company_url,
            });
            if (!isEditing) {
              setIsEditing(true); 
            }
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to research company.');
        } finally {
            setIsResearching(false);
        }
    }, [company.company_id, editableCompany.company_name, editableCompany.company_url, isEditing, onResearch]);

    // Auto-research when requested by the parent view
    useEffect(() => {
        if (!autoResearch) {
            autoResearchTriggeredRef.current = false;
            return;
        }

        if (autoResearchTriggeredRef.current || isResearching) {
            return;
        }

        autoResearchTriggeredRef.current = true;
        setActiveTab('intelligence');

        const timer = window.setTimeout(() => {
            handleResearchClick();
        }, 300);

        return () => window.clearTimeout(timer);
    }, [autoResearch, isResearching, handleResearchClick]);
    
    const handleGenerateComments = async () => {
        if (!postText) {
            setError('Please enter the text of a LinkedIn post.');
            return;
        }
        const promptId = commentTone === 'Expertise-Driven' ? 'GENERATE_EXPERT_COMMENT' : 'GENERATE_STRATEGIC_COMMENT';
        const prompt = prompts.find(p => p.id === promptId);
        
        if (!prompt) {
            setError(`LinkedIn comment generation prompt '${promptId}' is currently unavailable.`);
            return;
        }
        if (!activeNarrative) {
            setError('An active strategic narrative is required to generate comments.');
            return;
        }

        setIsGenerating(true);
        setError('');
        try {
            const context: PromptContext = {
                COMPANY_NAME: company.company_name,
                POST_TEXT: postText,
                MISSION: company.mission?.text,
                VALUES: company.values?.text,
                NEWS: company.news?.text,
                GOALS: company.goals?.text,
                ISSUES: company.issues?.text,
                NORTH_STAR: activeNarrative.positioning_statement,
                MASTERY: activeNarrative.signature_capability,
            };

            const comments = await geminiService.generateStrategicComment(context, prompt.content, debugCallbacks);
            setGeneratedComments(comments);
        } catch (e) {
            setError('Failed to generate comments. Please try again.');
            console.error(e);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSaveComment = async (commentText: string) => {
        try {
            await onCreateMessage({
                company_id: company.company_id,
                message_type: 'Comment',
                content: `Commented on post: "${postText.substring(0, 50)}..."\n\nComment: ${commentText}`,
                is_user_sent: true,
            });
            setGeneratedComments([]);
            setPostText('');
        } catch (e) {
            setError('Failed to save comment.');
        }
    };

    const companyApplications = useMemo(() => {
        return applications.filter(app => app.company_id === company.company_id);
    }, [applications, company.company_id]);

    const companyContacts = useMemo(() => {
        // Get IDs of all applications for this company
        const appIdsForCompany = new Set(
            applications.filter(app => app.company_id === company.company_id).map(app => app.job_application_id)
        );
    
        // Get IDs of all contacts from interviews related to these applications
        const contactIdsFromApps = new Set<string>();
        applications.forEach(app => {
            if (appIdsForCompany.has(app.job_application_id)) {
                app.interviews?.forEach(interview => {
                    interview.interview_contacts?.forEach(contact => {
                        contactIdsFromApps.add(contact.contact_id);
                    });
                });
            }
        });
    
        // Combine and de-duplicate contacts
        const allRelevantContacts = new Map<string, Contact>();
    
        // Add contacts directly employed by the company
        contacts.forEach(c => {
            if (c.company_id === company.company_id) {
                allRelevantContacts.set(c.contact_id, c);
            }
        });
    
        // Add contacts from related interviews (including external recruiters)
        contacts.forEach(c => {
            if (contactIdsFromApps.has(c.contact_id)) {
                allRelevantContacts.set(c.contact_id, c);
            }
        });
    
        return Array.from(allRelevantContacts.values());
    }, [contacts, applications, company.company_id]);

    const competitorsList = useMemo(() => {
        const competitorsText = (isEditing ? editableCompany.competitors?.text : company.competitors?.text);
        if (!competitorsText) return [];
        return competitorsText.split(',').map(name => name.trim()).filter(Boolean);
    }, [company.competitors, editableCompany.competitors, isEditing]);


    const tabClass = (tabName: ViewTab) => 
        `px-3 py-2 font-medium text-sm rounded-md cursor-pointer transition-colors ` +
        (activeTab === tabName 
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300' 
            : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200');

    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700 animate-fade-in">
             <header className="mb-6 flex justify-between items-start">
                <div>
                    <button onClick={onBack} className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 mb-2">
                        &larr; Back to Companies
                    </button>
                    <div className="flex items-center gap-3">
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{company.company_name}</h2>
                        {company.is_recruiting_firm && !isEditing && (
                            <span className="mt-1 inline-flex items-center rounded-md bg-sky-50 px-2 py-1 text-xs font-medium text-sky-700 ring-1 ring-inset ring-sky-600/20 dark:bg-sky-500/10 dark:text-sky-400 dark:ring-sky-500/20">
                                Recruiting Firm
                            </span>
                        )}
                    </div>
                </div>
                <div className="flex gap-2">
                     <button
                        onClick={handleResearchClick}
                        disabled={isResearching}
                        className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-lg text-white bg-teal-600 hover:bg-teal-700 shadow-sm disabled:bg-teal-400"
                    >
                        {isResearching ? <LoadingSpinner /> : 'Research with AI'}
                    </button>
                    {isEditing ? (
                        <div className="flex gap-2">
                             <button onClick={handleCancel} className="px-4 py-2 text-sm font-medium rounded-lg text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 border border-slate-300 dark:border-slate-500 shadow-sm">
                                Cancel
                            </button>
                            <button onClick={handleSave} className="px-4 py-2 text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 shadow-sm">
                                Save Changes
                            </button>
                        </div>
                     ) : (
                        <button onClick={() => setIsEditing(true)} className="px-4 py-2 text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-sm">
                            Edit Company Info
                        </button>
                    )}
                </div>
            </header>
            
            {error && <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-3 mb-4 text-sm text-red-700 dark:text-red-300">{error}</div>}

            <div className="border-b border-slate-200 dark:border-slate-700">
                <nav className="-mb-px flex space-x-4" aria-label="Tabs">
                    <button onClick={() => setActiveTab('intelligence')} className={tabClass('intelligence')}>Intelligence</button>
                    <button onClick={() => setActiveTab('applications')} className={tabClass('applications')}>Applications</button>
                    <button onClick={() => setActiveTab('engagement')} className={tabClass('engagement')}>Engagement</button>
                </nav>
            </div>
            
            <div className="mt-6">
                {activeTab === 'intelligence' && (
                     <div className="space-y-6">
                         <div>
                            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Company Intelligence</h3>
                            <dl className="mt-2 grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                                {isEditing && (
                                     <div className="sm:col-span-2">
                                        <div className="relative flex items-start">
                                            <div className="flex h-6 items-center">
                                                <input
                                                    id="is_recruiting_firm_detail"
                                                    type="checkbox"
                                                    checked={!!editableCompany.is_recruiting_firm}
                                                    onChange={(e) => setEditableCompany(prev => ({ ...prev, is_recruiting_firm: e.target.checked }))}
                                                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                />
                                            </div>
                                            <div className="ml-3 text-sm leading-6">
                                                <label htmlFor="is_recruiting_firm_detail" className="font-medium text-slate-700 dark:text-slate-300">
                                                    This is a recruiting firm
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                )}
                                <div className="sm:col-span-2">
                                    <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Company URL</dt>
                                    <dd className="mt-1 text-sm text-slate-900 dark:text-slate-100">
                                        {isEditing ? (
                                             <input
                                                type="url"
                                                value={editableCompany.company_url || ''}
                                                onChange={e => setEditableCompany(prev => ({...prev, company_url: e.target.value}))}
                                                className="mt-1 w-full p-2 text-sm rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                            />
                                        ) : company.company_url ? (
                                             <a href={company.company_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline break-all">
                                                {company.company_url}
                                            </a>
                                        ) : 'N/A'}
                                    </dd>
                                </div>
                                <InfoFieldDisplay label="Mission" field={editableCompany.mission} isEditing={isEditing} onChange={val => handleFieldChange('mission', val)} type="textarea" />
                                <InfoFieldDisplay label="Values" field={editableCompany.values} isEditing={isEditing} onChange={val => handleFieldChange('values', val)} type="textarea"/>
                                <InfoFieldDisplay label="Stated Goals" field={editableCompany.goals} isEditing={isEditing} onChange={val => handleFieldChange('goals', val)} type="textarea"/>
                                <InfoFieldDisplay label="Challenges / Issues" field={editableCompany.issues} isEditing={isEditing} onChange={val => handleFieldChange('issues', val)} type="textarea"/>
                                <InfoFieldDisplay label="Customer Segments" field={editableCompany.customer_segments} isEditing={isEditing} onChange={val => handleFieldChange('customer_segments', val)} type="textarea"/>
                                <InfoFieldDisplay label="Strategic Initiatives" field={editableCompany.strategic_initiatives} isEditing={isEditing} onChange={val => handleFieldChange('strategic_initiatives', val)} type="textarea"/>
                                <div className="sm:col-span-2">
                                    <InfoFieldDisplay label="Market Position" field={editableCompany.market_position} isEditing={isEditing} onChange={val => handleFieldChange('market_position', val)} type="textarea"/>
                                </div>
                                 <div className="sm:col-span-2">
                                    <InfoFieldDisplay label="Recent News" field={editableCompany.news} isEditing={isEditing} onChange={val => handleFieldChange('news', val)} type="textarea"/>
                                </div>
                                 <div className="sm:col-span-2">
                                    <InfoFieldDisplay label="Industry" field={editableCompany.industry} isEditing={isEditing} onChange={val => handleFieldChange('industry', val)} />
                                </div>
                                {isEditing ? (
                                    <div className="sm:col-span-2">
                                        <InfoFieldDisplay label="Competitors (comma-separated)" field={editableCompany.competitors} isEditing={isEditing} onChange={val => handleFieldChange('competitors', val)} type="textarea" />
                                    </div>
                                ) : (
                                    <div className="sm:col-span-2">
                                        <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Competitors</dt>
                                        <dd className="mt-1 flex flex-wrap gap-2">
                                            {competitorsList.length > 0 ? competitorsList.map((name, i) => {
                                                const existingCompany = allCompanies.find(ac => ac.company_name.toLowerCase() === name.toLowerCase());
                                                return (
                                                    <div key={i} className="flex items-center gap-1.5 p-1.5 rounded-md bg-slate-100 dark:bg-slate-700/50">
                                                        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{name}</span>
                                                        {existingCompany ? (
                                                             <span className="inline-flex items-center gap-x-1 rounded-full bg-green-50 px-1.5 py-0.5 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20">
                                                                <CheckBadgeIcon className="h-3 w-3" />
                                                                Tracked
                                                            </span>
                                                        ) : (
                                                            <button onClick={() => onOpenCreateCompanyModal({ company_name: name })} className="inline-flex items-center gap-x-1 rounded-full bg-blue-50 px-1.5 py-0.5 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-600/20 hover:bg-blue-100 dark:bg-blue-500/10 dark:text-blue-400 dark:ring-blue-500/20 dark:hover:bg-blue-500/20">
                                                                <PlusCircleIcon className="h-3 w-3"/>
                                                                Add
                                                            </button>
                                                        )}
                                                    </div>
                                                )
                                            }) : <p className="text-sm text-slate-500 dark:text-slate-400">No competitor data available.</p>}
                                        </dd>
                                    </div>
                                )}
                            </dl>
                        </div>
                    </div>
                )}
                {activeTab === 'applications' && (
                    <div>
                         <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Applications at {company.company_name}</h3>
                         {companyApplications.length > 0 ? (
                            <ul role="list" className="divide-y divide-slate-200 dark:divide-slate-700 mt-2">
                                {companyApplications.map(app => (
                                    <li key={app.job_application_id} className="flex justify-between gap-x-6 py-5 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/80 px-2 -mx-2 rounded-lg" onClick={() => onViewApplication(app.job_application_id)}>
                                        <div className="flex min-w-0 gap-x-4">
                                            <div className="min-w-0 flex-auto">
                                                <p className="text-sm font-semibold leading-6 text-slate-900 dark:text-white">{app.job_title}</p>
                                                <p className="mt-1 truncate text-xs leading-5 text-slate-500 dark:text-slate-400">Applied: {app.date_applied}</p>
                                            </div>
                                        </div>
                                         <div className="hidden shrink-0 sm:flex sm:flex-col sm:items-end">
                                            <p className="text-sm leading-6 text-slate-900 dark:text-white">{app.status?.status_name || 'N/A'}</p>
                                            <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">{app.salary || ''}</p>
                                         </div>
                                    </li>
                                ))}
                            </ul>
                         ) : (
                            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">No applications found for this company.</p>
                         )}
                    </div>
                )}
                 {activeTab === 'engagement' && (
                    <div className="space-y-6">
                        <div className="p-4 bg-yellow-50 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300 rounded-lg">
                            <p className="font-bold">Engagement Tools</p>
                            <p className="text-sm mt-1">Generate AI-powered comments for LinkedIn posts or draft follow-up messages.</p>
                        </div>

                        <div className="pt-6 border-t border-slate-200 dark:border-slate-700">
                            <div className="flex justify-between items-center">
                                <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Contacts for {company.company_name}</h3>
                                <button
                                    onClick={() => onOpenContactModal({ company_id: company.company_id })}
                                    className="inline-flex items-center gap-x-1.5 rounded-md bg-blue-600 px-2.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-500"
                                >
                                    <PlusCircleIcon className="h-4 w-4" /> Add Contact
                                </button>
                            </div>
                            <div className="mt-2 space-y-2 max-h-60 overflow-y-auto pr-2">
                                {companyContacts && companyContacts.length > 0 ? companyContacts.map(c => (
                                    <div key={c.contact_id} className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg flex justify-between items-center group">
                                        <div className="cursor-pointer flex-grow" onClick={() => onOpenContactModal(c)}>
                                            <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{c.first_name} {c.last_name}</p>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">{c.job_title}</p>
                                            {c.persona && <span className="mt-1 inline-flex items-center rounded-md bg-purple-50 px-2 py-1 text-xs font-medium text-purple-700 ring-1 ring-inset ring-purple-600/20 dark:bg-purple-400/10 dark:text-purple-400 dark:ring-purple-400/20">{c.persona}</span>}
                                        </div>
                                        <div className="flex items-center gap-2 flex-shrink-0">
                                            <span className="text-xs font-medium text-slate-500">{c.status}</span>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation(); // Prevent modal from opening
                                                    if (window.confirm('Are you sure you want to delete this contact?')) {
                                                        onDeleteContact(c.contact_id);
                                                    }
                                                }}
                                                className="p-1 text-slate-400 hover:text-red-500 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 opacity-0 group-hover:opacity-100 transition-opacity"
                                                title="Delete Contact"
                                            >
                                                <TrashIcon className="h-4 w-4" />
                                            </button>
                                        </div>
                                    </div>
                                )) : <p className="text-sm text-slate-500 py-4 text-center">No contacts recorded for this company yet.</p>}
                            </div>
                        </div>

                         <div>
                            <h4 className="text-md font-semibold text-slate-800 dark:text-slate-200">Generate LinkedIn Comments</h4>
                            <div className="mt-2 space-y-2">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Tone</label>
                                    <div className="mt-2 flex rounded-md shadow-sm">
                                        <button type="button" onClick={() => setCommentTone('Standard')} className={`px-4 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-l-md ${commentTone === 'Standard' ? 'bg-blue-600 text-white z-10' : 'bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600'}`}>Standard</button>
                                        <button type="button" onClick={() => setCommentTone('Expertise-Driven')} className={`-ml-px px-4 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-r-md ${commentTone === 'Expertise-Driven' ? 'bg-blue-600 text-white z-10' : 'bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600'}`}>Expertise-Driven</button>
                                    </div>
                                </div>
                                <label htmlFor="post-text" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Paste post text here:</label>
                                <textarea id="post-text" rows={4} value={postText} onChange={(e) => setPostText(e.target.value)} className="mt-1 w-full p-2 text-sm rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500" />
                                <button onClick={handleGenerateComments} disabled={isGenerating} className="px-4 py-2 text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400">
                                    {isGenerating ? <LoadingSpinner/> : 'Generate Comments'}
                                </button>
                            </div>
                            {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
                            {generatedComments.length > 0 && (
                                <div className="mt-4 space-y-2">
                                    {generatedComments.map((comment, index) => (
                                        <div key={index} className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg flex justify-between items-center">
                                            <p className="text-sm">{comment}</p>
                                            <button onClick={() => handleSaveComment(comment)} className="text-xs text-green-600 font-semibold hover:underline">Save as Comment</button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        
                         <div className="pt-6 border-t border-slate-200 dark:border-slate-700">
                            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Message History</h3>
                             <div className="mt-2 space-y-2 max-h-60 overflow-y-auto">
                                {messages && messages.length > 0 ? messages.sort((a,b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).map(msg => (
                                    <div key={msg.message_id} className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg group relative">
                                        <p className="text-xs text-slate-500 dark:text-slate-400">{msg.message_type} on {new Date(msg.created_at).toLocaleDateString()}</p>
                                        <p className="mt-1 text-sm whitespace-pre-wrap">{msg.content}</p>
                                    </div>
                                )) : <p className="text-sm text-slate-500">No messages for this company.</p>}
                            </div>
                         </div>
                    </div>
                )}
            </div>
        </div>
    );
};
