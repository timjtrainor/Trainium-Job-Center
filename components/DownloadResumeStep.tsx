import React, { useEffect, useState } from 'react';
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Tab, TabStopType, TabStopPosition, UnderlineType, Table, TableCell, TableRow, WidthType, BorderStyle, ExternalHyperlink } from 'docx';
import jsPDF from 'jspdf';
import { Resume, DateInfo, ResumeAccomplishment, WorkExperience, Education, SkillSection } from '../types';
import { LoadingSpinner, DocumentTextIcon, LightBulbIcon, ArrowDownTrayIcon, ClipboardDocumentListIcon, ClipboardDocumentCheckIcon } from './IconComponents';
import { ResetApplicationModal, ResetApplicationPayload, WorkflowModeOption } from './ResetApplicationModal';

interface DownloadResumeStepProps {
    finalResume: Resume | AiWorkflowResume;
    companyName: string;
    onNext?: () => void;
    onSaveAndStartAnother?: () => void;
    isLoading: boolean;
    onOpenJobDetailsModal?: () => void;
    onOpenAiAnalysisModal?: () => void;
    onClose?: () => void;
    jobApplicationId?: string;
    currentJobLink?: string;
    onUpdateJobLink?: (jobApplicationId: string, jobLink: string) => Promise<void>;
    onUpdateSalary?: (jobApplicationId: string, salary: string) => Promise<void>;
    jobTitle?: string;
    salary?: string;
    isMessageOnlyApp?: boolean;
    workflowMode?: string;
    jobDescription?: string;
    onResetToDraft?: (payload: ResetApplicationPayload) => Promise<void>;
    onMarkBadFit?: () => void;
}

// Type for AI workflow format - supports both wrapped and unwrapped formats
interface AiWorkflowResume {
    resume?: {
        header: Resume['header'];
        summary: Resume['summary'];
        skills: Array<{
            items: string[];
            heading: string;
        }> | {
            items: string[];
            heading: string;
        };
        education: {
            education: Array<{
                major: string[];
                minor: string[];
                degree: string;
                school: string;
                end_year: number;
                location: string;
                end_month: number;
                start_year: number;
                start_month: number;
            }>;
        };
        work_experience: Array<{
            end_date: { year: number; month: number };
            location: string;
            job_title: string;
            is_current: boolean;
            start_date: { year: number; month: number };
            company_name: string;
            role_context?: string;
            accomplishments: Array<{
                description: string;
                impact_focus?: string;
                proof_point_ref?: string;
                relevance_score?: number;
                keyword_suggestions?: string[];
            }>;
        }>;
        certifications?: Array<{
            name: string;
            organization: string;
            link?: string;
            issued_date: string;
        }>;
    };
    // Support for direct format without wrapper (new AI workflow format)
    header?: Resume['header'];
    summary?: Resume['summary'];
    skills?: Array<{
        items: string[];
        heading: string;
    }> | {
        items: string[];
        heading: string;
    };
    education?: {
        education: Array<{
            major: string[];
            minor: string[];
            degree: string;
            school: string;
            end_year: number;
            location: string;
            end_month: number;
            start_year: number;
            start_month: number;
        }>;
    };
    work_experience?: Array<{
        end_date: { year: number; month: number };
        location: string;
        job_title: string;
        is_current: boolean;
        start_date: { year: number; month: number };
        company_name: string;
        role_context?: string;
        accomplishments: Array<{
            description: string;
            impact_focus?: string;
            proof_point_ref?: string;
            relevance_score?: number;
            keyword_suggestions?: string[];
        }>;
    }>;
    certifications?: Array<{
        name: string;
        organization: string;
        link?: string;
        issued_date: string;
    }>;
}

interface ExportOptionProps {
    title: string;
    description: string;
    icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
    onClick: () => void | Promise<void>;
    isLoading: boolean;
    buttonText: string;
    showSpinner?: boolean;
}

const ExportOption: React.FC<ExportOptionProps> = ({
    title,
    description,
    icon: Icon,
    onClick,
    isLoading,
    buttonText,
    showSpinner = true,
}) => (
    <div className="flex flex-col justify-between rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 shadow-sm">
        <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300">
                <Icon className="h-5 w-5" />
            </span>
            <div>
                <h3 className="text-base font-semibold text-slate-900 dark:text-white">{title}</h3>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{description}</p>
            </div>
        </div>
        <button
            type="button"
            onClick={onClick}
            disabled={isLoading}
            className="mt-6 inline-flex w-full items-center justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-blue-400"
        >
            {isLoading && showSpinner ? (
                <span className="flex items-center gap-2">
                    <LoadingSpinner />
                    <span>{buttonText}</span>
                </span>
            ) : (
                buttonText
            )}
        </button>
    </div>
);

// Detect resume format - handle various formats based on data structure
const detectResumeFormat = (resume: Resume | AiWorkflowResume): 'current' | 'ai-workflow' => {
    // Check for wrapped format
    if ('resume' in resume) {
        return 'ai-workflow';
    }

    // Check if it's the new AI workflow format (no wrapper, but has AI workflow structure)
    // This handles the case where skills or education have nested AI workflow structures
    if ((resume.skills && 'items' in resume.skills) ||
        (resume.education && 'education' in resume.education)) {
        return 'ai-workflow';
    }

    return 'current';
};

