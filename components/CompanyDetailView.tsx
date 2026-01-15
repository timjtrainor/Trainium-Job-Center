import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Company, JobApplication, InfoField, Message, MessagePayload, PromptContext, Prompt, Contact, CompanyPayload, StrategicNarrative } from '../types';
import * as geminiService from '../services/geminiService';
import { researchCompany } from '../services/apiService';
import { LoadingSpinner, PlusCircleIcon, TrashIcon, CheckBadgeIcon, ArrowTopRightOnSquareIcon, PencilSquareIcon, SparklesIcon } from './IconComponents';

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

// --- UI Components ---

const SourceCitation = ({ source }: { source: string }) => {
    let hostname = source;
    try {
        hostname = new URL(source).hostname.replace('www.', '');
    } catch (e) { /* ignore */ }

    return (
        <a
            href={source}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-0.5 ml-1 text-[10px] uppercase tracking-wider font-semibold text-slate-400 hover:text-blue-500 transition-colors bg-slate-100 dark:bg-slate-700/50 px-1.5 py-0.5 rounded-sm"
            title={source}
        >
            {hostname}
            <ArrowTopRightOnSquareIcon className="w-2.5 h-2.5" />
        </a>
    );
};

const RichTextDisplay = ({ text, source }: { text?: string, source?: string | string[] }) => {
    if (!text) return <span className="text-slate-400 italic text-sm">No data available.</span>;

    const sources = Array.isArray(source) ? source : (source ? [source] : []);

    // Simple improved readability: add line breaks
    return (
        <div className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed whitespace-pre-wrap">
            {text}
            {sources.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                    {sources.map((src, i) => (
                        <SourceCitation key={i} source={src} />
                    ))}
                </div>
            )}
        </div>
    );
};

const InfoCard = ({ title, field, isEditing, onChange, className = "" }: { title: string, field?: InfoField, isEditing: boolean, onChange: (val: string) => void, className?: string }) => {
    return (
        <div className={`bg-slate-50 dark:bg-slate-800/50 rounded-lg p-5 border border-slate-100 dark:border-slate-700/50 ${className}`}>
            <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">{title}</h4>
            {isEditing ? (
                <textarea
                    rows={4}
                    className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    value={field?.text || ''}
                    onChange={e => onChange(e.target.value)}
                    placeholder={`Enter ${title.toLowerCase()}...`}
                />
            ) : (
                <RichTextDisplay text={field?.text} source={field?.source} />
            )}
        </div>
    );
};

// --- Competitors Widget ---

