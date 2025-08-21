-- French News Database Initialization Script
-- This script sets up the schema structure for the simplified pipeline
-- Run automatically when the PostgreSQL container starts for the first time

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- SCHEMAS FOR DIFFERENT ENVIRONMENTS
-- =============================================================================

-- Create schemas for organizing tables by environment
CREATE SCHEMA IF NOT EXISTS news_data_dev;    -- Development environment (make run)
CREATE SCHEMA IF NOT EXISTS news_data_test;   -- Test environment (make test)
CREATE SCHEMA IF NOT EXISTS news_data_prod;   -- Production environment

-- =============================================================================
-- TABLE CREATION FUNCTION
-- Creates only the table that is actually used
-- =============================================================================

CREATE OR REPLACE FUNCTION create_environment_tables(env_schema text)
RETURNS void AS $$
BEGIN
    -- Raw articles table - THE ONLY TABLE CURRENTLY USED
    -- Stores scraped HTML content from news sites
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.raw_articles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            url TEXT NOT NULL UNIQUE,
            raw_html TEXT NOT NULL,
            site TEXT NOT NULL,    -- News site: "slate.fr", "franceinfo.fr", "tf1info.fr", "ladepeche.fr" 
            scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            response_status INTEGER,
            content_length INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )', env_schema);

    -- Create indexes for performance
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_raw_articles_site ON %I.raw_articles(site)', 
                   replace(env_schema, '_', ''), env_schema);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_raw_articles_scraped_at ON %I.raw_articles(scraped_at)', 
                   replace(env_schema, '_', ''), env_schema);

    RAISE NOTICE 'Created raw_articles table and indexes for schema: %', env_schema;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- CREATE TABLES IN ALL ENVIRONMENTS
-- =============================================================================

SELECT create_environment_tables('news_data_dev');
SELECT create_environment_tables('news_data_test');
SELECT create_environment_tables('news_data_prod');

-- =============================================================================
-- PERMISSIONS FOR ALL SCHEMAS
-- =============================================================================

-- Grant necessary permissions to the news_user for all schemas
DO $$
DECLARE
    schema_name text;
BEGIN
    FOR schema_name IN VALUES ('news_data_dev'), ('news_data_test'), ('news_data_prod')
    LOOP
        EXECUTE format('GRANT USAGE ON SCHEMA %I TO news_user', schema_name);
        EXECUTE format('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I TO news_user', schema_name);
        EXECUTE format('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I TO news_user', schema_name);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL ON TABLES TO news_user', schema_name);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL ON SEQUENCES TO news_user', schema_name);
        RAISE NOTICE 'Granted permissions for schema: %', schema_name;
    END LOOP;
END $$;

-- Drop the helper function
DROP FUNCTION create_environment_tables(text);

-- Print confirmation message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════════╗';
    RAISE NOTICE '║     French News Database Initialized!     ║';
    RAISE NOTICE '╚════════════════════════════════════════════╝';
    RAISE NOTICE '';
    RAISE NOTICE 'Environment Schemas Created:';
    RAISE NOTICE '  • news_data_dev   (development - make run)';
    RAISE NOTICE '  • news_data_test  (testing - make test)'; 
    RAISE NOTICE '  • news_data_prod  (production)';
    RAISE NOTICE '';
    RAISE NOTICE 'Table: raw_articles (stores scraped HTML)';
    RAISE NOTICE 'Pipeline: Python Scraper → PostgreSQL';
    RAISE NOTICE 'Ready for scraping!';
    RAISE NOTICE '';
END $$;