import React, { useState, useMemo, useEffect } from 'react';
import { JobApplication, Company, Resume, DateInfo, Status, KeywordsResult, GuidanceResult, Prompt, PromptContext, JobProblemAnalysisResult, JobProblemAnalysisResultV1, JobProblemAnalysisResultV2, KeywordDetail, CoreProblemAnalysis, Education, Certification, WorkExperience, SkillSection, InterviewPayload, Interview, Contact, ResumeHeader, UserProfile, SuggestedContact, InterviewPrep, StrategicNarrative, Offer, InfoField, JobApplicationPayload, ApplicationDetailTab, ReviewedJob } from '../types';
import { LoadingSpinner, SparklesIcon, PlusCircleIcon, TrashIcon, StrategyIcon, MicrophoneIcon, RocketLaunchIcon, CubeIcon } from './IconComponents';
import * as geminiService from '../services/geminiService';
import * as apiService from '../services/apiService';
import { MarkdownPreview } from './MarkdownPreview';
import { INTERVIEW_TYPES } from '../constants';
import * as resumeExport from '../utils/resumeExport';
import { v4 as uuidv4 } from 'uuid';
import { ApplicationQuestion, Sprint, SprintActionPayload } from '../types';
import { CheckIcon, DocumentTextIcon, ClipboardDocumentListIcon, ClipboardDocumentCheckIcon, BeakerIcon, XMarkIcon } from './IconComponents';
import { useToast } from '../hooks/useToast';

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
    sprint?: Sprint | null;
    onAddActions?: (sprintId: string, actions: SprintActionPayload[]) => Promise<void>;
}

