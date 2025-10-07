BEGIN;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Schema: public is created by default, ensure comments
COMMENT ON SCHEMA public IS 'standard public schema';

-- statuses table
CREATE TABLE public.statuses (
    status_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    status_name text NOT NULL,
    CONSTRAINT statuses_pkey PRIMARY KEY (status_id),
    CONSTRAINT statuses_status_name_key UNIQUE (status_name)
);

-- users table
CREATE TABLE public.users (
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    first_name text,
    last_name text,
    email text,
    phone_number text,
    city text,
    state text,
    links text[],
    username text,
    profile_image_url text,
    timezone text,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (user_id),
    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT users_username_key UNIQUE (username)
);

-- companies table
CREATE TABLE public.companies (
    company_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    company_name text NOT NULL,
    mission jsonb,
    "values" jsonb,
    news jsonb,
    goals jsonb,
    issues jsonb,
    customer_segments jsonb,
    strategic_initiatives jsonb,
    market_position jsonb,
    competitors jsonb,
    is_recruiting_firm bool DEFAULT false,
    industry jsonb,
    company_url text,
    user_id uuid NOT NULL,
    CONSTRAINT companies_pkey PRIMARY KEY (company_id),
    CONSTRAINT companies_company_name_key UNIQUE (company_name),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE
);

-- resumes table
CREATE TABLE public.resumes (
    resume_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    resume_name text NOT NULL,
    summary_paragraph text,
    summary_bullets jsonb DEFAULT '[]'::jsonb,
    is_default bool DEFAULT false,
    visibility text DEFAULT 'private',
    created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_by uuid,
    is_locked bool DEFAULT false,
    CONSTRAINT resumes_pkey PRIMARY KEY (resume_id),
    CONSTRAINT resumes_visibility_check CHECK (visibility = ANY (ARRAY['private','public','shared'])),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE,
    CONSTRAINT resumes_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id),
    CONSTRAINT resumes_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id)
);
CREATE INDEX idx_resumes_user_id ON public.resumes USING btree (user_id);

-- strategic_narratives table
CREATE TABLE public.strategic_narratives (
    narrative_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    narrative_name text NOT NULL,
    desired_title text NOT NULL,
    positioning_statement text,
    signature_capability text,
    impact_story_title text,
    impact_story_body text,
    default_resume_id uuid,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    desired_industry text,
    desired_company_stage text,
    mission_alignment text,
    long_term_legacy text,
    key_strengths jsonb,
    representative_metrics jsonb,
    leadership_style text,
    communication_style text,
    working_preferences jsonb,
    preferred_locations jsonb,
    relocation_open bool,
    compensation_expectation text,
    impact_stories jsonb,
    CONSTRAINT strategic_narratives_pkey PRIMARY KEY (narrative_id),
    CONSTRAINT fk_default_resume FOREIGN KEY (default_resume_id) REFERENCES public.resumes(resume_id) ON DELETE SET NULL,
    CONSTRAINT strategic_narratives_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE
);
CREATE INDEX idx_strategic_narratives_user_id ON public.strategic_narratives USING btree (user_id);

