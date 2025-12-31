import type { Layout, Layouts } from 'react-grid-layout';

// Represents the user's core, non-strategic information
export interface UserProfile {
  user_id: string; // uuid
  email?: string;
  name?: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  city?: string;
  state?: string;
  links: string[];
}

export interface Prompt {
  id: string;
  name: string;
  description: string;
  content: string;
}

export type PromptContext = { [key: string]: any };

// Represents the main views of the application
export enum AppView {
  DASHBOARD,
  APPLICATIONS,
  ENGAGEMENT_HUB,
  POSITIONING_HUB,
  VIEW_COMPANY,
  NEW_APPLICATION,
  VIEW_APPLICATION,
  PROMPT_EDITOR,
  RESUME_EDITOR,
  INTERVIEW_STUDIO,
  BRAG_BANK,
  INTERVIEW_STRATEGY_STUDIO,
  INTERVIEW_CO_PILOT,
  POST_INTERVIEW_DEBRIEF,
}

export type ApplicationDetailTab = 'overview' | 'analysis' | 'resume' | 'interviews' | 'ai-content' | 'questions' | 'apply';
export type ApplicationLabTab = 'lab' | 'formulas' | 'offers';




// From groundingMetadata.groundingChunks
export interface GroundingChunk {
  web?: {
    uri?: string;
    title?: string;
  }
}

export interface ExtractedInitialDetails {
  companyName: string;
  jobTitle: string;
  jobDescription: string;
  salary?: string;
  companyHomepageUrl?: string;
  mission?: string;
  values?: string;
  location?: string;
  remoteStatus?: 'Remote' | 'Hybrid' | 'On-site' | '';
  error?: string;
}


export interface JobSummaryResult {
  key_responsibilities: string[];
  key_qualifications: string[];
}

export interface CoreProblemAnalysis {
  business_context: string;
  core_problem: string;
  strategic_importance: string;
}

export interface JobProblemAnalysisResultV1 {
  core_problem_analysis: CoreProblemAnalysis;
  key_success_metrics: string[];
  role_levers: string[];
  potential_blockers: string[];
  suggested_positioning: string;
  tags: string[];
}

export interface DiagnosticIntel {
  failure_state_portfolio: string[];
  composite_antidote_persona: string;
  experience_anchoring: {
    anchor_role_title: string;
    alignment_type: string;
    fidelity_logic: string;
  };
  mandate_quadrant: {
    solve: string;
    improve: string;
    deliver: string;
    maintain: string;
  };
  functional_gravity_stack: string[];
  strategic_friction_hooks: string[];
}

export interface EconomicLogicGates {
  primary_value_driver: string;
  metric_hierarchy: string[];
}

export interface ContentIntelligence {
  vocabulary_mirror: string[];
  must_have_tech_signals: string[];
}

export interface JobProblemAnalysisResultV2 {
  diagnostic_intel: DiagnosticIntel;
  economic_logic_gates: EconomicLogicGates;
  content_intelligence: ContentIntelligence;
}

export type JobProblemAnalysisResult = JobProblemAnalysisResultV1 | JobProblemAnalysisResultV2;

export interface StrategicAlignmentHook {
  role: string;
  company: string;
  friction_hook: string;
  mapped_pillar: string;
  context_type: string;
  secondary_alignments?: string[];
  role_index?: number;
}

export interface AlignmentStrategy {
  alignment_strategy: StrategicAlignmentHook[];
}

export interface InfoField {
  text: string;
  source: string;
}

// Result from the AI company research
export interface CompanyInfoResult {
  mission: InfoField;
  values: InfoField;
  news: InfoField;
  goals: InfoField;
  issues: InfoField;
  customer_segments: InfoField;
  strategic_initiatives: InfoField;
  market_position: InfoField;
  competitors: InfoField;
  industry?: InfoField;
  success_metrics?: InfoField;
  talent_expectations?: InfoField;
}

// Based on the 'companies' table
export interface Company {
  company_id: string; // uuid in DB
  user_id: string;
  company_name: string;
  company_url?: string;
  mission?: InfoField;
  values?: InfoField;
  news?: InfoField;
  goals?: InfoField;
  issues?: InfoField;
  customer_segments?: InfoField;
  strategic_initiatives?: InfoField;
  market_position?: InfoField;
  competitors?: InfoField;
  industry?: InfoField;
  success_metrics?: InfoField;
  talent_expectations?: InfoField;
  is_recruiting_firm?: boolean;
  funding_status?: string;
  culture_keywords?: string[];
  known_tech_stack?: string[];
}

