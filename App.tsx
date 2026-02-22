
import React, { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { HashRouter, Routes, Route, useNavigate, useParams, useSearchParams, useLocation } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import { AppView, Resume, JobApplication, BaseResume, Status, Company, CompanyInfoResult, KeywordsResult, GuidanceResult, Prompt, CompanyPayload, JobApplicationPayload, BaseResumePayload, SkillOptions, ExtractedInitialDetails, Contact, ContactPayload, ApplicationQuestion, WorkExperience, Interview, InterviewPayload, InterviewPrep, MessagePayload, Message, LinkedInPost, LinkedInPostPayload, PromptContext, JobProblemAnalysisResult, UserProfile, StrategicNarrative, StrategicNarrativePayload, UserProfilePayload, LinkedInEngagement, PostResponse, PostResponsePayload, LinkedInEngagementPayload, ResumeTailoringData, PostSubmissionPlan, InfoField, ResumeHeader, ScoutedOpportunity, Offer, OfferPayload, NinetyDayPlan, Sprint, BragBankEntry, SkillTrend, SkillTrendPayload, BragBankEntryPayload, CreateSprintPayload, SprintAction, AiSprintPlan, AiSprintAction, KeywordDetail, SprintActionPayload, SkillSection, ConsultativeClosePlan, StrategicHypothesisDraft, PostInterviewDebrief, ImpactStory, ApplicationDetailTab, ResumeTemplate, BaseResumePayload as ResumePayload, InterviewStoryDeckEntry } from './types';
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

import { ContactModal } from './components/ContactModal';
import { CreateCompanyModal } from './components/CreateCompanyModal';
import { QuickContactButton } from './components/QuickContactButton';
import { MyProfileModal } from './components/MyProfileModal';
import { DebugModal } from './components/DebugModal';
import { JobDetailsModal, UpdateJdModal } from './components/JobDetailsModal';
import { GuidanceModal } from './components/GuidanceModal';
import { OfferModal } from './components/OfferModal';
import { NinetyDayPlanModal } from './components/NinetyDayPlanModal';
import { SprintModal } from './components/SprintModal';
import { LoadingSpinner, PlusIcon } from './components/IconComponents';
import { InterviewStudioView } from './components/InterviewStudioView';
import { InterviewCopilotView } from './components/InterviewCopilotView';
import { PromptEditorView } from './components/PromptEditorView';
import { ScheduleManagementView } from './components/ScheduleManagementView';

import { ReviewedJobsView } from './components/ReviewedJobsView';
import { ManualJobCreate } from './components/ManualJobCreate';
import { WebhookConfigView } from './components/WebhookConfigView';
import { NetworkingView } from './components/NetworkingView';
import { InterviewLensView } from './components/interview/InterviewLensView';



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

const ApplicationDetailWrapper = ({
    applications, companies, contacts, allCompanies, userProfile, activeNarrative, statuses,
    isReanalyzing, isAppLoading, handleUpdateApplication, handleDeleteApplication, handleResumeApplication,
    handleReanalyzeApplication, handleSaveInterview, handleDeleteInterview, handleGenerateInterviewPrep,
    handleGenerateRecruiterScreenPrep, setIsContactModalOpen, setSelectedContact, handleOpenOfferModal,
    handleGenerate90DayPlan, handleAddSprintActions, sprint, handleGenerateCoverLetter, isGeneratingCoverLetter,
    handleNavigateToInterviewStudio, handleNavigateToDebriefStudio
}: any) => {
    const { appId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();

    const searchParams = new URLSearchParams(location.search);
    const initialTab = (searchParams.get('tab') as ApplicationDetailTab) || undefined;

    const handleTabChange = (newTab: ApplicationDetailTab) => {
        navigate({ pathname: location.pathname, search: `?tab=${newTab}` }, { replace: true });
    };

    const app = applications.find((a: any) => a.job_application_id === appId);
    const company = companies.find((c: any) => c.company_id === app?.company_id);

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
        // prompts prop removed
        statuses={statuses}
        userProfile={userProfile}
        activeNarrative={activeNarrative}
        onSaveInterview={handleSaveInterview}
        onDeleteInterview={handleDeleteInterview}
        onGenerateInterviewPrep={handleGenerateInterviewPrep}
        onGenerateRecruiterScreenPrep={handleGenerateRecruiterScreenPrep}
        onOpenContactModal={(contact) => { setSelectedContact(contact); setIsContactModalOpen(true); }}
        onOpenOfferModal={handleOpenOfferModal}
        onGenerate90DayPlan={handleGenerate90DayPlan}
        onAddQuestionToCommonPrep={(q) => handleAddSprintActions(sprint?.sprint_id || '', [{ action_name: `Prep Question: ${q}`, associated_goal: 'Prep' }])}
        onOpenStrategyStudio={(interview) => handleNavigateToInterviewStudio(app)}
        onNavigateToStudio={handleNavigateToInterviewStudio}
        handleLaunchCopilot={(app, interview) => navigate(`/interview-copilot/${interview.interview_id}`)}
        isLoading={isAppLoading}
        onOpenDebriefStudio={handleNavigateToDebriefStudio}
        initialTab={initialTab}
        onTabChange={handleTabChange}
        onGenerateCoverLetter={() => handleGenerateCoverLetter(app)}
        isGeneratingCoverLetter={isGeneratingCoverLetter}
    />;
};

const CompanyDetailWrapper = ({
    companies, applications, messages, contacts, fetchInitialData,
    handleCreateMessage, setInitialCompanyData, setIsCompanyModalOpen,
    setSelectedContact, setIsContactModalOpen, handleDeleteContact,
    activeNarrative
}: any) => {
    const { companyId } = useParams();
    const navigate = useNavigate();
    const company = companies.find((c: any) => c.company_id === companyId);
    if (!company) return <div className="p-8">Loading company...</div>;
    return <CompanyDetailView
        company={company}
        allCompanies={companies}
        applications={applications}
        messages={messages.filter((m: any) => m.company_id === companyId)}
        contacts={contacts}
        autoResearch={false}
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

const ResumeEditorWrapper = ({
    baseResumes, activeNarrative, handleSaveNarrative, activeNarrativeId, fetchInitialData, isAppLoading
}: any) => {
    const { resumeId } = useParams();
    const navigate = useNavigate();
    const resume = baseResumes.find((r: any) => r.resume_id === resumeId);
    if (!resume) return <div className="p-8">Loading Resume...</div>
    return <ResumeEditorView
        resume={resume}
        activeNarrative={activeNarrative}
        onSave={async (res) => {
            await apiService.saveResumeContent(res.resume_id, res.content as Resume);
            await apiService.updateBaseResume(res.resume_id, { resume_name: res.resume_name });
            fetchInitialData();
        }}
        onCancel={() => navigate('/applications')}
        onAutoSave={async (res) => { }}
        isLoading={isAppLoading}
        prompts={PROMPTS}
        commonKeywords={[]}
        onSetDefault={(id) => handleSaveNarrative({ default_resume_id: id }, activeNarrativeId!)}
    />
};

const InterviewCopilotWrapper = ({
    applications, companies, userProfile, activeNarrative, isAppLoading,
    handleSaveInterview, handleGenerateInterviewPrep, handleGenerateRecruiterScreenPrep,
    handleNavigateToDebriefStudio
}: any) => {
    const { interviewId } = useParams();
    const navigate = useNavigate();

    const { app, interview, company } = useMemo(() => {
        if (!applications || !companies) return { app: null, interview: null, company: null };
        for (const app of applications) {
            const interview = app.interviews?.find((i: any) => i.interview_id === interviewId);
            if (interview) {
                const company = companies.find((c: any) => c.company_id === app.company_id);
                return { app, interview, company };
            }
        }
        return { app: null, interview: null, company: null };
    }, [applications, interviewId, companies]);

    const fallbackNarrative = useMemo<StrategicNarrative>(() => ({
        narrative_id: 'fallback',
        user_id: userProfile?.user_id ?? '',
        narrative_name: 'Interview Copilot Fallback',
        desired_title: '',
        positioning_statement: '',
        impact_stories: [],
    }), [userProfile?.user_id]);

    if (isAppLoading || !app || !interview || !company) {
        return <div className="flex-1 flex items-center justify-center"><LoadingSpinner /></div>;
    }

    const narrativeForView = activeNarrative ?? fallbackNarrative;

    return (
        <InterviewCopilotView
            application={app}
            interview={interview}
            company={company}
            activeNarrative={narrativeForView}
            onBack={() => navigate(`/application/${app.job_application_id}?tab=interviews`)}
            onSaveInterview={handleSaveInterview}
            onGenerateInterviewPrep={handleGenerateInterviewPrep}
            onGenerateRecruiterScreenPrep={handleGenerateRecruiterScreenPrep}
            onOpenDebriefStudio={handleNavigateToDebriefStudio}
        />
    );
};

const PostInterviewDebriefWrapper = ({
    applications, companies, activeNarrative, isAppLoading, handleGeneratePostInterviewDebrief, isGeneratingDebrief
}: any) => {
    const { interviewId } = useParams();
    const navigate = useNavigate();

    const { app, interview, company } = useMemo(() => {
        if (!applications || !companies) return { app: null, interview: null, company: null };
        for (const app of applications) {
            const interview = app.interviews?.find((i: any) => i.interview_id === interviewId);
            if (interview) {
                const company = companies.find((c: any) => c.company_id === app.company_id);
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
    const [offers, setOffers] = useState<Offer[]>([]);
    const [bragBankItems, setBragBankItems] = useState<BragBankEntry[]>([]);
    const [skillTrends, setSkillTrends] = useState<SkillTrend[]>([]);
    const [sprint, setSprint] = useState<Sprint | null>(null);

    // --- New Application Flow State ---
    // Removed legacy wizard state


    // --- UI/Modal State ---
    const [isReanalyzing, setIsReanalyzing] = useState(false);
    const [isContactModalOpen, setIsContactModalOpen] = useState(false);
    const [selectedContact, setSelectedContact] = useState<Partial<Contact> | null>(null);
    const [isCompanyModalOpen, setIsCompanyModalOpen] = useState(false);
    const [initialCompanyData, setInitialCompanyData] = useState<Partial<CompanyPayload> | null>(null);

    type CompanyDetailModalOptions = {
        autoResearch?: boolean;
        homepageUrl?: string;
        onResearchComplete?: (status: 'completed' | 'failed') => void;
    };

    const [isCompanyDetailModalOpen, setIsCompanyDetailModalOpen] = useState(false);
    const [selectedCompanyForModal, setSelectedCompanyForModal] = useState<Company | null>(null);
    const [companyDetailAutoResearch, setCompanyDetailAutoResearch] = useState(false);
    const [companyDetailResearchCallback, setCompanyDetailResearchCallback] = useState<((status: 'completed' | 'failed') => void) | null>(null);
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
    const [isGeneratingCoverLetter, setIsGeneratingCoverLetter] = useState(false);

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
                profile, narratives, apps, comps, stats, resumes, conts, msgs, posts, engs, postRes, offers, bragItems, trends, activeSprint
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
                apiService.getOffers(),
                apiService.getBragBankEntries(),
                apiService.getSkillTrends(),
                apiService.getActiveSprint(),
            ]);

            setUserProfile(profile);
            setStrategicNarratives(narratives || []);
            setActiveNarrativeId(narratives?.[0]?.narrative_id || null);
            setApplications(apps || []);
            setCompanies(comps || []);
            setStatuses(stats || []);
            setBaseResumes(resumes || []);
            setContacts(conts || []);
            setMessages(msgs || []);
            setLinkedInPosts(posts || []);
            setEngagements(engs || []);
            setPostResponses(postRes || []);
            setOffers(offers || []);
            setBragBankItems(bragItems || []);
            setSkillTrends(trends || []);
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

    const handleStartNewApplication = async () => {
        try {
            // Create a placeholder application to start
            const newApp = await apiService.createApplication({
                job_title: 'New Application',
                date_applied: new Date().toISOString().split('T')[0],
            });
            await fetchInitialData();
            navigate(`/application/${newApp.job_application_id}`);
        } catch (err) {
            handleError(err, 'Failed to start new application');
        }
    };



    const handleCreateSprint = async (payload: CreateSprintPayload): Promise<void> => {
        try {
            const newSprint = await apiService.createSprintWithActions(payload);
            setSprint(newSprint);
            addToast('Sprint created.', 'success');
        } catch (err) {
            handleError(err, 'Failed to create sprint');
            throw err;
        }
    };

    const handleUpdateSprint = async (sprintId: string, payload: Partial<Sprint>): Promise<void> => {
        try {
            await apiService.updateSprint(sprintId, payload);
            const refreshed = await apiService.getActiveSprint();
            if (refreshed) {
                setSprint(refreshed);
            }
        } catch (err) {
            handleError(err, 'Failed to update sprint');
            throw err;
        }
    };

    const handleUpdateSprintAction = async (actionId: string, payload: SprintActionPayload): Promise<void> => {
        try {
            const updated = await apiService.updateSprintAction(actionId, payload);
            setSprint(prev => {
                if (!prev) return prev;
                return {
                    ...prev,
                    actions: prev.actions.map(action =>
                        action.action_id === updated.action_id ? { ...action, ...updated } : action
                    ),
                };
            });
        } catch (err) {
            handleError(err, 'Failed to update sprint action');
            throw err;
        }
    };

    const handleAddSprintActions = async (sprintId: string, actions: SprintActionPayload[]): Promise<void> => {
        if (!sprintId || actions.length === 0) {
            addToast('Nothing to add to the sprint yet.', 'info');
            return;
        }
        try {
            const createdActions = await apiService.addActionsToSprint(sprintId, actions);
            setSprint(prev => {
                if (!prev || prev.sprint_id !== sprintId) {
                    return prev;
                }
                return {
                    ...prev,
                    actions: [...prev.actions, ...createdActions],
                };
            });
            addToast('Sprint updated with networking focus.', 'success');
        } catch (err) {
            handleError(err, 'Failed to add sprint actions');
            throw err;
        }
    };

    const handleUpdateApplicationStatusInline = async (appId: string, statusId: string): Promise<void> => {
        try {
            await handleUpdateApplication(appId, { status_id: statusId });
            addToast('Status updated.', 'success');
        } catch (err) {
            handleError(err, 'Failed to update status');
            throw err;
        }
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

    const handleDeleteInterview = async (id: string) => {
        try {
            await apiService.deleteInterview(id);
            fetchInitialData();
            addToast('Interview deleted', 'success');
        } catch (err) {
            handleError(err, 'Failed to delete interview');
        }
    };

    const handleSaveInterviewOpening = async (interviewId: string, opening: string) => {
        await handleSaveInterview({ strategic_opening: opening }, interviewId);
    };

    const handleSaveInterviewDeck = async (interviewId: string, deck: InterviewStoryDeckEntry[]) => {
        await handleSaveInterview({ story_deck: deck }, interviewId);
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
        } catch (err) {
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

            setEngagements(prev => [newEngagement, ...prev].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));

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
        navigate(`/application/${appToResume.job_application_id}`);
    };

    const handleReanalyzeApplication = async (appToReanalyze: JobApplication) => {
        setIsReanalyzing(true);
        addToast('Rerunning full AI analysis...', 'info');
        try {
            // Step 1: Re-run Problem Analysis
            // Step 1: Re-run Problem Analysis
            const narrative = strategicNarratives.find(n => n.narrative_id === appToReanalyze.narrative_id);
            if (!narrative) throw new Error("Narrative not found for re-analysis.");

            const analysisContext = {
                NORTH_STAR: narrative.positioning_statement,
                MASTERY: narrative.signature_capability,
                DESIRED_TITLE: narrative.desired_title,
                JOB_TITLE: appToReanalyze.job_title,
                JOB_DESCRIPTION: appToReanalyze.job_description,
            };
            const analysisResult = await geminiService.performInitialJobAnalysis(analysisContext, 'INITIAL_JOB_ANALYSIS');
            const coreProblem = (analysisResult.job_problem_analysis as any).core_problem_analysis?.core_problem || (analysisResult.job_problem_analysis as any).diagnostic_intel?.composite_antidote_persona;
            if (!coreProblem) {
                throw new Error("Failed to extract core problem from the new analysis.");
            }

            // Step 2: Re-run Keywords & Guidance
            const keywordsContext = {
                JOB_DESCRIPTION: appToReanalyze.job_description,
                AI_SUMMARY: coreProblem
            };
            const keywordsResult = await geminiService.generateKeywordsAndGuidance(keywordsContext, 'GENERATE_KEYWORDS_AND_GUIDANCE');

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

    const handleGenerateCoverLetter = async (app: JobApplication) => {
        setIsGeneratingCoverLetter(true);
        try {
            if (!activeNarrative) throw new Error("No active narrative selected.");

            const context: PromptContext = {
                my_bio: activeNarrative?.positioning_statement || '',
                my_cv: JSON.stringify(app.tailored_resume_json || {}),
                job_description: app.job_description,
                job_title: app.job_title,
                company_name: companies.find(c => c.company_id === app.company_id)?.company_name || 'the company',
                strategic_narrative: JSON.stringify(activeNarrative)
            };

            const result = await geminiService.generateCoverLetter(context, 'GENERATE_ADVANCED_COVER_LETTER', debugModalState.isOpen ? undefined : undefined);
            await handleUpdateApplication(app.job_application_id, {
                cover_letter_draft: result.cover_letter
            });
            addToast('Cover letter generated!', 'success');
        } catch (err) {
            handleError(err, 'Failed to generate cover letter');
        } finally {
            setIsGeneratingCoverLetter(false);
        }
    };

    const handleGenerate90DayPlan = async (app: JobApplication) => {
        // Placeholder for 90-day plan generation logic
        addToast('90-Day Plan generation not yet implemented.', 'info');
    };

    const handleGenerateInterviewPrep = async (app: JobApplication, interview: Interview) => {
        try {
            const company = companies.find(c => c.company_id === app.company_id);

            const interviewerProfiles = (interview.interview_contacts || [])
                .map(ic => contacts.find(c => c.contact_id === ic.contact_id))
                .filter(Boolean)
                .map(c => ({
                    name: `${c!.first_name} ${c!.last_name}`,
                    role: c!.job_title,
                    profile: c!.linkedin_about,
                    persona_type: c!.persona
                }));

            const strategyResult = await apiService.generateInterviewBlueprint(
                app.job_description,
                company || {},
                activeNarrative || {},
                app.job_problem_analysis_result,
                interviewerProfiles,
                app.interview_strategy
            );

            // Clear stale widgets to ensure UI refreshes with new AI data
            const updatedWidgets = { ...(interview.widgets || {}) };
            delete updatedWidgets['strategicOpening'];
            delete updatedWidgets['battleMap'];
            delete updatedWidgets['interviewerIntel'];

            await handleSaveInterview({
                ai_prep_data: {
                    scripted_opening: strategyResult.scripted_opening,
                    diagnostic_matrix: strategyResult.diagnostic_matrix,
                    interviewer_intel: strategyResult.interviewer_intel
                },
                widgets: updatedWidgets
            }, interview.interview_id);

            addToast("Consultant Blueprint generated!", 'success');
        } catch (err) {
            handleError(err, 'Failed to generate interview blueprint');
        }
    };

    const handleGenerateRecruiterScreenPrep = async (app: JobApplication, interview: Interview) => {
        try {
            const company = companies.find(c => c.company_id === app.company_id);

            // Recruiter screens use the same blueprint generation but usually without specific interviewer profiles
            const strategyResult = await apiService.generateInterviewBlueprint(
                app.job_description,
                company || {},
                activeNarrative || {},
                app.job_problem_analysis_result,
                [],
                app.interview_strategy
            );

            const updatedWidgets = { ...(interview.widgets || {}) };
            delete updatedWidgets['strategicOpening'];
            delete updatedWidgets['battleMap'];
            delete updatedWidgets['interviewerIntel'];

            await handleSaveInterview({
                ai_prep_data: {
                    scripted_opening: strategyResult.scripted_opening,
                    diagnostic_matrix: strategyResult.diagnostic_matrix,
                    interviewer_intel: strategyResult.interviewer_intel
                },
                widgets: updatedWidgets
            }, interview.interview_id);

            addToast("Recruiter Screen prep generated!", 'success');
        } catch (err) {
            handleError(err, 'Failed to generate recruiter prep');
        }
    };

    const handleGeneratePostInterviewDebrief = async (interview: Interview, notes: { wins: string, fumbles: string, new_intelligence: string }) => {
        setIsGeneratingDebrief(true);
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

            const debriefData = await geminiService.generatePostInterviewCounter(context, 'GENERATE_POST_INTERVIEW_COUNTER', debugModalState.isOpen ? undefined : undefined);

            await handleSaveInterview({ post_interview_debrief: debriefData }, interview.interview_id);
            addToast("AI interview debrief generated!", 'success');

        } catch (err) {
            handleError(err, 'Failed to generate interview debrief');
        } finally {
            setIsGeneratingDebrief(false);
        }
    };

    const handleGetReframeSuggestion = async (question: string, coreStories: ImpactStory[]): Promise<string> => {
        try {
            const context = {
                INTERVIEW_QUESTION: question,
                CORE_STORIES_JSON: JSON.stringify((coreStories || []).map(s => ({ story_id: s.story_id, story_title: s.story_title, format: s.format })))
            };

            const result = await geminiService.generateQuestionReframeSuggestion(context, 'GENERATE_QUESTION_REFRAME_SUGGESTION', debugModalState.isOpen ? undefined : undefined);
            return result.suggestion;

        } catch (err) {
            handleError(err, 'Failed to get reframe suggestion');
            return "";
        }
    };

    const handleDeconstructQuestion = async (question: string): Promise<{ scope: string[], metrics: string[], constraints: string[] }> => {
        try {
            const context = {
                INTERVIEW_QUESTION: question,
            };
            const result = await geminiService.deconstructInterviewQuestion(context, 'DECONSTRUCT_INTERVIEW_QUESTION', debugModalState.isOpen ? undefined : undefined);
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




    return (
        <div className="flex h-screen bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-sans">
            <SideNav
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
                            <Route path="/" element={<DashboardView applications={applications} contacts={contacts} messages={messages} linkedInPosts={linkedInPosts} engagements={engagements} pendingFollowUps={messages.filter(m => m.follow_up_due_date)} userProfile={userProfile} prompts={PROMPTS} onCreateSynthesizedNarrative={handleCreateSynthesizedNarrative} sprint={sprint} weeklyProgress={""} onOpenContactModal={(contact) => { setSelectedContact(contact); setIsContactModalOpen(true); }} onUpdateContactStatus={(contactId, status) => handleSaveContact({ contact_id: contactId, status })} />} />
                            <Route path="/applications" element={<ApplicationsView applications={applications} companies={companies} statuses={statuses} offers={offers} onViewApplication={(appId) => navigate(`/application/${appId}`)} onViewCompany={(companyId) => navigate(`/company/${companyId}`)} onResumeApplication={handleResumeApplication} onAddNew={handleStartNewApplication} onDeleteApplication={handleDeleteApplication} onUpdateApplicationStatus={handleUpdateApplicationStatusInline} onDeleteOffer={async (id) => { await apiService.deleteOffer(id); fetchInitialData(); }} resumes={baseResumes} userProfile={userProfile} onAddNewResume={() => navigate('/resume/new')} onEditResume={(res) => navigate(`/resume/${res.resume_id}`)} onDeleteResume={handleDeleteResume} onCopyResume={async (res) => { }} onSetDefaultResume={(id) => handleSaveNarrative({ default_resume_id: id }, activeNarrativeId!)} onToggleLock={async () => { }} isLoading={isAppLoading} activeNarrative={activeNarrative} strategicNarratives={strategicNarratives} />} />
                            <Route path="/reviewed-jobs" element={<ReviewedJobsView />} />
                            <Route path="/add-manual-job" element={<ManualJobCreate />} />

                            <Route path="/positioning" element={<PositioningHub activeNarrative={activeNarrative} activeNarrativeId={activeNarrativeId} onSaveNarrative={handleSaveNarrative} onUpdateNarrative={handleUpdateNarrative} prompts={PROMPTS} baseResumes={baseResumes} />} />
                            <Route path="/networking" element={<NetworkingView />} />
                            <Route path="/engagement" element={<EngagementHub contacts={contacts} posts={linkedInPosts} engagements={engagements} postResponses={postResponses} applications={applications} allMessages={messages} userProfile={userProfile} onOpenContactModal={(contact) => { setSelectedContact(contact); setIsContactModalOpen(true); }} onCreatePostResponse={async () => { }} onUpdatePostResponse={handleUpdatePostResponse} onCreateLinkedInEngagement={handleCreateLinkedInEngagement} onCreatePost={handleCreatePost} onImportContacts={async () => { }} onDeleteContact={handleDeleteContact} companies={companies} onViewCompany={(id) => navigate(`/company/${id}`)} onAddNewCompany={() => setIsCompanyModalOpen(true)} baseResumes={baseResumes} strategicNarratives={strategicNarratives} activeNarrative={activeNarrative} onScoreEngagement={() => { }} onSaveContact={handleSaveContact} />} />
                            {/* FIX: `onSaveNarrative` was passed instead of `handleSaveNarrative` */}
                            <Route
                                path="/interview-studio"
                                element={(
                                    <InterviewStudioView
                                        applications={applications}
                                        companies={companies}
                                        contacts={contacts}
                                        activeNarrative={activeNarrative}
                                        onSaveNarrative={handleSaveNarrative}
                                        prompts={PROMPTS}
                                        initialApp={initialAppForStudio}
                                        onClearInitialApp={() => setInitialAppForStudio(null)}
                                        onGetReframeSuggestion={handleGetReframeSuggestion}
                                        onDeconstructQuestion={handleDeconstructQuestion}
                                        onSaveInterview={handleSaveInterview}
                                    />
                                )}
                            />
                            <Route path="/brag-bank" element={<BragDocumentView items={bragBankItems} onSave={async (item, id) => { if (id) { await apiService.updateBragBankEntry(id, item); } else { await apiService.createBragBankEntry(item); } fetchInitialData(); }} onDelete={async (id) => { await apiService.deleteBragBankEntry(id); fetchInitialData(); }} strategicNarratives={strategicNarratives} />} />
                            <Route path="/schedule-management" element={<ScheduleManagementView />} />
                            <Route path="/webhook-management" element={<WebhookConfigView />} />
                            <Route path="/health-checks" element={<PromptEditorView />} />


                            <Route path="/application/:appId" element={<ApplicationDetailWrapper
                                applications={applications} companies={companies} contacts={contacts} allCompanies={companies}
                                userProfile={userProfile} activeNarrative={activeNarrative} statuses={statuses}
                                isReanalyzing={isReanalyzing} isAppLoading={isAppLoading}
                                handleUpdateApplication={handleUpdateApplication} handleDeleteApplication={handleDeleteApplication}
                                handleResumeApplication={handleResumeApplication} handleReanalyzeApplication={handleReanalyzeApplication}
                                handleSaveInterview={handleSaveInterview} handleDeleteInterview={handleDeleteInterview}
                                handleGenerateInterviewPrep={handleGenerateInterviewPrep} handleGenerateRecruiterScreenPrep={handleGenerateRecruiterScreenPrep}
                                setIsContactModalOpen={setIsContactModalOpen} setSelectedContact={setSelectedContact}
                                handleOpenOfferModal={(app: any, offer: any) => {
                                    setInitialCompanyData({ company_id: app.company_id });
                                    setSelectedOffer(offer);
                                    setIsOfferModalOpen(true);
                                }}
                                handleGenerate90DayPlan={handleGenerate90DayPlan}
                                handleAddSprintActions={handleAddSprintActions}
                                sprint={sprint}
                                handleGenerateCoverLetter={handleGenerateCoverLetter}
                                isGeneratingCoverLetter={isGeneratingCoverLetter}
                                handleNavigateToInterviewStudio={handleNavigateToInterviewStudio}
                                handleNavigateToDebriefStudio={handleNavigateToDebriefStudio}
                            />} />
                            <Route path="/company/:companyId" element={<CompanyDetailWrapper
                                companies={companies} applications={applications} messages={messages} contacts={contacts}
                                fetchInitialData={fetchInitialData} handleCreateMessage={handleCreateMessage}
                                setInitialCompanyData={setInitialCompanyData} setIsCompanyModalOpen={setIsCompanyModalOpen}
                                setSelectedContact={setSelectedContact} setIsContactModalOpen={setIsContactModalOpen}
                                handleDeleteContact={handleDeleteContact} activeNarrative={activeNarrative}
                            />} />
                            <Route path="/resume/:resumeId" element={<ResumeEditorWrapper
                                baseResumes={baseResumes} activeNarrative={activeNarrative}
                                handleSaveNarrative={handleSaveNarrative} activeNarrativeId={activeNarrativeId}
                                fetchInitialData={fetchInitialData} isAppLoading={isAppLoading}
                            />} />
                            <Route path="/interview-copilot/:interviewId" element={<InterviewCopilotWrapper
                                applications={applications} companies={companies} userProfile={userProfile}
                                activeNarrative={activeNarrative} isAppLoading={isAppLoading}
                                handleSaveInterview={handleSaveInterview} handleGenerateInterviewPrep={handleGenerateInterviewPrep}
                                handleGenerateRecruiterScreenPrep={handleGenerateRecruiterScreenPrep}
                                handleNavigateToDebriefStudio={handleNavigateToDebriefStudio}
                            />} />
                            <Route path="/interview-lens/:interviewId" element={<InterviewLensView
                                applications={applications}
                                companies={companies}
                                activeNarrative={activeNarrative}
                                onSaveInterview={handleSaveInterview}
                                isAppLoading={isAppLoading}
                            />} />
                            <Route path="/post-interview-debrief/:interviewId" element={<PostInterviewDebriefWrapper
                                applications={applications} companies={companies} activeNarrative={activeNarrative}
                                isAppLoading={isAppLoading} handleGeneratePostInterviewDebrief={handleGeneratePostInterviewDebrief}
                                isGeneratingDebrief={isGeneratingDebrief}
                            />} />

                            {/* Modals are rendered outside Routes */}
                        </Routes>
                    </div>
                )}
            </main>

            <SprintModal
                isOpen={isSprintModalOpen}
                onClose={() => setIsSprintModalOpen(false)}
                sprint={sprint}
                activeNarrative={activeNarrative}
                prompts={PROMPTS}
                onCreateSprint={handleCreateSprint}
                onUpdateSprint={handleUpdateSprint}
                onUpdateAction={handleUpdateSprintAction}
                onAddActions={handleAddSprintActions}
                applications={applications}
                contacts={contacts}
                linkedInPosts={linkedInPosts}
                allMessages={messages}
            />



            {isContactModalOpen && <ContactModal isOpen={isContactModalOpen} onClose={() => setIsContactModalOpen(false)} onSaveContact={handleSaveContact} onCreateMessage={handleCreateMessage} onAddNewCompany={() => setIsCompanyModalOpen(true)} contact={selectedContact} companies={companies} applications={applications} baseResumes={baseResumes} linkedInPosts={linkedInPosts} userProfile={userProfile} strategicNarratives={strategicNarratives} activeNarrativeId={activeNarrativeId} prompts={PROMPTS} onDeleteContact={handleDeleteContact} />}
            {isCompanyModalOpen && <CreateCompanyModal isOpen={isCompanyModalOpen} onClose={() => setIsCompanyModalOpen(false)} onCreate={handleCreateCompany} initialData={initialCompanyData} prompts={PROMPTS} />}
            {isCompanyDetailModalOpen && selectedCompanyForModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white dark:bg-slate-800 rounded-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden">
                        <div className="flex justify-between items-center p-6 border-b border-slate-200 dark:border-slate-700">
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Company Research Results</h2>
                            <button
                                onClick={() => {
                                    if (companyDetailResearchCallback) {
                                        companyDetailResearchCallback('failed');
                                        setCompanyDetailResearchCallback(null);
                                    }
                                    setIsCompanyDetailModalOpen(false);
                                    setSelectedCompanyForModal(null);
                                    setCompanyDetailAutoResearch(false);
                                }}
                                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xl"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
                            <CompanyDetailView
                                company={selectedCompanyForModal}
                                allCompanies={companies}
                                applications={applications}
                                messages={messages.filter(m => m.company_id === selectedCompanyForModal.company_id)}
                                contacts={contacts}
                                autoResearch={companyDetailAutoResearch}
                                onBack={() => {
                                    if (companyDetailResearchCallback) {
                                        companyDetailResearchCallback('failed');
                                        setCompanyDetailResearchCallback(null);
                                    }
                                    setIsCompanyDetailModalOpen(false);
                                    setSelectedCompanyForModal(null);
                                    setCompanyDetailAutoResearch(false);
                                }}
                                onUpdate={async (payload) => { await apiService.updateCompany(selectedCompanyForModal.company_id, payload); fetchInitialData(); }}
                                onViewApplication={(appId) => {
                                    if (companyDetailResearchCallback) {
                                        companyDetailResearchCallback('failed');
                                        setCompanyDetailResearchCallback(null);
                                    }
                                    setIsCompanyDetailModalOpen(false);
                                    setSelectedCompanyForModal(null);
                                    setCompanyDetailAutoResearch(false);
                                    navigate(`/application/${appId}`);
                                }}
                                onCreateMessage={handleCreateMessage}
                                onOpenCreateCompanyModal={(data) => { setInitialCompanyData(data); setIsCompanyModalOpen(true); }}
                                onOpenContactModal={(contact) => { setSelectedContact(contact); setIsContactModalOpen(true); }}
                                onResearch={async (details) => {
                                    const researchContext = {
                                        COMPANY_NAME: details.name,
                                        COMPANY_HOMEPAGE: details.url || 'https://example.com',
                                    };

                                    const researchCallback = companyDetailResearchCallback;

                                    try {
                                        const aiResearchResult = await geminiService.researchCompanyInfo(researchContext, 'COMPANY_GOAL_ANALYSIS');

                                        const companyUpdates = {
                                            company_name: details.name,
                                            company_url: details.url,
                                            mission: { text: aiResearchResult.mission?.text || '', source: aiResearchResult.mission?.source || '' },
                                            values: { text: aiResearchResult.values?.text || '', source: aiResearchResult.values?.source || '' },
                                            goals: { text: aiResearchResult.goals?.text || '', source: aiResearchResult.goals?.source || '' },
                                            issues: { text: aiResearchResult.issues?.text || '', source: aiResearchResult.issues?.source || '' },
                                            customer_segments: { text: aiResearchResult.customer_segments?.text || '', source: aiResearchResult.customer_segments?.source || '' },
                                            strategic_initiatives: { text: aiResearchResult.strategic_initiatives?.text || '', source: aiResearchResult.strategic_initiatives?.source || '' },
                                            market_position: { text: aiResearchResult.market_position?.text || '', source: aiResearchResult.market_position?.source || '' },
                                            competitors: { text: aiResearchResult.competitors?.text || '', source: aiResearchResult.competitors?.source || '' },
                                            news: { text: aiResearchResult.news?.text || '', source: aiResearchResult.news?.source || '' },
                                            industry: { text: aiResearchResult.industry?.text || '', source: aiResearchResult.industry?.source || '' }
                                        };

                                        await apiService.updateCompany(details.id, companyUpdates);
                                        await fetchInitialData();

                                        if (researchCallback) {
                                            researchCallback('completed');
                                            setCompanyDetailResearchCallback(null);
                                        }
                                    } catch (error) {
                                        if (researchCallback) {
                                            researchCallback('failed');
                                            setCompanyDetailResearchCallback(null);
                                        }
                                        throw error;
                                    } finally {
                                        setCompanyDetailAutoResearch(false);
                                    }
                                }}
                                onDeleteContact={handleDeleteContact}
                                prompts={PROMPTS}
                                activeNarrative={activeNarrative}
                            />
                        </div>
                    </div>
                </div>
            )}

            <QuickContactButton
                onOpenContactModal={(contact) => { setSelectedContact(contact); setIsContactModalOpen(true); }}
                companies={companies}
                applications={applications}
            />
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