const formatDate = (date: DateInfo | string | undefined, format: 'short' | 'long' | 'year' = 'long'): string => {
    if (!date) return '';
    if (typeof date === 'string') {
        const d = new Date(date);
        if (isNaN(d.getTime())) return date;
        const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
        if (format === 'year') return d.getFullYear().toString();
        if (format === 'short') return `${monthNames[d.getMonth()].substring(0, 3)} ${d.getFullYear()}`;
        return `${monthNames[d.getMonth()]} ${d.getFullYear()}`;
    }
    if (!date.month || !date.year) return '';
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    if (format === 'year') return date.year.toString();
    if (format === 'short') return `${monthNames[date.month - 1].substring(0, 3)} ${date.year}`;
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


const ResumeViewer = ({ resume, version, companyName }: { resume: any, version?: number, companyName: string }) => {
    const [copySuccess, setCopySuccess] = useState(false);
    const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
    const [isGeneratingDocx, setIsGeneratingDocx] = useState(false);

    if (!resume) {
        return <div className="p-12 text-center text-slate-500 italic border border-dashed border-slate-300 dark:border-slate-700 rounded-lg">Final resume not available for this application yet. Complete the "Tailor Resume" step to generate it.</div>;
    }

    const handleDownloadPdf = async () => {
        setIsGeneratingPdf(true);
        try {
            resumeExport.generatePdf(resume, companyName);
        } catch (error) {
            console.error("Failed to generate PDF:", error);
        } finally {
            setIsGeneratingPdf(false);
        }
    };

    const handleDownloadDocx = async () => {
        setIsGeneratingDocx(true);
        try {
            await resumeExport.generateDocx(resume, companyName);
        } catch (error) {
            console.error("Failed to generate DOCX:", error);
        } finally {
            setIsGeneratingDocx(false);
        }
    };

    const handleCopyToClipboard = async () => {
        setCopySuccess(false);
        const markdownText = resumeExport.resumeToMarkdown(resume);
        try {
            await navigator.clipboard.writeText(markdownText);
            setCopySuccess(true);
            setTimeout(() => setCopySuccess(false), 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    };

    // Defensive check for V2 structure
    const isV2 = version && version >= 2.0;

    const { header, summary, work_experience, education, skills, certifications } = resume;

    return (
        <div className="space-y-6">
            <div className="flex justify-end gap-4">
                <button onClick={handleDownloadPdf} disabled={isGeneratingPdf} className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50">
                    {isGeneratingPdf ? <LoadingSpinner /> : <DocumentTextIcon className="h-4 w-4" />}
                    Download PDF
                </button>
                <button onClick={handleDownloadDocx} disabled={isGeneratingDocx} className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50">
                    {isGeneratingDocx ? <LoadingSpinner /> : <ClipboardDocumentListIcon className="h-4 w-4" />}
                    Download DOCX
                </button>
                <button onClick={handleCopyToClipboard} className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700">
                    {copySuccess ? <ClipboardDocumentCheckIcon className="h-4 w-4 text-green-500" /> : <ClipboardDocumentCheckIcon className="h-4 w-4" />}
                    {copySuccess ? 'Copied' : 'Copy Markdown'}
                </button>
            </div>

            <div className="p-8 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm font-sans text-slate-800 dark:text-slate-200 max-w-4xl mx-auto">
                {/* Header */}
                <div className="text-center mb-6 pb-6 border-b border-slate-200 dark:border-slate-700">
                    <h3 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">{header?.first_name} {header?.last_name}</h3>
                    <p className="text-xl font-medium text-slate-700 dark:text-slate-300 mt-1">{header?.job_title}</p>
                    <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-3 text-sm text-slate-600 dark:text-slate-400">
                        <span>{header?.city}{header?.state ? `, ${header.state}` : ''}</span>
                        {header?.email && <span>| {header.email}</span>}
                        {header?.phone_number && <span>| {header.phone_number}</span>}
                    </div>
                    {header?.links && header.links.length > 0 && (
                        <div className="flex flex-wrap justify-center gap-4 mt-2 text-sm">
                            {header.links.map((link: string, i: number) => (
                                <a key={i} href={link.startsWith('http') ? link : `https://${link}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 underline">
                                    {link.replace(/^https?:\/\/(www\.)?/, '').split('/')[0]}
                                </a>
                            ))}
                        </div>
                    )}
                </div>

                {/* Summary */}
                {summary && (
                    <div className="mb-6">
                        <h4 className="font-bold text-sm uppercase tracking-wider text-slate-900 dark:text-sky-400 border-b-2 border-slate-200 dark:border-slate-700 pb-1 mb-3">Professional Summary</h4>
                        <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300 mb-3">{summary.paragraph}</p>
                        {summary.bullets && summary.bullets.length > 0 && (
                            <ul className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 pl-4">
                                {summary.bullets.map((b: string, i: number) => (
                                    <li key={i} className="text-sm text-slate-700 dark:text-slate-300 flex items-start">
                                        <span className="mr-2 text-sky-500">•</span>
                                        <span>{b}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}

                {/* Work Experience */}
                {work_experience && work_experience.length > 0 && (
                    <div className="mb-6">
                        <h4 className="font-bold text-sm uppercase tracking-wider text-slate-900 dark:text-sky-400 border-b-2 border-slate-200 dark:border-slate-700 pb-1 mb-4">Professional Experience</h4>
                        <div className="space-y-6">
                            {work_experience.map((job: any, idx: number) => (
                                <div key={idx} className="relative pl-2 border-l-2 border-transparent hover:border-slate-100 dark:hover:border-slate-800 transition-colors">
                                    <div className="flex flex-col sm:flex-row justify-between sm:items-baseline mb-1">
                                        <h5 className="font-bold text-base text-slate-900 dark:text-slate-100">{job.company_name}</h5>
                                        <span className="text-sm font-medium text-slate-500 dark:text-slate-400 whitespace-nowrap">
                                            {formatDate(job.start_date)} – {job.is_current ? 'Present' : formatDate(job.end_date)}
                                        </span>
                                    </div>
                                    <div className="flex flex-col sm:flex-row justify-between sm:items-baseline mb-2">
                                        <p className="font-semibold italic text-slate-700 dark:text-slate-300">{job.job_title}</p>
                                        <span className="text-xs text-slate-500 dark:text-slate-500">{job.location}</span>
                                    </div>
                                    {job.role_context && (
                                        <p className="text-sm text-slate-600 dark:text-slate-400 mb-2 italic">
                                            {job.role_context}
                                        </p>
                                    )}
                                    <ul className="list-none space-y-1.5 mt-2">
                                        {job.accomplishments?.map((acc: any, accIdx: number) => (
                                            <li key={accIdx} className="text-sm text-slate-700 dark:text-slate-300 pl-4 relative group">
                                                <span className="absolute left-0 top-1.5 w-1.5 h-1.5 bg-slate-400 rounded-full group-hover:bg-sky-500 transition-colors"></span>
                                                {acc.description}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Skills */}
                {skills && skills.length > 0 && (
                    <div className="mb-6">
                        <h4 className="font-bold text-sm uppercase tracking-wider text-slate-900 dark:text-sky-400 border-b-2 border-slate-200 dark:border-slate-700 pb-1 mb-3">Technical Skills</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {skills.map((s: any, i: number) => (
                                <div key={i}>
                                    <span className="text-sm font-bold text-slate-800 dark:text-slate-200">{s.heading}</span>
                                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                                        {Array.isArray(s.items) ? s.items.join(', ') : s.items}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Education */}
                {education && education.length > 0 && (
                    <div className="mb-6">
                        <h4 className="font-bold text-sm uppercase tracking-wider text-slate-900 dark:text-sky-400 border-b-2 border-slate-200 dark:border-slate-700 pb-1 mb-3">Education</h4>
                        {education.map((edu: any, idx: number) => (
                            <div key={idx} className="mb-3">
                                <div className="flex justify-between items-baseline">
                                    <p className="font-bold text-base text-slate-900 dark:text-slate-100">{edu.school}</p>
                                    <p className="text-sm text-slate-500 dark:text-slate-400">
                                        {edu.start_year === edu.end_year ? edu.end_year : `${edu.start_year} - ${edu.end_year}`}
                                    </p>
                                </div>
                                <p className="text-sm text-slate-700 dark:text-slate-300">
                                    {edu.degree}{edu.major && edu.major.length > 0 ? `, ${edu.major.join(', ')}` : ''}
                                </p>
                            </div>
                        ))}
                    </div>
                )}
                {/* Certifications (Optional) */}
                {certifications && certifications.length > 0 && (
                    <div className="mb-6">
                        <h4 className="font-bold text-sm uppercase tracking-wider text-slate-900 dark:text-sky-400 border-b-2 border-slate-200 dark:border-slate-700 pb-1 mb-3">Certifications</h4>
                        {certifications.map((cert: any, idx: number) => (
                            <div key={idx} className="mb-2 flex justify-between items-baseline">
                                <div>
                                    <span className="font-semibold text-sm text-slate-900 dark:text-slate-200">{cert.name}</span>
                                    <span className="text-sm text-slate-600 dark:text-slate-400"> — {cert.organization}</span>
                                </div>
                                <span className="text-xs text-slate-500 dark:text-slate-500">{cert.issued_date}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};


export const ApplicationDetailView = (props: ApplicationDetailViewProps) => {
    const { application, company, contacts, allCompanies, onBack, onUpdate, onDeleteApplication, onResumeApplication, onReanalyze, isReanalyzing, prompts, statuses, userProfile, activeNarrative, onSaveInterview, onDeleteInterview, onGenerateInterviewPrep, onGenerateRecruiterScreenPrep, onOpenContactModal, onOpenOfferModal, onGenerate90DayPlan, onAddQuestionToCommonPrep, onOpenStrategyStudio, onNavigateToStudio, handleLaunchCopilot, isLoading, onOpenDebriefStudio, initialTab, onTabChange, debugCallbacks, sprint, onAddActions } = props;

    const currentStatus = application.status || statuses.find(s => s.status_id === (application as any).status_id);
    const isStep3 = currentStatus?.status_name === 'Step-3: Resume created';
    const [activeTab, setActiveTab] = useState<ApplicationDetailTab>(initialTab || (isStep3 ? 'apply' : 'overview'));
    const [isEditing, setIsEditing] = useState(false);
    const [editableApp, setEditableApp] = useState<JobApplication>(application);
    const [editingInterviewId, setEditingInterviewId] = useState<string | null>(null);
    const [editableInterview, setEditableInterview] = useState<Partial<InterviewPayload>>({});
    const [isGeneratingPrep, setIsGeneratingPrep] = useState<Record<string, boolean>>({});
    const [selectedContextContact, setSelectedContextContact] = useState<Contact | null>(null);
    const [isContextCompanyView, setIsContextCompanyView] = useState(true);
    const [reviewedJob, setReviewedJob] = useState<ReviewedJob | null>(null);
    const [isLoadingReview, setIsLoadingReview] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [copySuccess, setCopySuccess] = useState(false);
    const [localMessage, setLocalMessage] = useState(application.application_message || '');
    const [addedToSprint, setAddedToSprint] = useState(false);
    const [showCompanyModal, setShowCompanyModal] = useState(false);

    // V2 Data Parsers
    const parsedKeywords = useMemo(() => {
        if (!application.keywords) return null;
        try {
            const data = typeof application.keywords === 'string' ? JSON.parse(application.keywords) : application.keywords;
            // V2 detection
            if (data.keywords && Array.isArray(data.keywords)) {
                return { type: 'v2' as const, keywords: data.keywords };
            }
            // V1 fallback
            if (data.hard_keywords || data.soft_keywords) {
                return { type: 'v1' as const, hard: data.hard_keywords || [], soft: data.soft_keywords || [] };
            }
            return null;
        } catch (e) {
            return null;
        }
    }, [application.keywords]);

    const parsedGuidance = useMemo(() => {
        if (!application.guidance) return null;
        try {
            const data = typeof application.guidance === 'string' ? JSON.parse(application.guidance) : application.guidance;
            // V2 detection: headline, paragraph, bullets
            if (data.headline || data.paragraph) {
                return {
                    type: 'v2' as const,
                    headline: data.headline || '',
                    paragraph: data.paragraph || '',
                    bullets: Array.isArray(data.bullets) ? data.bullets : []
                };
            }
            // V1 fallback
            if (data.summary || data.bullets) {
                return {
                    type: 'v1' as const,
                    summary: Array.isArray(data.summary) ? data.summary : [],
                    bullets: Array.isArray(data.bullets) ? data.bullets : []
                };
            }
            return null;
        } catch (e) {
            return null;
        }
    }, [application.guidance]);

    const parsedProblemAnalysis = useMemo(() => {
        if (!application.job_problem_analysis_result) return null;
        try {
            const data = typeof application.job_problem_analysis_result === 'string'
                ? JSON.parse(application.job_problem_analysis_result)
                : application.job_problem_analysis_result;

            // V2 Detection
            if (data.diagnostic_intel) {
                return { type: 'v2' as const, data: data as JobProblemAnalysisResultV2 };
            }
            // V1 Fallback
            return { type: 'v1' as const, data: data as JobProblemAnalysisResultV1 };
        } catch (e) {
            return null;
        }
    }, [application.job_problem_analysis_result]);

    const parsedVocab = useMemo(() => {
        let results: string[] = [];

        // 1. Check top-level vocabulary_mirror
        if (application.vocabulary_mirror) {
            try {
                const data = typeof application.vocabulary_mirror === 'string' ? JSON.parse(application.vocabulary_mirror) : application.vocabulary_mirror;
                if (Array.isArray(data)) results = [...results, ...data];
                else results.push(application.vocabulary_mirror);
            } catch (e) {
                results.push(application.vocabulary_mirror);
            }
        }

        // 2. Check V2 Problem Analysis for vocabulary mirror
        if (parsedProblemAnalysis?.type === 'v2') {
            const v2Vocab = parsedProblemAnalysis.data.content_intelligence?.vocabulary_mirror;
            if (Array.isArray(v2Vocab)) {
                results = [...results, ...v2Vocab];
            }
        }

        // De-duplicate
        return Array.from(new Set(results));
    }, [application.vocabulary_mirror, parsedProblemAnalysis]);

    const [questions, setQuestions] = useState<ApplicationQuestion[]>(
        (application.application_questions && typeof application.application_questions === 'string'
            ? JSON.parse(application.application_questions)
            : application.application_questions) || []
    );
    const [includeCoverLetter, setIncludeCoverLetter] = useState(false);

    useEffect(() => {
        const fetchReview = async () => {
            if (application.source_job_id) {
                setIsLoadingReview(true);
                try {
                    const review = await apiService.getReviewedJob(application.source_job_id);
                    setReviewedJob(review);
                } catch (err) {
                    console.error('Failed to fetch job review:', err);
                } finally {
                    setIsLoadingReview(false);
                }
            }
        };
        fetchReview();
    }, [application.source_job_id]);

    useEffect(() => {
        setQuestions(
            (application.application_questions && typeof application.application_questions === 'string'
                ? JSON.parse(application.application_questions)
                : application.application_questions) || []
        );
        setLocalMessage(application.application_message || '');
    }, [application]);

    useEffect(() => {
        setEditableApp(application);
    }, [application]);

    useEffect(() => {
        if (initialTab) {
            setActiveTab(initialTab);
        }
    }, [initialTab]);

    useEffect(() => {
        if (activeTab === 'apply' && !isStep3) {
            setActiveTab('overview');
            onTabChange?.('overview');
        }
    }, [activeTab, isStep3, onTabChange]);

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

    const handleMarkAsApplied = async () => {
        setIsSaving(true);
        try {
            const appliedStatus = statuses.find(s => s.status_name === 'Step-4: Applied');
            if (appliedStatus) {
                const payload: JobApplicationPayload = {
                    ...application,
                    status_id: appliedStatus.status_id,
                    date_applied: new Date().toISOString()
                };
                await onUpdate(payload);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setIsSaving(false);
        }
    };

    const handleSaveMessage = async () => {
        setIsSaving(true);
        try {
            await onUpdate({ ...application, application_message: localMessage });
            addToast('Message saved!', 'success');
        } catch (e) {
            console.error(e);
        } finally {
            setIsSaving(false);
        }
    };

    const handleAddToSprint = async () => {
        if (!sprint || !onAddActions || addedToSprint) {
            return;
        }

        const baseOrder = sprint.actions.filter((a) => !a.is_goal).length || 0;
        const impactSections: string[] = [];

        if (application.job_description) {
            impactSections.push(`Job Context Available`);
        }

        const linkSegments: string[] = [];
        if (application.job_application_id) {
            linkSegments.push(`/application/${application.job_application_id}`);
        }
        if (application.company_id) {
            linkSegments.push(`/company/${application.company_id}`);
        }
        if (linkSegments.length > 0) {
            impactSections.push(`Links: ${linkSegments.join(' | ')}`);
        }

        const newAction: SprintActionPayload = {
            title: `${application.job_title} at ${company.company_name} • Networking`,
            impact: impactSections.join('\n\n'),
            is_completed: false,
            is_goal: false,
            order_index: baseOrder,
            strategic_tags: ['post-application', 'networking'],
        };

        await onAddActions(sprint.sprint_id, [newAction]);
        setAddedToSprint(true);
    };

    const handleQuestionChange = (index: number, field: keyof ApplicationQuestion, value: string) => {
        const newQuestions = questions.map((item, i) =>
            i === index ? { ...item, [field]: value } : item
        );
        setQuestions(newQuestions);
        // We trigger an update here to save periodically, or we could add a specific save button
    };

    const handleSaveQuestions = async () => {
        try {
            const payload: JobApplicationPayload = {
                ...application,
                application_questions: questions
            };
            await onUpdate(payload);
            addToast('Questions saved!', 'success');
        } catch (e) {
            console.error("Failed to save questions", e);
        }
    };

    const addQuestion = () => {
        setQuestions(prev => [...prev, { id: uuidv4(), question: '', answer: '', user_thoughts: '' }]);
    };

    const removeQuestion = (index: number) => {
        setQuestions(prev => prev.filter((_, i) => i !== index));
    };

    const { addToast } = useToast();

    const handleExportForAi = () => {
        const xmlContent = `
<JOB_APPLICATION_CONTEXT>
  <JOB_DETAILS>
    <TITLE>${application.job_title}</TITLE>
    <COMPANY>${company.company_name}</COMPANY>
    <LOCATION>${application.location || 'N/A'} (${application.remote_status || 'N/A'})</LOCATION>
    <SALARY>${application.salary || 'N/A'}</SALARY>
    <URL>${application.job_link || 'N/A'}</URL>
    <DESCRIPTION>
${application.job_description}
    </DESCRIPTION>
  </JOB_DETAILS>

  <STRATEGIC_CONTEXT>
    <POSITIONING_STATEMENT>${activeNarrative?.positioning_statement || 'N/A'}</POSITIONING_STATEMENT>
    <SIGNATURE_CAPABILITY>${activeNarrative?.signature_capability || 'N/A'}</SIGNATURE_CAPABILITY>
    <MISSION_ALIGNMENT>${activeNarrative?.mission_alignment || 'N/A'}</MISSION_ALIGNMENT>
  </STRATEGIC_CONTEXT>

  <TAILORED_RESUME_JSON>
${JSON.stringify(application.tailored_resume_json, null, 2)}
  </TAILORED_RESUME_JSON>

  <APPLICATION_MESSAGE>
${localMessage || application.application_message || 'N/A'}
  </APPLICATION_MESSAGE>

  <APPLICATION_QUESTIONS>
${JSON.stringify(questions, null, 2)}
  </APPLICATION_QUESTIONS>
</JOB_APPLICATION_CONTEXT>`.trim();

        navigator.clipboard.writeText(xmlContent);
        addToast('Application data copied to clipboard in XML format for AI!', 'success');
    };

    const tabClass = (tabName: ApplicationDetailTab) =>
        `px-3 py-2 font-medium text-sm rounded-md cursor-pointer transition-colors ` +
        (activeTab === tabName
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
            : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200');

    // Robustly handle analysis data which might come as JSON strings or objects
    const analysisRaw = typeof application.job_problem_analysis_result === 'string'
        ? JSON.parse(application.job_problem_analysis_result)
        : application.job_problem_analysis_result;

    // Check if it's an InitialJobAnalysisResult wrapper or the direct JobProblemAnalysisResult
    const analysis = analysisRaw?.job_problem_analysis || analysisRaw;

    const keywordsData = typeof application.keywords === 'string'
        ? JSON.parse(application.keywords) as KeywordsResult
        : application.keywords as KeywordsResult;

    const guidanceData = typeof application.guidance === 'string'
        ? JSON.parse(application.guidance) as GuidanceResult
        : application.guidance as GuidanceResult;

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
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${application.workflow_mode === 'ai_generated'
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
                    {sprint && onAddActions && (
                        <button
                            onClick={handleAddToSprint}
                            disabled={addedToSprint}
                            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-sm disabled:bg-blue-400 disabled:cursor-not-allowed"
                        >
                            {addedToSprint ? <CheckIcon className="h-5 w-5" /> : <PlusCircleIcon className="h-5 w-5" />}
                            {addedToSprint ? 'Added to Sprint' : 'Add to Sprint'}
                        </button>
                    )}
                    {application.status?.status_name === 'Interviewing' && (
                        <button onClick={() => onNavigateToStudio(application)} className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm">
                            <MicrophoneIcon className="h-5 w-5" />
                            Practice in Studio
                        </button>
                    )}
                </div>
            </header>

            <div className="border-b border-slate-200 dark:border-slate-700">
                <nav className="-mb-px flex space-x-4" aria-label="Tabs">
                    <button onClick={() => onTabChange?.('overview')} className={tabClass('overview')}>Overview</button>
                    {isStep3 && <button onClick={() => onTabChange?.('apply')} className={tabClass('apply')}>Apply</button>}
                    <button onClick={() => onTabChange?.('analysis')} className={tabClass('analysis')}>
                        <div className="flex items-center gap-2">
                            <StrategyIcon className="h-4 w-4" />
                            AI Strategy
                            {(application.job_problem_analysis_result || reviewedJob) && (
                                <span className="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse"></span>
                            )}
                        </div>
                    </button>
                    <button onClick={() => onTabChange?.('resume')} className={tabClass('resume')}>Final Resume</button>
                    <button onClick={() => onTabChange?.('questions')} className={tabClass('questions')}>Questions & Prep</button>
                    <button onClick={() => onTabChange?.('interviews')} className={tabClass('interviews')}>Interviews</button>
                </nav>
            </div>

            <div className="mt-6">
                {activeTab === 'apply' && isStep3 && (
                    <div className="space-y-8 animate-fade-in max-w-4xl mx-auto pb-20">
                        {/* Status Transition Header */}
                        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-8 text-white shadow-xl flex flex-col md:flex-row justify-between items-center gap-6">
                            <div className="flex-1">
                                <h3 className="text-2xl font-bold mb-2">Ready to Submit?</h3>
                                <p className="text-blue-100">Review your final materials below. Once you've submitted the application to the employer, mark it as applied here to move to the next stage.</p>
                            </div>
                            <button
                                onClick={handleMarkAsApplied}
                                disabled={isSaving}
                                className="whitespace-nowrap inline-flex items-center gap-2 px-8 py-3.5 text-lg font-bold rounded-xl bg-white text-blue-700 hover:bg-blue-50 transition-all hover:scale-105 shadow-lg disabled:opacity-50"
                            >
                                <CheckIcon className="h-6 w-6" />
                                Mark as Applied
                            </button>
                        </div>

                        {/* Job Snapshot */}
                        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 flex flex-wrap gap-8 items-center shadow-sm">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg">
                                    <StrategyIcon className="h-5 w-5 text-slate-500" />
                                </div>
                                <div>
                                    <span className="block text-xs text-slate-500 uppercase font-bold tracking-wider">Salary</span>
                                    <span className="font-semibold text-slate-900 dark:text-white">{application.salary || 'Not specified'}</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg">
                                    <MicrophoneIcon className="h-5 w-5 text-slate-500" />
                                </div>
                                <div>
                                    <span className="block text-xs text-slate-500 uppercase font-bold tracking-wider">Location</span>
                                    <span className="font-semibold text-slate-900 dark:text-white">
                                        {application.location || 'Not specified'}
                                        {application.remote_status && ` (${application.remote_status})`}
                                    </span>
                                </div>
                            </div>
                            {application.job_link && (
                                <a
                                    href={application.job_link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="ml-auto inline-flex items-center gap-2 px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-semibold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                                >
                                    View Original Post
                                    <RocketLaunchIcon className="h-4 w-4" />
                                </a>
                            )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Resume Card */}
                            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm flex flex-col">
                                <div className="flex items-center gap-2 mb-6">
                                    <DocumentTextIcon className="h-6 w-6 text-blue-500" />
                                    <h4 className="text-xl font-bold text-slate-900 dark:text-white">Final Resume</h4>
                                </div>
                                <div className="space-y-3 mt-auto">
                                    <button
                                        onClick={() => resumeExport.generatePdf(application.tailored_resume_json, company.company_name)}
                                        className="w-full flex items-center justify-between p-4 border border-slate-100 dark:border-slate-700 rounded-xl hover:border-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-all group"
                                    >
                                        <div className="flex items-center gap-3">
                                            <DocumentTextIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                                            <span className="font-semibold text-slate-900 dark:text-white">PDF Version</span>
                                        </div>
                                        <span className="text-xs text-slate-400 group-hover:text-blue-500">Download</span>
                                    </button>
                                    <button
                                        onClick={() => resumeExport.generateDocx(application.tailored_resume_json, company.company_name)}
                                        className="w-full flex items-center justify-between p-4 border border-slate-100 dark:border-slate-700 rounded-xl hover:border-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-all group"
                                    >
                                        <div className="flex items-center gap-3">
                                            <ClipboardDocumentListIcon className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                                            <span className="font-semibold text-slate-900 dark:text-white">DOCX Version</span>
                                        </div>
                                        <span className="text-xs text-slate-400 group-hover:text-blue-500">Download</span>
                                    </button>
                                    <button
                                        onClick={() => {
                                            const md = resumeExport.resumeToMarkdown(application.tailored_resume_json);
                                            navigator.clipboard.writeText(md);
                                            setCopySuccess(true);
                                            setTimeout(() => setCopySuccess(false), 2000);
                                        }}
                                        className="w-full flex items-center justify-between p-4 border border-slate-100 dark:border-slate-700 rounded-xl hover:border-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-all group"
                                    >
                                        <div className="flex items-center gap-3">
                                            {copySuccess ? <ClipboardDocumentCheckIcon className="h-5 w-5 text-green-500" /> : <ClipboardDocumentCheckIcon className="h-5 w-5 text-indigo-500" />}
                                            <span className="font-semibold text-slate-900 dark:text-white">{copySuccess ? 'Copied!' : 'Markdown Copy'}</span>
                                        </div>
                                        <span className="text-xs text-slate-400 group-hover:text-indigo-500">Copy Text</span>
                                    </button>
                                </div>
                            </div>

                            {/* Export for AI Card */}
                            <div className="bg-indigo-50 dark:bg-indigo-900/10 rounded-2xl border border-indigo-200 dark:border-indigo-900/30 p-8 flex flex-col justify-center items-center text-center shadow-sm">
                                <div className="p-4 bg-white dark:bg-slate-800 rounded-2xl shadow-md mb-4">
                                    <SparklesIcon className="h-10 w-10 text-indigo-600" />
                                </div>
                                <h4 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Need a custom letter?</h4>
                                <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">Export all job and resume data to paste into ChatGPT/Claude for custom drafting.</p>
                                <button
                                    onClick={handleExportForAi}
                                    className="w-full inline-flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-500/25"
                                >
                                    Export Data for AI
                                </button>
                            </div>
                        </div>

                        {/* Application Message Editor */}
                        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-8 shadow-sm">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-2">
                                    <SparklesIcon className="h-6 w-6 text-indigo-500" />
                                    <h4 className="text-xl font-bold text-slate-900 dark:text-white">Application Message</h4>
                                </div>
                                <div className="flex items-center gap-4">
                                    <button
                                        onClick={handleSaveMessage}
                                        disabled={isSaving || localMessage === application.application_message}
                                        className="text-sm font-bold text-green-600 hover:text-green-700 disabled:opacity-30 transition-opacity"
                                    >
                                        SAVE MESSAGE
                                    </button>
                                    <button
                                        onClick={() => {
                                            navigator.clipboard.writeText(localMessage);
                                            const toast = document.createElement('div');
                                            toast.className = 'fixed bottom-4 right-4 bg-slate-800 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in';
                                            toast.innerText = 'Message copied to clipboard!';
                                            document.body.appendChild(toast);
                                            setTimeout(() => toast.remove(), 2000);
                                        }}
                                        className="flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700"
                                    >
                                        <ClipboardDocumentListIcon className="h-4 w-4" />
                                        Copy Message
                                    </button>
                                </div>
                            </div>
                            <textarea
                                value={localMessage}
                                onChange={(e) => setLocalMessage(e.target.value)}
                                className="w-full h-48 p-4 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all resize-none leading-relaxed"
                                placeholder="Write your application message or cover letter here..."
                            />
                        </div>

                        {/* Questions Editor */}
                        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-8 shadow-sm">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-2">
                                    <ClipboardDocumentCheckIcon className="h-6 w-6 text-green-500" />
                                    <h4 className="text-xl font-bold text-slate-900 dark:text-white">Application Questions</h4>
                                </div>
                                <button
                                    onClick={addQuestion}
                                    className="flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700"
                                >
                                    <PlusCircleIcon className="h-4 w-4" />
                                    Add Question
                                </button>
                            </div>

                            <div className="space-y-6">
                                {questions.map((qa, idx) => (
                                    <div key={idx} className="bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-700 p-6 space-y-4 group">
                                        <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-2">
                                            <input
                                                type="text"
                                                value={qa.question}
                                                onChange={(e) => handleQuestionChange(idx, 'question', e.target.value)}
                                                className="flex-1 bg-transparent border-none p-0 text-lg font-bold text-slate-900 dark:text-white focus:ring-0 placeholder-slate-400"
                                                placeholder="Enter Question..."
                                            />
                                            <button
                                                onClick={() => removeQuestion(idx)}
                                                className="p-2 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                                            >
                                                <TrashIcon className="h-5 w-5" />
                                            </button>
                                        </div>
                                        <textarea
                                            value={qa.answer}
                                            onChange={(e) => handleQuestionChange(idx, 'answer', e.target.value)}
                                            rows={3}
                                            className="w-full p-4 bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-xl text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all resize-none"
                                            placeholder="Write your answer here..."
                                        />
                                        <div className="flex justify-end">
                                            <button
                                                onClick={() => {
                                                    navigator.clipboard.writeText(qa.answer);
                                                    const toast = document.createElement('div');
                                                    toast.className = 'fixed bottom-4 right-4 bg-slate-800 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in';
                                                    toast.innerText = 'Answer copied to clipboard!';
                                                    document.body.appendChild(toast);
                                                    setTimeout(() => toast.remove(), 2000);
                                                }}
                                                className="text-xs font-bold text-slate-400 hover:text-blue-500 flex items-center gap-1.5"
                                            >
                                                <ClipboardDocumentListIcon className="h-4 w-4" />
                                                COPY ANSWER
                                            </button>
                                        </div>
                                    </div>
                                ))}
                                {questions.length > 0 && (
                                    <div className="mt-8 flex justify-center">
                                        <button
                                            onClick={handleSaveQuestions}
                                            disabled={isSaving}
                                            className="px-8 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-bold hover:scale-105 transition-all shadow-lg shadow-black/10 disabled:opacity-50"
                                        >
                                            {isSaving ? <LoadingSpinner /> : 'SAVE ALL QUESTIONS'}
                                        </button>
                                    </div>
                                )}
                                {questions.length === 0 && (
                                    <div className="text-center py-12 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-2xl">
                                        <p className="text-slate-500 dark:text-slate-400">No questions added for this application yet.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        <div className="flex justify-end gap-2">
                            {isEditing ? (
                                <>
                                    <button onClick={handleCancel} className="px-4 py-2 text-sm font-medium rounded-lg text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 border border-slate-300 dark:border-slate-500 shadow-sm">Cancel</button>
                                    <button onClick={handleSave} disabled={isSaving} className="px-4 py-2 text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 shadow-sm disabled:opacity-50">{isSaving ? <LoadingSpinner /> : 'Save'}</button>
                                </>
                            ) : (
                                <button onClick={() => setIsEditing(true)} className="px-4 py-2 text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-sm">Edit Details</button>
                            )}
                        </div>
                        <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                            <DetailItem label="Company" value={company.company_name}>
                                {isEditing && (
                                    <select
                                        value={editableApp.company_id || ''}
                                        onChange={e => setEditableApp({ ...editableApp, company_id: e.target.value })}
                                        className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm"
                                    >
                                        <option value="">Select a company...</option>
                                        {[...allCompanies]
                                            .sort((a, b) => a.company_name.localeCompare(b.company_name))
                                            .map(c => (
                                                <option key={c.company_id} value={c.company_id}>
                                                    {c.company_name}
                                                </option>
                                            ))}
                                    </select>
                                )}
                            </DetailItem>
                            <DetailItem label="Job Title" value={isEditing ? undefined : editableApp.job_title}>
                                {isEditing && <input type="text" value={editableApp.job_title || ''} onChange={e => setEditableApp({ ...editableApp, job_title: e.target.value })} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm" />}
                            </DetailItem>
                            <DetailItem label="Date Applied" value={new Date(editableApp.date_applied).toLocaleDateString()} />
                            <DetailItem label="Status" value={isEditing ? undefined : editableApp.status?.status_name}>
                                {isEditing && <select value={editableApp.status?.status_id || ''} onChange={e => setEditableApp(prev => ({ ...prev, status: statuses.find(s => s.status_id === e.target.value) }))} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm">{statuses.map(s => <option key={s.status_id} value={s.status_id}>{s.status_name}</option>)}</select>}
                            </DetailItem>
                            <DetailItem label="Salary" value={isEditing ? undefined : editableApp.salary}>
                                {isEditing && <input type="text" value={editableApp.salary || ''} onChange={e => setEditableApp({ ...editableApp, salary: e.target.value })} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm" />}
                            </DetailItem>
                            <DetailItem label="Location" value={isEditing ? undefined : editableApp.location}>
                                {isEditing && <input type="text" value={editableApp.location || ''} onChange={e => setEditableApp({ ...editableApp, location: e.target.value })} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm" />}
                            </DetailItem>
                            <DetailItem label="Remote Status" value={isEditing ? undefined : editableApp.remote_status}>
                                {isEditing && <select value={editableApp.remote_status || ''} onChange={e => setEditableApp({ ...editableApp, remote_status: e.target.value as any })} className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm sm:text-sm"><option value="">Select...</option><option value="On-site">On-site</option><option value="Hybrid">Hybrid</option><option value="Remote">Remote</option></select>}
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
                    <div className="space-y-8 animate-fade-in max-w-6xl mx-auto">
                        <div className="flex justify-between items-center pb-4 border-b border-slate-200 dark:border-slate-700">
                            <div className="flex items-center gap-3">
                                <StrategyIcon className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
                                <div>
                                    <h3 className="text-2xl font-bold text-slate-900 dark:text-white">AI Strategy & Blueprint</h3>
                                    <p className="text-sm text-slate-500 dark:text-slate-400">Deep analysis of the job problem, company fit, and tactical guidance.</p>
                                </div>
                            </div>
                            <button
                                onClick={onReanalyze}
                                disabled={isReanalyzing}
                                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-md transition-all disabled:opacity-50"
                            >
                                {isReanalyzing ? <LoadingSpinner /> : <SparklesIcon className="h-5 w-5" />}
                                Rerun Analysis
                            </button>
                        </div>

                        {/* Top Stats/Scores */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-700 text-white shadow-lg">
                                <h4 className="text-sm font-medium opacity-80 mb-1">Strategic Alignment</h4>
                                <div className="flex items-end gap-2">
                                    <span className="text-4xl font-bold">{(reviewedJob?.overall_alignment_score || 0) * 100}%</span>
                                    <span className="text-sm mb-1 opacity-90">Company Fit</span>
                                </div>
                            </div>
                            <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                                <h4 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">Resume Keywords</h4>
                                <div className="flex items-end gap-2">
                                    <span className="text-4xl font-bold text-slate-900 dark:text-white">
                                        {parsedKeywords?.type === 'v2' ? parsedKeywords.keywords.length : parsedKeywords?.type === 'v1' ? parsedKeywords.hard.length : 0}
                                    </span>
                                    <span className="text-sm mb-1 text-slate-500">Targeted Terms</span>
                                </div>
                            </div>
                            <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                                <h4 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">Strategic Hooks</h4>
                                <div className="flex items-end gap-2">
                                    <span className="text-4xl font-bold text-slate-900 dark:text-white">
                                        {application.alignment_strategy?.alignment_strategy?.length || 0}
                                    </span>
                                    <span className="text-sm mb-1 text-slate-500">Tailored Hooks</span>
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                            {/* Left Column: Job & Problem Analysis */}
                            <div className="xl:col-span-2 space-y-8">
                                {/* Core Problem Analysis */}
                                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
                                    <div className="bg-slate-50 dark:bg-slate-800/50 px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center gap-2">
                                        <BeakerIcon className="h-5 w-5 text-purple-500" />
                                        <h4 className="font-bold text-slate-900 dark:text-white">
                                            {parsedProblemAnalysis?.type === 'v2' ? 'Diagnostic Intelligence & Mandate' : 'The Core Problem Analysis'}
                                        </h4>
                                    </div>
                                    <div className="p-6 space-y-8">
                                        {/* V2 Specific Rendering */}
                                        {parsedProblemAnalysis?.type === 'v2' && (
                                            <>
                                                {/* Diagnostic Intel Header */}
                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                                    <div className="md:col-span-2 p-5 bg-purple-50 dark:bg-purple-900/10 rounded-xl border border-purple-100 dark:border-purple-800/30">
                                                        <h5 className="text-xs font-bold text-purple-900 dark:text-purple-300 uppercase tracking-widest mb-3">Composite Antidote Persona</h5>
                                                        <p className="text-lg font-bold text-slate-900 dark:text-white leading-tight">
                                                            {parsedProblemAnalysis.data.diagnostic_intel?.composite_antidote_persona}
                                                        </p>
                                                        <div className="mt-4 flex flex-wrap gap-2">
                                                            {(parsedProblemAnalysis.data.diagnostic_intel?.failure_state_portfolio || []).map((state, i) => (
                                                                <span key={i} className="px-2 py-1 bg-red-100/50 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-[10px] font-bold rounded border border-red-200/50 uppercase tracking-tighter">
                                                                    {state}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    <div className="p-5 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-800/30">
                                                        <h5 className="text-xs font-bold text-blue-900 dark:text-blue-300 uppercase tracking-widest mb-3">Primary Value Driver</h5>
                                                        <p className="text-2xl font-black text-blue-600 dark:text-blue-400 uppercase italic">
                                                            {parsedProblemAnalysis.data.economic_logic_gates?.primary_value_driver}
                                                        </p>
                                                        <p className="text-[10px] text-slate-500 mt-2 uppercase font-bold">Economic Logic Gate</p>
                                                    </div>
                                                </div>

                                                {/* Mandate Quadrant */}
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                                    {(['solve', 'improve', 'deliver', 'maintain'] as const).map((key) => (
                                                        <div key={key} className="p-4 bg-slate-50 dark:bg-slate-900/40 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 transition-colors">
                                                            <h6 className="text-[10px] font-black uppercase text-slate-400 mb-2 tracking-widest">{key}</h6>
                                                            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                                                                {parsedProblemAnalysis.data.diagnostic_intel?.mandate_quadrant?.[key]}
                                                            </p>
                                                        </div>
                                                    ))}
                                                </div>

                                                {/* Experience Anchoring */}
                                                <div className="p-5 bg-emerald-50 dark:bg-emerald-900/10 rounded-xl border border-emerald-100 dark:border-emerald-800/30">
                                                    <div className="flex items-center gap-2 mb-3">
                                                        <CheckIcon className="h-4 w-4 text-emerald-600" />
                                                        <h5 className="text-xs font-bold text-emerald-900 dark:text-emerald-300 uppercase tracking-widest">Experience Anchoring</h5>
                                                    </div>
                                                    <div className="space-y-2">
                                                        <p className="text-sm font-bold text-slate-900 dark:text-white">
                                                            {parsedProblemAnalysis.data.diagnostic_intel?.experience_anchoring?.anchor_role_title}
                                                            <span className="ml-2 text-[10px] px-1.5 py-0.5 bg-emerald-200 dark:bg-emerald-800 rounded uppercase font-black text-emerald-800 dark:text-emerald-200">
                                                                {parsedProblemAnalysis.data.diagnostic_intel?.experience_anchoring?.alignment_type} Alignment
                                                            </span>
                                                        </p>
                                                        <p className="text-xs text-slate-600 dark:text-slate-400 italic leading-relaxed">
                                                            {parsedProblemAnalysis.data.diagnostic_intel?.experience_anchoring?.fidelity_logic}
                                                        </p>
                                                    </div>
                                                </div>

                                                {/* Gravity Stack, Metrics, Tech Signals */}
                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                                    <div>
                                                        <h5 className="text-xs font-bold text-slate-500 uppercase mb-4 tracking-widest">Functional Gravity</h5>
                                                        <div className="space-y-2">
                                                            {(parsedProblemAnalysis.data.diagnostic_intel?.functional_gravity_stack || []).map((item, i) => (
                                                                <div key={i} className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
                                                                    <div className="h-1 w-1 rounded-full bg-blue-500" />
                                                                    {item}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <h5 className="text-xs font-bold text-slate-500 uppercase mb-4 tracking-widest">Metric Hierarchy</h5>
                                                        <div className="space-y-2">
                                                            {(parsedProblemAnalysis.data.economic_logic_gates?.metric_hierarchy || []).map((item, i) => (
                                                                <div key={i} className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
                                                                    <div className="h-1 w-1 rounded-full bg-emerald-500" />
                                                                    {item}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <h5 className="text-xs font-bold text-slate-500 uppercase mb-4 tracking-widest">Tech Signals</h5>
                                                        <div className="flex flex-wrap gap-1.5">
                                                            {(parsedProblemAnalysis.data.content_intelligence?.must_have_tech_signals || []).map((item, i) => (
                                                                <span key={i} className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-700/50 text-slate-600 dark:text-slate-400 text-[10px] font-medium rounded border border-slate-200 dark:border-slate-600">
                                                                    {item}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Strategic Friction Hooks (V2) */}
                                                <div>
                                                    <h5 className="text-xs font-bold text-red-500 uppercase mb-4 tracking-widest flex items-center gap-2">
                                                        <RocketLaunchIcon className="h-3 w-3" />
                                                        Strategic Friction Hooks
                                                    </h5>
                                                    <div className="flex flex-wrap gap-3">
                                                        {(parsedProblemAnalysis.data.diagnostic_intel?.strategic_friction_hooks || []).map((hook, i) => (
                                                            <div key={i} className="flex items-center gap-2 text-xs font-bold text-slate-800 dark:text-slate-200 bg-white dark:bg-slate-800 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                                                                <span className="text-indigo-500 text-lg">#</span>
                                                                {hook}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </>
                                        )}

                                        {/* V1 Specific Rendering Fallback */}
                                        {parsedProblemAnalysis?.type === 'v1' && (
                                            <>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                    <div className="p-4 bg-purple-50 dark:bg-purple-900/10 rounded-xl border border-purple-100 dark:border-purple-800/30">
                                                        <h5 className="text-xs font-bold text-purple-900 dark:text-purple-300 uppercase tracking-wider mb-2">The Mission-Critical Problem</h5>
                                                        <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">
                                                            {parsedProblemAnalysis.data.core_problem_analysis?.core_problem || "Analysis pending..."}
                                                        </p>
                                                    </div>
                                                    <div className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-800/30">
                                                        <h5 className="text-xs font-bold text-blue-900 dark:text-blue-300 uppercase tracking-wider mb-2">Strategic Importance</h5>
                                                        <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">
                                                            {parsedProblemAnalysis.data.core_problem_analysis?.strategic_importance}
                                                        </p>
                                                    </div>
                                                </div>

                                                <div>
                                                    <h5 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Key Success Metrics</h5>
                                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                                        {(parsedProblemAnalysis.data.key_success_metrics || []).map((metric: string, i: number) => (
                                                            <div key={i} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-400">
                                                                <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0" />
                                                                {metric}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>

                                                <div>
                                                    <h5 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Critical Blockers & Risks</h5>
                                                    <div className="flex flex-wrap gap-2">
                                                        {(parsedProblemAnalysis.data.potential_blockers || []).map((blocker: string, i: number) => (
                                                            <span key={i} className="px-3 py-1 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-xs font-medium rounded-lg border border-red-100 dark:border-red-800/30">
                                                                {blocker}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </div>

                                {/* Strategic Alignment Hooks */}
                                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
                                    <div className="bg-slate-50 dark:bg-slate-800/50 px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center gap-2">
                                        <SparklesIcon className="h-5 w-5 text-indigo-500" />
                                        <h4 className="font-bold text-slate-900 dark:text-white">Strategic Alignment Hooks</h4>
                                    </div>
                                    <div className="p-6">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            {application.alignment_strategy?.alignment_strategy?.map((item: any, idx: number) => (
                                                <div key={idx} className="p-5 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-700 transition-all group">
                                                    <div className="flex justify-between items-start mb-3">
                                                        <div>
                                                            {item.context_type && (
                                                                <span className={`inline-block mb-1 text-[8px] px-1.5 py-0.5 rounded-full font-bold uppercase tracking-widest ${item.context_type.includes('Direct')
                                                                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                                                                    : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                                                                    }`}>
                                                                    {item.context_type}
                                                                </span>
                                                            )}
                                                            <p className="font-bold text-sm text-slate-900 dark:text-white group-hover:text-indigo-600">{item.role}</p>
                                                            <p className="text-xs text-slate-500">{item.company}</p>
                                                        </div>
                                                        <span className="text-[10px] uppercase font-black px-2 py-0.5 bg-indigo-100 text-indigo-800 rounded tracking-tighter">
                                                            {item.mapped_pillar}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm italic text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
                                                        "{item.friction_hook}"
                                                    </p>
                                                    {item.secondary_alignments && item.secondary_alignments.length > 0 && (
                                                        <div className="flex flex-wrap gap-1 mt-3">
                                                            {item.secondary_alignments.map((sa: string, si: number) => (
                                                                <span key={si} className="text-[9px] px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-500 rounded border border-slate-200 dark:border-slate-700 opacity-70 group-hover:opacity-100">
                                                                    {sa}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {/* AI Interaction Hub / Questions Preview? */}
                                {application.application_message && (
                                    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
                                        <div className="bg-slate-50 dark:bg-slate-800/50 px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center gap-2">
                                            <SparklesIcon className="h-5 w-5 text-blue-500" />
                                            <h4 className="font-bold text-slate-900 dark:text-white">AI-Drafted Intro</h4>
                                        </div>
                                        <div className="p-6">
                                            <div className="bg-slate-900 text-slate-300 p-6 rounded-xl font-mono text-sm leading-relaxed border border-slate-800 shadow-inner max-h-80 overflow-y-auto">
                                                {application.application_message}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Right Column: Guidance & Company Context */}
                            <div className="space-y-8">
                                {/* Resume Guidance */}
                                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
                                    <div className="bg-slate-50 dark:bg-slate-800/50 px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center gap-2">
                                        <DocumentTextIcon className="h-5 w-5 text-blue-500" />
                                        <h4 className="font-bold text-slate-900 dark:text-white">Resume Tailoring & Summary</h4>
                                    </div>
                                    <div className="p-6 space-y-6">
                                        {/* V2 Resume Summary Headline & Paragraph */}
                                        {parsedGuidance?.type === 'v2' && (
                                            <div className="space-y-4">
                                                <div className="p-4 bg-indigo-50 dark:bg-indigo-900/10 rounded-xl border border-indigo-100 dark:border-indigo-800/30">
                                                    <h5 className="text-xs font-bold text-indigo-900 dark:text-indigo-300 uppercase tracking-wider mb-2">Resume Headline</h5>
                                                    <p className="text-sm font-bold text-slate-900 dark:text-white leading-tight">
                                                        {parsedGuidance.headline}
                                                    </p>
                                                </div>
                                                <div className="p-4 bg-slate-50 dark:bg-slate-900/10 rounded-xl border border-slate-200 dark:border-slate-700">
                                                    <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Bio Paragraph</h5>
                                                    <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                                                        {parsedGuidance.paragraph}
                                                    </p>
                                                </div>
                                            </div>
                                        )}

                                        {/* Keywords (V2 or V1) */}
                                        <div>
                                            <h5 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-3">
                                                {parsedKeywords?.type === 'v2' ? 'Targeted Professional Keywords' : 'Tactical Hard Skills'}
                                            </h5>
                                            <div className="flex flex-wrap gap-1.5">
                                                {parsedKeywords?.type === 'v2' && parsedKeywords.keywords.map((kw: string, i: number) => (
                                                    <span key={i} className="px-2 py-1 text-xs font-medium rounded-md bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-100 dark:border-blue-800">
                                                        {kw}
                                                    </span>
                                                ))}
                                                {parsedKeywords?.type === 'v1' && parsedKeywords.hard.map((kw: any, i: number) => (
                                                    <span key={i} className="px-2 py-1 text-xs font-medium rounded-md bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-100 dark:border-blue-800">
                                                        {kw.keyword}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Vocabulary Mirror (V2) */}
                                        {parsedVocab.length > 0 && (
                                            <div>
                                                <h5 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-3">Vocabulary Mirroring</h5>
                                                <div className="flex flex-wrap gap-1.5">
                                                    {parsedVocab.map((word: string, i: number) => (
                                                        <span key={i} className="px-2 py-1 text-xs font-medium rounded-md bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 border border-purple-100 dark:border-purple-800">
                                                            {word}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* V1 Narrative Guidance Fallback */}
                                        {parsedGuidance?.type === 'v1' && (
                                            <div className="p-4 bg-amber-50 dark:bg-amber-900/10 rounded-xl border border-amber-100 dark:border-amber-800/30">
                                                <h5 className="text-xs font-bold text-amber-900 dark:text-amber-300 uppercase tracking-wider mb-2">Narrative Guidance</h5>
                                                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                                                    {parsedGuidance.summary.join(' ')}
                                                </p>
                                            </div>
                                        )}

                                        {/* Bullets (Common for both V1 and V2) */}
                                        {parsedGuidance?.bullets && parsedGuidance.bullets.length > 0 && (
                                            <div>
                                                <h5 className="text-xs font-bold text-slate-500 uppercase mb-3">Impact Proof Points</h5>
                                                <ul className="space-y-2">
                                                    {parsedGuidance.bullets.map((bullet: string, i: number) => (
                                                        <li key={i} className="text-xs text-slate-600 dark:text-slate-400 flex gap-2">
                                                            <span className="text-blue-500 font-bold">•</span>
                                                            {bullet}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Company Context (AI Board Data) */}
                                {reviewedJob && (
                                    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
                                        <div className="bg-slate-50 dark:bg-slate-800/50 px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center gap-2">
                                            <CubeIcon className="h-5 w-5 text-emerald-500" />
                                            <h4 className="font-bold text-slate-900 dark:text-white">AI Board Analysis</h4>
                                        </div>
                                        <div className="p-6 space-y-4">
                                            <div>
                                                <h5 className="text-xs font-bold text-slate-500 uppercase mb-2">AI Rationale</h5>
                                                <p className="text-xs text-slate-600 dark:text-slate-400 italic">"{reviewedJob.rationale}"</p>
                                            </div>

                                            <div>
                                                <h5 className="text-xs font-bold text-slate-500 uppercase mb-2">TLDR Summary</h5>
                                                <p className="text-sm text-slate-800 dark:text-slate-200">{reviewedJob.tldr_summary}</p>
                                            </div>

                                            <div>
                                                <h5 className="text-xs font-bold text-slate-500 uppercase mb-3">Recommended Actions</h5>
                                                <ul className="space-y-2">
                                                    {(reviewedJob.crew_output?.human_centric_review?.recommended_actions || []).map((action: string, i: number) => (
                                                        <li key={i} className="flex gap-2 text-xs text-slate-600 dark:text-slate-400">
                                                            <PlusCircleIcon className="h-4 w-4 text-blue-500 flex-shrink-0" />
                                                            {action}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Company Research Snapshot */}
                                {company && (
                                    <div className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl text-white shadow-xl relative overflow-hidden group">
                                        <div className="flex items-center gap-2 mb-6">
                                            <StrategyIcon className="h-5 w-5 text-emerald-400" />
                                            <h4 className="font-bold tracking-tight">Company Intelligence</h4>
                                        </div>
                                        <div className="space-y-5 text-sm">
                                            {company.strategic_initiatives?.text && (
                                                <div>
                                                    <span className="text-emerald-400 block text-[10px] uppercase font-black tracking-widest mb-1.5 opacity-80">Strategic Initiatives</span>
                                                    <p className="text-slate-300 text-xs leading-relaxed">{company.strategic_initiatives.text}</p>
                                                </div>
                                            )}

                                            {Array.isArray(company.known_tech_stack) && company.known_tech_stack.length > 0 && (
                                                <div>
                                                    <span className="text-blue-400 block text-[10px] uppercase font-black tracking-widest mb-2 opacity-80">Known Tech Stack</span>
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {company.known_tech_stack.slice(0, 12).map(tech => (
                                                            <span key={tech} className="px-2 py-0.5 bg-slate-700/60 rounded text-[10px] border border-slate-600/40 text-slate-200">{tech}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {company.success_metrics?.text && (
                                                <div>
                                                    <span className="text-amber-400 block text-[10px] uppercase font-black tracking-widest mb-1.5 opacity-80">Success Metrics</span>
                                                    <p className="text-slate-300 text-xs leading-relaxed">{company.success_metrics.text}</p>
                                                </div>
                                            )}

                                            {company.talent_expectations?.text && (
                                                <div>
                                                    <span className="text-indigo-400 block text-[10px] uppercase font-black tracking-widest mb-1.5 opacity-80">Talent Expectations</span>
                                                    <p className="text-slate-300 text-xs leading-relaxed border-l-2 border-indigo-500/30 pl-3 italic font-medium">
                                                        {company.talent_expectations.text}
                                                    </p>
                                                </div>
                                            )}

                                            <button
                                                onClick={() => setShowCompanyModal(true)}
                                                className="w-full mt-4 py-2 border border-slate-700 bg-slate-800/50 hover:bg-slate-700/50 rounded-xl text-[10px] uppercase font-bold tracking-[0.2em] text-slate-400 hover:text-white transition-all"
                                            >
                                                Launch Deep Research Modal
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'resume' && (
                    <ResumeViewer resume={application.tailored_resume_json} version={application.tailored_resume_json_version} companyName={company.company_name} />
                )}

                {activeTab === 'questions' && (
                    <div className="space-y-8 animate-fade-in max-w-4xl mx-auto">
                        <div className="border-b border-slate-200 dark:border-slate-700 pb-5">
                            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Prepare Application Questions</h2>
                            <p className="mt-2 text-slate-600 dark:text-slate-400">Add any required application questions below. Bundle them with job and company research to export a prompt for your Gemini Gem.</p>
                        </div>

                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Application Questions</h3>
                                <div className="flex gap-2">
                                    <button
                                        type="button"
                                        onClick={handleSaveQuestions}
                                        className="inline-flex items-center gap-x-1.5 rounded-md bg-white dark:bg-slate-800 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700"
                                    >
                                        Save Questions
                                    </button>
                                    <button
                                        type="button"
                                        onClick={addQuestion}
                                        className="inline-flex items-center gap-x-1.5 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
                                    >
                                        <PlusCircleIcon className="-ml-0.5 h-5 w-5" />
                                        Add Question
                                    </button>
                                </div>
                            </div>

                            {questions.length === 0 ? (
                                <div className="text-center py-12 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl">
                                    <p className="text-slate-500 dark:text-slate-400">No questions added yet.</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {questions.map((qa, index) => (
                                        <div key={qa.id} className="group relative p-6 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-800/50 shadow-sm transition-all hover:shadow-md">
                                            <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button type="button" onClick={() => removeQuestion(index)} className="p-2 text-slate-400 hover:text-red-500 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
                                                    <TrashIcon className="h-5 w-5" />
                                                </button>
                                            </div>
                                            <div className="space-y-4">
                                                <div>
                                                    <label htmlFor={`question-${index}`} className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">Question {index + 1}</label>
                                                    <textarea
                                                        id={`question-${index}`}
                                                        rows={2}
                                                        value={qa.question}
                                                        onChange={(e) => handleQuestionChange(index, 'question', e.target.value)}
                                                        placeholder="Paste the application question here..."
                                                        className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                                    />
                                                </div>
                                                <div>
                                                    <label htmlFor={`thoughts-${index}`} className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">Your Context / Notes (Optional)</label>
                                                    <textarea
                                                        id={`thoughts-${index}`}
                                                        rows={2}
                                                        value={qa.user_thoughts || ''}
                                                        onChange={(e) => handleQuestionChange(index, 'user_thoughts', e.target.value)}
                                                        placeholder="Add specific points or experiences you want the AI to emphasize..."
                                                        className="block w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-2xl p-8 border border-blue-100 dark:border-blue-800/50">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                                <div className="space-y-1">
                                    <h3 className="text-xl font-bold text-blue-900 dark:text-blue-100">AI Export</h3>
                                    <p className="text-blue-700 dark:text-blue-300">Bundle all application context into a single prompt for your Gemini Gem.</p>

                                    <div className="flex items-center mt-4 bg-white dark:bg-slate-900/50 self-start px-4 py-2 rounded-full border border-blue-200 dark:border-blue-800 shadow-sm cursor-pointer select-none" onClick={() => setIncludeCoverLetter(!includeCoverLetter)}>
                                        <input
                                            id="include-cover-letter"
                                            type="checkbox"
                                            checked={includeCoverLetter}
                                            onChange={(e) => setIncludeCoverLetter(e.target.checked)}
                                            className="h-5 w-5 rounded border-blue-300 text-blue-600 focus:ring-blue-500 transition-colors"
                                            onClick={(e) => e.stopPropagation()}
                                        />
                                        <label htmlFor="include-cover-letter" className="ml-3 text-sm font-medium text-blue-900 dark:text-blue-200 cursor-pointer">
                                            Include Cover Letter Request
                                        </label>
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    onClick={handleExportForAi}
                                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-8 py-4 text-lg font-bold text-white shadow-lg shadow-blue-500/30 hover:bg-blue-700 hover:-translate-y-0.5 transition-all active:translate-y-0 focus:outline-none focus:ring-4 focus:ring-blue-500/50"
                                >
                                    <SparklesIcon className="h-6 w-6" />
                                    Export Data for AI
                                </button>
                            </div>
                        </div>
                    </div>
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
                                                <p className="text-sm text-slate-500 dark:text-slate-400">{interview.interview_date ? new Date(interview.interview_date + 'T00:00:00Z').toLocaleDateString() : 'Date TBD'}</p>
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
                                                    <RocketLaunchIcon className="h-4 w-4" /> Co-pilot
                                                </button>
                                                <button onClick={() => onOpenStrategyStudio(interview)} disabled={isLoading} className="p-1.5 text-xs font-semibold rounded-md bg-white dark:bg-slate-700 ring-1 ring-inset ring-slate-300 dark:ring-slate-600 inline-flex items-center gap-1.5 hover:bg-slate-50" title="Open Strategy Studio">
                                                    <StrategyIcon className="h-4 w-4" /> Studio
                                                </button>
                                                <button onClick={() => { setEditingInterviewId(interview.interview_id); setEditableInterview({ interview_type: interview.interview_type, interview_date: interview.interview_date, live_notes: interview.live_notes || '', contact_ids: (interview.interview_contacts || []).map(c => c.contact_id) }); }} className="p-1.5 text-xs font-semibold rounded-md bg-white dark:bg-slate-700 ring-1 ring-inset ring-slate-300 dark:ring-slate-600">Edit</button>
                                                <button onClick={() => onDeleteInterview(interview.interview_id)} className="p-1 text-red-500 hover:text-red-400" title="Delete Interview"><TrashIcon className="h-5 w-5" /></button>
                                            </div>
                                        </div>
                                        {hasPrepData ? (
                                            <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                                                <details><summary className="text-sm font-semibold cursor-pointer">View AI Prep</summary>
                                                    <div className="text-xs mt-2 space-y-2 prose prose-xs dark:prose-invert max-w-none">
                                                        <p><strong>Focus Areas:</strong> {(interview.ai_prep_data.keyFocusAreas || []).join(', ')}</p>
                                                        <div><strong>Potential Questions They Might Ask You:</strong><ul>{(interview.ai_prep_data.potentialQuestions || []).map(q => <li key={q.question}><strong>{q.question}</strong><br /><em>Strategy: {q.strategy}</em></li>)}</ul></div>
                                                        <div><strong>Strategic Questions for You to Ask Them:</strong><ul>{(interview.ai_prep_data.questionsToAsk || []).map((q, i) => <li key={i}>{q}</li>)}</ul></div>
                                                        <div><strong>Potential Red Flags to Watch For:</strong><ul>{(interview.ai_prep_data.redFlags || []).map((flag, i) => <li key={i}>{flag}</li>)}</ul></div>
                                                    </div>
                                                </details>
                                            </div>
                                        ) : (
                                            <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700 text-center">
                                                <button onClick={() => handleGeneratePrep(interview, isRecruiterScreen)} disabled={isGeneratingPrep[interview.interview_id]} className="text-sm font-semibold text-blue-600 hover:underline">
                                                    {isGeneratingPrep[interview.interview_id] ? <LoadingSpinner /> : (isRecruiterScreen ? 'Generate Quick Prep' : 'Generate Prep with AI')}
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
                                        <div><label className={labelClass}>Interview Type</label><select value={editableInterview.interview_type || ''} onChange={e => setEditableInterview(prev => ({ ...prev, interview_type: e.target.value }))} className={inputClass}><option value="">Select type...</option>{INTERVIEW_TYPES.map(type => <option key={type} value={type}>{type}</option>)}</select></div>
                                        <div><label className={labelClass}>Date</label><input type="date" value={editableInterview.interview_date || ''} onChange={e => setEditableInterview(prev => ({ ...prev, interview_date: e.target.value }))} className={inputClass} /></div>
                                        <div>
                                            <label className={labelClass}>Interviewers</label>
                                            <div className="mt-1 max-h-32 overflow-y-auto border rounded-md p-2 space-y-1 bg-white dark:bg-slate-800">
                                                {relevantContactsForInterview.map(contact => (
                                                    <div key={contact.contact_id} className="flex items-center"><input type="checkbox" id={`contact-${contact.contact_id}`} checked={editableInterview.contact_ids?.includes(contact.contact_id) || false} onChange={e => { const { checked } = e.target; setEditableInterview(prev => ({ ...prev, contact_ids: checked ? [...(prev.contact_ids || []), contact.contact_id] : (prev.contact_ids || []).filter(id => id !== contact.contact_id) })); }} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" /><label htmlFor={`contact-${contact.contact_id}`} className="ml-2 text-sm text-slate-700 dark:text-slate-300">{contact.first_name} {contact.last_name}</label></div>
                                                ))}
                                                {relevantContactsForInterview.length === 0 && (
                                                    <p className="text-xs text-slate-500 dark:text-slate-400 p-2">
                                                        No relevant contacts found. Add contacts for "{company.company_name}" or for recruiting firms in the Engagement Hub.
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                        <div><label className={labelClass}>Live Notes</label><textarea rows={4} value={editableInterview.live_notes || ''} onChange={e => setEditableInterview(prev => ({ ...prev, live_notes: e.target.value }))} className={inputClass} /></div>
                                        <div className="flex justify-end gap-2"><button onClick={() => { setEditingInterviewId(null); setEditableInterview({}); }} className="px-3 py-1.5 text-sm font-semibold rounded-md bg-white dark:bg-slate-700 ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600">Cancel</button><button onClick={() => handleSaveInterview({ job_application_id: application.job_application_id, ...editableInterview }, editingInterviewId === 'new' ? undefined : editingInterviewId)} disabled={isSaving} className="px-3 py-1.5 text-sm font-semibold rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50">{isSaving ? <LoadingSpinner /> : 'Save'}</button></div>
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

                {/* Company Deep Research Modal */}
                {showCompanyModal && company && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm animate-fade-in">
                        <div className="bg-white dark:bg-slate-900 w-full max-w-5xl max-h-[90vh] rounded-3xl shadow-2xl overflow-hidden border border-slate-200 dark:border-slate-800 flex flex-col animate-scale-up">
                            {/* Modal Header */}
                            <div className="px-8 py-6 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl text-emerald-600 dark:text-emerald-400">
                                        <StrategyIcon className="h-6 w-6" />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-slate-900 dark:text-white leading-tight">{company.company_name}</h3>
                                        <p className="text-xs text-slate-500 font-medium tracking-wide uppercase">Deep Intelligence Research</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setShowCompanyModal(false)}
                                    className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-full transition-colors"
                                >
                                    <XMarkIcon className="h-6 w-6 text-slate-400" />
                                </button>
                            </div>

                            {/* Modal Body */}
                            <div className="flex-1 overflow-y-auto p-8 bg-white dark:bg-slate-900">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                                    {/* Left Column: Mission & Strategy */}
                                    <div className="space-y-10">
                                        <section>
                                            <h4 className="text-[10px] uppercase font-black text-indigo-500 tracking-[0.2em] mb-4">Mission & Values</h4>
                                            <div className="space-y-4">
                                                <div className="p-5 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-slate-700/50">
                                                    <p className="text-sm text-slate-700 dark:text-slate-300 italic leading-relaxed">"{company.mission?.text || 'No mission statement available.'}"</p>
                                                </div>
                                                <p className="text-sm text-slate-600 dark:text-slate-400 font-medium leading-relaxed">{company.values?.text}</p>
                                            </div>
                                        </section>

                                        <section>
                                            <h4 className="text-[10px] uppercase font-black text-emerald-500 tracking-[0.2em] mb-4">Strategic Initiatives</h4>
                                            <div className="p-6 bg-emerald-50/30 dark:bg-emerald-900/10 rounded-2xl border border-emerald-100 dark:border-emerald-900/30">
                                                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">{company.strategic_initiatives?.text || 'No strategic initiatives recorded.'}</p>
                                            </div>
                                        </section>

                                        <section>
                                            <h4 className="text-[10px] uppercase font-black text-amber-500 tracking-[0.2em] mb-4">Success Metrics & Goals</h4>
                                            <div className="space-y-4">
                                                <div className="flex items-start gap-3">
                                                    <div className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0" />
                                                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed font-bold">Metrics: <span className="font-normal text-slate-700 dark:text-slate-300">{company.success_metrics?.text || 'N/A'}</span></p>
                                                </div>
                                                <div className="flex items-start gap-3">
                                                    <div className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0" />
                                                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed font-bold">Goals: <span className="font-normal text-slate-700 dark:text-slate-300">{company.goals?.text || 'N/A'}</span></p>
                                                </div>
                                            </div>
                                        </section>
                                    </div>

                                    {/* Right Column: Market & Tech */}
                                    <div className="space-y-10">
                                        <section>
                                            <h4 className="text-[10px] uppercase font-black text-blue-500 tracking-[0.2em] mb-4">Technology Architecture</h4>
                                            <div className="flex flex-wrap gap-2">
                                                {Array.isArray(company.known_tech_stack) ? (
                                                    company.known_tech_stack.map(tech => (
                                                        <span key={tech} className="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-700">
                                                            {tech}
                                                        </span>
                                                    ))
                                                ) : (
                                                    <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{String(company.known_tech_stack || '')}</p>
                                                )}
                                                {(!company.known_tech_stack || (Array.isArray(company.known_tech_stack) && company.known_tech_stack.length === 0)) && !(!Array.isArray(company.known_tech_stack) && company.known_tech_stack) && (
                                                    <p className="text-sm text-slate-500 italic">No technology stack listed.</p>
                                                )}
                                            </div>
                                        </section>

                                        <section>
                                            <h4 className="text-[10px] uppercase font-black text-purple-500 tracking-[0.2em] mb-4">Market & Competitive Positioning</h4>
                                            <div className="space-y-4">
                                                <div className="p-5 bg-purple-50/50 dark:bg-purple-900/10 rounded-2xl border border-purple-100 dark:border-purple-900/30">
                                                    <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{company.market_position?.text}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Key Competitors</p>
                                                    <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{company.competitors?.text}</p>
                                                </div>
                                            </div>
                                        </section>

                                        <section>
                                            <h4 className="text-[10px] uppercase font-black text-indigo-500 tracking-[0.2em] mb-4">Talent Expectations</h4>
                                            <div className="p-6 bg-slate-900 text-slate-100 rounded-2xl shadow-inner border border-slate-800">
                                                <p className="text-sm leading-relaxed italic opacity-90">{company.talent_expectations?.text || 'No talent expectations research found.'}</p>
                                            </div>
                                        </section>
                                    </div>
                                </div>
                            </div>

                            {/* Modal Footer */}
                            <div className="px-8 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-700 flex justify-end items-center">
                                <button
                                    onClick={() => setShowCompanyModal(false)}
                                    className="px-6 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-bold text-sm hover:scale-105 active:scale-95 transition-all"
                                >
                                    Close Intelligence
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