COMMENT ON COLUMN public.strategic_narratives.positioning_statement IS 'The core one-sentence professional brand statement.';
COMMENT ON COLUMN public.strategic_narratives.signature_capability IS 'A unique, memorable professional capability.';
COMMENT ON COLUMN public.strategic_narratives.impact_story_title IS 'A short, compelling title for the main impact story.';
COMMENT ON COLUMN public.strategic_narratives.impact_story_body IS 'The full text of the impact story, often using the STAR method.';
COMMENT ON COLUMN public.strategic_narratives.default_resume_id IS 'The resume_id of the resume formula to be used by default for this narrative.';
COMMENT ON COLUMN public.strategic_narratives.desired_industry IS 'Target industry for this narrative (e.g., FinTech, HealthTech).';
COMMENT ON COLUMN public.strategic_narratives.desired_company_stage IS 'Ideal company stage (e.g., early-stage, growth, enterprise).';
COMMENT ON COLUMN public.strategic_narratives.mission_alignment IS 'Statement on what kind of work is energizing.';
COMMENT ON COLUMN public.strategic_narratives.long_term_legacy IS 'What the user wants to be remembered for in their next role.';
COMMENT ON COLUMN public.strategic_narratives.key_strengths IS 'A JSON array of key professional strengths.';
COMMENT ON COLUMN public.strategic_narratives.representative_metrics IS 'A JSON array of key metrics that represent success.';
COMMENT ON COLUMN public.strategic_narratives.leadership_style IS 'Description of the user''s leadership approach.';
COMMENT ON COLUMN public.strategic_narratives.communication_style IS 'Description of the user''s communication style.';
COMMENT ON COLUMN public.strategic_narratives.working_preferences IS 'A JSON array of preferred working styles or environments.';
COMMENT ON COLUMN public.strategic_narratives.preferred_locations IS 'A JSON array of preferred work locations.';
COMMENT ON COLUMN public.strategic_narratives.relocation_open IS 'Whether the user is open to relocation.';
COMMENT ON COLUMN public.strategic_narratives.compensation_expectation IS 'User''s salary and compensation expectations.';
COMMENT ON COLUMN public.strategic_narratives.impact_stories IS 'Stores an array of structured Core Stories, each including a title, target questions, body (STAR format), and speaker notes.';

-- weekly_sprints table
CREATE TABLE public.weekly_sprints (
    sprint_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    theme text NOT NULL,
    start_date date NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    mode text DEFAULT 'search',
    learning_goal text,
    cross_functional_collaboration text,
    growth_alignment text,
    promotion_readiness_notes text,
    tags text[],
    strategic_score numeric(3,1),
    CONSTRAINT daily_sprints_pk PRIMARY KEY (sprint_id),
    CONSTRAINT weekly_sprints_mode_check CHECK (mode = ANY (ARRAY['search','career'])),
    CONSTRAINT weekly_sprints_strategic_value_score_check CHECK (strategic_score >= 0 AND strategic_score <= 10),
    CONSTRAINT weekly_sprints_user_id_start_date_key UNIQUE (user_id, start_date),
    CONSTRAINT weekly_sprints_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE
);
CREATE INDEX idx_weekly_sprints_user_mode ON public.weekly_sprints USING btree (user_id, mode);
CREATE INDEX idx_weekly_sprints_user_tags ON public.weekly_sprints USING gin (tags);

-- common_interview_answers table
CREATE TABLE public.common_interview_answers (
    answer_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    question text NOT NULL,
    answer text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    speaker_notes text,
    narrative_id uuid,
    CONSTRAINT common_interview_answers_pkey PRIMARY KEY (answer_id),
    CONSTRAINT fk_common_answers_narrative FOREIGN KEY (narrative_id) REFERENCES public.strategic_narratives(narrative_id) ON DELETE SET NULL
);
CREATE INDEX idx_common_interview_answers_user_id ON public.common_interview_answers USING btree (user_id);

-- job_applications table
CREATE TABLE public.job_applications (
    job_application_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    company_id uuid,
    status_id uuid,
    job_title text NOT NULL,
    job_description text NOT NULL,
    job_link text,
    salary text,
    "location" text,
    remote_status text,
    date_applied date,
    created_at timestamptz DEFAULT now(),
    ai_summary text,
    job_problem_analysis_result jsonb,
    keywords jsonb,
    guidance jsonb,
    resume_summary text,
    resume_summary_bullets text,
    tailored_resume_json jsonb,
    application_questions jsonb,
    referral_target_suggestion text,
    strategic_fit_score int,
    assumed_requirements jsonb,
    initial_interview_prep jsonb,
    keyword_coverage_score numeric,
    next_steps_plan text,
    post_submission_summary text,
    why_this_job text,
    narrative_id uuid NOT NULL,
    user_id uuid NOT NULL,
    first_90_day_plan jsonb,
    application_message text,
    CONSTRAINT job_applications_pkey PRIMARY KEY (job_application_id),
    CONSTRAINT fk_job_applications_narrative FOREIGN KEY (narrative_id) REFERENCES public.strategic_narratives(narrative_id) ON DELETE SET NULL,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE,
    CONSTRAINT job_applications_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(company_id) ON DELETE SET NULL,
    CONSTRAINT job_applications_status_id_fkey FOREIGN KEY (status_id) REFERENCES public.statuses(status_id) ON DELETE SET NULL
);
CREATE INDEX idx_job_applications_company_id ON public.job_applications USING btree (company_id);
CREATE INDEX idx_job_applications_status_id ON public.job_applications USING btree (status_id);
COMMENT ON COLUMN public.job_applications.first_90_day_plan IS 'Stores the AI-generated 30-60-90 day plan upon accepting an offer.';