// Based on the 'statuses' table
export interface Status {
  status_id: string; // Changed from number to string for UUID
  status_name: string;
}

export interface KeywordDetail {
  keyword: string;
  frequency: number;
  emphasis: boolean;
  reason: string;
  is_required: boolean;
  match_strength: number;
  resume_boost: boolean;
}

export interface KeywordsResult {
  hard_keywords: KeywordDetail[];
  soft_keywords: KeywordDetail[];
}

export interface GuidanceResult {
  summary: string[];
  bullets: string[];
  keys: string[];
}

export interface ApplicationQuestion {
  id: string; // Unique ID for React key prop
  question: string;
  answer: string;
  user_thoughts?: string;
}

export interface ApplicationAnswersResult {
  answers: {
    question: string;
    answer: string;
  }[];
}

export interface NextStep {
  step: number;
  action: string;
  details: string;
}

export interface NinetyDayPlan {
  title: string;
  thirty_day_plan: { theme: string; goals: string[] };
  sixty_day_plan: { theme: string; goals: string[] };
  ninety_day_plan: { theme: string; goals: string[] };
}

export interface StrategicHypothesisDraft {
  problem: string;
  evidence: string;
  angle: string;
  outcome: string;
}

// New type for the Consultative Close feature
export interface ConsultativeClosePlan {
  thirty_day_plan: {
    theme: string;
    goals: string[];
  };
  sixty_day_plan: {
    theme: string;
    goals: string[];
  };
  ninety_day_plan: {
    theme: string;
    goals: string[];
  };
  key_talking_points: string[];
  briefing_email_draft: string;
}


// A simplified representation of the 'job_applications' table for the frontend
export interface JobApplication {
  job_application_id: string; // Changed from number to string for UUID
  user_id: string;
  narrative_id: string; // Foreign key to strategic_narratives
  company_id: string;
  job_title: string;
  job_description: string;
  job_link?: string;
  salary?: string;
  location?: string;
  remote_status?: 'Remote' | 'Hybrid' | 'On-site';
  source_job_id?: string; // References job ID from reviewed jobs when created from AI Jobs Board
  date_applied: string;
  created_at: string;
  status?: Status;
  ai_summary?: string;
  job_problem_analysis_result?: JobProblemAnalysisResult;
  keywords?: string | KeywordsResult;
  guidance?: string | GuidanceResult;
  resume_summary?: string;
  resume_summary_bullets?: string;
  tailored_resume_json?: Resume;
  tailored_resume_json_version?: number;
  application_questions?: ApplicationQuestion[];
  application_message?: string;
  cover_letter_draft?: string;
  workflow_mode?: string; // 'ai_generated', 'fast_track', or 'manual'
  // New relational data
  messages?: Message[];
  interviews?: Interview[];
  offers?: Offer[];
  // New strategic fields
  strategic_fit_score?: number;
  initial_interview_prep?: string[];
  why_this_job?: string;
  next_steps_plan?: NextStep[];
  first_90_day_plan?: NinetyDayPlan | null;
  keyword_coverage_score?: number;
  assumed_requirements?: string[];
  referral_target_suggestion?: string;
  vocabulary_mirror?: string;
  alignment_strategy?: AlignmentStrategy;
}

// ----- New Detailed Resume Structures -----

export interface ResumeHeader {
  first_name: string;
  last_name: string;
  job_title: string;
  email: string;
  phone_number: string;
  city: string;
  state: string;
  location?: string;
  links: string[];
}

export interface Summary {
  headline?: string;
  paragraph: string;
  bullets: string[];
}

export interface DateInfo {
  month: number;
  year: number;
  day?: number;
}

export interface ResumeAccomplishment {
  achievement_id: string;
  description: string;
  original_description?: string;
  ai_suggestion?: string;
  keyword_suggestions?: string[];
  always_include: boolean;
  themes?: string[];
  score?: AchievementScore;
  original_score?: AchievementScore;
  order_index: number;
  relevance_score?: number;
}

export interface WorkExperience {
  company_name: string;
  job_title: string;
  location: string;
  start_date: DateInfo;
  end_date: DateInfo;
  is_current: boolean;
  filter_accomplishment_count: number;
  role_context?: string;
  accomplishments: ResumeAccomplishment[];
}

