-- Migration: Add trafilatura extraction fields
-- Created: 2025-08-21
-- Description: Adds columns for storing trafilatura-extracted content

-- Add trafilatura fields to existing raw_articles tables
DO $$
DECLARE
    schema_name text;
BEGIN
    FOR schema_name IN VALUES ('news_data_dev'), ('news_data_test'), ('news_data_prod')
    LOOP
        -- Check if columns already exist before adding
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = schema_name 
            AND table_name = 'raw_articles' 
            AND column_name = 'extracted_text'
        ) THEN
            -- Add each column separately (PostgreSQL requires separate ADD COLUMN statements)
            EXECUTE format('ALTER TABLE %I.raw_articles ADD COLUMN extracted_text TEXT', schema_name);
            EXECUTE format('ALTER TABLE %I.raw_articles ADD COLUMN title TEXT', schema_name);
            EXECUTE format('ALTER TABLE %I.raw_articles ADD COLUMN author TEXT', schema_name);
            EXECUTE format('ALTER TABLE %I.raw_articles ADD COLUMN date_published TEXT', schema_name);
            EXECUTE format('ALTER TABLE %I.raw_articles ADD COLUMN language TEXT', schema_name);
            EXECUTE format('ALTER TABLE %I.raw_articles ADD COLUMN summary TEXT', schema_name);
            EXECUTE format('ALTER TABLE %I.raw_articles ADD COLUMN keywords TEXT[]', schema_name);
            EXECUTE format('ALTER TABLE %I.raw_articles ADD COLUMN extraction_status TEXT DEFAULT ''pending''', schema_name);
            
            RAISE NOTICE 'Added trafilatura columns to %.raw_articles', schema_name;
        ELSE
            RAISE NOTICE 'Trafilatura columns already exist in %.raw_articles', schema_name;
        END IF;
    END LOOP;
END $$;