-- linkedin_posts table
CREATE TABLE public.linkedin_posts (
    post_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    theme text NOT NULL,
    "content" text NOT NULL,
    created_at timestamptz DEFAULT now(),
    variant text,
    tags text[],
    narrative_id uuid,
    user_id uuid NOT NULL,
    narrative_focus text,
    CONSTRAINT linkedin_posts_pkey PRIMARY KEY (post_id),
    CONSTRAINT fk_linkedin_posts_narrative FOREIGN KEY (narrative_id) REFERENCES public.strategic_narratives(narrative_id) ON DELETE SET NULL,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE
);
COMMENT ON COLUMN public.linkedin_posts.narrative_id IS 'Foreign key to the strategic narrative this post supports. Can be NULL for "Document the Journey" posts.';

-- offers table
CREATE TABLE public.offers (
    offer_id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_application_id uuid NOT NULL,
    user_id uuid NOT NULL,
    company_name text NOT NULL,
    job_title text NOT NULL,
    base_salary numeric,
    bonus_potential text,
    equity_details text,
    benefits_summary text,
    deadline date,
    status text DEFAULT 'Received' NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT offers_pkey PRIMARY KEY (offer_id),
    CONSTRAINT offers_job_application_id_fkey FOREIGN KEY (job_application_id) REFERENCES public.job_applications(job_application_id) ON DELETE SET NULL,
    CONSTRAINT offers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE
);
COMMENT ON TABLE public.offers IS 'Stores details of job offers received for applications.';
COMMENT ON COLUMN public.offers.status IS 'The current status of the offer negotiation process.';

-- post_responses table
CREATE TABLE public.post_responses (
    comment_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    post_id uuid,
    comment_text text,
    ai_analysis jsonb,
    created_at timestamptz DEFAULT now(),
    post_excerpt text NOT NULL,
    conversation jsonb,
    user_id uuid NOT NULL,
    CONSTRAINT post_responses_pkey PRIMARY KEY (comment_id),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE,
    CONSTRAINT post_responses_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.linkedin_posts(post_id) ON DELETE CASCADE
);

-- resume_certifications table
CREATE TABLE public.resume_certifications (
    certification_id uuid DEFAULT gen_random_uuid() NOT NULL,
    resume_id uuid,
    "name" text,
    organization text,
    issued_date date,
    expiration_date date,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    link text,
    CONSTRAINT resume_certifications_pkey PRIMARY KEY (certification_id),
    CONSTRAINT resume_certifications_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(resume_id) ON DELETE CASCADE
);

-- resume_education table
CREATE TABLE public.resume_education (
    education_id uuid DEFAULT gen_random_uuid() NOT NULL,
    resume_id uuid,
    school text,
    "degree" text,
    major text[],
    minor text[],
    start_year smallint,
    start_month smallint,
    end_year smallint,
    end_month smallint,
    "location" text,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT resume_education_pkey PRIMARY KEY (education_id),
    CONSTRAINT resume_education_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(resume_id) ON DELETE CASCADE
);

