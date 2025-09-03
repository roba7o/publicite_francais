-- Add trafilatura extraction fields to raw_articles table
-- These fields store extracted content from raw HTML

-- Add trafilatura fields to dev schema
ALTER TABLE news_data_dev.raw_articles 
ADD COLUMN IF NOT EXISTS extracted_text TEXT,
ADD COLUMN IF NOT EXISTS title TEXT,
ADD COLUMN IF NOT EXISTS author TEXT,
ADD COLUMN IF NOT EXISTS date_published TEXT,
ADD COLUMN IF NOT EXISTS language TEXT,
ADD COLUMN IF NOT EXISTS summary TEXT,
ADD COLUMN IF NOT EXISTS keywords TEXT[],
ADD COLUMN IF NOT EXISTS extraction_status TEXT DEFAULT 'pending';

-- Add trafilatura fields to test schema
ALTER TABLE news_data_test.raw_articles 
ADD COLUMN IF NOT EXISTS extracted_text TEXT,
ADD COLUMN IF NOT EXISTS title TEXT,
ADD COLUMN IF NOT EXISTS author TEXT,
ADD COLUMN IF NOT EXISTS date_published TEXT,
ADD COLUMN IF NOT EXISTS language TEXT,
ADD COLUMN IF NOT EXISTS summary TEXT,
ADD COLUMN IF NOT EXISTS keywords TEXT[],
ADD COLUMN IF NOT EXISTS extraction_status TEXT DEFAULT 'pending';

-- Add trafilatura fields to prod schema
ALTER TABLE news_data_prod.raw_articles 
ADD COLUMN IF NOT EXISTS extracted_text TEXT,
ADD COLUMN IF NOT EXISTS title TEXT,
ADD COLUMN IF NOT EXISTS author TEXT,
ADD COLUMN IF NOT EXISTS date_published TEXT,
ADD COLUMN IF NOT EXISTS language TEXT,
ADD COLUMN IF NOT EXISTS summary TEXT,
ADD COLUMN IF NOT EXISTS keywords TEXT[],
ADD COLUMN IF NOT EXISTS extraction_status TEXT DEFAULT 'pending';

-- Create index on extraction status for filtering
CREATE INDEX IF NOT EXISTS idx_dev_raw_articles_extraction_status ON news_data_dev.raw_articles(extraction_status);
CREATE INDEX IF NOT EXISTS idx_test_raw_articles_extraction_status ON news_data_test.raw_articles(extraction_status);
CREATE INDEX IF NOT EXISTS idx_prod_raw_articles_extraction_status ON news_data_prod.raw_articles(extraction_status);