const CompetitorsWidget = ({
    field,
    allCompanies,
    isEditing,
    onChange,
    onOpenCreateCompanyModal,
    onNavigateToCompany
}: {
    field?: InfoField,
    allCompanies: Company[],
    isEditing: boolean,
    onChange: (val: string) => void,
    onOpenCreateCompanyModal: (data: Partial<CompanyPayload>) => void,
    onNavigateToCompany: (id: string) => void
}) => {
    const rawText = field?.text || '';

    // Heuristic: Split by comma if it looks like a list
    const competitorNames = useMemo(() => {
        return rawText.split(',').map(s => s.trim()).filter(Boolean);
    }, [rawText]);

    if (isEditing) {
        return (
            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-lg p-5 border border-slate-100 dark:border-slate-700/50 col-span-full">
                <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">Competitive Landscape</h4>
                <textarea
                    rows={3}
                    className="w-full text-sm rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    value={rawText}
                    onChange={e => onChange(e.target.value)}
                    placeholder="Enter competitors, comma separated..."
                />
                <p className="mt-1 text-xs text-slate-400">Separate company names with commas (e.g. OpenAI, Anthropic, Google)</p>
            </div>
        );
    }

    return (
        <div className="bg-slate-50 dark:bg-slate-800/50 rounded-lg p-5 border border-slate-100 dark:border-slate-700/50 col-span-full">
            <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">Competitive Landscape</h4>

            {competitorNames.length === 0 ? (
                <span className="text-slate-400 italic text-sm">No competitors identified.</span>
            ) : (
                <div className="flex flex-wrap gap-2">
                    {competitorNames.map((name, i) => {
                        const existingMatch = allCompanies.find(c => c.company_name.toLowerCase() === name.toLowerCase());

                        if (existingMatch) {
                            return (
                                <button
                                    key={i}
                                    onClick={() => onNavigateToCompany(existingMatch.company_id)}
                                    className="group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 shadow-sm hover:border-blue-300 hover:ring-1 hover:ring-blue-200 transition-all text-sm font-medium text-slate-700 dark:text-slate-200"
                                >
                                    <CheckBadgeIcon className="w-4 h-4 text-blue-500" />
                                    {name}
                                </button>
                            );
                        }

                        return (
                            <div key={i} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-slate-200/50 dark:bg-slate-700/30 border border-transparent text-sm text-slate-600 dark:text-slate-400">
                                {name}
                                <button
                                    onClick={() => onOpenCreateCompanyModal({ company_name: name })}
                                    className="ml-1 p-0.5 hover:bg-slate-300 dark:hover:bg-slate-600 rounded-full text-slate-400 hover:text-blue-600 transition-colors"
                                    title={`Add ${name} to database`}
                                >
                                    <PlusCircleIcon className="w-4 h-4" />
                                </button>
                            </div>
                        );
                    })}
                </div>
            )}
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
    const autoResearchTriggeredRef = useRef(false);

    useEffect(() => {
        setEditableCompany(company);

        // Auto-switch to edit mode if we detect fresh, unreviewed research (heuristic: mission changed externally)
        if (company.mission?.text && company.mission.text !== editableCompany.mission?.text && !isEditing) {
            // Optional: setIsEditing(true); 
        }
    }, [company]);

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
                    source: currentField?.source || 'manual' // Preserve source or set manual
                }
            };
        });
    };

    // Special handler for simple URL string
    const handleUrlChange = (value: string) => {
        setEditableCompany(prev => ({ ...prev, company_url: value }));
    };

    const handleResearchClick = useCallback(async () => {
        setIsResearching(true);
        setError('');
        console.log("Research initiated for:", editableCompany.company_name);
        try {
            // Call the new web-research endpoint
            const result = await researchCompany(editableCompany.company_name, editableCompany.company_url, company.company_id);

            // Merge result into editableCompany
            // Note: apiService now handles parsing, so 'result' should have correct structure
            setEditableCompany(prev => ({
                ...prev,
                ...result
            }));

            if (!isEditing) {
                setIsEditing(true);
            }
        } catch (e) {
            console.error("Research failed:", e);
            setError(e instanceof Error ? e.message : 'Failed to research company.');
        } finally {
            setIsResearching(false);
        }
    }, [company.company_id, editableCompany.company_name, editableCompany.company_url, isEditing]);

    // Auto-research logic
    useEffect(() => {
        if (!autoResearch) {
            autoResearchTriggeredRef.current = false;
            return;
        }

        if (autoResearchTriggeredRef.current || isResearching) return;

        autoResearchTriggeredRef.current = true;
        setActiveTab('intelligence');
        const timer = window.setTimeout(() => handleResearchClick(), 300);
        return () => window.clearTimeout(timer);
    }, [autoResearch, isResearching, handleResearchClick]);

    // --- Tab Navigation ---
    const tabClass = (tabName: ViewTab) =>
        `px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === tabName
            ? 'border-blue-500 text-blue-600 dark:text-blue-400'
            : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}`;

    return (
        <div className="bg-white dark:bg-slate-900 min-h-screen">
            {/* Header */}
            <header className="sticky top-0 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button onClick={onBack} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors text-slate-500">
                        &larr;
                    </button>
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-xl font-bold text-slate-900 dark:text-white">{company.company_name}</h1>
                            {company.company_url && (
                                <a href={company.company_url} target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-blue-500 transition-colors">
                                    <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                                </a>
                            )}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                            <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10 dark:bg-blue-400/10 dark:text-blue-400 dark:ring-blue-400/20">
                                {company.industry?.text || 'Tech'}
                            </span>
                            {company.is_recruiting_firm && (
                                <span className="inline-flex items-center rounded-md bg-purple-50 px-2 py-1 text-xs font-medium text-purple-700 ring-1 ring-inset ring-purple-700/10 dark:bg-purple-400/10 dark:text-purple-400 dark:ring-purple-400/20">
                                    Recruiting Firm
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {isEditing ? (
                        <>
                            <button onClick={handleResearchClick} disabled={isResearching} className="inline-flex items-center px-3 py-1.5 text-xs font-semibold rounded-md text-teal-700 bg-teal-50 border border-teal-200 hover:bg-teal-100 disabled:opacity-50">
                                {isResearching ? <LoadingSpinner size="sm" /> : <><SparklesIcon className="w-3 h-3 mr-1.5" /> Auto-Research</>}
                            </button>
                            <div className="h-6 w-px bg-slate-300 dark:bg-slate-700"></div>
                            <button onClick={handleCancel} className="text-sm font-medium text-slate-600 hover:text-slate-800 dark:text-slate-400">Cancel</button>
                            <button onClick={handleSave} className="inline-flex items-center px-4 py-2 text-sm font-semibold rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-all">Save Changes</button>
                        </>
                    ) : (
                        <button onClick={() => setIsEditing(true)} className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 shadow-sm transition-all">
                            <PencilSquareIcon className="w-4 h-4 mr-2 text-slate-400" />
                            Edit
                        </button>
                    )}
                </div>
            </header>

            {/* Tabs */}
            <div className="px-6 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <nav className="flex space-x-2" aria-label="Tabs">
                    <button onClick={() => setActiveTab('intelligence')} className={tabClass('intelligence')}>Intelligence Board</button>
                    <button onClick={() => setActiveTab('applications')} className={tabClass('applications')}>Applications <span className="ml-1.5 bg-slate-100 text-slate-600 py-0.5 px-1.5 rounded-full text-xs">{applications.filter(a => a.company_id === company.company_id).length}</span></button>
                    <button onClick={() => setActiveTab('engagement')} className={tabClass('engagement')}>Engagement Hub</button>
                </nav>
            </div>

            {/* Main Content */}
            <main className="p-6 max-w-7xl mx-auto">
                {error && <div className="mb-6 rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</div>}

                {/* --- INTELLIGENCE TAB --- */}
                {activeTab === 'intelligence' && (
                    <div className="animate-fade-in space-y-8">

                        {/* Section: Strategic Foundation */}
                        <section>
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                                <span className="w-1 h-6 bg-blue-500 rounded-full"></span>
                                Strategic Foundation
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <InfoCard title="Mission" field={editableCompany.mission} isEditing={isEditing} onChange={v => handleFieldChange('mission', v)} className="md:col-span-2" />
                                <InfoCard title="Core Values" field={editableCompany.values} isEditing={isEditing} onChange={v => handleFieldChange('values', v)} />
                                <InfoCard title="Culture Keywords" field={editableCompany.cultural_keywords} isEditing={isEditing} onChange={v => handleFieldChange('cultural_keywords', v)} />
                                <InfoCard title="Stated Goals" field={editableCompany.goals} isEditing={isEditing} onChange={v => handleFieldChange('goals', v)} className="md:col-span-2" />
                            </div>
                        </section>

                        {/* Section: Market & Competitive Landscape */}
                        <section>
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                                <span className="w-1 h-6 bg-purple-500 rounded-full"></span>
                                Market & Competitive Landscape
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="md:col-span-2">
                                    <CompetitorsWidget
                                        field={editableCompany.competitors}
                                        allCompanies={allCompanies}
                                        isEditing={isEditing}
                                        onChange={v => handleFieldChange('competitors', v)}
                                        onOpenCreateCompanyModal={onOpenCreateCompanyModal}
                                        onNavigateToCompany={(id) => {
                                            // Ideally we'd have a prop for this, but for now we can maybe piggyback or just allow the parent to handle?
                                            // The simplest way strictly within this view's props is tricky without a direct 'onSelectCompany' prop.
                                            // We'll assume the user might need to go "Back" then select. 
                                            // ACTUALLY: Let's just log for now or add a TODO, as we don't have a direct 'onSwitchCompany' prop.
                                            // Wait, we can implement it if we pass a callback. For now, we'll keep it visual.
                                            console.log("Navigate to company:", id);
                                            // In a real app we'd likely use router.push(`/company/${id}`)
                                            window.location.hash = `company=${id}`; // Hacky temp solution unless we have a callback
                                        }}
                                    />
                                </div>
                                <InfoCard title="Market Position" field={editableCompany.market_position} isEditing={isEditing} onChange={v => handleFieldChange('market_position', v)} className="md:col-span-2" />
                                <InfoCard title="Economic Model" field={editableCompany.economic_model} isEditing={isEditing} onChange={v => handleFieldChange('economic_model', v)} />
                                <InfoCard title="Funding Status" field={editableCompany.funding_status} isEditing={isEditing} onChange={v => handleFieldChange('funding_status', v)} />
                            </div>
                        </section>

                        {/* Section: Operational Deep Dive */}
                        <section>
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                                <span className="w-1 h-6 bg-teal-500 rounded-full"></span>
                                Operational Deep Dive
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <InfoCard title="Operating Model" field={editableCompany.operating_model} isEditing={isEditing} onChange={v => handleFieldChange('operating_model', v)} />
                                <InfoCard title="Known Tech Stack" field={editableCompany.known_tech_stack} isEditing={isEditing} onChange={v => handleFieldChange('known_tech_stack', v)} />
                                <InfoCard title="Organizational Headwinds" field={editableCompany.org_headwinds} isEditing={isEditing} onChange={v => handleFieldChange('org_headwinds', v)} className="md:col-span-2" />
                            </div>
                        </section>

                        {/* Section: Leadership & Talent */}
                        <section>
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                                <span className="w-1 h-6 bg-orange-500 rounded-full"></span>
                                Leadership & Talent
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* <InfoCard title="Leadership Pedigree" field={editableCompany.leadership_pedigree_and_success_mythology} isEditing={isEditing} onChange={v => handleFieldChange('leadership_pedigree_and_success_mythology', v)} /> */}
                                <InfoCard title="Talent Expectations" field={editableCompany.talent_expectations} isEditing={isEditing} onChange={v => handleFieldChange('talent_expectations', v)} />
                                <InfoCard title="Internal Gripes / Challenges" field={editableCompany.internal_gripes} isEditing={isEditing} onChange={v => handleFieldChange('internal_gripes', v)} className="md:col-span-2 border-l-4 border-l-red-400" />
                            </div>
                        </section>

                        {/* Section: Recent News */}
                        <InfoCard title="Recent Signals & News" field={editableCompany.news} isEditing={isEditing} onChange={v => handleFieldChange('news', v)} className="bg-slate-100/50" />
                    </div>
                )}

                {/* --- APPLICATIONS TAB --- */}
                {activeTab === 'applications' && (
                    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
                        {applications.filter(app => app.company_id === company.company_id).length > 0 ? (
                            <ul role="list" className="divide-y divide-slate-200 dark:divide-slate-700">
                                {applications.filter(app => app.company_id === company.company_id).map(app => (
                                    <li key={app.job_application_id} className="flex justify-between gap-x-6 px-6 py-5 hover:bg-slate-50 cursor-pointer transition-colors" onClick={() => onViewApplication(app.job_application_id)}>
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
                            <div className="p-12 text-center">
                                <p className="text-sm text-slate-500">No active applications for this company.</p>
                                <button className="mt-4 text-blue-600 hover:text-blue-500 text-sm font-medium">Create Application</button>
                            </div>
                        )}
                    </div>
                )}

                {/* --- ENGAGEMENT TAB (Minimally Refactored for now) --- */}
                {activeTab === 'engagement' && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-2 space-y-6">
                            {/* Generator */}
                            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                                <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Draft LinkedIn Comment</h3>
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Strategies</label>
                                        <div className="flex rounded-md shadow-sm">
                                            <button type="button" onClick={() => setCommentTone('Standard')} className={`px-4 py-2 text-xs font-medium border border-slate-300 dark:border-slate-600 rounded-l-md ${commentTone === 'Standard' ? 'bg-blue-600 text-white z-10' : 'bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600'}`}>Standard</button>
                                            <button type="button" onClick={() => setCommentTone('Expertise-Driven')} className={`-ml-px px-4 py-2 text-xs font-medium border border-slate-300 dark:border-slate-600 rounded-r-md ${commentTone === 'Expertise-Driven' ? 'bg-blue-600 text-white z-10' : 'bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600'}`}>Expertise-Driven</button>
                                        </div>
                                    </div>
                                    <textarea
                                        rows={4}
                                        value={postText}
                                        onChange={(e) => setPostText(e.target.value)}
                                        className="w-full text-sm rounded-lg border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900/50 p-3"
                                        placeholder="Paste the LinkedIn post here..."
                                    />
                                    <div className="flex justify-end">
                                        <button onClick={() => {/* TODO */ }} disabled={isGenerating} className="px-4 py-2 text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400">
                                            {isGenerating ? <LoadingSpinner className="w-3 h-3" /> : 'Generate Magic Comment'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Contacts Sidebar */}
                        <div className="space-y-6">
                            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="text-base font-semibold text-slate-900 dark:text-white">Key Contacts</h3>
                                    <button onClick={() => onOpenContactModal({ company_id: company.company_id })} className="text-blue-600 hover:text-blue-500 text-xs font-medium">+ Add</button>
                                </div>
                                <div className="space-y-3">
                                    {contacts.filter(c => c.company_id === company.company_id).map(c => (
                                        <div key={c.contact_id} className="flex justify-between items-start group">
                                            <div>
                                                <p className="text-sm font-medium text-slate-900 dark:text-white">{c.first_name} {c.last_name}</p>
                                                <p className="text-xs text-slate-500">{c.job_title}</p>
                                            </div>
                                            <button onClick={() => onOpenContactModal(c)} className="opacity-0 group-hover:opacity-100 text-xs text-slate-400 hover:text-blue-500">Edit</button>
                                        </div>
                                    ))}
                                    {contacts.filter(c => c.company_id === company.company_id).length === 0 && (
                                        <p className="text-xs text-slate-400 italic">No contacts added.</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};