-- resume_skill_sections table
CREATE TABLE public.resume_skill_sections (
    skill_section_id uuid DEFAULT gen_random_uuid() NOT NULL,
    resume_id uuid,
    heading text NOT NULL,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT resume_skill_sections_pkey PRIMARY KEY (skill_section_id),
    CONSTRAINT resume_skill_sections_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(resume_id) ON DELETE CASCADE
);

-- resume_work_experience table
CREATE TABLE public.resume_work_experience (
    work_experience_id uuid DEFAULT gen_random_uuid() NOT NULL,
    resume_id uuid,
    company_name text,
    job_title text,
    "location" text,
    start_date date,
    end_date date,
    is_current bool DEFAULT false,
    is_deleted bool DEFAULT false,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    filter_accomplishment_count int4 DEFAULT 0,
    CONSTRAINT resume_work_experience_pkey PRIMARY KEY (work_experience_id),
    CONSTRAINT resume_work_experience_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(resume_id) ON DELETE CASCADE
);

-- skill_trends table
CREATE TABLE public.skill_trends (
    trend_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    narrative_id uuid NOT NULL,
    skill text NOT NULL,
    demand_score int,
    trend_direction text,
    checked_at date DEFAULT CURRENT_DATE NOT NULL,
    learning_resources jsonb,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT skill_trends_pkey PRIMARY KEY (trend_id),
    CONSTRAINT skill_trends_narrative_id_fkey FOREIGN KEY (narrative_id) REFERENCES public.strategic_narratives(narrative_id) ON DELETE CASCADE,
    CONSTRAINT skill_trends_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE
);
COMMENT ON TABLE public.skill_trends IS 'Stores historical skill trend data from the AI-powered skill radar.';

-- sprint_actions table
CREATE TABLE public.sprint_actions (
    action_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    sprint_id uuid NOT NULL,
    job_application_id uuid,
    action_type text,
    title text,
    details text,
    is_completed bool DEFAULT false NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    is_goal bool DEFAULT false,
    goal_type text,
    goal_target int,
    impact text,
    effort_estimate text,
    strategic_tags text[],
    measurable_value text,
    description text,
    order_index int,
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    CONSTRAINT sprint_actions_pkey PRIMARY KEY (action_id),
    CONSTRAINT sprint_actions_sprint_id_fkey FOREIGN KEY (sprint_id) REFERENCES public.weekly_sprints(sprint_id) ON DELETE CASCADE,
    CONSTRAINT sprint_actions_job_application_id_fkey FOREIGN KEY (job_application_id) REFERENCES public.job_applications(job_application_id) ON DELETE SET NULL,
    CONSTRAINT fk_sprint_actions_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE
);
CREATE INDEX idx_sprint_actions_user_tags ON public.sprint_actions USING gin (strategic_tags);

-- standard_job_roles table
CREATE TABLE public.standard_job_roles (
    role_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    role_title text NOT NULL,
    role_description text,
    skills_required jsonb,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    narrative_id uuid NOT NULL,
    CONSTRAINT standard_job_roles_pkey PRIMARY KEY (role_id),
    CONSTRAINT standard_job_roles_title_key UNIQUE (role_title),
    CONSTRAINT fk_narrative FOREIGN KEY (narrative_id) REFERENCES public.strategic_narratives(narrative_id) ON DELETE CASCADE
);

-- brag_bank_entries table
CREATE TABLE public.brag_bank_entries (
    entry_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    action_id uuid,
    title text NOT NULL,
    description text,
    tags text[],
    source_context text,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT brag_bank_entries_pkey PRIMARY KEY (entry_id),
    CONSTRAINT brag_bank_entries_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.sprint_actions(action_id) ON DELETE SET NULL,
    CONSTRAINT brag_bank_entries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE
);

