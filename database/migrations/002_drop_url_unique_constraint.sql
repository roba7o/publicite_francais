-- Drop URL unique constraint to allow duplicate URLs
-- Allows storing same URL multiple times with different UUIDs
-- This removes the UNIQUE constraint added in migration 000

-- Check and drop constraint if it exists in dev schema
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_schema = 'news_data_dev' 
        AND table_name = 'raw_articles' 
        AND constraint_name = 'raw_articles_url_key'
    ) THEN
        ALTER TABLE news_data_dev.raw_articles DROP CONSTRAINT raw_articles_url_key;
    END IF;
END $$;

-- Check and drop constraint if it exists in test schema  
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_schema = 'news_data_test' 
        AND table_name = 'raw_articles' 
        AND constraint_name = 'raw_articles_url_key'
    ) THEN
        ALTER TABLE news_data_test.raw_articles DROP CONSTRAINT raw_articles_url_key;
    END IF;
END $$;

-- Check and drop constraint if it exists in prod schema
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_schema = 'news_data_prod' 
        AND table_name = 'raw_articles' 
        AND constraint_name = 'raw_articles_url_key'
    ) THEN
        ALTER TABLE news_data_prod.raw_articles DROP CONSTRAINT raw_articles_url_key;
    END IF;
END $$;