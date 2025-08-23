-- Initial Migration: Bootstrap French News Database
-- Created: 2025-08-23
-- Description: Creates initial schema structure and migration tracking system
-- This replaces the old init.sql with a proper Django-style migration approach

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- MIGRATION TRACKING SYSTEM (Django-style)
-- =============================================================================

-- Create migration history table to track applied migrations
CREATE TABLE IF NOT EXISTS migration_history (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_migration_history_name ON migration_history(migration_name);
CREATE INDEX IF NOT EXISTS idx_migration_history_applied ON migration_history(applied_at);

-- =============================================================================
-- ENVIRONMENT SCHEMAS
-- =============================================================================

-- Create schemas for organizing tables by environment
CREATE SCHEMA IF NOT EXISTS news_data_dev;    -- Development environment (make run)
CREATE SCHEMA IF NOT EXISTS news_data_test;   -- Test environment (make test)
CREATE SCHEMA IF NOT EXISTS news_data_prod;   -- Production environment

-- =============================================================================
-- MAIN TABLE CREATION FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION create_initial_tables(env_schema text)
RETURNS void AS $$
BEGIN
    -- Raw articles table - stores scraped HTML content from news sites
    -- NOTE: This includes ALL fields from migration 001 (trafilatura) and 002 (no unique url)
    -- to create the complete current schema state
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.raw_articles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            url TEXT NOT NULL,  -- No UNIQUE constraint (removed in migration 002)
            raw_html TEXT NOT NULL,
            site TEXT NOT NULL,    -- News site: "slate.fr", "franceinfo.fr", "tf1info.fr", "ladepeche.fr" 
            scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            response_status INTEGER,
            content_length INTEGER,
            
            -- Trafilatura extraction fields (from migration 001)
            extracted_text TEXT,
            title TEXT,
            author TEXT,
            date_published TEXT,
            language TEXT,
            summary TEXT,
            keywords TEXT[],
            extraction_status TEXT DEFAULT ''pending'',
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )', env_schema);

    -- Create performance indexes
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_raw_articles_site ON %I.raw_articles(site)', 
                   replace(env_schema, '_', ''), env_schema);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_raw_articles_scraped_at ON %I.raw_articles(scraped_at)', 
                   replace(env_schema, '_', ''), env_schema);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_raw_articles_extraction_status ON %I.raw_articles(extraction_status)', 
                   replace(env_schema, '_', ''), env_schema);

    RAISE NOTICE 'Created raw_articles table with all current fields for schema: %', env_schema;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- CREATE TABLES IN ALL ENVIRONMENTS
-- =============================================================================

SELECT create_initial_tables('news_data_dev');
SELECT create_initial_tables('news_data_test');
SELECT create_initial_tables('news_data_prod');

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

-- Grant permissions on migration_history table
GRANT ALL PRIVILEGES ON migration_history TO news_user;
GRANT ALL PRIVILEGES ON SEQUENCE migration_history_id_seq TO news_user;

-- Clean up helper function
DROP FUNCTION create_initial_tables(text);

-- =============================================================================
-- RECORD THIS MIGRATION AS APPLIED
-- =============================================================================

-- This migration incorporates the effects of:
-- - 000_initial.sql (this file)
-- - 001_add_trafilatura_fields.sql (fields already included above)
-- - 002_drop_url_unique_constraint.sql (constraint already omitted above)

INSERT INTO migration_history (migration_name) VALUES 
    ('000_initial.sql'),
    ('001_add_trafilatura_fields.sql'),
    ('002_drop_url_unique_constraint.sql')
ON CONFLICT (migration_name) DO NOTHING;

-- =============================================================================
-- CONFIRMATION MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '╔══════════════════════════════════════════════╗';
    RAISE NOTICE '║   French News Database Initialized (v2.0)   ║';
    RAISE NOTICE '║        Django-Style Migration System        ║';
    RAISE NOTICE '╚══════════════════════════════════════════════╝';
    RAISE NOTICE '';
    RAISE NOTICE 'Environment Schemas Created:';
    RAISE NOTICE '  • news_data_dev   (development - make run)';
    RAISE NOTICE '  • news_data_test  (testing - make test)'; 
    RAISE NOTICE '  • news_data_prod  (production)';
    RAISE NOTICE '';
    RAISE NOTICE 'Migration Tracking:';
    RAISE NOTICE '  • migration_history table created';
    RAISE NOTICE '  • Migrations 000-002 marked as applied';
    RAISE NOTICE '';
    RAISE NOTICE 'Schema State: Complete with all current fields';
    RAISE NOTICE 'Pipeline: Python Scraper → PostgreSQL';
    RAISE NOTICE 'Ready for scraping!';
    RAISE NOTICE '';
END $$;