-- contacts table
CREATE TABLE public.contacts (
    contact_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    first_name text NOT NULL,
    last_name text NOT NULL,
    job_title text,
    company_id uuid,
    job_application_id uuid,
    linkedin_url text,
    email text,
    status text NOT NULL,
    is_referral bool DEFAULT false,
    date_contacted date,
    notes text,
    created_at timestamptz DEFAULT now(),
    persona text,
    strategic_alignment_score numeric DEFAULT 0,
    linkedin_about text,
    user_id uuid NOT NULL,
    CONSTRAINT contacts_pkey PRIMARY KEY (contact_id),
    CONSTRAINT contacts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(company_id) ON DELETE SET NULL,
    CONSTRAINT contacts_job_application_id_fkey FOREIGN KEY (job_application_id) REFERENCES public.job_applications(job_application_id) ON DELETE SET NULL,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE
);
CREATE INDEX idx_contacts_company_id ON public.contacts USING btree (company_id);
CREATE INDEX idx_contacts_job_application_id ON public.contacts USING btree (job_application_id);

-- interviews table
CREATE TABLE public.interviews (
    interview_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    job_application_id uuid NOT NULL,
    interview_date timestamptz,
    interview_type text NOT NULL,
    notes text,
    created_at timestamptz DEFAULT now(),
    ai_prep_data jsonb,
    strategic_plan jsonb,
    post_interview_debrief jsonb,
    strategic_opening text,
    strategic_questions_to_ask jsonb,
    CONSTRAINT interviews_pkey PRIMARY KEY (interview_id),
    CONSTRAINT interviews_job_application_id_fkey FOREIGN KEY (job_application_id) REFERENCES public.job_applications(job_application_id) ON DELETE CASCADE
);
CREATE INDEX idx_interviews_job_application_id ON public.interviews USING btree (job_application_id);
COMMENT ON COLUMN public.interviews.strategic_plan IS 'Stores the AI-generated consultative close plan, including the 30-60-90 day plan and briefing email.';
COMMENT ON COLUMN public.interviews.post_interview_debrief IS 'Stores the user''s post-interview notes (wins, fumbles, new intelligence) and the AI-generated strategic follow-up.';
COMMENT ON COLUMN public.interviews.strategic_opening IS 'Stores the user-customized strategic opening for a specific interview, to be displayed in the Co-pilot view.';
COMMENT ON COLUMN public.interviews.strategic_questions_to_ask IS 'Stores the AI-generated strategic questions for the user to ask during an interview (for the Co-pilot view).';

-- interview_story_decks table
CREATE TABLE public.interview_story_decks (
    interview_id uuid NOT NULL,
    story_id uuid NOT NULL,
    order_index int4 NOT NULL,
    custom_notes jsonb,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT interview_story_decks_pkey PRIMARY KEY (interview_id, story_id),
    CONSTRAINT interview_story_decks_interview_id_fkey FOREIGN KEY (interview_id) REFERENCES public.interviews(interview_id) ON DELETE CASCADE
);
CREATE INDEX idx_interview_story_decks_interview_order ON public.interview_story_decks USING btree (interview_id, order_index);
COMMENT ON COLUMN public.interview_story_decks.custom_notes IS 'Optional JSON structure holding per-role speaker note tweaks for a specific interview story deck entry.';

-- messages table
CREATE TABLE public.messages (
    message_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    contact_id uuid,
    job_application_id uuid,
    message_type text NOT NULL,
    "content" text NOT NULL,
    follow_up_due_date date,
    created_at timestamptz DEFAULT now(),
    company_id uuid,
    response_received bool DEFAULT false,
    message_variant text,
    ai_analysis jsonb,
    response_timestamp timestamptz,
    variant text,
    is_user_sent bool,
    user_id uuid NOT NULL,
    CONSTRAINT chk_parent_exists CHECK ((contact_id IS NOT NULL) OR (job_application_id IS NOT NULL) OR (company_id IS NOT NULL)),
    CONSTRAINT messages_pkey PRIMARY KEY (message_id),
    CONSTRAINT fk_messages_to_companies FOREIGN KEY (company_id) REFERENCES public.companies(company_id) ON DELETE SET NULL,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE,
    CONSTRAINT messages_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(contact_id) ON DELETE CASCADE,
    CONSTRAINT messages_job_application_id_fkey FOREIGN KEY (job_application_id) REFERENCES public.job_applications(job_application_id) ON DELETE CASCADE
);
CREATE INDEX idx_messages_contact_id ON public.messages USING btree (contact_id);
CREATE INDEX idx_messages_job_application_id ON public.messages USING btree (job_application_id);
COMMENT ON COLUMN public.messages.company_id IS 'Foreign key to the companies table for company-level engagement messages.';
COMMENT ON CONSTRAINT chk_parent_exists ON public.messages IS 'Ensures that every message is associated with at least one parent (a contact, an application, or a company).';