export interface Education {
  school: string;
  location: string;
  degree: string;
  major: string[];
  minor: string[];
  start_month: number;
  start_year: number;
  end_month: number;
  end_year: number;
}

export interface Certification {
  name: string;
  organization: string;
  link?: string;
  issued_date: string; // YYYY-MM-DD
}

export interface SkillSection {
  heading: string;
  items: string[];
}

export interface Resume {
  header: ResumeHeader;
  summary: Summary;
  work_experience: WorkExperience[];
  education: Education[];
  certifications: Certification[];
  skills: SkillSection[];
}


// Represents a saved, base resume, based on the 'resumes' table
export interface BaseResume {
  resume_id: string; // Changed from number to string for UUID
  resume_name: string;
  user_id: string; // Foreign key to users table
  created_at?: string;
  updated_at?: string;
  is_locked: boolean;
  // The 'content' is now assembled from normalized tables, not a direct DB field.
  // It's included here as an optional property for UI state management.
  content?: Resume;
}


// New type for Contact Personas
export type ContactPersona =
  | 'Hiring Manager'
  | 'Peer'
  | 'Recruiter'
  | 'Product Leader'
  | 'Cross-Functional Stakeholder'
  | 'Alumni Contact'
  | 'Executive Contact';


// Represents a professional contact for networking
export interface Contact {
  contact_id: string; // uuid
  first_name: string;
  last_name: string;
  job_title: string;
  company_id?: string; // uuid, optional FK
  company_name?: string; // from the view
  company_url?: string; // from the view
  job_application_id?: string; // uuid, optional FK
  job_application?: Pick<JobApplication, 'job_application_id' | 'job_title'>; // for joined data
  email?: string;
  linkedin_url?: string;
  linkedin_about?: string;
  persona?: ContactPersona;
  status: string; // 'To Contact', 'Initial Outreach', 'In Conversation', etc.
  is_referral?: boolean;
  date_contacted: string; // YYYY-MM-DD
  notes?: string;
  messages?: Message[];
  strategic_alignment_score?: number;
  narrative_ids?: string[]; // For UI state
  strategic_narratives?: { narrative_id: string; narrative_name: string }[]; // For data from API
}

// ----- New Relational Data Types -----
export interface Message {
  message_id: string; // uuid
  user_id: string;
  contact_id?: string;
  company_id?: string;
  job_application_id?: string;
  message_type: 'Connection' | 'Follow-up' | 'Comment' | 'Note';
  content: string;
  follow_up_due_date?: string; // YYYY-MM-DD
  created_at: string;
  contact?: Pick<Contact, 'contact_id' | 'first_name' | 'last_name'>; // for dashboard widget
  company?: Pick<Company, 'company_id' | 'company_name'>;
  is_user_sent?: boolean;
  ai_analysis?: MessageAiAnalysis | null;
}

export interface PostInterviewDebrief {
  thank_you_note_draft: string;
  performance_analysis: {
    wins: string[];
    areas_for_improvement: string[];
  };
  coaching_recommendations: string[];
}

export interface InterviewPrepOutline {
  role_intelligence?: {
    core_problem?: string;
    suggested_positioning?: string;
    key_success_metrics?: string[];
    role_levers?: string[];
    potential_blockers?: string[];
  };
  jd_insights?: {
    business_context?: string;
    strategic_importance?: string;
    tags?: string[];
  };
}

export interface Interview {
  interview_id: string; // uuid
  job_application_id: string;
  interview_date?: string;
  interview_type: string; // e.g., "Phone Screen", "Technical", "Hiring Manager"
  notes?: string;
  prep_outline?: InterviewPrepOutline | null;
  live_notes?: string | null;
  ai_prep_data?: InterviewPrep | null;
  strategic_plan?: ConsultativeClosePlan | null;
  strategic_opening?: string | null;
  strategic_questions_to_ask?: string[] | null;
  post_interview_debrief?: PostInterviewDebrief | null;
  interview_contacts?: {
    contact_id: string;
    first_name: string;
    last_name: string;
  }[];
  story_deck?: InterviewStoryDeckEntry[];
  layout?: InterviewLayoutState | null;
  widgets?: InterviewWidgetStateMap | null;
  widget_metadata?: InterviewWidgetMetadataMap | null;
}

