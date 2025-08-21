-- Migration: Drop URL unique constraint to allow duplicate URLs
-- Created: 2025-08-21
-- Description: Removes UNIQUE constraint on URL field to allow storing duplicate URLs with different UUIDs

-- Drop the URL unique constraint from all schemas
DO $$
DECLARE
    schema_name text;
BEGIN
    FOR schema_name IN VALUES ('news_data_dev'), ('news_data_test'), ('news_data_prod')
    LOOP
        -- Check if the constraint exists before trying to drop it
        IF EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE table_schema = schema_name 
            AND table_name = 'raw_articles' 
            AND constraint_name = 'raw_articles_url_key'
        ) THEN
            EXECUTE format('ALTER TABLE %I.raw_articles DROP CONSTRAINT raw_articles_url_key', schema_name);
            RAISE NOTICE 'Dropped URL unique constraint from %.raw_articles', schema_name;
        ELSE
            RAISE NOTICE 'URL unique constraint does not exist in %.raw_articles', schema_name;
        END IF;
    END LOOP;
END $$;