-- Deploy career_trainium:add_interview_copilot_columns to pg

BEGIN;

-- Add prep workspace and live note storage to interviews
ALTER TABLE public.interviews
    ADD COLUMN IF NOT EXISTS prep_outline jsonb,
    ADD COLUMN IF NOT EXISTS live_notes text;

-- Ensure legacy text column is converted to jsonb without data loss
ALTER TABLE public.interviews
    ALTER COLUMN prep_outline TYPE jsonb
    USING CASE
        WHEN prep_outline IS NULL OR prep_outline::text ~ '^\\s*$' THEN NULL::jsonb
        WHEN prep_outline::text ~ '^\\s*(\{|\[)' THEN prep_outline::jsonb
        ELSE to_jsonb(prep_outline::text)
    END;

COMMENT ON COLUMN public.interviews.prep_outline IS 'Structured prep workspace data capturing role intelligence, JD insights, and other research notes prior to the interview.';
COMMENT ON COLUMN public.interviews.live_notes IS 'Free-form notes captured during the live interview experience without overwriting the prep workspace.';

-- Persist story deck ordering notes on interview records and return them from a single function call
CREATE OR REPLACE FUNCTION public.save_interview_with_contacts(
    p_interview_id uuid,
    p_job_application_id uuid,
    p_interview_date timestamptz,
    p_interview_type text,
    p_notes text,
    p_ai_prep_data jsonb,
    p_prep_outline jsonb,
    p_live_notes text,
    p_contact_ids uuid[]
)
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
AS $function$
    WITH upserted AS (
        INSERT INTO interviews (
            interview_id,
            job_application_id,
            interview_date,
            interview_type,
            notes,
            ai_prep_data,
            prep_outline,
            live_notes
        )
        VALUES (
            COALESCE(p_interview_id, gen_random_uuid()),
            p_job_application_id,
            p_interview_date,
            p_interview_type,
            p_notes,
            p_ai_prep_data,
            p_prep_outline,
            p_live_notes
        )
        ON CONFLICT (interview_id) DO UPDATE SET
            job_application_id = EXCLUDED.job_application_id,
            interview_date = EXCLUDED.interview_date,
            interview_type = EXCLUDED.interview_type,
            notes = EXCLUDED.notes,
            ai_prep_data = EXCLUDED.ai_prep_data,
            prep_outline = EXCLUDED.prep_outline,
            live_notes = EXCLUDED.live_notes
        RETURNING *
    ),
    deleted_contacts AS (
        DELETE FROM public.interview_contacts ic
        USING upserted u
        WHERE ic.interview_id = u.interview_id
        RETURNING 1
    ),
    inserted_contacts AS (
        INSERT INTO public.interview_contacts (interview_id, contact_id)
        SELECT u.interview_id, contact_id
        FROM upserted u
        CROSS JOIN LATERAL unnest(COALESCE(p_contact_ids, '{}')) AS c(contact_id)
        ON CONFLICT (interview_id, contact_id) DO NOTHING
        RETURNING 1
    )
    SELECT
        u.interview_id,
        u.job_application_id,
        u.interview_date,
        u.interview_type,
        u.notes,
        u.created_at,
        u.ai_prep_data,
        u.prep_outline,
        u.live_notes,
        u.strategic_plan,
        u.post_interview_debrief,
        u.strategic_opening,
        u.strategic_questions_to_ask,
        COALESCE(
            (
                SELECT jsonb_agg(jsonb_build_object(
                    'story_id', d.story_id,
                    'order_index', d.order_index,
                    'custom_notes', d.custom_notes
                ) ORDER BY d.order_index)
                FROM public.interview_story_decks d
                WHERE d.interview_id = u.interview_id
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
                WHERE ic.interview_id = u.interview_id
            ),
            '[]'::jsonb
        ) AS interview_contacts
    FROM upserted u;
$function$;

-- Expose full interview decks, prep outline, and live notes from a single RPC
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
        i.prep_outline::jsonb,
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
        ) AS interview_contacts
    -- Source interviews for the given application; alias i is referenced above.
    FROM public.interviews i
    WHERE i.job_application_id = p_job_application_id
    ORDER BY i.interview_date NULLS LAST, i.created_at DESC;
$function$;

-- Allow upserting interviews while maintaining associated contacts
CREATE OR REPLACE FUNCTION public.upsert_interview_with_contacts(
    p_job_application_id uuid,
    p_interview_type text,
    p_interview_id uuid DEFAULT NULL::uuid,
    p_interview_date timestamptz DEFAULT NULL::timestamptz,
    p_notes text DEFAULT NULL::text,
    p_ai_prep_data jsonb DEFAULT NULL::jsonb,
    p_prep_outline jsonb DEFAULT NULL::jsonb,
    p_live_notes text DEFAULT NULL::text,
    p_contact_ids uuid[] DEFAULT '{}'::uuid[]
)
RETURNS SETOF interviews
LANGUAGE plpgsql
AS $function$
DECLARE
    v_interview_id uuid;
BEGIN
    INSERT INTO interviews (
        interview_id,
        job_application_id,
        interview_date,
        interview_type,
        notes,
        ai_prep_data,
        prep_outline,
        live_notes
    )
    VALUES (
        COALESCE(p_interview_id, uuid_generate_v4()),
        p_job_application_id,
        p_interview_date,
        p_interview_type,
        p_notes,
        p_ai_prep_data,
        p_prep_outline,
        p_live_notes
    )
    ON CONFLICT (interview_id)
    DO UPDATE SET
        job_application_id = EXCLUDED.job_application_id,
        interview_date = EXCLUDED.interview_date,
        interview_type = EXCLUDED.interview_type,
        notes = EXCLUDED.notes,
        ai_prep_data = EXCLUDED.ai_prep_data,
        prep_outline = EXCLUDED.prep_outline,
        live_notes = EXCLUDED.live_notes
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

COMMIT;