export type InterviewLayoutState = Partial<Layouts>;

export type InterviewLayoutItem = Layout;

export interface InterviewWidgetStateValue<TData = unknown> {
  data?: TData;
  lastUpdated?: string | null;
  metadata?: Record<string, unknown>;
}

export type InterviewWidgetStateMap = Record<string, InterviewWidgetStateValue>;

export interface InterviewWidgetMetadataEntry {
  collapsed?: boolean;
  custom?: Record<string, unknown>;
}

export type InterviewWidgetMetadataMap = Record<string, InterviewWidgetMetadataEntry>;

export interface Offer {
  offer_id: string; // uuid
  job_application_id: string; // uuid
  user_id: string; // uuid
  company_name: string;
  job_title: string;
  base_salary?: number;
  bonus_potential?: string;
  equity_details?: string;
  benefits_summary?: string;
  deadline?: string; // YYYY-MM-DD
  status: 'Received' | 'Negotiating' | 'Accepted' | 'Declined';
  created_at: string;
}


export interface InterviewPrep {
  keyFocusAreas: string[];
  potentialQuestions: { question: string; strategy: string; }[];
  questionsToAsk: string[];
  redFlags: string[];
  salaryNegotiation?: {
    suggestion: string;
    reasoning: string;
  };
}

export interface InterviewCoachingQuestion {
  question: string;
  answer: string;
  feedback: string;
  score: number;
  clarifying_questions?: string;
  clarifying_feedback?: string;
  clarifying_score?: number;
  reframe_suggestion?: string;
  deconstructed_questions?: {
    scope: string[];
    metrics: string[];
    constraints: string[];
  };
}

export interface LinkedInPost {
  post_id: string; // uuid
  user_id: string;
  narrative_id: string | null;
  theme: string;
  content: string;
  created_at: string;
  tags?: string[];
  engagements?: LinkedInEngagement[];
}

export interface LinkedInEngagement {
  engagement_id: string; // uuid
  post_id: string; // uuid
  contact_id?: string | null;
  contact_name: string;
  contact_title: string;
  contact_company_name?: string;
  interaction_type: 'like' | 'comment' | 'share';
  content?: string; // for comments
  created_at: string;
  post_theme: string; // From the original post
  contact_linkedin_url?: string;
  notes?: string;
  strategic_score?: number;
  contact?: Pick<Contact, 'contact_id' | 'first_name' | 'last_name' | 'job_title'> | null;
}

export interface PostResponseAiAnalysis {
  tone: string;
  depth: 'surface' | 'moderate' | 'deep';
  strategic_relevance: 'low' | 'medium' | 'high';
}

export interface PostResponse {
  comment_id: string; // uuid
  user_id: string;
  post_excerpt: string;
  conversation: { author: 'user' | 'other', text: string }[];
  created_at: string;
  post_id?: string; // Optional link to a user's own post
  ai_analysis?: PostResponseAiAnalysis | null;
}

// ----- Career Brand Framework -----
export type CareerBrandSection =
  | "north_star"
  | "trajectory_mastery"
  | "values_compass"
  | "lifestyle_alignment"
  | "compensation_philosophy"
  | "purpose_impact"
  | "career_story"
  | "narratives_proof_points"
  | "full_document";


export const CAREER_BRAND_SECTIONS: { id: CareerBrandSection; name: string; description: string }[] = [
  {
    id: "full_document",
    name: "Career Brand (Full Document)",
    description: "The complete source material for your brand, such as your full resume or an exhaustive professional profile."
  },
  {
    id: "north_star",
    name: "North Star & Vision",
    description: "Your long-term career destination, core ambition, and the 'why' behind your journey."
  },
  {
    id: "trajectory_mastery",
    name: "Trajectory & Mastery",
    description: "Your professional expertise, signature capabilities, and the unique skills you've mastered."
  },
  {
    id: "values_compass",
    name: "Values Compass",
    description: "The core principles, work style preferences, and professional values that guide your decisions."
  },
  {
    id: "purpose_impact",
    name: "Purpose & Impact",
    description: "The measurable difference you make, your contribution to the world, and your core 'why'."
  },
  {
    id: "lifestyle_alignment",
    name: "Lifestyle Alignment",
    description: "How your work integrates with your broader lifestyle goals, boundaries, and well-being."
  },
  {
    id: "compensation_philosophy",
    name: "Compensation Philosophy",
    description: "Your value-based approach to earnings, negotiation philosophy, and financial goals."
  },
  {
    id: "career_story",
    name: "Career Story (Past → Present → Future)",
    description: "The coherent narrative of your journey: where you've been, where you are, and where you're going."
  },
  {
    id: "narratives_proof_points",
    name: "Narratives & Proof Points",
    description: "Specific evidence, data points, and stories that validate your brand and capabilities."
  },
];

