-- Revert backfill_application_missing_data from pg

BEGIN;

-- Note: This migration is non-destructive (backfill only adds missing data)
-- No true revert needed - the original empty/null values are not recoverable
-- but this placeholder ensures Sqitch migration tracking consistency

DO $$
BEGIN
    RAISE NOTICE 'Backfill migration reverted - note that backfilled data remains in place';
    RAISE NOTICE 'No automatic removal of backfilled data (original empty values not stored)';
END $$;

COMMIT;