// Transform AI workflow format to current format
const transformAiWorkflowResume = (aiResume: AiWorkflowResume): Resume => {
    // Handle both wrapped and unwrapped formats
    const resumeData = aiResume.resume || aiResume;

    // Transform work experience - strip extra fields from accomplishments
    const workExperienceSource = Array.isArray(resumeData.work_experience) ? resumeData.work_experience : [];
    const work_experience: WorkExperience[] = workExperienceSource.map(exp => ({
        company_name: exp.company_name,
        job_title: exp.job_title,
        location: exp.location,
        start_date: normalizeDateField(exp.start_date),
        end_date: normalizeDateField(exp.end_date),
        is_current: exp.is_current,
        role_context: exp.role_context,
        filter_accomplishment_count: exp.accomplishments.length,
        accomplishments: exp.accomplishments.map(acc => ({
            achievement_id: '', // Will be filled by the system
            description: acc.description,
            always_include: true,
            order_index: 0,
            // Ignore: impact_focus, proof_point_ref, relevance_score, keyword_suggestions
        })) as ResumeAccomplishment[]
    }));

    // Transform education - extract from nested structure for unwrapped format
    const educationSource = Array.isArray(resumeData.education?.education)
        ? resumeData.education.education
        : Array.isArray(resumeData.education)
            ? resumeData.education
            : [];
    const education: Education[] = educationSource.map(edu => ({
        school: edu.school,
        location: edu.location,
        degree: edu.degree,
        major: edu.major || [],
        minor: edu.minor || [],
        start_month: edu.start_month,
        start_year: edu.start_year,
        end_month: edu.end_month,
        end_year: edu.end_year,
    }));

    // Transform skills - handle AI workflow format (object or array)
    let skills: SkillSection[] = [];
    const skillsSource = resumeData.skills;
    if (Array.isArray(skillsSource)) {
        skills = skillsSource;
    } else if (skillsSource && 'items' in skillsSource) {
        skills = [{
            heading: skillsSource.heading || 'Skills',
            items: skillsSource.items,
        }];
    }

    // Extract certifications from AI workflow data if they exist
    const certifications: Array<{
        name: string;
        organization: string;
        link?: string;
        issued_date: string;
    }> = resumeData.certifications || [];

    // Only include summary if it exists and has content
    let summary = undefined;
    if (resumeData.summary) {
        const hasParagraph = resumeData.summary.paragraph?.trim();
        const hasBullets = Array.isArray(resumeData.summary.bullets) && resumeData.summary.bullets.length > 0;
        if (hasParagraph || hasBullets || resumeData.summary.headline) {
            summary = {
                headline: resumeData.summary.headline || '',
                paragraph: resumeData.summary.paragraph || '',
                bullets: Array.isArray(resumeData.summary.bullets) ? resumeData.summary.bullets : [],
            };
        }
    }

    return {
        header: resumeData.header,
        summary,
        work_experience,
        education,
        certifications,
        skills,
    };

};