// ----- New User Strategy Profile -----
export type StorytellingFormat = 'STAR' | 'SCOPE' | 'WINS' | 'SPOTLIGHT';

export interface StarBody {
  situation: string;
  task: string;
  action: string;
  result: string;
}

export interface ScopeBody {
  situation: string;
  complication: string;
  opportunity: string;
  product_thinking: string;
  end_result: string;
}

export interface WinsBody {
  situation: string;
  what_i_did: string;
  impact: string;
  nuance: string;
}

export interface SpotlightBody {
  situation: string;
  positive_moment_or_goal: string;
  observation_opportunity: string;
  task_action: string;
  learnings_leverage: string;
  impact_results: string;
  growth_grit: string;
  highlights_key_trait: string;
  takeaway_tie_in: string;
}

export interface ImpactStory {
  story_id: string; // uuid
  story_title: string;
  format: StorytellingFormat;
  story_body: StarBody | ScopeBody | WinsBody | SpotlightBody | { [key: string]: string };
  target_questions: string[];
  speaker_notes?: { [key: string]: string };
}

export interface InterviewStoryDeckEntry {
  story_id: string;
  order_index: number;
  custom_notes?: {
    [role: string]: {
      [field: string]: string;
    };
  } | null;
}

// New type for Interview Studio
export interface CommonInterviewAnswer {
  answer_id: string; // uuid
  user_id: string; // uuid
  narrative_id: string; // uuid
  question: string;
  answer: string;
  speaker_notes?: string;
}

export interface StrategicNarrative {
  narrative_id: string;
  user_id: string; // uuid
  narrative_name: string;
  // Strategic info
  mission_alignment?: string;
  long_term_legacy?: string;
  positioning_statement?: string;
  key_strengths?: string[];
  signature_capability?: string;
  impact_story_title?: string;
  impact_story_body?: string;
  impact_stories?: ImpactStory[];
  representative_metrics?: string[];
  leadership_style?: string;
  communication_style?: string;
  working_preferences?: string[];
  preferred_locations?: string[];
  relocation_open?: boolean;
  compensation_expectation?: string;
  common_interview_answers?: CommonInterviewAnswer[];
  created_at?: string;
  updated_at?: string;
  default_resume_id?: string;
}



// Represents the AI-generated suggestions for a single accomplishment
export interface ResumeSuggestion {
  original: string;
  suggestions: string[];
}

export interface SkillOptions {
  heading: string;
  options: string[];
}

// ----- New AI Types -----
export interface AchievementScore {
  clarity: number;
  drama: number;
  alignment_with_mastery: number;
  alignment_with_job?: number;
  overall_score: number;
}

export interface InterviewAnswerScore {
  clarity: number;
  impact: number;
  brand_alignment: number;
  overall_score: number;
}

export interface MessageAiAnalysis {
  tone: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  strategy_alignment_score: number;
}

export interface CombinedAchievementSuggestion {
  original_indices: number[];
  suggestions: string[];
}

export interface CombineAchievementsResult {
  combinations: CombinedAchievementSuggestion[];
}

// ----- Engagement Agent Types -----

export type AgentActionType = 'CREATE_CONTACT' | 'LOG_ENGAGEMENT' | 'DRAFT_MESSAGE' | 'UPDATE_STRATEGY';

export interface AgentAction {
  type: AgentActionType;
  data: any; // Flexible payload depending on action type
}

export interface AgentMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  action?: AgentAction;
  timestamp: Date;
}

// ----- New Combined AI Result Types for Cost Savings -----

export interface InitialJobAnalysisResult {
  job_problem_analysis: JobProblemAnalysisResult;
  strategic_fit_score: number;
  assumed_requirements: string[];
}

export interface KeywordsAndGuidanceResult {
  keywords: KeywordsResult;
  guidance: GuidanceResult;
}

