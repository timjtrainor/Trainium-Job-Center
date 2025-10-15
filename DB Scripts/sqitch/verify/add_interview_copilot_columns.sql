-- Verify career_trainium:add_interview_copilot_columns on pg

BEGIN;

-- Verify new columns exist
SELECT layout, widgets, widget_metadata FROM public.interviews LIMIT 0;

-- Verify the function exposes the new columns
SELECT layout, widgets, widget_metadata
FROM public.get_interviews_with_deck('00000000-0000-0000-0000-000000000000'::uuid)
LIMIT 0;

ROLLBACK;