-- networking_suggestions table
CREATE TABLE public.networking_suggestions (
    suggestion_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    contact_id uuid NOT NULL,
    suggestion_type text NOT NULL,
    suggestion_text text NOT NULL,
    context_url text,
    context_title text,
    status text DEFAULT 'new' NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT networking_suggestions_pkey PRIMARY KEY (suggestion_id),
    CONSTRAINT networking_suggestions_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(contact_id) ON DELETE CASCADE,
    CONSTRAINT networking_suggestions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE
);
COMMENT ON TABLE public.networking_suggestions IS 'Stores AI-generated suggestions for proactive networking.';

-- post_engagements table
CREATE TABLE public.post_engagements (
    engagement_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    post_id uuid NOT NULL,
    engagement_type text NOT NULL,
    comment_text text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_by uuid,
    contact_name text NOT NULL,
    contact_title text,
    "content" text,
    contact_linkedin_url text,
    notes text,
    post_theme text,
    user_id uuid,
    strategic_score numeric(3,1),
    contact_id uuid,
    CONSTRAINT post_engagements_pkey PRIMARY KEY (engagement_id),
    CONSTRAINT fk_post_engagements_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE SET NULL,
    CONSTRAINT post_engagements_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(contact_id) ON DELETE SET NULL,
    CONSTRAINT post_engagements_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.linkedin_posts(post_id) ON DELETE CASCADE
);
COMMENT ON COLUMN public.post_engagements.strategic_score IS 'An AI-generated score (0-10) indicating the strategic value of this engagement.';

-- resume_accomplishments table
CREATE TABLE public.resume_accomplishments (
    accomplishment_id uuid DEFAULT gen_random_uuid() NOT NULL,
    work_experience_id uuid,
    description text NOT NULL,
    original_description text,
    ai_optimize bool DEFAULT false,
    always_include bool DEFAULT false,
    score jsonb,
    themes text[],
    order_index int4 DEFAULT 0,
    is_deleted bool DEFAULT false,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT resume_accomplishments_pkey PRIMARY KEY (accomplishment_id),
    CONSTRAINT resume_accomplishments_work_experience_id_fkey FOREIGN KEY (work_experience_id) REFERENCES public.resume_work_experience(work_experience_id) ON DELETE CASCADE
);

-- resume_skill_items table
CREATE TABLE public.resume_skill_items (
    skill_item_id uuid DEFAULT gen_random_uuid() NOT NULL,
    skill_section_id uuid,
    item_text text NOT NULL,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT resume_skill_items_pkey PRIMARY KEY (skill_item_id),
    CONSTRAINT resume_skill_items_skill_section_id_item_text_key UNIQUE (skill_section_id, item_text),
    CONSTRAINT resume_skill_items_skill_section_id_fkey FOREIGN KEY (skill_section_id) REFERENCES public.resume_skill_sections(skill_section_id) ON DELETE CASCADE
);

-- contact_narratives table
CREATE TABLE public.contact_narratives (
    contact_id uuid NOT NULL,
    narrative_id uuid NOT NULL,
    CONSTRAINT contact_narratives_pkey PRIMARY KEY (contact_id, narrative_id),
    CONSTRAINT contact_narratives_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(contact_id) ON DELETE CASCADE,
    CONSTRAINT contact_narratives_narrative_id_fkey FOREIGN KEY (narrative_id) REFERENCES public.strategic_narratives(narrative_id) ON DELETE CASCADE
);