export interface ResumeTailoringData {
  keywords: KeywordsResult;
  guidance: GuidanceResult;
  processed_work_experience: {
    company_name: string;
    job_title: string;
    location: string;
    start_date: DateInfo;
    end_date: DateInfo;
    is_current: boolean;
    filter_accomplishment_count: number;
    accomplishments: {
      description: string;
      keyword_suggestions?: string[];
      relevance_score: number;
      original_score: AchievementScore;
    }[];
  }[];
  summary_suggestions: string[];
  comprehensive_skills: string[];
  ai_selected_skills: string[];
  missing_keywords: KeywordDetail[];
  initial_alignment_score: number;
}


export interface PostSubmissionPlan {
  why_this_job: string;
  next_steps_plan: NextStep[];
}

// ----- Dashboard & Engagement Hub AI Types -----

// For AI-generated sprint plans (temporary, not saved to DB)
export interface AiSprintAction {
  action_type: 'application' | 'networking' | 'branding' | 'execution';
  title: string;
  details: string;
  is_completed?: boolean;
}

export interface AiSprintPlan {
  theme_of_the_week: string;
  actions: AiSprintAction[];
}

// For AI-Powered Dashboard Feed
export interface AiFocusItem {
  item_type: 'follow_up' | 'networking_goal' | 'application_goal' | 'branding_goal' | 'skill_gap' | 'congrats';
  title: string;
  suggestion: string;
  related_id?: string; // e.g., contact_id, job_application_id, skill_name
  cta?: string; // e.g., "Draft Message"
}

// New types for persistent, user-defined sprints
export const GOAL_TYPES = ['applications', 'contacts', 'posts', 'follow-ups'] as const;
export type GoalType = typeof GOAL_TYPES[number];

export interface SprintAction {
  action_id: string; // uuid
  sprint_id: string; // uuid
  user_id: string; // uuid
  title: string;
  is_completed: boolean;
  is_goal: boolean;
  goal_type: GoalType | null;
  goal_target: number | null;
  order_index: number;
  // New strategic fields
  impact?: string | null;
  effort_estimate?: string | null;
  strategic_tags?: string[] | null;
  measurable_value?: string | null;
}

export interface Sprint {
  sprint_id: string; // uuid
  user_id: string; // uuid
  start_date: string; // date
  theme?: string;
  created_at: string;
  actions: SprintAction[];
  // New fields for career mode
  mode: 'search' | 'career';
  learning_goal?: string;
  cross_functional_collaboration?: string;
  growth_alignment?: string;
  promotion_readiness_notes?: string;
  // New fields for strategic tracking
  tags?: string[] | null;
  strategic_score?: number | null;
}


// For Dashboard "Opportunity Scout"
export interface ScoutedOpportunity {
  job_title: string;
  company_name: string;
  job_url: string;
  reasoning: string;
  fit_score: number; // 0-10
  source?: GroundingChunk;
}

// For Contact Modal "Brand Voice Analysis"
export interface BrandVoiceAnalysis {
  alignment_score: number; // 0-10
  tone_feedback: string;
  suggestion: string;
}

// For Application Detail "Intelligent Contact Suggestions"
export interface SuggestedContact {
  full_name: string;
  job_title: string;
  linkedin_url: string;
  reasoning: string;
  source?: GroundingChunk;
}

// For Skill Gap Analysis
export interface SkillToDevelop {
  skill: string;
  suggestion: string;
}

export interface LearningResource {
  title: string;
  url: string;
  type: 'Course' | 'Article';
  summary: string;
}

export interface SkillGapAnalysisResult {
  skills_to_amplify: SkillToDevelop[];
  skills_to_acquire: SkillToDevelop[];
}

// For Narrative Synthesis
export interface SuggestedPath {
  suggested_title: string;
  suggested_positioning_statement: string;
  reasoning: string;
  next_steps: string[];
}

export interface NarrativeSynthesisResult {
  synthesis_summary: string;
  suggested_paths: SuggestedPath[];
}

// New Brag Bank type
export interface BragBankEntry {
  entry_id: string; // uuid
  user_id: string;
  action_id: string | null;
  title: string;
  description: string | null;
  tags: string[] | null;
  source_context: string | null;
  created_at: string;
}

// New Skill Trend type
export interface SkillTrend {
  skill_trend_id: string; // uuid
  user_id: string;
  narrative_id: string;
  skill: string;
  skill_type: 'amplify' | 'acquire';
  suggestion: string;
  created_at: string;
}

