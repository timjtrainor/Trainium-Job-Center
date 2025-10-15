-- Deploy career_trainium:add_interview_copilot_columns to pg

BEGIN;

ALTER TABLE public.interviews
    ADD COLUMN IF NOT EXISTS layout jsonb DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS widgets jsonb DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS widget_metadata jsonb DEFAULT '{}'::jsonb;

COMMENT ON COLUMN public.interviews.layout IS 'Responsive grid layout configuration for Interview Co-pilot widgets.';
COMMENT ON COLUMN public.interviews.widgets IS 'Serialized widget data payloads captured from the Interview Co-pilot experience.';
COMMENT ON COLUMN public.interviews.widget_metadata IS 'Per-widget UI metadata (collapse state, sizing hints) for Interview Co-pilot sessions.';

CREATE OR REPLACE FUNCTION public.get_interviews_with_deck(p_job_application_id uuid)
RETURNS TABLE (
    interview_id uuid,
    job_application_id uuid,
    interview_date timestamptz,
    interview_type text,
    notes text,
    created_at timestamptz,
    ai_prep_data jsonb,
    prep_outline jsonb,
    live_notes text,
    strategic_plan jsonb,
    post_interview_debrief jsonb,
    strategic_opening text,
    strategic_questions_to_ask jsonb,
    layout jsonb,
    widgets jsonb,
    widget_metadata jsonb,
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
        i.prep_outline,
        i.live_notes,
        i.strategic_plan,
        i.post_interview_debrief,
        i.strategic_opening,
        i.strategic_questions_to_ask,
        i.layout,
        i.widgets,
        i.widget_metadata,
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
        ) AS interview_contacts;
$function$;

COMMIT;
