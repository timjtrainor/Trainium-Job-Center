import React, { useState, useMemo, useEffect } from 'react';
import { JobApplication, Company, Resume, DateInfo, Status, KeywordsResult, GuidanceResult, Prompt, PromptContext, JobProblemAnalysisResult, KeywordDetail, CoreProblemAnalysis, Education, Certification, WorkExperience, SkillSection, InterviewPayload, Interview, Contact, ResumeHeader, UserProfile, SuggestedContact, InterviewPrep, StrategicNarrative, Offer, InfoField, JobApplicationPayload, ApplicationDetailTab } from '../types';
import { LoadingSpinner, SparklesIcon, PlusCircleIcon, TrashIcon, StrategyIcon, MicrophoneIcon, RocketLaunchIcon } from './IconComponents';
import * as geminiService from '../services/geminiService';
import { MarkdownPreview } from './MarkdownPreview';
import { INTERVIEW_TYPES } from '../constants';
import { AIGeneratedContentReview } from './AIGeneratedContentReview';

interface ApplicationDetailViewProps {
    application: JobApplication;
    company: Company;
    allCompanies: Company[];
    contacts: Contact[];
    onBack: () => void;
    onUpdate: (payload: JobApplicationPayload) => void;
    onDeleteApplication: (appId: string) => void;
    onResumeApplication: (app: JobApplication) => void;
    onReanalyze: () => void;
    isReanalyzing: boolean;
    prompts: Prompt[];
    statuses: Status[];
    userProfile: UserProfile | null;
    activeNarrative: StrategicNarrative | null;
    onSaveInterview: (interviewData: InterviewPayload, interviewId?: string) => Promise<void>;
    onDeleteInterview: (interviewId: string) => Promise<void>;
    onGenerateInterviewPrep: (app: JobApplication, interview: Interview) => Promise<void>;
    onGenerateRecruiterScreenPrep: (app: JobApplication, interview: Interview) => Promise<void>;
    onOpenContactModal: (contact?: Partial<Contact> | null) => void;
    onOpenOfferModal: (app: JobApplication, offer?: Offer) => void;
    onGenerate90DayPlan: (app: JobApplication) => void;
    onAddQuestionToCommonPrep: (question: string) => void;
    onOpenStrategyStudio: (interview: Interview) => void;
    onNavigateToStudio: (app: JobApplication) => void;
    handleLaunchCopilot: (app: JobApplication, interview: Interview) => void; // Added prop
    isLoading: boolean;
    onOpenDebriefStudio: (interview: Interview) => void;
    initialTab?: ApplicationDetailTab;
    onTabChange?: (tab: ApplicationDetailTab) => void;
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
}

const formatDate = (date: DateInfo, format: 'short' | 'long' | 'year' = 'long'): string => {
    if (!date || !date.month || !date.year) return '';
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    if (format === 'year') return date.year.toString();
    if (format === 'short') return `${monthNames[date.month - 1].substring(0,3)} ${date.year}`;
    return `${monthNames[date.month - 1]} ${date.year}`;
};

const DetailItem = ({ label, value, children, isLink = false }: { label: string, value?: string | number | null, children?: React.ReactNode, isLink?: boolean }) => (
    <div>
        <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</dt>
        <dd className="mt-1 text-sm text-slate-900 dark:text-slate-100">
            {children ? children : isLink && value ? (
                <a href={value as string} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline dark:text-blue-400 break-all">
                    {value}
                </a>
            ) : (
                value || 'N/A'
            )}
        </dd>
    </div>
);