export const DownloadResumeStep = ({
    finalResume,
    companyName,
    onNext,
    onSaveAndStartAnother,
    isLoading,
    onOpenJobDetailsModal,
    onOpenAiAnalysisModal,
    onClose,
    jobApplicationId,
    currentJobLink,
    onUpdateJobLink,
    onUpdateSalary,
    jobTitle,
    salary,
    isMessageOnlyApp,
    workflowMode,
    jobDescription,
    onResetToDraft,
    onMarkBadFit
}: DownloadResumeStepProps): React.ReactNode => {
    const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
    const [isGeneratingDocx, setIsGeneratingDocx] = useState(false);
    const [copySuccess, setCopySuccess] = useState(false);
    const [jobLink, setJobLink] = useState(currentJobLink || '');
    const [currentSalary, setCurrentSalary] = useState(salary || '');
    const [isResetModalOpen, setIsResetModalOpen] = useState(false);
    const [isSubmittingReset, setIsSubmittingReset] = useState(false);
    const [linkSaveState, setLinkSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
    const [salarySaveState, setSalarySaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

    useEffect(() => {
        setJobLink(currentJobLink || '');
    }, [currentJobLink]);

    useEffect(() => {
        setCurrentSalary(salary || '');
    }, [salary]);

    const handleDownloadPdf = async () => {
        setIsGeneratingPdf(true);
        try {
            generatePdf(finalResume, companyName);
        } catch (error) {
            console.error("Failed to generate PDF:", error);
        } finally {
            setIsGeneratingPdf(false);
        }
    };

    const handleDownloadDocx = async () => {
        setIsGeneratingDocx(true);
        try {
            await generateDocx(finalResume, companyName);
        } catch (error) {
            console.error("Failed to generate DOCX:", error);
        } finally {
            setIsGeneratingDocx(false);
        }
    };

    const handleCopyToClipboard = async () => {
        setCopySuccess(false);
        const markdownText = resumeToMarkdown(finalResume);
        try {
            await navigator.clipboard.writeText(markdownText);
            setCopySuccess(true);
            setTimeout(() => setCopySuccess(false), 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    };

    const handleSaveLink = async () => {
        if (!onUpdateJobLink || !jobApplicationId) {
            return;
        }
        try {
            setLinkSaveState('saving');
            await onUpdateJobLink(jobApplicationId, jobLink);
            setLinkSaveState('saved');
            setTimeout(() => setLinkSaveState('idle'), 2500);
        } catch (error) {
            console.error('Failed to update job link', error);
            setLinkSaveState('error');
            setTimeout(() => setLinkSaveState('idle'), 4000);
        }
    };

    const handleSaveSalary = async () => {
        if (!onUpdateSalary || !jobApplicationId) {
            return;
        }
        try {
            setSalarySaveState('saving');
            await onUpdateSalary(jobApplicationId, currentSalary);
            setSalarySaveState('saved');
            setTimeout(() => setSalarySaveState('idle'), 2500);
        } catch (error) {
            console.error('Failed to update salary', error);
            setSalarySaveState('error');
            setTimeout(() => setSalarySaveState('idle'), 4000);
        }
    };

    const defaultWorkflowMode: WorkflowModeOption =
        workflowMode === 'ai_generated' || workflowMode === 'fast_track' || workflowMode === 'manual'
            ? workflowMode
            : 'manual';

    const handleResetSubmit = async (payload: ResetApplicationPayload) => {
        if (!onResetToDraft) {
            return;
        }
        try {
            setIsSubmittingReset(true);
            await onResetToDraft(payload);
            setIsResetModalOpen(false);
        } finally {
            setIsSubmittingReset(false);
        }
    };

    return (
        <>
            <div className="space-y-6 animate-fade-in">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Export Your Resume</h2>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">Download your resume, or copy the text to paste into Google Docs or another editor.</p>
                </div>

                {/* Job Summary Section */}
                {(companyName || jobTitle || salary || isMessageOnlyApp !== undefined) && (
                    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Job Summary</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <div className="text-sm font-medium text-slate-500 dark:text-slate-400">Company</div>
                                <div className="text-base text-slate-900 dark:text-white">{companyName || 'N/A'}</div>
                            </div>
                            <div>
                                <div className="text-sm font-medium text-slate-500 dark:text-slate-400">Job Title</div>
                                <div className="text-base text-slate-900 dark:text-white">{jobTitle || 'N/A'}</div>
                            </div>
                            <div>
                                <div className="text-sm font-medium text-slate-500 dark:text-slate-400">Salary</div>
                                <div className="text-base text-slate-900 dark:text-white">{salary || 'N/A'}</div>
                            </div>
                            <div>
                                <div className="text-sm font-medium text-slate-500 dark:text-slate-400">Workflow Mode</div>
                                <div className="text-base text-slate-900 dark:text-white">
                                    {(() => {
                                        if (isMessageOnlyApp) {
                                            return 'Message Only';
                                        }
                                        const normalizedMode: WorkflowModeOption | 'unknown' =
                                            workflowMode === 'ai_generated' || workflowMode === 'fast_track' || workflowMode === 'manual'
                                                ? workflowMode
                                                : 'unknown';
                                        switch (normalizedMode) {
                                            case 'ai_generated':
                                                return 'AI Generated';
                                            case 'fast_track':
                                                return 'Fast Track';
                                            case 'manual':
                                                return 'Manual AI';
                                            default:
                                                return 'Manual AI';
                                        }
                                    })()}
                                </div>
                            </div>
                        </div>

                        {(onResetToDraft || onMarkBadFit) && (
                            <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                                {onResetToDraft && (
                                    <button
                                        onClick={() => setIsResetModalOpen(true)}
                                        disabled={isLoading || isGeneratingPdf || isGeneratingDocx}
                                        className="inline-flex items-center px-4 py-2 border border-red-300 dark:border-red-600 text-red-700 dark:text-red-400 rounded-md hover:bg-red-50 dark:hover:bg-red-900/20 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors disabled:opacity-60"
                                    >
                                        <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                                        Reset to Draft
                                    </button>
                                )}
                                {onMarkBadFit && (
                                    <button
                                        onClick={onMarkBadFit}
                                        disabled={isLoading || isGeneratingPdf || isGeneratingDocx}
                                        className="inline-flex items-center px-4 py-2 border border-amber-300 dark:border-amber-600 text-amber-700 dark:text-amber-400 rounded-md hover:bg-amber-50 dark:hover:bg-amber-900/20 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-colors disabled:opacity-60"
                                    >
                                        Mark as Bad Fit
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {(onOpenJobDetailsModal && onOpenAiAnalysisModal) && (
                    <div className="flex space-x-2">
                        <button
                            type="button"
                            onClick={onOpenJobDetailsModal}
                            className="inline-flex items-center gap-x-1.5 rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600"
                        >
                            <DocumentTextIcon className="h-5 w-5" />
                            View Job Details
                        </button>
                        <button
                            type="button"
                            onClick={onOpenAiAnalysisModal}
                            className="inline-flex items-center gap-x-1.5 rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600"
                        >
                            <LightBulbIcon className="h-5 w-5" />
                            View AI Analysis
                        </button>
                    </div>
                )}

                {jobApplicationId && onUpdateJobLink && (
                    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                        <h3 className="text-lg font-semibold mb-2 text-slate-900 dark:text-white">Job Application Link</h3>
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                            <div className="flex-1 w-full">
                                <input
                                    type="url"
                                    value={jobLink}
                                    onChange={(e) => {
                                        setJobLink(e.target.value);
                                        if (linkSaveState !== 'idle') {
                                            setLinkSaveState('idle');
                                        }
                                    }}
                                    placeholder="https://company.com/jobs/..."
                                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                                />
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={handleSaveLink}
                                    disabled={linkSaveState === 'saving'}
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-60 disabled:cursor-not-allowed"
                                >
                                    {linkSaveState === 'saving' ? 'Saving…' : 'Save Link'}
                                </button>
                                {linkSaveState === 'saved' && (
                                    <span className="text-sm text-green-600 dark:text-green-400">Saved!</span>
                                )}
                                {linkSaveState === 'error' && (
                                    <span className="text-sm text-red-600 dark:text-red-400">Save failed. Try again.</span>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {jobApplicationId && onUpdateSalary && (
                    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                        <h3 className="text-lg font-semibold mb-2 text-slate-900 dark:text-white">Salary Information</h3>
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                            <div className="flex-1 w-full">
                                <input
                                    type="text"
                                    value={currentSalary}
                                    onChange={(e) => {
                                        setCurrentSalary(e.target.value);
                                        if (salarySaveState !== 'idle') {
                                            setSalarySaveState('idle');
                                        }
                                    }}
                                    placeholder="e.g. $120,000 - $150,000"
                                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                                />
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={handleSaveSalary}
                                    disabled={salarySaveState === 'saving'}
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-60 disabled:cursor-not-allowed"
                                >
                                    {salarySaveState === 'saving' ? 'Saving…' : 'Save Salary'}
                                </button>
                                {salarySaveState === 'saved' && (
                                    <span className="text-sm text-green-600 dark:text-green-400">Saved!</span>
                                )}
                                {salarySaveState === 'error' && (
                                    <span className="text-sm text-red-600 dark:text-red-400">Save failed. Try again.</span>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                    <ExportOption
                        title="Professional PDF"
                        description="A clean, polished PDF ready to send. Best for direct applications."
                        icon={DocumentTextIcon}
                        onClick={handleDownloadPdf}
                        isLoading={isGeneratingPdf}
                        buttonText="Download PDF"
                    />
                    <ExportOption
                        title="Editable DOCX"
                        description="A .docx file optimized for Google Docs. Best for making final manual edits."
                        icon={ClipboardDocumentListIcon}
                        onClick={handleDownloadDocx}
                        isLoading={isGeneratingDocx}
                        buttonText="Download .docx"
                    />
                    <ExportOption
                        title="Copy as Markdown"
                        description="Copies formatted Markdown. Best for quick use in GitHub, Notion, or other MD-supported platforms."
                        icon={ClipboardDocumentCheckIcon}
                        onClick={handleCopyToClipboard}
                        isLoading={copySuccess}
                        buttonText={copySuccess ? 'Copied!' : 'Copy Markdown'}
                        showSpinner={false}
                    />
                </div>

                <div className="flex items-center justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
                    {onClose ? (
                        <button
                            onClick={onClose}
                            disabled={isLoading || isGeneratingPdf || isGeneratingDocx}
                            className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                        >
                            Close
                        </button>
                    ) : (
                        <div className="flex items-center justify-between w-full">
                            {onSaveAndStartAnother && (
                                <button
                                    onClick={onSaveAndStartAnother}
                                    disabled={isLoading || isGeneratingPdf || isGeneratingDocx}
                                    className="px-6 py-2 text-base font-medium rounded-lg text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 border border-slate-300 dark:border-slate-500 shadow-sm transition-colors disabled:opacity-50"
                                >
                                    Save & Start Another
                                </button>
                            )}
                            {onNext && (
                                <button
                                    onClick={onNext}
                                    disabled={isLoading || isGeneratingPdf || isGeneratingDocx}
                                    className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors disabled:bg-green-400"
                                >
                                    {isLoading ? <LoadingSpinner /> : 'Next: Answer Questions'}
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>
            {onResetToDraft && (
                <ResetApplicationModal
                    isOpen={isResetModalOpen}
                    onClose={() => setIsResetModalOpen(false)}
                    onSubmit={handleResetSubmit}
                    initialValues={{
                        workflowMode: defaultWorkflowMode,
                        jobTitle: jobTitle || '',
                        jobLink: jobLink,
                        jobDescription: jobDescription || '',
                        isMessageOnlyApp: !!isMessageOnlyApp,
                    }}
                    isSaving={isSubmittingReset}
                />
            )}
        </>
    );
};
// Normalize resume to current format
const normalizeResume = (resume: Resume | AiWorkflowResume): Resume => {
    const format = detectResumeFormat(resume);
    let normalized: Resume;

    if (format === 'ai-workflow') {
        normalized = transformAiWorkflowResume(resume as AiWorkflowResume);
    } else {
        // Handle standard resume format
        normalized = { ...(resume as Resume) };
    }

    // Apply normalization to ensure all required fields exist with proper defaults

    // Ensure education is always an array and properly structured
    if (normalized.education) {
        // Handle case where education is nested like { education: [] }
        const eduAsAny = normalized.education as any;
        if (!Array.isArray(normalized.education) && eduAsAny && 'education' in eduAsAny && Array.isArray(eduAsAny.education)) {
            normalized.education = eduAsAny.education;
        } else if (!Array.isArray(normalized.education)) {
            normalized.education = [];
        }
    } else {
        normalized.education = [];
    }

    if (!Array.isArray(normalized.work_experience)) {
        normalized.work_experience = [];
    }

    if (!Array.isArray(normalized.skills)) {
        normalized.skills = [];
    }

    if (!Array.isArray(normalized.certifications)) {
        normalized.certifications = [];
    }

    if (!normalized.summary) {
        normalized.summary = { headline: '', paragraph: '', bullets: [] };
    } else {
        normalized.summary = {
            headline: normalized.summary.headline || '',
            paragraph: normalized.summary.paragraph || '',
            bullets: Array.isArray(normalized.summary.bullets) ? normalized.summary.bullets : [],
        };
    }

    if (normalized.header && !Array.isArray(normalized.header.links)) {
        normalized.header = {
            ...normalized.header,
            links: normalized.header.links ? [normalized.header.links].flat() : [],
        };
    }

    return normalized;
};

const formatDate = (date: DateInfo, format: 'short' | 'long' | 'year' = 'long'): string => {
    if (!date || !date.month || !date.year) return '';
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    if (format === 'year') return date.year.toString();
    if (format === 'short') return `${monthNames[date.month - 1].substring(0, 3)} ${date.year}`;
    return `${monthNames[date.month - 1]} ${date.year}`;
};

const resumeToMarkdown = (resume: Resume | AiWorkflowResume): string => {
    const normalized = normalizeResume(resume);
    const { header, summary, work_experience, education, certifications, skills } = normalized;

    const sections: string[] = [];

    const fullName = [header?.first_name, header?.last_name].filter(Boolean).join(' ').trim();
    if (fullName) {
        sections.push(`# ${fullName}`);
    }

    if (header?.job_title) {
        sections.push(`**${header.job_title}**`);
    }

    const contactParts: string[] = [];
    if (header) {
        const location = [header.city, header.state].filter(Boolean).join(' | ');
        if (location) contactParts.push(location);
        if (header.email) contactParts.push(header.email);
        if (header.phone_number) contactParts.push(header.phone_number);
        if (header.links && header.links.length > 0) {
            contactParts.push(header.links.join(' | '));
        }
    }
    if (contactParts.length > 0) {
        sections.push(contactParts.join(' | '));
    }

    const summaryLines: string[] = [];
    if (summary?.headline) {
        summaryLines.push(`## ${summary.headline.toUpperCase()}`);
    }
    if (summary?.paragraph) {
        summaryLines.push(summary.paragraph);
    }
    if (summary?.bullets && summary.bullets.length > 0) {
        summaryLines.push(summary.bullets.join(' • '));
    }
    if (summaryLines.length > 0) {
        // Remove '## Summary' and just use the billboard content if headline exists
        if (summary?.headline) {
            sections.push(summaryLines.join('\n\n'));
        } else {
            sections.push(['## Summary', summaryLines.join('\n\n')].join('\n'));
        }
    }

    if (work_experience.length > 0) {
        const experienceLines: string[] = ['## Professional Experience'];
        work_experience.forEach(job => {
            const titlePieces = [job.job_title, job.company_name].filter(Boolean).join(' · ');
            const startText = job.start_date ? formatDate(job.start_date, 'short') : '';
            const endText = job.is_current ? 'Present' : (job.end_date ? formatDate(job.end_date, 'short') : '');
            const dateRange = [startText, endText].filter(Boolean).join(' - ');
            const subtitleParts = [job.location, dateRange].filter(Boolean).join(' • ');

            if (titlePieces) {
                experienceLines.push(`### ${titlePieces}`);
            }
            if (subtitleParts) {
                experienceLines.push(`_${subtitleParts}_`);
            }
            if (job.role_context) {
                experienceLines.push(`_${job.role_context}_`);
            }
            if (job.accomplishments && job.accomplishments.length > 0) {
                job.accomplishments.forEach(acc => {
                    if (acc.description) {
                        experienceLines.push(`- ${acc.description}`);
                    }
                });
            }
            experienceLines.push('');
        });
        sections.push(experienceLines.join('\n').trim());
    }

    if (education.length > 0) {
        const educationLines: string[] = ['## Education'];
        education.forEach(edu => {
            const titlePieces = [edu.degree, [...(edu.major || [])].join(', ')].filter(Boolean).join(' in ');
            const schoolLine = [edu.school, edu.location].filter(Boolean).join(' · ');

            if (schoolLine) {
                educationLines.push(`### ${schoolLine}`);
            }
            if (titlePieces) {
                educationLines.push(titlePieces);
            }
            educationLines.push('');
        });
        sections.push(educationLines.join('\n').trim());
    }

    if (certifications.length > 0) {
        const certificationLines: string[] = ['## Certifications'];
        certifications.forEach(cert => {
            const certParts = [cert.name, cert.organization, cert.issued_date].filter(Boolean);
            if (certParts.length > 0) {
                certificationLines.push(`- ${certParts.join(' • ')}`);
            }
        });
        sections.push(certificationLines.join('\n'));
    }

    if (skills.length > 0) {
        const skillLines: string[] = ['## Skills'];
        skills.forEach(section => {
            if (section.heading || (section.items && section.items.length > 0)) {
                const heading = section.heading ? `**${section.heading}**: ` : '';
                const itemsText = (section.items || []).join(', ');
                skillLines.push(heading + itemsText);
            }
        });
        sections.push(skillLines.join('\n'));
    }

    return sections.filter(Boolean).join('\n\n').trim();
};

const generateDocx = async (resume: Resume | AiWorkflowResume, companyName: string) => {
    const normalizedResume = normalizeResume(resume);
    const { header, summary, work_experience, education, certifications, skills } = normalizedResume;

    const docChildren: (Paragraph | Table)[] = [
        new Paragraph({ style: "ApplicantName", text: `${header.first_name || ''} ${header.last_name || ''}` }),
        new Paragraph({ style: "JobTitle", text: header.job_title || '' }),
        new Paragraph({
            style: "ContactInfo",
            children: [
                new ExternalHyperlink({
                    children: [new TextRun({ text: header.email || '', style: "ContactInfo" })],
                    link: `mailto:${header.email}`,
                }),
                new TextRun({ text: " | ", style: "ContactInfo" }),
                new ExternalHyperlink({
                    children: [new TextRun({ text: header.phone_number || '', style: "ContactInfo" })],
                    link: `tel:${header.phone_number}`,
                }),
                new TextRun({
                    text: (header.city || header.state) ? ` | ${[header.city, header.state].filter(Boolean).join(', ')}` : '',
                    style: "ContactInfo"
                }),
            ],
            spacing: { after: 0 }
        }),
        new Paragraph({
            style: "ContactInfo",
            children: (header.links || []).flatMap((link, i) => {
                const cleanLink = link.replace(/^https?:\/\//, '');
                const parts: any[] = [
                    new ExternalHyperlink({
                        children: [new TextRun({ text: cleanLink, style: "ContactInfo" })],
                        link: link.startsWith('http') ? link : `https://${link}`,
                    })
                ];
                if (i < (header.links?.length || 0) - 1) {
                    parts.push(new TextRun({ text: " | ", style: "ContactInfo" }));
                }
                return parts;
            })
        }),
    ];

    // --- BILLBOARD SUMMARY ---
    if (summary.headline || summary.paragraph || (summary.bullets && summary.bullets.length > 0)) {
        if (summary.headline) {
            docChildren.push(new Paragraph({
                style: "Section",
                text: summary.headline.toUpperCase(),
                alignment: AlignmentType.LEFT,
                thematicBreak: true
            }));
        } else {
            docChildren.push(new Paragraph({ style: "Section", text: "Executive Profile", thematicBreak: true }));
        }

        if (summary.paragraph) {
            docChildren.push(new Paragraph({ text: summary.paragraph, style: "Normal" }));
        }

        if (summary.bullets && summary.bullets.length > 0) {
            docChildren.push(new Paragraph({
                text: summary.bullets.join('  •  '),
                style: "Normal",
                alignment: AlignmentType.CENTER
            }));
        }
    }

    // --- PROFESSIONAL EXPERIENCE ---
    if (work_experience && work_experience.length > 0) {
        docChildren.push(new Paragraph({ style: "Section", text: "Professional Experience", thematicBreak: true }));
        work_experience.forEach((exp, index) => {
            const spacingBefore = index === 0 ? 0 : 200;

            docChildren.push(
                new Paragraph({
                    spacing: { before: spacingBefore, after: 0 },
                    keepNext: true,
                    keepLines: true,
                    children: [
                        new TextRun({ text: `${exp.company_name}, ${exp.location}`, bold: true, size: 24, font: "Calibri" }),
                        new TextRun({ children: [new Tab(), `${formatDate(exp.start_date)} - ${exp.is_current ? 'Present' : formatDate(exp.end_date)}`], size: 24, font: "Calibri" }),
                    ],
                    tabStops: [{ type: TabStopType.RIGHT, position: 9600 }],
                }),
                new Paragraph({
                    style: "JobHeading2",
                    text: exp.job_title,
                    keepNext: true,
                    keepLines: true,
                })
            );

            if (exp.role_context) {
                docChildren.push(new Paragraph({
                    style: "JobHeading2",
                    text: exp.role_context,
                    keepNext: true,
                    keepLines: true,
                }));
            }

            exp.accomplishments.forEach((acc, i) => {
                const isLast = i === exp.accomplishments.length - 1;
                docChildren.push(new Paragraph({
                    text: acc.description,
                    style: "ListParagraph",
                    bullet: { level: 0 },
                    keepNext: !isLast,
                    keepLines: true,
                    spacing: { after: isLast ? 100 : 0 }
                }));
            });
        });
    }

    if (education && education.length > 0 && education[0].school) {
        docChildren.push(new Paragraph({ style: "Section", text: "Education", thematicBreak: true }));
        education.forEach(edu => {
            docChildren.push(
                new Paragraph({
                    // Set spacing after to 40 twips (approx 2pt)
                    spacing: { after: 40 },
                    children: [
                        new TextRun({ text: `${edu.degree} in ${edu.major.join(', ')}`, bold: true, size: 24, font: "Calibri" }),
                    ],
                    tabStops: [{ type: TabStopType.RIGHT, position: 9600 }],
                }),
                new Paragraph({
                    style: "EduOther",
                    text: `${edu.school}, ${edu.location}`,
                    spacing: { after: 100 }
                })
            );
        });
    }

    // --- CERTIFICATIONS ---
    if (certifications && certifications.length > 0) {
        docChildren.push(new Paragraph({ style: "Section", text: "Certifications", thematicBreak: true }));
        certifications.forEach(cert => {
            let year = "";
            if (cert.issued_date) {
                const yearMatch = cert.issued_date.match(/\b(19|20)\d{2}\b/);
                year = yearMatch ? yearMatch[0] : cert.issued_date;
            }

            docChildren.push(
                new Paragraph({
                    spacing: { after: 0 },
                    children: [
                        new TextRun({ text: cert.name, bold: true, size: 24, font: "Calibri" }),
                        new TextRun({ text: ` - ${cert.organization}`, size: 24, font: "Calibri" }),
                        new TextRun({ children: [new Tab(), year], size: 24, font: "Calibri" }),
                    ],
                    tabStops: [{ type: TabStopType.RIGHT, position: 9600 }],
                })
            );
        });
    }

    // --- SKILLS AT BOTTOM ---
    if (skills && skills.length > 0) {
        docChildren.push(new Paragraph({ style: "Section", text: "Skills", thematicBreak: true }));
        skills.forEach((skillGroup, i) => {
            docChildren.push(new Paragraph({
                children: [
                    new TextRun({ text: `${skillGroup.heading}: `, bold: true, size: 22, font: "Calibri" }),
                    new TextRun({ text: skillGroup.items.join(', '), size: 22, font: "Calibri" }),
                ],
                spacing: { after: i === skills.length - 1 ? 200 : 0 }
            }));
        });
    }

    const doc = new Document({
        styles: {
            default: {
                document: {
                    run: { font: "Calibri", size: 22 },
                },
            },
            paragraphStyles: [
                { id: "Normal", name: "Normal", run: { font: "Calibri", size: 22 }, paragraph: { spacing: { after: 120 } } },
                { id: "ApplicantName", name: "Applicant Name", basedOn: "Normal", run: { font: "Calibri", size: 48, bold: true }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 0 } } },
                { id: "JobTitle", name: "Job Title", basedOn: "Normal", run: { font: "Calibri", size: 28 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 0 } } },
                { id: "ContactInfo", name: "Contact Info", basedOn: "Normal", run: { font: "Calibri", size: 22 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 120 } } },
                { id: "Section", name: "Section", basedOn: "Normal", run: { font: "Calibri", size: 24, bold: true, allCaps: true }, paragraph: { spacing: { before: 240, after: 120 } } },
                { id: "JobHeading2", name: "Job Heading 2", basedOn: "Normal", run: { font: "Calibri", size: 22, italics: true }, paragraph: { spacing: { after: 100 } } },
                { id: "EduOther", name: "EduOther", basedOn: "Normal", run: { font: "Calibri", size: 22, italics: true } },
                { id: "ListParagraph", name: "List Paragraph", basedOn: "Normal", paragraph: { indent: { left: 288 }, spacing: { after: 0 } } },
                { id: "SkillCell", name: "Skill Cell", basedOn: "ListParagraph", run: { font: "Calibri", size: 22 }, paragraph: { indent: { left: 200 }, spacing: { after: 40 } } },
            ]
        },
        sections: [{
            properties: {
                page: {
                    margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
                },
            },
            children: docChildren
        }],
    });

    const filename = `${header.first_name || 'Resume'} ${header.last_name || ''} - ${normalizedResume.header.job_title} - ${companyName}.docx`;
    const blob = await Packer.toBlob(doc);
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
};

const generatePdf = (resume: Resume | AiWorkflowResume, companyName: string) => {
    const normalizedResume = normalizeResume(resume);
    const doc = new jsPDF('p', 'pt', 'a4');
    const { header, summary, work_experience, education, certifications, skills } = normalizedResume;

    const styles = {
        margin: 54,
        colors: {
            text: [31, 41, 55] as [number, number, number],
            accent: [37, 99, 235] as [number, number, number],
            divider: [148, 163, 184] as [number, number, number],
        },
        typography: {
            name: { font: 'helvetica', size: 24, lineHeight: 30 },
            title: { font: 'helvetica', size: 13, lineHeight: 18 },
            contact: { font: 'helvetica', size: 10, lineHeight: 14 },
            section: { font: 'helvetica', size: 11, lineHeight: 16 },
            body: { font: 'helvetica', size: 10.5, lineHeight: 15 },
        },
        spacing: {
            afterName: 8,
            afterTitle: 4,
            afterContact: 2,
            afterLinks: 12,
            sectionTop: 14,
            sectionBottom: 6,
            bulletIndent: 12,
            bulletMarkerOffset: 4,
            jobSpacing: 14,
            jobMetaSpacing: 10,
            betweenColumns: 16,
        },
    } as const;

    type PdfFontWeight = 'normal' | 'bold' | 'italic' | 'bolditalic';

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const contentWidth = pageWidth - styles.margin * 2;
    const bodyLineHeight = styles.typography.body.lineHeight;
    const bulletIndent = styles.spacing.bulletIndent;
    const bulletMarkerOffset = styles.spacing.bulletMarkerOffset;

    doc.setTextColor(...styles.colors.text);
    doc.setLineHeightFactor(1.4);

    let cursorY = styles.margin;

    const setFont = (style: { font: string; size: number }, weight: PdfFontWeight = 'normal') => {
        doc.setFont(style.font, weight).setFontSize(style.size);
    };

    const setBodyFont = (weight: PdfFontWeight = 'normal') => {
        setFont(styles.typography.body, weight);
    };

    const addSpacing = (amount: number) => {
        cursorY += amount;
    };

    const checkPageBreak = (heightNeeded: number = bodyLineHeight) => {
        if (cursorY + heightNeeded > pageHeight - styles.margin) {
            doc.addPage();
            cursorY = styles.margin;
            doc.setTextColor(...styles.colors.text);
            doc.setLineHeightFactor(1.4);
            setBodyFont();
        }
    };

    const drawSectionHeading = (title: string) => {
        const requiredHeight = styles.spacing.sectionTop + styles.typography.section.lineHeight + styles.spacing.sectionBottom;
        checkPageBreak(requiredHeight);
        addSpacing(styles.spacing.sectionTop);
        setFont(styles.typography.section, 'bold');
        doc.text(title.toUpperCase(), styles.margin, cursorY);
        doc.setDrawColor(...styles.colors.divider);
        doc.setLineWidth(1);
        doc.line(styles.margin, cursorY + 6, pageWidth - styles.margin, cursorY + 6);
        addSpacing(styles.typography.section.lineHeight + styles.spacing.sectionBottom);
        setBodyFont();
    };

    const drawBulletedBlock = (items: string[], width: number) => {
        items.forEach(item => {
            const trimmed = item?.trim();
            if (!trimmed) {
                return;
            }
            const lines = doc.splitTextToSize(trimmed, width - bulletIndent);
            const blockHeight = Math.max(lines.length, 1) * bodyLineHeight;
            checkPageBreak(blockHeight);
            doc.text('•', styles.margin + bulletMarkerOffset, cursorY);
            doc.text(lines, styles.margin + bulletIndent, cursorY);
            addSpacing(blockHeight);
        });
    };

    const fullName = [header?.first_name, header?.last_name].filter(Boolean).join(' ').trim() || 'Resume';

    setFont(styles.typography.name, 'bold');
    doc.text(fullName, pageWidth / 2, cursorY, { align: 'center' });
    addSpacing(styles.spacing.afterName);

    if (header?.job_title) {
        setFont(styles.typography.title);
        doc.text(header.job_title, pageWidth / 2, cursorY, { align: 'center' });
        addSpacing(styles.spacing.afterTitle);
    }

    const location = [header?.city, header?.state].filter(Boolean).join(' | ');
    const contactParts = [location, header?.email, header?.phone_number].filter(Boolean).join(' | ');
    if (contactParts) {
        setFont(styles.typography.contact);
        doc.text(contactParts, pageWidth / 2, cursorY, { align: 'center' });
        addSpacing(12); // Explicit space before links
    }

    if (header?.links && header.links.length > 0) {
        setFont(styles.typography.contact);
        doc.setTextColor(...styles.colors.accent);
        doc.text(header.links.join(' | '), pageWidth / 2, cursorY, { align: 'center' });
        doc.setTextColor(...styles.colors.text);
        addSpacing(styles.spacing.afterLinks);
    }

    setBodyFont();

    const summaryHeadline = summary?.headline?.trim();
    const summaryParagraph = summary?.paragraph?.trim();
    const summaryBullets = summary?.bullets || [];

    if (summaryHeadline || summaryParagraph || summaryBullets.length > 0) {
        if (summaryHeadline) {
            drawSectionHeading(summaryHeadline.toUpperCase());
        } else {
            drawSectionHeading('Executive Profile');
        }

        if (summaryParagraph) {
            const paragraphLines = doc.splitTextToSize(summaryParagraph, contentWidth);
            const blockHeight = Math.max(paragraphLines.length, 1) * bodyLineHeight;
            checkPageBreak(blockHeight);
            doc.text(paragraphLines, styles.margin, cursorY);
            addSpacing(blockHeight);
        }

        if (summaryBullets.length > 0) {
            const bulletText = summaryBullets.join('  •  ');
            const bulletLines = doc.splitTextToSize(bulletText, contentWidth);
            const blockHeight = Math.max(bulletLines.length, 1) * bodyLineHeight;
            checkPageBreak(blockHeight);
            setBodyFont();
            doc.text(bulletLines, pageWidth / 2, cursorY, { align: 'center' });
            addSpacing(blockHeight + 8);
        }
    }

    // Move skills to after certifications (handled later)

    if (work_experience.length > 0) {
        drawSectionHeading('Professional Experience');

        work_experience.forEach((job, index) => {
            const companyLine = [job.company_name, job.location].filter(Boolean).join(', ');
            const startText = job.start_date ? formatDate(job.start_date, 'short') : '';
            const endText = job.is_current ? 'Present' : (job.end_date ? formatDate(job.end_date, 'short') : '');
            const dateRange = [startText, endText].filter(Boolean).join(' - ');

            // Calculate job block height for "keep together" logic
            let jobBlockHeight = bodyLineHeight * 2; // Company line + title
            if (job.role_context) jobBlockHeight += styles.spacing.jobMetaSpacing;

            job.accomplishments.forEach(acc => {
                const lines = doc.splitTextToSize(acc.description || '', contentWidth - bulletIndent);
                jobBlockHeight += Math.max(lines.length, 1) * bodyLineHeight;
            });
            jobBlockHeight += styles.spacing.jobSpacing;

            checkPageBreak(jobBlockHeight);

            setBodyFont('bold');
            if (companyLine) {
                doc.text(companyLine, styles.margin, cursorY);
            }
            if (dateRange) {
                doc.text(dateRange, pageWidth - styles.margin, cursorY, { align: 'right' });
            }
            addSpacing(bodyLineHeight);

            if (job.job_title) {
                setBodyFont('italic');
                doc.text(job.job_title, styles.margin, cursorY);
                addSpacing(styles.spacing.jobMetaSpacing);
            }

            if (job.role_context) {
                setBodyFont('italic');
                const contextLines = doc.splitTextToSize(job.role_context, contentWidth);
                doc.text(contextLines, styles.margin, cursorY);
                addSpacing(contextLines.length * bodyLineHeight + 6); // Extra gap before bullets
            }

            setBodyFont();

            if (job.accomplishments && job.accomplishments.length > 0) {
                job.accomplishments.forEach(acc => {
                    const description = acc.description?.trim();
                    if (!description) return;
                    const lines = doc.splitTextToSize(description, contentWidth - bulletIndent);
                    const blockHeight = Math.max(lines.length, 1) * bodyLineHeight;
                    // No need for checkPageBreak here because we checked the whole job block
                    doc.text('•', styles.margin + bulletMarkerOffset, cursorY);
                    doc.text(lines, styles.margin + bulletIndent, cursorY);
                    addSpacing(blockHeight);
                });
            }

            setBodyFont();

            if (index < work_experience.length - 1) {
                addSpacing(styles.spacing.jobSpacing);
            }
        });
    }

    const hasEducation = education.some(edu => edu.school || edu.degree || (edu.major && edu.major.length > 0));
    if (hasEducation) {
        drawSectionHeading('Education');

        education.forEach(edu => {
            const degreeText = [edu.degree, (edu.major || []).filter(Boolean).join(', ')].filter(Boolean).join(' in ');
            const schoolLine = [edu.school, edu.location].filter(Boolean).join(', ');
            const topHeight = degreeText ? bodyLineHeight : 0;
            const bottomHeight = schoolLine ? bodyLineHeight : 0;
            checkPageBreak(topHeight + bottomHeight || bodyLineHeight);

            if (degreeText) {
                setBodyFont('bold');
                doc.text(degreeText || '', styles.margin, cursorY);
                addSpacing(bodyLineHeight);
            }

            if (schoolLine) {
                setBodyFont('italic');
                doc.text(schoolLine, styles.margin, cursorY);
                addSpacing(bodyLineHeight);
            }

            setBodyFont();
        });
    }

    if (certifications && certifications.length > 0) {
        drawSectionHeading('Certifications');

        certifications.forEach(cert => {
            const certText = `${cert.name}${cert.organization ? ` - ${cert.organization}` : ''}`;
            const dateText = cert.issued_date || '';

            checkPageBreak(bodyLineHeight);

            setBodyFont('bold');
            doc.text(certText, styles.margin, cursorY);

            if (dateText) {
                setBodyFont('normal');
                doc.text(dateText, pageWidth - styles.margin, cursorY, { align: 'right' });
            }

            addSpacing(bodyLineHeight + 2);
            setBodyFont();
        });
    }

    if (skills.length > 0) {
        drawSectionHeading('Skills');

        skills.forEach(skillGroup => {
            const heading = skillGroup.heading ? `${skillGroup.heading}: ` : '';
            const text = heading + (skillGroup.items || []).join(', ');
            const lines = doc.splitTextToSize(text, contentWidth);
            const blockHeight = Math.max(lines.length, 1) * bodyLineHeight;

            checkPageBreak(blockHeight);

            if (skillGroup.heading) {
                setBodyFont('bold');
                doc.text(`${skillGroup.heading}: `, styles.margin, cursorY);
                const headingWidth = doc.getTextWidth(`${skillGroup.heading}: `);
                setBodyFont('normal');
                const remainingText = (skillGroup.items || []).join(', ');
                const wrappedRemaining = doc.splitTextToSize(remainingText, contentWidth - headingWidth);
                doc.text(wrappedRemaining, styles.margin + headingWidth, cursorY);
                addSpacing(blockHeight + 4);
            } else {
                setBodyFont('normal');
                doc.text(lines, styles.margin, cursorY);
                addSpacing(blockHeight + 4);
            }
        });
    }

    const filename = `${header.first_name || 'Resume'} ${header.last_name || ''} - ${header.job_title || 'Role'} - ${companyName}.pdf`;
    doc.save(filename);
};
const normalizeDateField = (value: any): DateInfo => {
    if (!value) {
        return { month: 0, year: 0 };
    }

    // Already in expected shape
    if (typeof value === 'object' && typeof value.month === 'number' && typeof value.year === 'number') {
        return {
            month: value.month || 0,
            year: value.year || 0,
        };
    }

    if (typeof value === 'string') {
        // Expecting formats like YYYY-MM or YYYY
        const trimmed = value.trim();
        const [yearPart, monthPart] = trimmed.split('-');
        const year = parseInt(yearPart, 10);
        const month = monthPart ? parseInt(monthPart, 10) : 0;
        if (!Number.isNaN(year)) {
            if (!Number.isNaN(month) && month >= 1 && month <= 12) {
                return { year, month };
            }
            return { year, month: 0 };
        }
    }

    return { month: 0, year: 0 };
};
