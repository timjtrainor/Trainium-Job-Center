import React, { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { HashRouter, Routes, Route, useNavigate, useParams, useSearchParams, useLocation } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import { AppView, NewAppStep, Resume, JobApplication, BaseResume, Status, Company, CompanyInfoResult, KeywordsResult, GuidanceResult, Prompt, CompanyPayload, JobApplicationPayload, BaseResumePayload, SkillOptions, ExtractedInitialDetails, Contact, ContactPayload, ApplicationQuestion, WorkExperience, Interview, InterviewPayload, InterviewPrep, MessagePayload, Message, LinkedInPost, LinkedInPostPayload, PromptContext, JobProblemAnalysisResult, UserProfile, StrategicNarrative, StrategicNarrativePayload, UserProfilePayload, LinkedInEngagement, PostResponse, PostResponsePayload, LinkedInEngagementPayload, StandardJobRole, StandardJobRolePayload, ResumeTailoringData, PostSubmissionPlan, InfoField, ResumeHeader, ScoutedOpportunity, Offer, OfferPayload, NinetyDayPlan, Sprint, BragBankEntry, SkillTrend, SkillTrendPayload, BragBankEntryPayload, CreateSprintPayload, SprintAction, AiSprintPlan, AiSprintAction, KeywordDetail, SprintActionPayload, SkillSection, ConsultativeClosePlan, StrategicHypothesisDraft, PostInterviewDebrief, ImpactStory, ApplicationDetailTab, ResumeTemplate, BaseResumePayload as ResumePayload } from './types';
import * as apiService from './services/apiService';
import * as geminiService from './services/geminiService';
import { PROMPTS } from './promptsData';
import { ensureUniqueAchievementIds } from './utils/resume';

import { ToastProvider, useToast } from './hooks/useToast';

import { SideNav } from './components/SideNav';
import { DashboardView } from './components/DashboardView';
import { ApplicationsView } from './components/ApplicationsView';
import { PositioningHub } from './components/PositioningHub';
import { EngagementHub } from './components/EngagementHub';
import { CompanyDetailView } from './components/CompanyDetailView';
import { ApplicationDetailView } from './components/ApplicationDetailView';
import { ResumeEditorView } from './components/ResumeEditorView';
import { InterviewStrategyStudio } from './components/InterviewStrategyStudio';
import { PostInterviewDebriefStudio } from './components/PostInterviewDebriefStudio';
import { BragDocumentView } from './components/BragDocumentView';
import { InitialInputStep } from './components/InitialInputStep';
import { JobDetailsStep } from './components/JobDetailsStep';
import { CompanyConfirmationStep } from './components/CompanyConfirmationStep';
import { ProblemAnalysisStep } from './components/ProblemAnalysisStep';
import { SelectResumeStep } from './components/ResumeInputStep';
import { TailorResumeStep } from './components/TailorResumeStep';
import { DownloadResumeStep } from './components/DownloadResumeStep';
import { AnswerQuestionsStep } from './components/AnswerQuestionsStep';
import { PostSubmitPlan } from './components/PostSubmitPlan';
import { ContactModal } from './components/ContactModal';
import { CreateCompanyModal } from './components/CreateCompanyModal';
import { MyProfileModal } from './components/MyProfileModal';
import { DebugModal } from './components/DebugModal';
import { JobDetailsModal, UpdateJdModal } from './components/JobDetailsModal';
import { GuidanceModal } from './components/GuidanceModal';
import { OfferModal } from './components/OfferModal';
import { NinetyDayPlanModal } from './components/NinetyDayPlanModal';
import { SprintModal } from './components/SprintModal';
import { LoadingSpinner } from './components/IconComponents';
import { InterviewStudioView } from './components/InterviewStudioView';
import { InterviewCopilotView } from './components/InterviewCopilotView';
import { PromptEditorView } from './components/PromptEditorView';
import { ScheduleManagementView } from './components/ScheduleManagementView';
import { StepTracker } from './components/StepTracker';
import { CraftMessageStep } from './components/CraftMessageStep';
import { ChromaUploadView } from './components/ChromaUploadView';


type JobDetailsPayload = {
  companyName: string;
  isRecruitingFirm: boolean;
  jobTitle: string;
  jobLink: string;
  salary: string;
  location: string;
  remoteStatus: 'Remote' | 'Hybrid' | 'On-site' | '';
  jobDescription: string;
}

const AppContent = () => {
    // --- Core App State ---
    const [isAppLoading, setIsAppLoading] = useState(true);
    const { addToast } = useToast();
    const navigate = useNavigate();
    const location = useLocation();

    // --- Data State ---
    const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
    const [strategicNarratives, setStrategicNarratives] = useState<StrategicNarrative[]>([]);
    const [activeNarrativeId, setActiveNarrativeId] = useState<string | null>(null);
    const [applications, setApplications] = useState<JobApplication[]>([]);
    const [companies, setCompanies] = useState<Company[]>([]);
    const [statuses, setStatuses] = useState<Status[]>([]);
    const [baseResumes, setBaseResumes] = useState<BaseResume[]>([]);
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [messages, setMessages] = useState<Message[]>([]);
    const [linkedInPosts, setLinkedInPosts] = useState<LinkedInPost[]>([]);
    const [engagements, setEngagements] = useState<LinkedInEngagement[]>([]);
    const [postResponses, setPostResponses] = useState<PostResponse[]>([]);
    const [standardRoles, setStandardRoles] = useState<StandardJobRole[]>([]);
    const [offers, setOffers] = useState<Offer[]>([]);
    const [bragBankItems, setBragBankItems] = useState<BragBankEntry[]>([]);
    const [skillTrends, setSkillTrends] = useState<SkillTrend[]>([]);
    const [sprint, setSprint] = useState<Sprint | null>(null);

    // --- New Application Flow State ---
    const [newAppLoadingState, setNewAppLoadingState] = useState<'idle' | 'extracting' | 'analyzing' | 'keywords' | 'tailoring' | 'saving' | 'planning'>('idle');
    const [newAppStep, setNewAppStep] = useState<NewAppStep>(NewAppStep.INITIAL_INPUT);
    const [currentApplicationId, setCurrentApplicationId] = useState<string | null>(null);
    const [isMessageOnlyApp, setIsMessageOnlyApp] = useState(false);
    const [jobDetails, setJobDetails] = useState({
        companyName: '',
        jobTitle: '',
        jobDescription: '',
        jobLink: '',
        salary: '',
        location: '',
        remoteStatus: '' as 'Remote' | 'Hybrid' | 'On-site' | '',
        isRecruitingFirm: false,
        mission: '',
        values: '',
    });
    const [jobUrlSources, setJobUrlSources] = useState<any[]>([]);
    const [jobProblemAnalysisResult, setJobProblemAnalysisResult] = useState<JobProblemAnalysisResult | null>(null);
    const [strategicFitScore, setStrategicFitScore] = useState<number | null>(null);
    const [assumedRequirements, setAssumedRequirements] = useState<string[]>([]);
    const [keywords, setKeywords] = useState<KeywordsResult | null>(null);
    const [guidance, setGuidance] = useState<GuidanceResult | null>(null);
    const [baseResume, setBaseResume] = useState<Resume | null>(null);
    const [finalResume, setFinalResume] = useState<Resume | null>(null);
    const [applicationMessageDrafts, setApplicationMessageDrafts] = useState<string[]>([]);
    const [finalApplicationMessage, setFinalApplicationMessage] = useState<string>('');
    const [summaryParagraphOptions, setSummaryParagraphOptions] = useState<string[]>([]);
    const [allSkillOptions, setAllSkillOptions] = useState<string[]>([]);
    const [missingKeywords, setMissingKeywords] = useState<KeywordDetail[]>([]);
    const [resumeAlignmentScore, setResumeAlignmentScore] = useState<number | null>(null);
    const [applicationQuestions, setApplicationQuestions] = useState<ApplicationQuestion[]>([]);
    const [postSubmissionPlan, setPostSubmissionPlan] = useState<PostSubmissionPlan | null>(null);
    
    // --- UI/Modal State ---
    const [isReanalyzing, setIsReanalyzing] = useState(false);
    const [isContactModalOpen, setIsContactModalOpen] = useState(false);
    const [selectedContact, setSelectedContact] = useState<Partial<Contact> | null>(null);
    const [isCompanyModalOpen, setIsCompanyModalOpen] = useState(false);
    const [initialCompanyData, setInitialCompanyData] = useState<Partial<CompanyPayload> | null>(null);
    const [isCompanyModalForNewApp, setIsCompanyModalForNewApp] = useState(false);
    const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
    const [isJdModalOpen, setIsJdModalOpen] = useState(false);
    const [isGuidanceModalOpen, setIsGuidanceModalOpen] = useState(false);
    const [isUpdateJdModalOpen, setIsUpdateJdModalOpen] = useState(false);
    const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
    const [selectedOffer, setSelectedOffer] = useState<Partial<Offer> | null>(null);
    const [is90DayPlanModalOpen, setIs90DayPlanModalOpen] = useState(false);
    const [isSprintModalOpen, setIsSprintModalOpen] = useState(false);
    const [selectedInterviewForStrategy, setSelectedInterviewForStrategy] = useState<Interview | null>(null);
    const [strategicHypothesisDraft, setStrategicHypothesisDraft] = useState<StrategicHypothesisDraft | null>(null);
    const [selectedInterviewForCopilot, setSelectedInterviewForCopilot] = useState<Interview | null>(null);
    const [selectedInterviewForDebrief, setSelectedInterviewForDebrief] = useState<Interview | null>(null);
    const [initialAppForStudio, setInitialAppForStudio] = useState<JobApplication | null>(null);
    const [isGeneratingDebrief, setIsGeneratingDebrief] = useState(false);

    // --- AI & Debug State ---
    const [isDebugMode, setIsDebugMode] = useState(false);
    const [modelName, setModelName] = useState('gemini-2.5-flash');
    const [debugModalState, setDebugModalState] = useState<{ isOpen: boolean; stage: 'request' | 'response'; prompt: string; response: string | null; resolve?: (value: unknown) => void }>({ isOpen: false, stage: 'request', prompt: '', response: null });
    
    // --- Computed State ---
    const activeNarrative = useMemo(() => strategicNarratives.find(n => n.narrative_id === activeNarrativeId), [strategicNarratives, activeNarrativeId]);

    const handleError = (err: unknown, messagePrefix: string) => {
        const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred.';
        addToast(`${messagePrefix}: ${errorMessage}`, 'error');
        console.error(err);
    };
    
    // --- Data Fetching ---
    const fetchInitialData = useCallback(async () => {
        setIsAppLoading(true);
        try {
            const [
                profile, narratives, apps, comps, stats, resumes, conts, msgs, posts, engs, postRes, roles, offers, bragItems, trends, activeSprint
            ] = await Promise.all([
                apiService.getUserProfile(),
                apiService.getStrategicNarratives(),
                apiService.getApplications(),
                apiService.getCompanies(),
                apiService.getStatuses(),
                apiService.getBaseResumes(),
                apiService.getContacts(),
                apiService.getAllMessages(),
                apiService.getLinkedInPosts(),
                apiService.getLinkedInEngagements(),
                apiService.getPostResponses(),
                apiService.getStandardJobRoles(),
                apiService.getOffers(),
                apiService.getBragBankEntries(),
                apiService.getSkillTrends(),
                apiService.getActiveSprint(),
            ]);

            setUserProfile(profile);
            setStrategicNarratives(narratives);
            setActiveNarrativeId(narratives[0]?.narrative_id || null);
            setApplications(apps);
            setCompanies(comps);
            setStatuses(stats);
            setBaseResumes(resumes);
            setContacts(conts);
            setMessages(msgs);
            setLinkedInPosts(posts);
            setEngagements(engs);
            setPostResponses(postRes);
            setStandardRoles(roles);
            setOffers(offers);
            setBragBankItems(bragItems);
            setSkillTrends(trends);
            setSprint(activeSprint);

        } catch (err) {
            handleError(err, 'Failed to load initial data');
        } finally {
            setIsAppLoading(false);
        }
    }, [addToast]);

    useEffect(() => {
        fetchInitialData();
    }, [fetchInitialData]);

    const handleNavigateToInterviewStudio = (app: JobApplication) => {
        setInitialAppForStudio(app);
        navigate('/interview-studio');
    };
    
    // --- New App Flow Handlers ---
    
    const handleStartNewApplication = () => {
        resetNewAppFlow();
        navigate('/new-application');
    };
    
    const handleStepClick = (step: NewAppStep) => {
        // This simple implementation allows navigating back to completed steps.
        // The StepTracker component's own logic prevents jumping forward.
        setNewAppStep(step);
    };

    const resetNewAppFlow = () => {
        setNewAppStep(NewAppStep.INITIAL_INPUT);
        setCurrentApplicationId(null);
        setJobDetails({ companyName: '', jobTitle: '', jobDescription: '', jobLink: '', salary: '', location: '', remoteStatus: '', isRecruitingFirm: false, mission: '', values: '' });
        setJobUrlSources([]);
        setJobProblemAnalysisResult(null);
        setStrategicFitScore(null);
        setAssumedRequirements([]);
        setKeywords(null);
        setGuidance(null);
        setBaseResume(null);
        setFinalResume(null);
        setSummaryParagraphOptions([]);
        setAllSkillOptions([]);
        setMissingKeywords([]);
        setResumeAlignmentScore(null);
        setApplicationQuestions([]);
        setPostSubmissionPlan(null);
        setIsMessageOnlyApp(false);
        setApplicationMessageDrafts([]);
        setFinalApplicationMessage('');
    };

    const handleInitialSubmit = async () => {
        setNewAppLoadingState('extracting');
        try {
            const prompt = PROMPTS.find(p => p.id === 'EXTRACT_DETAILS_FROM_PASTE');
            if (!prompt) throw new Error("Extraction prompt not found.");

            const context = { JOB_DESCRIPTION: jobDetails.jobDescription };
            const result = await geminiService.extractInitialDetailsFromPaste(context, prompt.content);

            // Update state with AI extracted details, preserving original link
            setJobDetails(prev => ({
                ...prev,
                ...result,
                jobLink: prev.jobLink,
            }));
            setNewAppStep(NewAppStep.JOB_DETAILS);
        } catch (err) {
            handleError(err, 'Failed to extract details');
        } finally {
            setNewAppLoadingState('idle');
        }
    };

    const handleJobDetailsSubmit = (payload: JobDetailsPayload & { narrativeId: string }) => {
        const { narrativeId, ...jobDetailsPayload } = payload;
        setJobDetails(prev => ({ ...prev, ...jobDetailsPayload }));
        setActiveNarrativeId(narrativeId);
        setNewAppStep(NewAppStep.COMPANY_CONFIRMATION);
    };
    
    const handleCompanySelectionAndAnalyze = async (companyId: string) => {
        setNewAppLoadingState('analyzing');
        try {
            const jobLoadedStatusId = statuses.find(s => s.status_name === 'Step-1: Job loaded')?.status_id;
            const payload: JobApplicationPayload = {
                company_id: companyId,
                job_title: jobDetails.jobTitle,
                job_description: jobDetails.jobDescription,
                job_link: jobDetails.jobLink,
                salary: jobDetails.salary,
                location: jobDetails.location,
                remote_status: jobDetails.remoteStatus as any,
                date_applied: new Date().toISOString().split('T')[0],
                narrative_id: activeNarrativeId || undefined,
                status_id: jobLoadedStatusId,
            };

            let app: JobApplication;
            if (currentApplicationId) {
                app = await apiService.updateApplication(currentApplicationId, payload);
            } else {
                app = await apiService.createApplication(payload);
            }
            
            setCurrentApplicationId(app.job_application_id);
            setApplications(prev => {
                const existing = prev.find(p => p.job_application_id === app.job_application_id);
                if (existing) {
                    return prev.map(p => p.job_application_id === app.job_application_id ? app : p);
                }
                return [...prev, app];
            });

            setNewAppStep(NewAppStep.AI_PROBLEM_ANALYSIS);
            await handleAnalyzeJob(app);

        } catch (err) {
            handleError(err, 'Failed to save application or start analysis');
            setNewAppStep(NewAppStep.COMPANY_CONFIRMATION); // Go back on error
        } finally {
            setNewAppLoadingState('idle');
        }
    };
    
    const handleAnalyzeJob = async (appToAnalyze: JobApplication) => {
        try {
            const analysisPrompt = PROMPTS.find(p => p.id === 'INITIAL_JOB_ANALYSIS');
            if (!analysisPrompt || !activeNarrative) throw new Error("Analysis prompt or active narrative not found.");

            const context = {
                NORTH_STAR: activeNarrative.positioning_statement,
                MASTERY: activeNarrative.signature_capability,
                DESIRED_TITLE: activeNarrative.desired_title,
                JOB_TITLE: appToAnalyze.job_title,
                JOB_DESCRIPTION: appToAnalyze.job_description,
                STANDARD_ROLES_JSON: JSON.stringify(standardRoles.filter(r => r.narrative_id === activeNarrativeId))
            };
            const result = await geminiService.performInitialJobAnalysis(context, analysisPrompt.content);

            const job_problem_analysis = result.job_problem_analysis || null;
            const strategic_fit_score = result.strategic_fit_score || null;
            const assumed_requirements = result.assumed_requirements || [];

            setJobProblemAnalysisResult(job_problem_analysis);
            setStrategicFitScore(strategic_fit_score);
            setAssumedRequirements(assumed_requirements);

            const payload = { 
                job_problem_analysis_result: job_problem_analysis,
                strategic_fit_score: strategic_fit_score === null ? null : Math.round(strategic_fit_score),
                assumed_requirements: assumed_requirements,
            };
            await handleUpdateApplication(appToAnalyze.job_application_id, payload);

        } catch (err) {
            handleError(err, 'Failed job analysis');
        }
    };
    
    const handleConfirmFit = async (isInterested: boolean) => {
        if (!currentApplicationId) return;
        if (!isInterested) {
            await handleUpdateApplication(currentApplicationId, { status_id: statuses.find(s => s.status_name === 'Bad Fit')?.status_id });
            navigate('/applications');
            return;
        }
        
        setNewAppLoadingState('keywords');
        try {
            const keywordsPrompt = PROMPTS.find(p => p.id === 'GENERATE_KEYWORDS_AND_GUIDANCE');
            if (!keywordsPrompt || !jobProblemAnalysisResult) throw new Error("Keywords prompt or analysis data missing.");

            const context = {
                JOB_DESCRIPTION: jobDetails.jobDescription,
                AI_SUMMARY: jobProblemAnalysisResult.core_problem_analysis.core_problem
            };
            const result = await geminiService.generateKeywordsAndGuidance(context, keywordsPrompt.content);

            const keywordsResult = result.keywords || null;
            const guidanceResult = result.guidance || null;
            const approvedStatusId = statuses.find(s => s.status_name === 'Step-2: Approved by Applicant')?.status_id;

            setKeywords(keywordsResult);
            setGuidance(guidanceResult);
            await handleUpdateApplication(currentApplicationId, { 
                keywords: keywordsResult, 
                guidance: guidanceResult,
                status_id: approvedStatusId,
            });
            setNewAppStep(NewAppStep.RESUME_SELECT);
        } catch (err) {
            handleError(err, 'Failed to get keywords/guidance');
        } finally {
            setNewAppLoadingState('idle');
        }
    };

    const handleResumeSelect = async (selectedResume: Resume) => {
        setNewAppLoadingState('tailoring');
        const sanitizedResume = ensureUniqueAchievementIds(selectedResume);
        setBaseResume(sanitizedResume);

        if (isMessageOnlyApp) {
             try {
                const prompt = PROMPTS.find(p => p.id === 'GENERATE_APPLICATION_MESSAGE');
                if (!prompt || !jobProblemAnalysisResult || !activeNarrative) throw new Error("Message generation prompt or context missing.");
                
                const context = {
                    COMPANY_NAME: jobDetails.companyName,
                    JOB_TITLE: jobDetails.jobTitle,
                    CORE_PROBLEM_ANALYSIS: jobProblemAnalysisResult.core_problem_analysis.core_problem,
                    KEYWORDS_STRING: (keywords?.hard_keywords || []).map(k => k.keyword).join(', '),
                    POSITIONING_STATEMENT: activeNarrative.positioning_statement,
                    MASTERY: activeNarrative.signature_capability,
                    IMPACT_STORY: activeNarrative.impact_story_body,
                };

                const drafts = await geminiService.generateApplicationMessage(context, prompt.content);
                setApplicationMessageDrafts(drafts);
                setFinalApplicationMessage(drafts[0] || '');
                setNewAppStep(NewAppStep.CRAFT_MESSAGE);
             } catch (err) {
                handleError(err, 'Failed to generate application message drafts');
             } finally {
                setNewAppLoadingState('idle');
             }
        } else {
            try {
                const prompt = PROMPTS.find(p => p.id === 'GENERATE_RESUME_TAILORING_DATA');
                if (!prompt || !jobProblemAnalysisResult || !activeNarrative) throw new Error("Resume tailoring prompt or context missing.");
                
                  const context: PromptContext = {
                      JOB_DESCRIPTION: jobDetails.jobDescription,
                      CORE_PROBLEM_ANALYSIS: JSON.stringify(jobProblemAnalysisResult.core_problem_analysis),
                      KEY_SUCCESS_METRICS: jobProblemAnalysisResult.key_success_metrics.join(', '),
                      FULL_RESUME_JSON: JSON.stringify(sanitizedResume),
                      RESUME_SUMMARY: sanitizedResume.summary.paragraph,
                      POSITIONING_STATEMENT: activeNarrative.positioning_statement,
                      MASTERY: activeNarrative.signature_capability,
                      JOB_CONTEXT_JSON: JSON.stringify({ title: jobDetails.jobTitle, company: jobDetails.companyName, keywords }),
                      MISSION: jobDetails.mission || '',
                      VALUES: jobDetails.values || '',
                  };

                const result = await geminiService.generateResumeTailoringData(context, prompt.content);
                
                setKeywords(result.keywords || null);
                setGuidance(result.guidance || null);
                
                  const uniqueSummaries = new Set([sanitizedResume.summary.paragraph, ...(result.summary_suggestions || [])]);
                setSummaryParagraphOptions(Array.from(uniqueSummaries));
                
                setAllSkillOptions(result.comprehensive_skills || []);
                setMissingKeywords(result.missing_keywords || []);
                setResumeAlignmentScore(result.initial_alignment_score || null);

                  const tailoredResume: Resume = ensureUniqueAchievementIds({
                      ...sanitizedResume,
                      summary: { paragraph: sanitizedResume.summary.paragraph, bullets: [] },
                      skills: [{ heading: 'Core Competencies', items: result.ai_selected_skills || [] }],
                      work_experience: (result.processed_work_experience || []).map((exp, expIndex) => ({
                          ...sanitizedResume.work_experience[expIndex],
                          accomplishments: (exp.accomplishments || []).map((acc, accIndex) => ({
                              ...(sanitizedResume.work_experience[expIndex].accomplishments[accIndex] || { achievement_id: uuidv4(), description: '', always_include: false, order_index: 0 }),
                              description: acc.description,
                              keyword_suggestions: acc.keyword_suggestions,
                              relevance_score: acc.relevance_score,
                              original_score: acc.original_score,
                          }))
                      }))
                  });
                  setFinalResume(tailoredResume);
                setNewAppStep(NewAppStep.TAILOR_RESUME);

            } catch (err) {
                handleError(err, 'Failed to tailor resume');
            } finally {
                setNewAppLoadingState('idle');
            }
        }
    };
    
    const handleRecalculateScore = async () => {
        if (!finalResume || !jobProblemAnalysisResult) return;
        setNewAppLoadingState('saving');
        try {
            const prompt = PROMPTS.find(p => p.id === 'SCORE_RESUME_ALIGNMENT');
            if (!prompt) throw new Error("Score resume prompt not found.");
            
            const context: PromptContext = {
                FULL_RESUME_JSON: JSON.stringify(finalResume),
                JOB_DESCRIPTION: jobDetails.jobDescription,
                CORE_PROBLEM_ANALYSIS: JSON.stringify(jobProblemAnalysisResult.core_problem_analysis),
            };
            const result = await geminiService.scoreResumeAlignment(context, prompt.content);
            setResumeAlignmentScore(result.alignment_score);
            addToast('Score recalculated!', 'success');
        } catch (err) {
            handleError(err, 'Failed to recalculate score');
        } finally {
            setNewAppLoadingState('idle');
        }
    };
    
    const handleSaveTailoredResume = async () => {
        if (!currentApplicationId || !finalResume) return;
        setNewAppLoadingState('saving');
    
        const resumeToSave = { ...finalResume };
        resumeToSave.work_experience = resumeToSave.work_experience.map(job => {
            const visibleAccomplishments = (job.accomplishments || []).filter(acc => {
                // This logic is simplified; in a real app, we'd check against a visibility flag
                // For now, we assume all are visible
                return true; 
            });
            return { ...job, accomplishments: visibleAccomplishments };
        });
    
        try {
            const resumeCreatedStatusId = statuses.find(s => s.status_name === 'Step-3: Resume created')?.status_id;
            await handleUpdateApplication(currentApplicationId, { 
                tailored_resume_json: resumeToSave, 
                resume_summary: resumeToSave.summary.paragraph, 
                resume_summary_bullets: JSON.stringify(resumeToSave.summary.bullets),
                status_id: resumeCreatedStatusId,
            });
            setFinalResume(resumeToSave);
            setNewAppStep(NewAppStep.DOWNLOAD_RESUME);
        } catch (err) {
            handleError(err, 'Failed to save resume');
        } finally {
            setNewAppLoadingState('idle');
        }
    };

    const handleSaveMessage = async () => {
        if (!currentApplicationId || !finalApplicationMessage) return;
        setNewAppLoadingState('saving');
        try {
            const messageCreatedStatusId = statuses.find(s => s.status_name === 'Step-3: Message created')?.status_id;
            await handleUpdateApplication(currentApplicationId, { 
                application_message: finalApplicationMessage,
                status_id: messageCreatedStatusId
            });
            // Here, we can decide if we want to ask supplemental questions or go to plan.
            // For now, let's go straight to the plan.
             await handleSaveAnswersAndGeneratePlan();
        } catch (err) {
            handleError(err, 'Failed to save application message');
        } finally {
            setNewAppLoadingState('idle');
        }
    };
    
    const handleSaveAnswersAndGeneratePlan = async () => {
        if (!currentApplicationId) return;
        setNewAppLoadingState('planning');
        try {
            await handleUpdateApplication(currentApplicationId, { application_questions: applicationQuestions });

            const prompt = PROMPTS.find(p => p.id === 'GENERATE_POST_SUBMISSION_PLAN');
            const app = applications.find(a => a.job_application_id === currentApplicationId);
            if (!prompt || !app || !activeNarrative) throw new Error("Missing context for plan generation.");

            const context = {
                COMPANY_NAME: companies.find(c => c.company_id === app.company_id)?.company_name || '',
                JOB_TITLE: app.job_title,
                AI_SUMMARY: app.job_problem_analysis_result?.core_problem_analysis.core_problem,
                NORTH_STAR: activeNarrative.positioning_statement,
                MASTERY: activeNarrative.signature_capability,
                REFERRAL_TARGET: app.referral_target_suggestion || 'Hiring Manager or Peer',
            };

            const plan = await geminiService.generatePostSubmissionPlan(context, prompt.content);
            setPostSubmissionPlan(plan);

            await handleUpdateApplication(currentApplicationId, {
                why_this_job: plan?.why_this_job || '',
                next_steps_plan: plan?.next_steps_plan || [],
            });
            
            setNewAppStep(NewAppStep.POST_SUBMIT_PLAN);
        } catch (err) {
            handleError(err, 'Failed to generate post-submission plan');
        } finally {
            setNewAppLoadingState('idle');
        }
    };

    const handleFinishApplication = async () => {
        if (currentApplicationId) {
            const appliedStatusId = statuses.find(s => s.status_name === 'Step-4: Applied')?.status_id;
            if (appliedStatusId) {
                await handleUpdateApplication(currentApplicationId, { status_id: appliedStatusId });
            }
        }
        navigate('/applications');
    };
    
    // --- Generic Handlers ---

    const handleUpdateApplication = async (appId: string, payload: JobApplicationPayload): Promise<JobApplication> => {
        try {
            const updatedApp = await apiService.updateApplication(appId, payload);
            setApplications(prev => prev.map(a => a.job_application_id === appId ? updatedApp : a));
            return updatedApp;
        } catch (err) {
            handleError(err, 'Failed to update application');
            throw err;
        }
    };

    const handleDeleteApplication = async (appId: string) => {
        try {
            await apiService.deleteApplication(appId);
            setApplications(prev => prev.filter(a => a.job_application_id !== appId));
            addToast('Application deleted', 'success');
            navigate('/applications');
        } catch (err) {
            handleError(err, 'Failed to delete application');
        }
    };
    
    const handleDeleteResume = async (resumeId: string) => {
        try {
            await apiService.deleteBaseResume(resumeId);
            setBaseResumes(prev => prev.filter(r => r.resume_id !== resumeId));
            addToast('Resume deleted', 'success');
        } catch (err) {
            handleError(err, 'Failed to delete resume');
        }
    };

    const handleCreateCompany = async (payload: CompanyPayload): Promise<Company> => {
        try {
            const newCompany = await apiService.createCompany(payload);
            setCompanies(prev => [...prev, newCompany].sort((a, b) => a.company_name.localeCompare(b.company_name)));
            addToast('Company created successfully!', 'success');
            return newCompany;
        } catch (err) {
            handleError(err, 'Failed to create company');
            throw err;
        }
    };

    const handleCreateCompanyForNewApp = async (payload: CompanyPayload): Promise<Company> => {
        const newCompany = await handleCreateCompany(payload);
        setIsCompanyModalOpen(false);
        setIsCompanyModalForNewApp(false);
        await handleCompanySelectionAndAnalyze(newCompany.company_id);
        return newCompany;
    };

    const handleSaveContact = async (contactData: Partial<Contact>): Promise<Contact> => {
        try {
            let savedContact: Contact;
            if (contactData.contact_id) {
                // Update existing contact
                savedContact = await apiService.updateContact(contactData.contact_id, contactData);
                setContacts(prev => prev.map(c => c.contact_id === savedContact.contact_id ? savedContact : c));
            } else {
                // Create new contact
                savedContact = await apiService.createContact(contactData);
                setContacts(prev => [...prev, savedContact].sort((a, b) => (a.last_name || '').localeCompare(b.last_name || '')));
            }
            
            if (contactData.narrative_ids) {
                await apiService.setContactNarratives(savedContact.contact_id, contactData.narrative_ids);
                savedContact = await apiService.getSingleContact(savedContact.contact_id);
                setContacts(prev => prev.map(c => c.contact_id === savedContact.contact_id ? savedContact : c));
            }

            addToast('Contact saved successfully!', 'success');
            return savedContact;
        } catch (err) {
            handleError(err, 'Failed to save contact');
            throw err;
        }
    };

    const handleCreateMessage = async (messageData: MessagePayload): Promise<void> => {
        try {
            const newMessage = await apiService.createMessage(messageData);
            setMessages(prev => [newMessage, ...prev]);
            if (newMessage.contact_id) {
                setContacts(prev => prev.map(c => 
                    c.contact_id === newMessage.contact_id 
                    ? { ...c, messages: [newMessage, ...(c.messages || [])] } 
                    : c
                ));
            }
            addToast('Message saved!', 'success');
        } catch (err) {
            handleError(err, "Failed to save message");
        }
    };

    const handleDeleteContact = async (contactId: string): Promise<void> => {
        try {
            await apiService.deleteContact(contactId);
            setContacts(prev => prev.filter(c => c.contact_id !== contactId));
            addToast('Contact deleted.', 'success');
        } catch (err) {
            handleError(err, "Failed to delete contact");
        }
    };
    
    const handleSaveNarrative = async (payload: StrategicNarrativePayload, narrativeId: string) => {
        try {
            const savedNarrative = await apiService.saveStrategicNarrative(payload, narrativeId);
            setStrategicNarratives(prev => prev.map(n => n.narrative_id === narrativeId ? savedNarrative : n));
            addToast('Narrative saved!', 'success');
        } catch (err) {
            handleError(err, 'Failed to save narrative');
        }
    };
    
    const handleUpdateNarrative = (updatedNarrative: StrategicNarrative) => {
        setStrategicNarratives(prev => prev.map(n => n.narrative_id === updatedNarrative.narrative_id ? updatedNarrative : n));
    };

    const handleSaveInterview = async (interviewData: InterviewPayload, interviewId?: string) => {
        try {
            const savedInterview = await apiService.saveInterview(interviewData, interviewId);
            const updatedApp = await apiService.getSingleApplication(savedInterview.job_application_id);
            setApplications(prev => prev.map(app => app.job_application_id === updatedApp.job_application_id ? updatedApp : app));
            addToast('Interview saved', 'success');
        } catch (err) {
            handleError(err, 'Failed to save interview');
            throw err;
        }
    };

    const handleUpdatePostResponse = async (commentId: string, payload: PostResponsePayload) => {
        const updatedResponse = await apiService.updatePostResponse(commentId, payload);
        setPostResponses(prev => prev.map(pr => pr.comment_id === commentId ? { ...pr, ...updatedResponse } : pr));
        addToast('Post response updated!', 'success');
    };

    const handleCreatePost = async (payload: LinkedInPostPayload) => {
        try {
            const newPost = await apiService.createLinkedInPost(payload);
            setLinkedInPosts(prev => [newPost, ...prev]);
            addToast('Post saved to history!', 'success');
        } catch(err) {
            handleError(err, 'Failed to save post');
        }
    };

    const handleCreateLinkedInEngagement = async (payload: LinkedInEngagementPayload) => {
        try {
            const contactName = payload.contact_name;
            let contactToLink: Contact | undefined = contacts.find(c => 
                `${c.first_name} ${c.last_name}`.trim().toLowerCase() === contactName.trim().toLowerCase()
            );
    
            // If contact doesn't exist, create it first.
            if (!contactToLink) {
                const [firstName, ...lastNameParts] = contactName.split(' ');
                const lastName = lastNameParts.join(' ');
    
                const newContactPayload: Partial<Contact> = {
                    first_name: firstName,
                    last_name: lastName,
                    job_title: payload.contact_title,
                    linkedin_url: payload.contact_linkedin_url,
                    status: 'Initial Outreach',
                    notes: `Created from engagement on a post.`,
                    date_contacted: new Date().toISOString().split('T')[0],
                };
                
                contactToLink = await handleSaveContact(newContactPayload);
            }
            
            if (!contactToLink) {
                throw new Error("Could not find or create contact to link engagement.");
            }
            
            // Now create the engagement with the contact_id
            const engagementPayload: LinkedInEngagementPayload = {
                ...payload,
                contact_id: contactToLink.contact_id
            };
    
            const newEngagement = await apiService.createLinkedInEngagement(engagementPayload);
            
            setEngagements(prev => [newEngagement, ...prev].sort((a,b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
            
            addToast('Engagement tracked and linked to contact!', 'success');
            
        } catch (err) {
            handleError(err, 'Failed to track engagement');
        }
    };
    
    const handleCreateSynthesizedNarrative = async (payload: StrategicNarrativePayload): Promise<void> => {
        try {
            const newNarrative = await apiService.createNarrative(payload);
            setStrategicNarratives(prev => [...prev, newNarrative]);
            addToast('New narrative created!', 'success');
        } catch (err) {
            handleError(err, 'Failed to create new narrative');
        }
    };

    const handleSaveSkillTrends = async (trends: SkillTrendPayload[]): Promise<void> => {
        try {
            const promises = trends.map(trend => apiService.saveSkillTrend(trend));
            const savedTrends = await Promise.all(promises);

            setSkillTrends(prevTrends => {
                const trendsMap = new Map(prevTrends.map(t => [t.skill_trend_id, t]));
                savedTrends.forEach(st => trendsMap.set(st.skill_trend_id, st));
                return Array.from(trendsMap.values());
            });

            addToast(`${savedTrends.length} skill trend(s) saved.`, 'success');
        } catch (err) {
            handleError(err, 'Failed to save skill trends');
        }
    };

    const handleResumeApplication = (appToResume: JobApplication) => {
        resetNewAppFlow();
    
        setCurrentApplicationId(appToResume.job_application_id);
        setActiveNarrativeId(appToResume.narrative_id);
    
        const company = companies.find(c => c.company_id === appToResume.company_id);
        setJobDetails({
            companyName: company?.company_name || '',
            isRecruitingFirm: company?.is_recruiting_firm || false,
            jobTitle: appToResume.job_title,
            jobDescription: appToResume.job_description,
            jobLink: appToResume.job_link || '',
            salary: appToResume.salary || '',
            location: appToResume.location || '',
            remoteStatus: appToResume.remote_status || '',
            mission: company?.mission?.text || '',
            values: company?.values?.text || '',
        });
    
        setJobProblemAnalysisResult(appToResume.job_problem_analysis_result || null);
        setStrategicFitScore(appToResume.strategic_fit_score || null);
        setAssumedRequirements(appToResume.assumed_requirements || []);
    
        const parsedKeywords = typeof appToResume.keywords === 'string' ? JSON.parse(appToResume.keywords) : appToResume.keywords;
        const parsedGuidance = typeof appToResume.guidance === 'string' ? JSON.parse(appToResume.guidance) : appToResume.guidance;
        setKeywords(parsedKeywords || null);
        setGuidance(parsedGuidance || null);
    
        const wasMessageOnly = !!appToResume.application_message && !appToResume.tailored_resume_json;
        setIsMessageOnlyApp(wasMessageOnly);
        
        setFinalResume(appToResume.tailored_resume_json || null);
        setApplicationQuestions(appToResume.application_questions || []);
        setFinalApplicationMessage(appToResume.application_message || '');
    
        if (appToResume.why_this_job && appToResume.next_steps_plan) {
            setPostSubmissionPlan({
                why_this_job: appToResume.why_this_job,
                next_steps_plan: appToResume.next_steps_plan,
            });
        }
    
        let resumeStep: NewAppStep;
        if (appToResume.why_this_job) {
            resumeStep = NewAppStep.POST_SUBMIT_PLAN;
        } else if (appToResume.application_message) {
            resumeStep = NewAppStep.CRAFT_MESSAGE;
        } else if (appToResume.application_questions && appToResume.application_questions.length > 0) {
            resumeStep = NewAppStep.ANSWER_QUESTIONS;
        } else if (appToResume.tailored_resume_json) {
            resumeStep = NewAppStep.DOWNLOAD_RESUME;
        } else if (appToResume.keywords) {
            resumeStep = NewAppStep.RESUME_SELECT;
        } else if (appToResume.job_problem_analysis_result) {
            resumeStep = NewAppStep.AI_PROBLEM_ANALYSIS;
        } else {
            resumeStep = NewAppStep.AI_PROBLEM_ANALYSIS;
        }
        setNewAppStep(resumeStep);
    
        navigate('/new-application');
    };
    
    const handleReanalyzeApplication = async (appToReanalyze: JobApplication) => {
        setIsReanalyzing(true);
        addToast('Rerunning full AI analysis...', 'info');
        try {
            // Step 1: Re-run Problem Analysis
            const analysisPrompt = PROMPTS.find(p => p.id === 'INITIAL_JOB_ANALYSIS');
            const narrative = strategicNarratives.find(n => n.narrative_id === appToReanalyze.narrative_id);
            if (!analysisPrompt || !narrative) throw new Error("Analysis prompt or narrative not found for re-analysis.");
    
            const analysisContext = {
                NORTH_STAR: narrative.positioning_statement,
                MASTERY: narrative.signature_capability,
                DESIRED_TITLE: narrative.desired_title,
                JOB_TITLE: appToReanalyze.job_title,
                JOB_DESCRIPTION: appToReanalyze.job_description,
                STANDARD_ROLES_JSON: JSON.stringify(standardRoles.filter(r => r.narrative_id === narrative.narrative_id))
            };
            const analysisResult = await geminiService.performInitialJobAnalysis(analysisContext, analysisPrompt.content);
            const coreProblem = analysisResult.job_problem_analysis?.core_problem_analysis?.core_problem;
            if (!coreProblem) {
                throw new Error("Failed to extract core problem from the new analysis.");
            }
    
            // Step 2: Re-run Keywords & Guidance
            const keywordsPrompt = PROMPTS.find(p => p.id === 'GENERATE_KEYWORDS_AND_GUIDANCE');
            if (!keywordsPrompt) throw new Error("Keywords prompt missing.");
    
            const keywordsContext = {
                JOB_DESCRIPTION: appToReanalyze.job_description,
                AI_SUMMARY: coreProblem
            };
            const keywordsResult = await geminiService.generateKeywordsAndGuidance(keywordsContext, keywordsPrompt.content);
    
            // Step 3: Update application with all new data
            const payload: JobApplicationPayload = {
                job_problem_analysis_result: analysisResult.job_problem_analysis,
                strategic_fit_score: analysisResult.strategic_fit_score ? Math.round(analysisResult.strategic_fit_score) : null,
                assumed_requirements: analysisResult.assumed_requirements,
                keywords: keywordsResult.keywords,
                guidance: keywordsResult.guidance,
            };
    
            await handleUpdateApplication(appToReanalyze.job_application_id, payload);
            addToast('AI analysis complete!', 'success');
    
        } catch (err) {
            handleError(err, 'Failed to re-run AI analysis');
        } finally {
            setIsReanalyzing(false);
        }
    };

    const handleGenerateInterviewPrep = async (app: JobApplication, interview: Interview) => {
        const prepPrompt = PROMPTS.find(p => p.id === 'GENERATE_INTERVIEW_PREP');
        if (!prepPrompt) {
            handleError(new Error("Interview prep prompt not found."), 'AI Prep Error');
            return;
        }

        try {
            const interviewerProfiles = (interview.interview_contacts || [])
                .map(ic => contacts.find(c => c.contact_id === ic.contact_id))
                .filter((c): c is Contact => !!c)
                .map(c => ({
                    name: `${c.first_name} ${c.last_name}`,
                    title: c.job_title,
                    profile: c.linkedin_about || ''
                }));
                
            const context = {
                FULL_RESUME_JSON: JSON.stringify(app.tailored_resume_json || {}),
                JOB_DESCRIPTION: app.job_description,
                INTERVIEW_TYPE: interview.interview_type,
                INTERVIEWER_PROFILES_JSON: JSON.stringify(interviewerProfiles)
            };

            const prepData = await geminiService.generateInterviewPrep(context, prepPrompt.content, debugModalState.isOpen ? undefined : undefined);

            await handleSaveInterview({ ai_prep_data: prepData }, interview.interview_id);
            addToast("AI interview prep generated!", 'success');

        } catch (err) {
            handleError(err, 'Failed to generate interview prep');
        }
    };
    
    const handleGenerateRecruiterScreenPrep = async (app: JobApplication, interview: Interview) => {
        const prepPrompt = PROMPTS.find(p => p.id === 'GENERATE_RECRUITER_SCREEN_PREP');
        if (!prepPrompt || !activeNarrative) {
            handleError(new Error("Recruiter prep prompt or active narrative not found."), 'AI Prep Error');
            return;
        }

        try {
            const context = {
                POSITIONING_STATEMENT: activeNarrative.positioning_statement,
                MASTERY: activeNarrative.signature_capability,
                JOB_TITLE: app.job_title,
                CORE_PROBLEM_ANALYSIS: app.job_problem_analysis_result?.core_problem_analysis.core_problem,
                COMPENSATION_EXPECTATION: activeNarrative.compensation_expectation,
            };

            const prepData = await geminiService.generateRecruiterScreenPrep(context, prepPrompt.content, debugModalState.isOpen ? undefined : undefined);

            await handleSaveInterview({ ai_prep_data: prepData }, interview.interview_id);
            addToast("AI quick prep generated!", 'success');

        } catch (err) {
            handleError(err, 'Failed to generate recruiter prep');
        }
    };
    
    const handleGeneratePostInterviewDebrief = async (interview: Interview, notes: { wins: string, fumbles: string, new_intelligence: string }) => {
        setIsGeneratingDebrief(true);
        const debriefPrompt = PROMPTS.find(p => p.id === 'GENERATE_POST_INTERVIEW_COUNTER');
        if (!debriefPrompt || !activeNarrative) {
            handleError(new Error("Debrief prompt or active narrative not found."), 'AI Debrief Error');
            setIsGeneratingDebrief(false);
            return;
        }

        try {
            const interviewerContact = interview.interview_contacts?.[0] ? contacts.find(c => c.contact_id === interview.interview_contacts![0].contact_id) : null;

            const context = {
                INTERVIEWER_FIRST_NAME: interviewerContact?.first_name || 'the interviewer',
                INTERVIEWER_TITLE: interviewerContact?.job_title || 'Interviewer',
                NORTH_STAR: activeNarrative.positioning_statement,
                MASTERY: activeNarrative.signature_capability,
                NEW_INTELLIGENCE: notes.new_intelligence,
                WINS: notes.wins,
                FUMBLES: notes.fumbles,
            };

            const debriefData = await geminiService.generatePostInterviewCounter(context, debriefPrompt.content, debugModalState.isOpen ? undefined : undefined);
            
            await handleSaveInterview({ post_interview_debrief: debriefData }, interview.interview_id);
            addToast("AI interview debrief generated!", 'success');

        } catch (err) {
            handleError(err, 'Failed to generate interview debrief');
        } finally {
            setIsGeneratingDebrief(false);
        }
    };

    const handleGetReframeSuggestion = async (question: string, coreStories: ImpactStory[]): Promise<string> => {
        const prompt = PROMPTS.find(p => p.id === 'GENERATE_QUESTION_REFRAME_SUGGESTION');
        if (!prompt) {
            handleError(new Error("Reframe suggestion prompt not found."), 'AI Studio Error');
            return "";
        }
        
        try {
            const context = {
                INTERVIEW_QUESTION: question,
                CORE_STORIES_JSON: JSON.stringify((coreStories || []).map(s => ({ story_id: s.story_id, story_title: s.story_title, format: s.format })))
            };

            const result = await geminiService.generateQuestionReframeSuggestion(context, prompt.content, debugModalState.isOpen ? undefined : undefined);
            return result.suggestion;

        } catch (err) {
            handleError(err, 'Failed to get reframe suggestion');
            return "";
        }
    };

    const handleDeconstructQuestion = async (question: string): Promise<{ scope: string[], metrics: string[], constraints: string[] }> => {
        const prompt = PROMPTS.find(p => p.id === 'DECONSTRUCT_INTERVIEW_QUESTION');
        if (!prompt) {
            handleError(new Error("Deconstruct question prompt not found."), 'AI Studio Error');
            return { scope: [], metrics: [], constraints: [] };
        }
        
        try {
            const context = {
                INTERVIEW_QUESTION: question,
            };
            const result = await geminiService.deconstructInterviewQuestion(context, prompt.content, debugModalState.isOpen ? undefined : undefined);
            return result;

        } catch (err) {
            handleError(err, 'Failed to deconstruct question');
            return { scope: [], metrics: [], constraints: [] };
        }
    };

    const handleNavigateToDebriefStudio = (interview: Interview) => {
        setSelectedInterviewForDebrief(interview);
        navigate(`/post-interview-debrief/${interview.interview_id}`);
    };

    // --- Component Wrappers for Routing ---
    const ApplicationDetailWrapper = () => {
        const { appId } = useParams();
        const location = useLocation();
        const navigate = useNavigate();
        
        const searchParams = new URLSearchParams(location.search);
        const initialTab = (searchParams.get('tab') as ApplicationDetailTab) || 'overview';

        const handleTabChange = (newTab: ApplicationDetailTab) => {
            navigate({ pathname: location.pathname, search: `?tab=${newTab}` }, { replace: true });
        };

        const app = applications.find(a => a.job_application_id === appId);
        const company = companies.find(c => c.company_id === app?.company_id);
        
        if (!app || !company) return <div className="p-8">Loading application...</div>;
        
        return <ApplicationDetailView 
            application={app} 
            company={company}
            allCompanies={companies}
            contacts={contacts}
            onBack={() => navigate('/applications')}
            onUpdate={(payload) => handleUpdateApplication(app.job_application_id, payload)}
            onDeleteApplication={handleDeleteApplication}
            onResumeApplication={(appToResume) => handleResumeApplication(appToResume)}
            onReanalyze={() => handleReanalyzeApplication(app)}
            isReanalyzing={isReanalyzing}
            prompts={PROMPTS}
            statuses={statuses}
            userProfile={userProfile}
            activeNarrative={activeNarrative}
            onSaveInterview={handleSaveInterview}
            onDeleteInterview={async (id) => { await apiService.deleteInterview(id); fetchInitialData(); }}
            onGenerateInterviewPrep={handleGenerateInterviewPrep}
            onGenerateRecruiterScreenPrep={handleGenerateRecruiterScreenPrep}
            onOpenContactModal={(contact) => { setSelectedContact(contact); setIsContactModalOpen(true); }}
            onOpenOfferModal={(app, offer) => {}}
            onGenerate90DayPlan={(app) => {}}
            onAddQuestionToCommonPrep={(q) => {}}
            onOpenStrategyStudio={(interview) => handleNavigateToInterviewStudio(app)}
            onNavigateToStudio={handleNavigateToInterviewStudio}
            handleLaunchCopilot={(app, interview) => navigate(`/interview-copilot/${interview.interview_id}`)}
            isLoading={isAppLoading}
            onOpenDebriefStudio={handleNavigateToDebriefStudio}
            initialTab={initialTab}
            onTabChange={handleTabChange}
        />;
    };
    
    const CompanyDetailWrapper = () => {
        const { companyId } = useParams();
        const company = companies.find(c => c.company_id === companyId);
        if (!company) return <div className="p-8">Loading company...</div>;
        return <CompanyDetailView
            company={company}
            allCompanies={companies}
            applications={applications}
            messages={messages.filter(m => m.company_id === companyId)}
            contacts={contacts}
            onBack={() => navigate('/engagement')}
            onUpdate={async (payload) => { await apiService.updateCompany(company.company_id, payload); fetchInitialData(); }}
            onViewApplication={(appId) => navigate(`/application/${appId}`)}
            onCreateMessage={handleCreateMessage}
            onOpenCreateCompanyModal={(data) => { setInitialCompanyData(data); setIsCompanyModalOpen(true); }}
            onOpenContactModal={(contact) => { setSelectedContact(contact); setIsContactModalOpen(true); }}
            onResearch={async (details) => { await apiService.updateCompany(details.id, { company_name: details.name, company_url: details.url }); }}
            onDeleteContact={handleDeleteContact}
            prompts={PROMPTS}
            activeNarrative={activeNarrative}
        />;
    };

    const ResumeEditorWrapper = () => {
        const { resumeId } = useParams();
        const resume = baseResumes.find(r => r.resume_id === resumeId);
        if(!resume) return <div className="p-8">Loading Resume...</div>
        return <ResumeEditorView 
            resume={resume}
            activeNarrative={activeNarrative}
            onSave={async (res) => {
                await apiService.saveResumeContent(res.resume_id, res.content as Resume);
                await apiService.updateBaseResume(res.resume_id, { resume_name: res.resume_name });
                fetchInitialData();
            }}
            onCancel={() => navigate('/applications')}
            onAutoSave={async (res) => {}}
            isLoading={isAppLoading}
            prompts={PROMPTS}
            commonKeywords={[]}
            onSetDefault={(id) => handleSaveNarrative({ default_resume_id: id }, activeNarrativeId!)}
        />
    }

    const InterviewCopilotWrapper = () => {
        const { interviewId } = useParams();
        const navigate = useNavigate();
    
        const { app, interview, company } = useMemo(() => {
            if (!applications || !companies) return { app: null, interview: null, company: null };
            for (const app of applications) {
                const interview = app.interviews?.find(i => i.interview_id === interviewId);
                if (interview) {
                    const company = companies.find(c => c.company_id === app.company_id);
                    return { app, interview, company };
                }
            }
            return { app: null, interview: null, company: null };
        }, [applications, interviewId, companies]);
    
        if (isAppLoading || !app || !interview || !activeNarrative || !company) {
            return <div className="flex-1 flex items-center justify-center"><LoadingSpinner /></div>;
        }
    
        return (
            <InterviewCopilotView
                application={app}
                interview={interview}
                company={company}
                activeNarrative={activeNarrative}
                onBack={() => navigate(`/application/${app.job_application_id}?tab=interviews`)}
                onSaveInterview={handleSaveInterview}
                onGenerateInterviewPrep={handleGenerateInterviewPrep}
                onGenerateRecruiterScreenPrep={handleGenerateRecruiterScreenPrep}
            />
        );
    };

    const PostInterviewDebriefWrapper = () => {
        const { interviewId } = useParams();
        const navigate = useNavigate();

        const { app, interview, company } = useMemo(() => {
            if (!applications || !companies) return { app: null, interview: null, company: null };
            for (const app of applications) {
                const interview = app.interviews?.find(i => i.interview_id === interviewId);
                if (interview) {
                    const company = companies.find(c => c.company_id === app.company_id);
                    return { app, interview, company };
                }
            }
            return { app: null, interview: null, company: null };
        }, [applications, interviewId, companies]);

        if (isAppLoading || !app || !interview || !activeNarrative || !company) {
            return <div className="flex-1 flex items-center justify-center"><LoadingSpinner /></div>;
        }

        return (
            <PostInterviewDebriefStudio
                application={app}
                interview={interview}
                company={company}
                activeNarrative={activeNarrative}
                onBack={() => navigate(`/application/${app.job_application_id}?tab=interviews`)}
                onGenerate={handleGeneratePostInterviewDebrief}
                isLoading={isGeneratingDebrief}
            />
        );
    };

    const NewApplicationWrapper = () => (
        <div className="flex flex-col h-full">
             <header className="flex-shrink-0 bg-white dark:bg-slate-800/80 p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                <StepTracker 
                    currentStep={newAppStep}
                    onStepClick={handleStepClick}
                    isMessageOnlyApp={isMessageOnlyApp}
                    progressData={{
                        jobProblemAnalysisResult,
                        keywords,
                        finalResume,
                        applicationQuestions,
                        postSubmissionPlan,
                        applicationMessage: finalApplicationMessage
                    }}
                />
            </header>
            <div className="flex-grow p-6 sm:p-8 overflow-y-auto bg-slate-100 dark:bg-slate-900">
                <div className="max-w-4xl mx-auto bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700">
                    {newAppStep === NewAppStep.INITIAL_INPUT && <InitialInputStep 
                        onNext={handleInitialSubmit} 
                        isLoading={newAppLoadingState === 'extracting'}
                        jobLink={jobDetails.jobLink}
                        onJobLinkChange={(value) => setJobDetails(prev => ({...prev, jobLink: value}))}
                        jobDescription={jobDetails.jobDescription}
                        onJobDescriptionChange={(value) => setJobDetails(prev => ({...prev, jobDescription: value}))}
                        isMessageOnlyApp={isMessageOnlyApp}
                        onIsMessageOnlyChange={setIsMessageOnlyApp}
                    />}
                    {newAppStep === NewAppStep.JOB_DETAILS && <JobDetailsStep onNext={handleJobDetailsSubmit} isLoading={false} initialJobDetails={jobDetails} narratives={strategicNarratives} selectedNarrativeId={activeNarrativeId!} />}
                    {newAppStep === NewAppStep.COMPANY_CONFIRMATION && <CompanyConfirmationStep initialCompanyName={jobDetails.companyName} allCompanies={companies} onConfirm={handleCompanySelectionAndAnalyze} onOpenCreateCompanyModal={() => { setIsCompanyModalForNewApp(true); setInitialCompanyData({ company_name: jobDetails.companyName, company_url: jobDetails.jobLink, is_recruiting_firm: jobDetails.isRecruitingFirm }); setIsCompanyModalOpen(true); }} isLoading={newAppLoadingState === 'analyzing'} />}
                    {newAppStep === NewAppStep.AI_PROBLEM_ANALYSIS && <ProblemAnalysisStep jobProblemAnalysisResult={jobProblemAnalysisResult} strategicFitScore={strategicFitScore} assumedRequirements={assumedRequirements} onConfirm={handleConfirmFit} companyName={jobDetails.companyName} isLoadingAnalysis={!jobProblemAnalysisResult} isConfirming={newAppLoadingState === 'keywords'} />}
                    {newAppStep === NewAppStep.RESUME_SELECT && baseResumes && userProfile && <SelectResumeStep baseResumes={baseResumes} onNext={handleResumeSelect} isLoading={newAppLoadingState === 'tailoring'} prompts={PROMPTS} keywords={keywords} userProfile={userProfile} applicationNarrative={activeNarrative} />}
                    {newAppStep === NewAppStep.TAILOR_RESUME && finalResume && <TailorResumeStep finalResume={finalResume} setFinalResume={setFinalResume} summaryParagraphOptions={summaryParagraphOptions} allSkillOptions={allSkillOptions} keywords={keywords} missingKeywords={missingKeywords} setMissingKeywords={setMissingKeywords} onNext={handleSaveTailoredResume} isLoading={newAppLoadingState === 'saving'} prompts={PROMPTS} userProfile={userProfile} activeNarrative={activeNarrative} jobTitle={jobDetails.jobTitle} companyName={jobDetails.companyName} resumeAlignmentScore={resumeAlignmentScore} onRecalculateScore={handleRecalculateScore} />}
                    {newAppStep === NewAppStep.CRAFT_MESSAGE && <CraftMessageStep drafts={applicationMessageDrafts} onSelectDraft={setFinalApplicationMessage} finalMessage={finalApplicationMessage} setFinalMessage={setFinalApplicationMessage} onNext={handleSaveMessage} isLoading={newAppLoadingState === 'saving'} />}
                    {newAppStep === NewAppStep.DOWNLOAD_RESUME && finalResume && <DownloadResumeStep finalResume={finalResume} companyName={jobDetails.companyName} onNext={() => setNewAppStep(NewAppStep.ANSWER_QUESTIONS)} isLoading={false} />}
                    {newAppStep === NewAppStep.ANSWER_QUESTIONS && <AnswerQuestionsStep questions={applicationQuestions} setQuestions={setApplicationQuestions} onGenerateAllAnswers={async ()=>{}} onSaveApplication={handleSaveAnswersAndGeneratePlan} onBack={() => setNewAppStep(NewAppStep.DOWNLOAD_RESUME)} isLoading={newAppLoadingState === 'planning'} onOpenJobDetailsModal={() => setIsJdModalOpen(true)} onOpenAiAnalysisModal={() => setIsGuidanceModalOpen(true)} />}
                    {newAppStep === NewAppStep.POST_SUBMIT_PLAN && postSubmissionPlan && <PostSubmitPlan summary={postSubmissionPlan.why_this_job} plan={postSubmissionPlan.next_steps_plan} onFinish={handleFinishApplication} sprint={sprint} onAddActions={async ()=>{}} companyName={jobDetails.companyName} />}
                </div>
            </div>
        </div>
    );
    
    return (
        <div className="flex h-screen bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-sans">
             <SideNav 
                narratives={strategicNarratives}
                activeNarrativeId={activeNarrativeId}
                onSetNarrative={setActiveNarrativeId}
                onOpenProfileModal={() => setIsProfileModalOpen(true)}
                onOpenSprintModal={() => setIsSprintModalOpen(true)}
            />
            <main className="flex-1 flex flex-col overflow-hidden">
                {isAppLoading ? (
                     <div className="flex-1 flex items-center justify-center">
                        <LoadingSpinner />
                     </div>
                ) : (
                    <div className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
                        <Routes>
                            <Route path="/" element={<DashboardView applications={applications} contacts={contacts} messages={messages} linkedInPosts={linkedInPosts} engagements={engagements} pendingFollowUps={messages.filter(m => m.follow_up_due_date)} userProfile={userProfile} activeNarrative={activeNarrative || null} strategicNarratives={strategicNarratives} onOpenContactModal={(contact) => { setSelectedContact(contact); setIsContactModalOpen(true); }} onScoutForOpportunities={() => {}} onUpdateContactStatus={(contactId, status) => handleSaveContact({ contact_id: contactId, status })} prompts={PROMPTS} baseResumes={baseResumes} onCreateSynthesizedNarrative={handleCreateSynthesizedNarrative} onSaveSkillTrends={handleSaveSkillTrends} sprint={sprint} skillTrends={skillTrends} companies={companies} weeklyProgress={""} onAddActions={async () => {}} />} />
                            <Route path="/applications" element={<ApplicationsView applications={applications} companies={companies} statuses={statuses} offers={offers} onViewApplication={(appId) => navigate(`/application/${appId}`)} onViewCompany={(companyId) => navigate(`/company/${companyId}`)} onResumeApplication={handleResumeApplication} onAddNew={handleStartNewApplication} onDeleteApplication={handleDeleteApplication} onDeleteOffer={async (id) => { await apiService.deleteOffer(id); fetchInitialData(); }} resumes={baseResumes} userProfile={userProfile} onAddNewResume={() => navigate('/resume/new')} onEditResume={(res) => navigate(`/resume/${res.resume_id}`)} onDeleteResume={handleDeleteResume} onCopyResume={async (res) => {}} onSetDefaultResume={(id) => handleSaveNarrative({ default_resume_id: id }, activeNarrativeId!)} onToggleLock={async ()=>{}} isLoading={isAppLoading} activeNarrative={activeNarrative} strategicNarratives={strategicNarratives} />} />
                            <Route path="/positioning" element={<PositioningHub narratives={strategicNarratives} activeNarrative={activeNarrative} activeNarrativeId={activeNarrativeId} onSetNarrative={setActiveNarrativeId} onSaveNarrative={handleSaveNarrative} onUpdateNarrative={handleUpdateNarrative} prompts={PROMPTS} standardRoles={standardRoles} onCreateStandardRole={async (payload, narrativeId) => { await apiService.createStandardJobRole(payload, narrativeId); fetchInitialData(); }} onUpdateStandardRole={async (roleId, payload) => { await apiService.updateStandardJobRole(roleId, payload); fetchInitialData(); }} onDeleteStandardRole={async (roleId) => { await apiService.deleteStandardJobRole(roleId); fetchInitialData(); }} baseResumes={baseResumes} />} />
                            <Route path="/engagement" element={<EngagementHub contacts={contacts} posts={linkedInPosts} engagements={engagements} postResponses={postResponses} applications={applications} allMessages={messages} userProfile={userProfile} onOpenContactModal={(contact) => { setSelectedContact(contact); setIsContactModalOpen(true); }} onCreatePostResponse={async ()=>{}} onUpdatePostResponse={handleUpdatePostResponse} onCreateLinkedInEngagement={handleCreateLinkedInEngagement} onCreatePost={handleCreatePost} onImportContacts={async ()=>{}} prompts={PROMPTS} onDeleteContact={handleDeleteContact} companies={companies} onViewCompany={(id)=>navigate(`/company/${id}`)} onAddNewCompany={()=>setIsCompanyModalOpen(true)} baseResumes={baseResumes} strategicNarratives={strategicNarratives} activeNarrative={activeNarrative} onScoreEngagement={()=>{}} />} />
                            <Route path="/interview-studio" element={<InterviewStudioView applications={applications} companies={companies} contacts={contacts} activeNarrative={activeNarrative} onSaveNarrative={handleSaveNarrative} prompts={PROMPTS} initialApp={initialAppForStudio} onClearInitialApp={()=>setInitialAppForStudio(null)} onGetReframeSuggestion={handleGetReframeSuggestion} onDeconstructQuestion={handleDeconstructQuestion} onSaveInterviewOpening={async (interviewId, opening)=>{await handleSaveInterview({strategic_opening: opening}, interviewId)}} />} />
                            <Route path="/brag-bank" element={<BragDocumentView items={bragBankItems} onSave={async (item, id) => { if(id) { await apiService.updateBragBankEntry(id, item); } else { await apiService.createBragBankEntry(item); } fetchInitialData(); }} onDelete={async (id) => { await apiService.deleteBragBankEntry(id); fetchInitialData(); }} strategicNarratives={strategicNarratives} prompts={PROMPTS} />} />
                            <Route path="/schedule-management" element={<ScheduleManagementView />} />
                            <Route path="/chroma-upload" element={<ChromaUploadView strategicNarratives={strategicNarratives} activeNarrativeId={activeNarrativeId} />} />
                            <Route path="/health-checks" element={<PromptEditorView />} />
                            
                            <Route path="/new-application" element={<NewApplicationWrapper />} />
                            <Route path="/application/:appId" element={<ApplicationDetailWrapper />} />
                            <Route path="/company/:companyId" element={<CompanyDetailWrapper />} />
                            <Route path="/resume/:resumeId" element={<ResumeEditorWrapper />} />
                            <Route path="/interview-copilot/:interviewId" element={<InterviewCopilotWrapper />} />
                            <Route path="/post-interview-debrief/:interviewId" element={<PostInterviewDebriefWrapper />} />
                            
                            {/* Modals are rendered outside Routes */}
                        </Routes>
                    </div>
                )}
            </main>
             {isContactModalOpen && <ContactModal isOpen={isContactModalOpen} onClose={() => setIsContactModalOpen(false)} onSaveContact={handleSaveContact} onCreateMessage={handleCreateMessage} onAddNewCompany={() => setIsCompanyModalOpen(true)} contact={selectedContact} companies={companies} applications={applications} baseResumes={baseResumes} linkedInPosts={linkedInPosts} userProfile={userProfile} strategicNarratives={strategicNarratives} activeNarrativeId={activeNarrativeId} prompts={PROMPTS} onDeleteContact={handleDeleteContact} />}
             {isCompanyModalOpen && <CreateCompanyModal isOpen={isCompanyModalOpen} onClose={() => setIsCompanyModalOpen(false)} onCreate={isCompanyModalForNewApp ? handleCreateCompanyForNewApp : handleCreateCompany} initialData={initialCompanyData} prompts={PROMPTS} />}
        </div>
    );
};

export const App = () => (
    <ToastProvider>
        <HashRouter>
            <AppContent />
        </HashRouter>
    </ToastProvider>
);