// ----- NEW Dev Mode / Scheduler Types -----
export interface SiteDetails {
  site_name: string;
  supports_remote?: boolean;
  supports_salary_filter?: boolean;
  requires?: string[];
  optional?: string[];
  conflicts?: string[];
  notes?: string[];
}

export interface SiteSchedule {
  id: string; // uuid
  site_name: string;
  enabled: boolean;
  interval_minutes: number;
  last_run_at?: string | null; // timestampz
  next_run_at?: string | null; // timestampz
  created_at: string; // timestampz
  updated_at: string; // timestampz
  payload?: { [key: string]: any } | null;
}

export type SiteSchedulePayload = Partial<Omit<SiteSchedule, 'id' | 'created_at' | 'updated_at'>>;


export const ResumeTemplate: Resume = {
  header: { first_name: "", last_name: "", job_title: "", email: "", phone_number: "", city: "", state: "", links: [] },
  summary: { paragraph: "", bullets: [] },
  work_experience: [],
  education: [],
  certifications: [],
  skills: []
};

// ----- Toast Notification Types -----
export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
}


// ----- API Payload Types -----

export type CompanyPayload = Partial<Omit<Company, 'company_id' | 'user_id'>>;

export type JobApplicationPayload = Partial<Omit<JobApplication, 'job_application_id' | 'user_id' | 'status' | 'messages' | 'interviews' | 'offers' | 'created_at'>> & {
  status_id?: string;
};

export type BaseResumePayload = Partial<Omit<BaseResume, 'resume_id' | 'user_id' | 'created_at' | 'updated_at'>> & {
  content?: Resume;
};

export type ContactPayload = Partial<Omit<Contact, 'user_id' | 'job_application' | 'messages' | 'strategic_narratives'>>;

export type MessagePayload = Partial<Omit<Message, 'message_id' | 'user_id' | 'created_at' | 'contact' | 'company'>>;

export type InterviewPayload = Partial<Omit<Interview, 'interview_id' | 'interview_contacts'>> & {
  contact_ids?: string[];
};

export type OfferPayload = Omit<Offer, 'offer_id' | 'user_id' | 'created_at'>;

export type LinkedInPostPayload = Omit<LinkedInPost, 'post_id' | 'user_id' | 'created_at' | 'engagements'>;

export type LinkedInEngagementPayload = Omit<LinkedInEngagement, 'engagement_id' | 'post_theme' | 'contact'>;

export type PostResponsePayload = Partial<Omit<PostResponse, 'comment_id' | 'user_id' | 'created_at'>>;

export type StrategicNarrativePayload = Partial<Omit<StrategicNarrative, 'narrative_id' | 'user_id' | 'created_at' | 'updated_at' | 'impact_stories' | 'common_interview_answers'>> & {
  impact_stories?: Omit<ImpactStory, 'story_id'>[] | ImpactStory[];
  common_interview_answers?: Omit<CommonInterviewAnswer, 'answer_id' | 'user_id' | 'narrative_id'>[];
};

export type UserProfilePayload = Partial<Omit<UserProfile, 'user_id'>>;


export type SprintActionPayload = Partial<Omit<SprintAction, 'action_id' | 'sprint_id' | 'user_id'>>;

export type CreateSprintPayload = Partial<Omit<Sprint, 'sprint_id' | 'user_id' | 'created_at' | 'start_date' | 'actions'>> & {
  actions?: SprintActionPayload[];
};

export type BragBankEntryPayload = Partial<Omit<BragBankEntry, 'entry_id' | 'user_id' | 'created_at'>>;

export type SkillTrendPayload = Omit<SkillTrend, 'skill_trend_id' | 'user_id' | 'created_at'>;

// --- Document Upload types ---
export type ContentType =
  | 'career_brand'
  | 'career_brand_full'
  | 'career_path'
  | 'job_search_strategy'
  | 'resume'
  | 'resumes'
  | 'proof_points'
  | string;

export interface DocumentMetadata {
  status?: string | null;
  is_latest?: boolean | null;
  latest_version?: boolean | null;
  job_target?: string | null;
  role_title?: string | null;
  company?: string | null;
  selected_proof_points?: string[];
  impact_tags?: string[];
  approved_by?: string | null;
  approved_at?: string | null;
  approval_notes?: string | null;
  skills?: string[];
  collection_name?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  uploaded_at?: string | null;
  [key: string]: unknown;
}

