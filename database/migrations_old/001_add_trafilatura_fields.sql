-- Migration 001: Add trafilatura extraction fields to raw_articles table
-- Clean SQL - executed via Python migration runner

-- Add trafilatura fields to raw_articles table
ALTER TABLE raw_articles
ADD COLUMN IF NOT EXISTS extracted_text TEXT,
ADD COLUMN IF NOT EXISTS title TEXT,
ADD COLUMN IF NOT EXISTS author TEXT,
ADD COLUMN IF NOT EXISTS date_published TEXT,
ADD COLUMN IF NOT EXISTS language TEXT,
ADD COLUMN IF NOT EXISTS summary TEXT,
ADD COLUMN IF NOT EXISTS keywords TEXT[],
ADD COLUMN IF NOT EXISTS extraction_status TEXT DEFAULT 'pending';

-- Create index on extraction status for filtering
CREATE INDEX IF NOT EXISTS idx_raw_articles_extraction_status
ON raw_articles(extraction_status);