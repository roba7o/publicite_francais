-- Migration 002: Drop URL unique constraint to allow duplicate URLs
-- Clean SQL - executed via Python migration runner
-- Allows storing same URL multiple times with different UUIDs

-- Check if constraint exists and drop it safely
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_schema = current_schema()
        AND table_name = 'raw_articles'
        AND constraint_name = 'raw_articles_url_key'
    ) THEN
        ALTER TABLE raw_articles DROP CONSTRAINT raw_articles_url_key;
    END IF;
END $$;