export interface UploadedDocument {
  id: string; // uuid from backend
  profile_id: string;
  title: string;
  section: string;
  content_type: ContentType;
  collection_name?: string;
  created_at: string;
  content_snippet?: string;
  chunk_count?: number;
  metadata?: DocumentMetadata;
}

export interface DocumentDetail {
  id: string;
  title: string;
  collection_name: ContentType;
  content: string;
  metadata: DocumentMetadata;
  chunk_count?: number;
  created_at?: string;
}

export interface UploadSuccessResponse {
  success: boolean;
  message: string;
  document: UploadedDocument;
}

export interface DocumentUploadPayload {
  profile_id: string;
  section: string;
  title: string;
  content: string;
  metadata?: object;
}

export interface StandardResponse<T> {
  status: 'success' | 'error' | 'warning';
  data?: T;
  error?: string | null;
  message?: string | null;
}

export interface ChromaUploadResponseData {
  success: boolean;
  message?: string | null;
  collection_name: string;
  document_id: string;
  metadata?: DocumentMetadata;
}

export interface ResumeDocumentResponseData {
  document_id: string;
  metadata: DocumentMetadata;
  message?: string | null;
}

export interface StatusTransitionPayload {
  from?: string | null;
  to: string;
  changed_at?: string;
  changed_by?: string | null;
  notes?: string | null;
}

export interface ProofPointPayload {
  profile_id: string;
  role_title: string;
  job_title?: string | null;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  company: string;
  title: string;
  content: string;
  status?: string;
  job_metadata?: Record<string, unknown> | null;
  impact_tags?: string[];
  uploaded_at?: string;
  status_transitions?: StatusTransitionPayload[];
  additional_metadata?: Record<string, unknown> | null;
}

export interface ResumeCreatePayload {
  profile_id: string;
  title: string;
  content: string;
  section?: string;
  job_target?: string | null;
  status?: string;
  selected_proof_points?: string[];
  status_transitions?: StatusTransitionPayload[];
  approved_by?: string | null;
  approved_at?: string | null;
  approval_notes?: string | null;
  version?: number | null;
  is_latest?: boolean | null;
  uploaded_at?: string;
  additional_metadata?: Record<string, unknown> | null;
}

export interface ResumeUpdatePayload {
  status?: string | null;
  selected_proof_points?: string[] | null;
  approved_by?: string | null;
  approved_at?: string | null;
  approval_notes?: string | null;
  status_transitions?: StatusTransitionPayload[] | null;
  is_latest?: boolean | null;
}

// For Reviewed Jobs View
export type ReviewedJobRecommendation = 'Recommended' | 'Not Recommended';

export interface ReviewedJob {
  job_id: string; // uuid
  url: string | null;
  title: string | null;
  company_name: string | null;
  source?: string | null;
  location: string | null;
  date_posted: string | null; // ISO date string
  recommendation: ReviewedJobRecommendation;
  confidence: number; // 0.0 to 1.0
  overall_alignment_score: number; // 0.0 to 10.0
  is_eligible_for_application: boolean;
  is_remote?: boolean | null;
  salary_min?: string | null;
  salary_max?: string | null;
  salary_currency?: string | null;
  salary_range?: string | null;
  // AI review details
  rationale?: string; // AI explanation for the recommendation
  tldr_summary?: string; // Crew AI job description TLDR from crew_output JSON
  confidence_level?: string; // 'high' | 'medium' | 'low'
  crew_output?: Record<string, unknown> | null;
  // Job description content
  description?: string | null;
  // HITL override fields
  override_recommend?: boolean | null;
  override_comment?: string | null;
  override_by?: string | null;
  override_at?: string | null; // ISO date string
}

export interface CrewOutputSource {
  dimension: string; // 'north_star' | 'trajectory_mastery' | 'values_compass' | 'lifestyle_alignment' | 'compensation_philosophy' | 'functional_match'
  score: number;
  summary: string;
}

export interface CrewOutputFinal {
  rationale: string;
  recommend: boolean;
  confidence: string;
}

export interface CrewOutput {
  sources: CrewOutputSource[];
  final?: CrewOutputFinal;
  tldr_summary?: string;
  overall_alignment_score?: number;
  [key: string]: any;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