-- interview_contacts table
CREATE TABLE public.interview_contacts (
    interview_contact_id uuid DEFAULT uuid_generate_v4() NOT NULL,
    interview_id uuid NOT NULL,
    contact_id uuid NOT NULL,
    created_at timestamptz DEFAULT now(),
    ai_interviewer_analysis jsonb,
    CONSTRAINT interview_contacts_interview_id_contact_id_key UNIQUE (interview_id, contact_id),
    CONSTRAINT interview_contacts_pkey PRIMARY KEY (interview_contact_id),
    CONSTRAINT interview_contacts_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(contact_id) ON DELETE CASCADE,
    CONSTRAINT interview_contacts_interview_id_fkey FOREIGN KEY (interview_id) REFERENCES public.interviews(interview_id) ON DELETE CASCADE
);
COMMENT ON COLUMN public.interview_contacts.ai_interviewer_analysis IS 'Stores the AI-generated persona analysis and strategic insights for a specific interviewer in the context of one interview.';

-- Functions

CREATE OR REPLACE FUNCTION public.create_sprint_with_actions(p_user_id uuid, p_theme text, p_start_date date, p_actions jsonb)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
    new_sprint_id uuid;
    action jsonb;
BEGIN
    INSERT INTO public.weekly_sprints (user_id, theme, start_date)
    VALUES (p_user_id, p_theme, p_start_date)
    RETURNING sprint_id INTO new_sprint_id;

    FOR action IN SELECT * FROM jsonb_array_elements(p_actions)
    LOOP
        INSERT INTO public.sprint_actions (
            sprint_id,
            action_type,
            title,
            details,
            is_completed
        )
        VALUES (
            new_sprint_id,
            action->>'action_type',
            action->>'title',
            action->>'details',
            COALESCE((action->>'is_completed')::boolean, false)
        );
    END LOOP;

    RETURN new_sprint_id;
END;
$function$;

CREATE OR REPLACE FUNCTION public.save_interview_with_contacts(p_interview_id uuid, p_job_application_id uuid, p_interview_date timestamptz, p_interview_type text, p_notes text, p_ai_prep_data jsonb, p_contact_ids uuid[])
RETURNS interviews
LANGUAGE plpgsql
AS $function$
DECLARE
    saved_interview interviews;
BEGIN
    INSERT INTO interviews (interview_id, job_application_id, interview_date, interview_type, notes, ai_prep_data)
    VALUES (COALESCE(p_interview_id, gen_random_uuid()), p_job_application_id, p_interview_date, p_interview_type, p_notes, p_ai_prep_data)
    ON CONFLICT (interview_id)
    DO UPDATE SET
        job_application_id = EXCLUDED.job_application_id,
        interview_date = EXCLUDED.interview_date,
        interview_type = EXCLUDED.interview_type,
        notes = EXCLUDED.notes,
        ai_prep_data = EXCLUDED.ai_prep_data
    RETURNING * INTO saved_interview;

    DELETE FROM interview_contacts WHERE interview_id = saved_interview.interview_id;

    IF p_contact_ids IS NOT NULL THEN
        INSERT INTO interview_contacts (interview_id, contact_id)
        SELECT saved_interview.interview_id, unnest(p_contact_ids);
    END IF;

    RETURN saved_interview;
END;
$function$;

