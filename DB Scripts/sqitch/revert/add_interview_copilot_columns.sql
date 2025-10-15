-- Revert career_trainium:add_interview_copilot_columns from pg

BEGIN;

ALTER TABLE public.interviews
    DROP COLUMN IF EXISTS widget_metadata,
    DROP COLUMN IF EXISTS widgets,
    DROP COLUMN IF EXISTS layout;

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