const ResumeViewer = ({ resume }: { resume: Resume | undefined | null }) => {
    if (!resume) {
        return <div className="p-4 text-center text-slate-500">Final resume not available for this application.</div>;
    }
    const { header, summary, work_experience, education, skills, certifications } = resume;
    return (
        <div className="p-4 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700 font-sans text-slate-800 dark:text-slate-200">
            {/* Header */}
            <div className="text-center mb-4">
                <h3 className="text-2xl font-bold">{header?.first_name} {header?.last_name}</h3>
                <p className="text-lg font-medium">{header?.job_title}</p>
                <p className="text-xs">{header?.city}, {header?.state} | {header?.email} | {header?.phone_number}</p>
                <p className="text-xs">{header?.links?.join(' | ')}</p>
            </div>
            
            {/* Summary */}
            <div className="mb-4">
                <h4 className="font-bold text-sm uppercase border-b border-slate-300 dark:border-slate-600 pb-1 mb-2">Summary</h4>
                <p className="text-sm">{summary?.paragraph}</p>
                <ul className="list-disc pl-5 mt-1 text-sm space-y-1">
                    {summary?.bullets?.map((b, i) => <li key={i}>{b}</li>)}
                </ul>
            </div>

            {/* Work Experience */}
            <div className="mb-4">
                 <h4 className="font-bold text-sm uppercase border-b border-slate-300 dark:border-slate-600 pb-1 mb-2">Experience</h4>
                 {work_experience?.map((job, idx) => (
                    <div key={idx} className="mb-3">
                        <div className="flex justify-between items-baseline"><p className="font-bold text-base">{job.company_name}</p><p className="text-xs">{formatDate(job.start_date)} - {job.is_current ? 'Present' : formatDate(job.end_date)}</p></div>
                        <div className="flex justify-between items-baseline"><p className="font-semibold italic text-sm">{job.job_title}</p><p className="text-xs">{job.location}</p></div>
                        <ul className="list-disc pl-5 mt-1 text-sm space-y-1">
                            {job.accomplishments?.map((acc, accIdx) => <li key={accIdx}>{acc.description}</li>)}
                        </ul>
                    </div>
                 ))}
            </div>

            {/* Skills */}
            <div className="mb-4">
                <h4 className="font-bold text-sm uppercase border-b border-slate-300 dark:border-slate-600 pb-1 mb-2">Skills</h4>
                {skills?.map((s, i) => <p key={i} className="text-sm"><span className="font-semibold">{s.heading}:</span> {s.items.join(', ')}</p>)}
            </div>

            {/* Education */}
            {education?.length > 0 && (
                <div className="mb-4">
                    <h4 className="font-bold text-sm uppercase border-b border-slate-300 dark:border-slate-600 pb-1 mb-2">Education</h4>
                    {education.map((edu, idx) => (
                        <div key={idx} className="mb-2">
                             <div className="flex justify-between items-baseline"><p className="font-bold text-base">{edu.school}</p><p className="text-xs">{edu.start_year} - {edu.end_year}</p></div>
                             <p className="text-sm">{edu.degree} in {edu.major.join(', ')}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};


export const ApplicationDetailView = (props: ApplicationDetailViewProps) => {
    const { application, company, contacts, allCompanies, onBack, onUpdate, onDeleteApplication, onResumeApplication, onReanalyze, isReanalyzing, prompts, statuses, userProfile, activeNarrative, onSaveInterview, onDeleteInterview, onGenerateInterviewPrep, onGenerateRecruiterScreenPrep, onOpenContactModal, onOpenOfferModal, onGenerate90DayPlan, onAddQuestionToCommonPrep, onOpenStrategyStudio, onNavigateToStudio, handleLaunchCopilot, isLoading, onOpenDebriefStudio, initialTab, onTabChange, debugCallbacks } = props;
    
    const [activeTab, setActiveTab] = useState<ApplicationDetailTab>(initialTab || 'overview');
    const [isEditing, setIsEditing] = useState(false);
    const [editableApp, setEditableApp] = useState<JobApplication>(application);
    const [editingInterviewId, setEditingInterviewId] = useState<string | null>(null);
    const [editableInterview, setEditableInterview] = useState<Partial<InterviewPayload>>({});
    const [isGeneratingPrep, setIsGeneratingPrep] = useState<Record<string, boolean>>({});
    const [selectedContextContact, setSelectedContextContact] = useState<Contact | null>(null);
    const [isContextCompanyView, setIsContextCompanyView] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        setEditableApp(application);
    }, [application]);

    useEffect(() => {
        if (initialTab) {
            setActiveTab(initialTab);
        }
    }, [initialTab]);
    
    useEffect(() => {
        if (activeTab !== 'interviews') {
            setSelectedContextContact(null);
            setIsContextCompanyView(true);
        }
    }, [activeTab]);

    const relevantContactsForInterview = useMemo(() => {
        if (!application || !contacts || !allCompanies) return [];

        const applicationCompanyId = application.company_id;
        const recruitingFirmIds = new Set(
            allCompanies.filter(c => c.is_recruiting_firm).map(c => c.company_id)
        );

        return contacts.filter(contact => {
            if (contact.company_id === applicationCompanyId) {
                return true;
            }
            if (contact.company_id && recruitingFirmIds.has(contact.company_id)) {
                return true;
            }
            if (!contact.company_id) {
                return true;
            }
            return false;
        });
    }, [application, contacts, allCompanies]);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const {
                job_application_id,
                user_id,
                status,
                messages,
                interviews,
                offers,
                created_at,
                ...payloadData
            } = editableApp;
    
            const payload: JobApplicationPayload = {
                ...payloadData,
                status_id: status?.status_id
            };
    
            await onUpdate(payload);
            setIsEditing(false);
        } catch (e) {
            console.error(e);
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        setEditableApp(application);
        setIsEditing(false);
    };

    const handleSaveInterview = async (payload: InterviewPayload, id?: string) => {
        setIsSaving(true);
        try {
            await onSaveInterview(payload, id);
            setEditingInterviewId(null);
            setEditableInterview({});
        } catch (e) {
            console.error(e);
        } finally {
            setIsSaving(false);
        }
    };
    
    const handleGeneratePrep = async (interview: Interview, isQuickPrep: boolean) => {
        setIsGeneratingPrep(prev => ({ ...prev, [interview.interview_id]: true }));
        try {
            if (isQuickPrep) {
                await onGenerateRecruiterScreenPrep(application, interview);
            } else {
                await onGenerateInterviewPrep(application, interview);
            }
        } catch (e) {
            console.error("Failed to generate interview prep:", e);
        } finally {
            setIsGeneratingPrep(prev => ({ ...prev, [interview.interview_id]: false }));
        }
    };

    const tabClass = (tabName: ApplicationDetailTab) => 
        `px-3 py-2 font-medium text-sm rounded-md cursor-pointer transition-colors ` +
        (activeTab === tabName 
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300' 
            : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200');
    
    const analysis = application.job_problem_analysis_result;
    const inputClass = "mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
    const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";

    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700 animate-fade-in">
            <header className="mb-6 flex justify-between items-start">
                <div>
                    <button onClick={onBack} className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 mb-2">
                        &larr; Back to Applications
                    </button>
                    <div className="flex items-center gap-3 mb-2">
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{company.company_name}</h2>
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                            application.workflow_mode === 'ai_generated'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                                : application.workflow_mode === 'fast_track'
                                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300'
                                : 'bg-gray-100 text-gray-800 dark:bg-gray-900/50 dark:text-gray-300'
                        }`}>
                            {application.workflow_mode === 'ai_generated' ? '🚀 Full AI Application' :
                             application.workflow_mode === 'fast_track' ? '⚡ Fast Track Application' :
                             '📝 Manual Application'}
                        </span>
                    </div>
                    <p className="text-lg text-slate-600 dark:text-slate-300">{application.job_title}</p>
                </div>
                 <div className="flex gap-2">
                    {application.status?.status_name === 'Interviewing' && (
                        <button onClick={() => onNavigateToStudio(application)} className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm">
                            <MicrophoneIcon className="h-5 w-5"/>
                            Practice in Studio
                        </button>
                    )}
                 </div>
            </header>
            
            <div className="border-b border-slate-200 dark:border-slate-700">
                <nav className="-mb-px flex space-x-4" aria-label="Tabs">
                    <button onClick={() => onTabChange?.('overview')} className={tabClass('overview')}>Overview</button>
                    <button onClick={() => onTabChange?.('analysis')} className={tabClass('analysis')}>AI Analysis</button>
                    <button onClick={() => onTabChange?.('resume')} className={tabClass('resume')}>Final Resume</button>
                    <button onClick={() => onTabChange?.('ai-content')} className={tabClass('ai-content')}>
                        <div className="flex items-center gap-1">
                            <SparklesIcon className="h-4 w-4" />
                            AI Generated
                        </div>
                    </button>
                    <button onClick={() => onTabChange?.('interviews')} className={tabClass('interviews')}>Interviews</button>
                </nav>
            </div>
            
            <div className="mt-6">
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                         <div className="flex justify-end gap-2">
                            {isEditing ? (
                                <>
                                    <button onClick={handleCancel} className="px-4 py-2 text-sm font-medium rounded-lg text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 border border-slate-300 dark:border-slate-500 shadow-sm">Cancel</button>
                                    <button onClick={handleSave} disabled={isSaving} className="px-4 py-2 text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 shadow-sm disabled:opacity-50">{isSaving ? <LoadingSpinner/> : 'Save'}</button>
                                </>
                            ) : (
                                 <button onClick={() => setIsEditing(true)} className="px-4 py-2 text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-sm">Edit Details</button>
                            )}
                        </div>
                        <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                            <DetailItem label="Company" value={company.company_name} />
                            <DetailItem label="Job Title" value={isEditing ? undefined : editableApp.job_title}>
                                {isEditing && <input type="text" value={editableApp.job_title || ''} onChange={e => setEditableApp({...editableApp, job_title: e.target.value})} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm" />}
                            </DetailItem>
                            <DetailItem label="Date Applied" value={new Date(editableApp.date_applied).toLocaleDateString()} />
                             <DetailItem label="Status" value={isEditing ? undefined : editableApp.status?.status_name}>
                                {isEditing && <select value={editableApp.status?.status_id || ''} onChange={e => setEditableApp(prev => ({...prev, status: statuses.find(s => s.status_id === e.target.value)}))} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm">{statuses.map(s => <option key={s.status_id} value={s.status_id}>{s.status_name}</option>)}</select>}
                            </DetailItem>
                            <DetailItem label="Salary" value={isEditing ? undefined : editableApp.salary}>
                                 {isEditing && <input type="text" value={editableApp.salary || ''} onChange={e => setEditableApp({...editableApp, salary: e.target.value})} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm" />}
                            </DetailItem>
                            <DetailItem label="Location" value={isEditing ? undefined : editableApp.location}>
                                 {isEditing && <input type="text" value={editableApp.location || ''} onChange={e => setEditableApp({...editableApp, location: e.target.value})} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm" />}
                            </DetailItem>
                             <DetailItem label="Remote Status" value={isEditing ? undefined : editableApp.remote_status}>
                                {isEditing && <select value={editableApp.remote_status || ''} onChange={e => setEditableApp({...editableApp, remote_status: e.target.value as any})} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm"><option value="">Select...</option><option value="On-site">On-site</option><option value="Hybrid">Hybrid</option><option value="Remote">Remote</option></select>}
                            </DetailItem>
                            <DetailItem label="Job Link" value={editableApp.job_link} isLink />
                             <div className="sm:col-span-2">
                                <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Job Description</dt>
                                <dd className="mt-2 p-3 border rounded-md border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 max-h-60 overflow-y-auto">
                                    <MarkdownPreview markdown={application.job_description} />
                                </dd>
                            </div>
                        </dl>
                    </div>
                )}
                
                {activeTab === 'analysis' && (
                     <div className="space-y-6">
                        <div className="flex justify-between items-center pb-4 border-b border-slate-200 dark:border-slate-700">
                            <h3 className="text-xl font-bold text-slate-900 dark:text-white">AI Analysis</h3>
                            <button
                                onClick={onReanalyze}
                                disabled={isReanalyzing}
                                className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-semibold rounded-md bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-300 ring-1 ring-inset ring-indigo-200 dark:ring-indigo-500/30 hover:bg-indigo-100 dark:hover:bg-indigo-500/20 disabled:opacity-50"
                            >
                                {isReanalyzing ? <LoadingSpinner /> : <SparklesIcon className="h-4 w-4" />}
                                Rerun Full Analysis
                            </button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-4">
                                <h4 className="font-semibold text-slate-800 dark:text-slate-200">Core Problem Analysis</h4>
                                 <p><strong className="text-slate-500 dark:text-slate-400">Context:</strong> {analysis?.core_problem_analysis?.business_context}</p>
                                 <p><strong className="text-slate-500 dark:text-slate-400">Problem:</strong> {analysis?.core_problem_analysis?.core_problem}</p>
                                 <p><strong className="text-slate-500 dark:text-slate-400">Importance:</strong> {analysis?.core_problem_analysis?.strategic_importance}</p>
                                 <div><h4 className="font-semibold text-slate-700 dark:text-slate-300">Key Success Metrics</h4><ul className="list-disc pl-5">{(analysis?.key_success_metrics || []).map((m,i)=><li key={i}>{m}</li>)}</ul></div>
                                 <div><h4 className="font-semibold text-slate-700 dark:text-slate-300">Potential Blockers</h4><ul className="list-disc pl-5">{(analysis?.potential_blockers || []).map((b,i)=><li key={i}>{b}</li>)}</ul></div>
                            </div>
                             <div className="space-y-4">
                                <h4 className="font-semibold text-slate-800 dark:text-slate-200">Resume Guidance</h4>
                                <div><h4 className="font-semibold text-slate-700 dark:text-slate-300">Hard Keywords</h4><div className="flex flex-wrap gap-1 mt-1">{(application.keywords as KeywordsResult)?.hard_keywords?.map(kw => <span key={kw.keyword} className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">{kw.keyword}</span>)}</div></div>
                                <div><h4 className="font-semibold text-slate-700 dark:text-slate-300">Soft Keywords</h4><div className="flex flex-wrap gap-1 mt-1">{(application.keywords as KeywordsResult)?.soft_keywords?.map(kw => <span key={kw.keyword} className="px-2 py-1 text-xs rounded-full bg-sky-100 text-sky-800 dark:bg-sky-900/50 dark:text-sky-300">{kw.keyword}</span>)}</div></div>
                                <div><h4 className="font-semibold text-slate-700 dark:text-slate-300">Summary Guidance</h4><p>{(application.guidance as GuidanceResult)?.summary?.join(' ')}</p></div>
                             </div>
                        </div>
                    </div>
                )}

                {activeTab === 'resume' && (
                    <ResumeViewer resume={application.tailored_resume_json} />
                )}

                {activeTab === 'ai-content' && (
                    <AIGeneratedContentReview application={application} />
                )}

                {activeTab === 'interviews' && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-2 space-y-4">
                            {(application.interviews || []).map(interview => {
                                const todayString = new Date().toISOString().split('T')[0];
                                const isPastOrToday = interview.interview_date ? interview.interview_date <= todayString : false;
                                const isRecruiterScreen = interview.interview_type === "Step 6.1: Recruiter Screen";
                                const hasPrepData = interview.ai_prep_data && Object.values(interview.ai_prep_data).some(val => Array.isArray(val) ? val.length > 0 : !!val);

                                return (
                                <div key={interview.interview_id} className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h4 className="font-bold text-slate-800 dark:text-slate-200">{interview.interview_type}</h4>
                                            <p className="text-sm text-slate-500 dark:text-slate-400">{interview.interview_date ? new Date(interview.interview_date+'T00:00:00Z').toLocaleDateString() : 'Date TBD'}</p>
                                            <div className="mt-2 flex flex-wrap gap-2">
                                                {(interview.interview_contacts || []).map(c => {
                                                    const contact = contacts.find(storedContact => storedContact.contact_id === c.contact_id);
                                                    return (
                                                        <button key={c.contact_id} onClick={() => {
                                                            setSelectedContextContact(contact || null);
                                                            setIsContextCompanyView(false);
                                                        }} className="text-xs font-semibold px-2 py-1 rounded-full bg-blue-100 text-blue-800 hover:bg-blue-200 dark:bg-blue-900/50 dark:text-blue-300 dark:hover:bg-blue-900">
                                                            {c.first_name} {c.last_name}
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {isPastOrToday && (
                                                <button onClick={() => onOpenDebriefStudio(interview)} className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-md bg-yellow-50 dark:bg-yellow-500/10 text-yellow-600 dark:text-yellow-300 ring-1 ring-inset ring-yellow-200 dark:ring-yellow-500/30 hover:bg-yellow-100 dark:hover:bg-yellow-500/20">
                                                    Debrief
                                                </button>
                                            )}
                                            <button onClick={() => handleLaunchCopilot(application, interview)} disabled={isLoading} className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-md bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-300 ring-1 ring-inset ring-green-200 dark:ring-green-500/30 hover:bg-green-100 dark:hover:bg-green-500/20 disabled:opacity-50" title="Launch Interview Co-pilot">
                                                <RocketLaunchIcon className="h-4 w-4"/> Co-pilot
                                            </button>
                                             <button onClick={() => onOpenStrategyStudio(interview)} disabled={isLoading} className="p-1.5 text-xs font-semibold rounded-md bg-white dark:bg-slate-700 ring-1 ring-inset ring-slate-300 dark:ring-slate-600 inline-flex items-center gap-1.5 hover:bg-slate-50" title="Open Strategy Studio">
                                                <StrategyIcon className="h-4 w-4"/> Studio
                                             </button>
                                             <button onClick={() => { setEditingInterviewId(interview.interview_id); setEditableInterview({ interview_type: interview.interview_type, interview_date: interview.interview_date, notes: interview.notes, contact_ids: (interview.interview_contacts || []).map(c => c.contact_id) }); }} className="p-1.5 text-xs font-semibold rounded-md bg-white dark:bg-slate-700 ring-1 ring-inset ring-slate-300 dark:ring-slate-600">Edit</button>
                                             <button onClick={() => onDeleteInterview(interview.interview_id)} className="p-1 text-red-500 hover:text-red-400" title="Delete Interview"><TrashIcon className="h-5 w-5"/></button>
                                        </div>
                                    </div>
                                    {hasPrepData ? (
                                        <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                                            <details><summary className="text-sm font-semibold cursor-pointer">View AI Prep</summary>
                                                <div className="text-xs mt-2 space-y-2 prose prose-xs dark:prose-invert max-w-none">
                                                   <p><strong>Focus Areas:</strong> {(interview.ai_prep_data.keyFocusAreas || []).join(', ')}</p>
                                                   <div><strong>Potential Questions They Might Ask You:</strong><ul>{(interview.ai_prep_data.potentialQuestions || []).map(q => <li key={q.question}><strong>{q.question}</strong><br/><em>Strategy: {q.strategy}</em></li>)}</ul></div>
                                                   <div><strong>Strategic Questions for You to Ask Them:</strong><ul>{(interview.ai_prep_data.questionsToAsk || []).map((q, i) => <li key={i}>{q}</li>)}</ul></div>
                                                   <div><strong>Potential Red Flags to Watch For:</strong><ul>{(interview.ai_prep_data.redFlags || []).map((flag, i) => <li key={i}>{flag}</li>)}</ul></div>
                                                </div>
                                            </details>
                                        </div>
                                    ) : (
                                        <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700 text-center">
                                            <button onClick={() => handleGeneratePrep(interview, isRecruiterScreen)} disabled={isGeneratingPrep[interview.interview_id]} className="text-sm font-semibold text-blue-600 hover:underline">
                                                {isGeneratingPrep[interview.interview_id] ? <LoadingSpinner/> : (isRecruiterScreen ? 'Generate Quick Prep' : 'Generate Prep with AI')}
                                            </button>
                                        </div>
                                    )}
                                </div>
                                );
                            })}
                             
                             {editingInterviewId ? (
                                <div className="mt-4 p-4 rounded-lg bg-slate-100 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-600">
                                    <h4 className="font-bold text-slate-800 dark:text-slate-200 mb-3">{editingInterviewId === 'new' ? 'Add New Interview' : 'Edit Interview'}</h4>
                                    <div className="space-y-4">
                                        <div><label className={labelClass}>Interview Type</label><select value={editableInterview.interview_type || ''} onChange={e => setEditableInterview(prev => ({...prev, interview_type: e.target.value}))} className={inputClass}><option value="">Select type...</option>{INTERVIEW_TYPES.map(type => <option key={type} value={type}>{type}</option>)}</select></div>
                                        <div><label className={labelClass}>Date</label><input type="date" value={editableInterview.interview_date || ''} onChange={e => setEditableInterview(prev => ({...prev, interview_date: e.target.value}))} className={inputClass} /></div>
                                        <div>
                                            <label className={labelClass}>Interviewers</label>
                                            <div className="mt-1 max-h-32 overflow-y-auto border rounded-md p-2 space-y-1 bg-white dark:bg-slate-800">
                                                {relevantContactsForInterview.map(contact => (
                                                    <div key={contact.contact_id} className="flex items-center"><input type="checkbox" id={`contact-${contact.contact_id}`} checked={editableInterview.contact_ids?.includes(contact.contact_id) || false} onChange={e => { const { checked } = e.target; setEditableInterview(prev => ({...prev, contact_ids: checked ? [...(prev.contact_ids || []), contact.contact_id] : (prev.contact_ids || []).filter(id => id !== contact.contact_id)})); }} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" /><label htmlFor={`contact-${contact.contact_id}`} className="ml-2 text-sm text-slate-700 dark:text-slate-300">{contact.first_name} {contact.last_name}</label></div>
                                                ))}
                                                {relevantContactsForInterview.length === 0 && (
                                                    <p className="text-xs text-slate-500 dark:text-slate-400 p-2">
                                                        No relevant contacts found. Add contacts for "{company.company_name}" or for recruiting firms in the Engagement Hub.
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                        <div><label className={labelClass}>Notes</label><textarea rows={4} value={editableInterview.notes || ''} onChange={e => setEditableInterview(prev => ({...prev, notes: e.target.value}))} className={inputClass} /></div>
                                        <div className="flex justify-end gap-2"><button onClick={() => { setEditingInterviewId(null); setEditableInterview({}); }} className="px-3 py-1.5 text-sm font-semibold rounded-md bg-white dark:bg-slate-700 ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600">Cancel</button><button onClick={() => handleSaveInterview({ job_application_id: application.job_application_id, ...editableInterview }, editingInterviewId === 'new' ? undefined : editingInterviewId)} disabled={isSaving} className="px-3 py-1.5 text-sm font-semibold rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50">{isSaving ? <LoadingSpinner/> : 'Save'}</button></div>
                                    </div>
                                </div>
                             ) : (
                                <button onClick={() => { setEditingInterviewId('new'); setEditableInterview({ interview_date: new Date().toISOString().split('T')[0] }); }} className="w-full flex justify-center items-center gap-2 py-3 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:border-slate-400 dark:hover:border-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition">
                                    <PlusCircleIcon className="h-5 w-5" /> Add Interview
                                </button>
                             )}
                        </div>
                         <div className="sticky top-8">
                            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
                                <div className="flex justify-between items-center mb-2">
                                    <h4 className="font-bold text-slate-800 dark:text-slate-200">Context Hub</h4>
                                    {!isContextCompanyView && <button onClick={() => setIsContextCompanyView(true)} className="text-xs font-semibold text-blue-600 hover:underline">&larr; Show Company</button>}
                                </div>
                                {isContextCompanyView ? (
                                    <div className="space-y-3 text-xs">
                                        <DetailItem label="Mission" value={company.mission?.text} />
                                        <DetailItem label="Values" value={company.values?.text} />
                                        <DetailItem label="Challenges/Issues" value={company.issues?.text} />
                                        <DetailItem label="Goals" value={company.goals?.text} />
                                        <DetailItem label="Strategic Initiatives" value={company.strategic_initiatives?.text} />
                                        <DetailItem label="Recent News" value={company.news?.text} />
                                    </div>
                                ) : (
                                    <div className="space-y-3 text-xs">
                                        {selectedContextContact ? (
                                            <>
                                                <DetailItem label="Name" value={`${selectedContextContact.first_name} ${selectedContextContact.last_name}`} />
                                                <DetailItem label="Title" value={selectedContextContact.job_title} />
                                                <DetailItem label="Persona" value={selectedContextContact.persona} />
                                                <DetailItem label="About">
                                                    <p className="whitespace-pre-wrap max-h-48 overflow-y-auto">{selectedContextContact.linkedin_about || 'N/A'}</p>
                                                </DetailItem>
                                            </>
                                        ) : (
                                            <p className="text-xs text-slate-500 dark:text-slate-400">Click an interviewer to see their details.</p>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