CREATE OR REPLACE FUNCTION public.get_interviews_with_deck(p_job_application_id uuid)
RETURNS TABLE (
    interview_id uuid,
    job_application_id uuid,
    interview_date timestamptz,
    interview_type text,
    notes text,
    created_at timestamptz,
    ai_prep_data jsonb,
    strategic_plan jsonb,
    post_interview_debrief jsonb,
    strategic_opening text,
    strategic_questions_to_ask jsonb,
    story_deck jsonb,
    interview_contacts jsonb
)
LANGUAGE sql
STABLE
AS $function$
    SELECT
        i.interview_id,
        i.job_application_id,
        i.interview_date,
        i.interview_type,
        i.notes,
        i.created_at,
        i.ai_prep_data,
        i.strategic_plan,
        i.post_interview_debrief,
        i.strategic_opening,
        i.strategic_questions_to_ask,
        COALESCE(
            (
                SELECT jsonb_agg(jsonb_build_object(
                    'story_id', d.story_id,
                    'order_index', d.order_index,
                    'custom_notes', d.custom_notes
                ) ORDER BY d.order_index)
                FROM public.interview_story_decks d
                WHERE d.interview_id = i.interview_id
            ),
            '[]'::jsonb
        ) AS story_deck,
        COALESCE(
            (
                SELECT jsonb_agg(jsonb_build_object(
                    'contact_id', c.contact_id,
                    'first_name', c.first_name,
                    'last_name', c.last_name
                ) ORDER BY c.first_name, c.last_name)
                FROM public.interview_contacts ic
                JOIN public.contacts c ON c.contact_id = ic.contact_id
                WHERE ic.interview_id = i.interview_id
            ),
            '[]'::jsonb
        ) AS interview_contacts
    FROM public.interviews i
    WHERE i.job_application_id = p_job_application_id
    ORDER BY i.interview_date NULLS LAST, i.created_at DESC;
$function$;

CREATE OR REPLACE FUNCTION public.update_timestamp()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.upsert_interview_with_contacts(p_job_application_id uuid, p_interview_type text, p_interview_id uuid DEFAULT NULL::uuid, p_interview_date timestamptz DEFAULT NULL::timestamptz, p_notes text DEFAULT NULL::text, p_ai_prep_data jsonb DEFAULT NULL::jsonb, p_contact_ids uuid[] DEFAULT '{}'::uuid[])
RETURNS SETOF interviews
LANGUAGE plpgsql
AS $function$
DECLARE
    v_interview_id uuid;
BEGIN
    INSERT INTO interviews (interview_id, job_application_id, interview_date, interview_type, notes, ai_prep_data)
    VALUES (COALESCE(p_interview_id, uuid_generate_v4()), p_job_application_id, p_interview_date, p_interview_type, p_notes, p_ai_prep_data)
    ON CONFLICT (interview_id)
    DO UPDATE SET
        job_application_id = EXCLUDED.job_application_id,
        interview_date = EXCLUDED.interview_date,
        interview_type = EXCLUDED.interview_type,
        notes = EXCLUDED.notes,
        ai_prep_data = EXCLUDED.ai_prep_data
    RETURNING interviews.interview_id INTO v_interview_id;

    IF p_contact_ids IS NOT NULL THEN
        DELETE FROM interview_contacts
        WHERE interview_id = v_interview_id AND NOT (contact_id = ANY(p_contact_ids));

        INSERT INTO interview_contacts (interview_id, contact_id)
        SELECT v_interview_id, unnest_contact_id
        FROM unnest(p_contact_ids) AS unnest_contact_id
        ON CONFLICT (interview_id, contact_id) DO NOTHING;
    ELSE
        DELETE FROM interview_contacts WHERE interview_id = v_interview_id;
    END IF;

    RETURN QUERY SELECT * FROM interviews WHERE interview_id = v_interview_id;
END;
$function$;

-- Triggers
CREATE TRIGGER set_timestamp_users BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER set_timestamp_resumes BEFORE UPDATE ON public.resumes FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER set_timestamp_resume_certifications BEFORE UPDATE ON public.resume_certifications FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER set_timestamp_resume_education BEFORE UPDATE ON public.resume_education FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER set_timestamp_resume_skill_sections BEFORE UPDATE ON public.resume_skill_sections FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER set_timestamp_resume_work_experience BEFORE UPDATE ON public.resume_work_experience FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER set_timestamp_resume_accomplishments BEFORE UPDATE ON public.resume_accomplishments FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER set_timestamp_post_engagements BEFORE UPDATE ON public.post_engagements FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER set_timestamp_interview_story_decks BEFORE UPDATE ON public.interview_story_decks FOR EACH ROW EXECUTE FUNCTION update_timestamp();

COMMIT;
