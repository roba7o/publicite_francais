-- French News Database Initialization Script
-- This script sets up the schema structure for all environments
-- Run automatically when the PostgreSQL container starts for the first time

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- SCHEMAS FOR DIFFERENT ENVIRONMENTS
-- =============================================================================

-- Create schemas for organizing tables by environment
CREATE SCHEMA IF NOT EXISTS news_data_dev;    -- Development environment
CREATE SCHEMA IF NOT EXISTS news_data_test;   -- Test environment 
CREATE SCHEMA IF NOT EXISTS news_data_prod;   -- Production environment

-- Create dbt schemas for text processing
CREATE SCHEMA IF NOT EXISTS dbt_staging;      -- dbt development target
CREATE SCHEMA IF NOT EXISTS dbt_test;         -- dbt test target
CREATE SCHEMA IF NOT EXISTS dbt_prod;         -- dbt production target

-- =============================================================================
-- TABLE CREATION FUNCTION
-- This creates the same tables in each environment schema
-- =============================================================================

CREATE OR REPLACE FUNCTION create_environment_tables(env_schema text)
RETURNS void AS $$
BEGIN
    -- Raw articles table (ELT approach - stores unprocessed HTML)
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.raw_articles (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            url TEXT NOT NULL UNIQUE,
            raw_html TEXT NOT NULL,
            source TEXT NOT NULL,  -- Domain: "slate.fr", "franceinfo.fr" 
            scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            response_status INTEGER,
            content_length INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )', env_schema);

    -- Word frequencies table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.word_frequencies (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            article_id UUID NOT NULL REFERENCES %I.articles(id) ON DELETE CASCADE,
            word VARCHAR(100) NOT NULL,
            frequency INTEGER NOT NULL CHECK (frequency > 0),
            context TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )', env_schema, env_schema);

    -- Processing logs table for monitoring
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.processing_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            source_id UUID REFERENCES %I.news_sources(id),
            run_type VARCHAR(20) NOT NULL CHECK (run_type IN (''live'', ''offline'', ''test'')),
            articles_attempted INTEGER DEFAULT 0,
            articles_processed INTEGER DEFAULT 0,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP WITH TIME ZONE,
            status VARCHAR(20) DEFAULT ''running'' CHECK (status IN (''running'', ''completed'', ''failed'')),
            error_message TEXT
        )', env_schema, env_schema);

    -- Create indexes for performance
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_articles_source_id ON %I.articles(source_id)', env_schema, env_schema);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_articles_scraped_at ON %I.articles(scraped_at)', env_schema, env_schema);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_articles_article_date ON %I.articles(article_date)', env_schema, env_schema);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_articles_url ON %I.articles(url)', env_schema, env_schema);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_word_frequencies_article_id ON %I.word_frequencies(article_id)', env_schema, env_schema);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_word_frequencies_word ON %I.word_frequencies(word)', env_schema, env_schema);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_word_frequencies_frequency ON %I.word_frequencies(frequency)', env_schema, env_schema);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_processing_logs_source_id ON %I.processing_logs(source_id)', env_schema, env_schema);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_processing_logs_started_at ON %I.processing_logs(started_at)', env_schema, env_schema);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_processing_logs_status ON %I.processing_logs(status)', env_schema, env_schema);

    RAISE NOTICE 'Created tables and indexes for schema: %', env_schema;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- CREATE TABLES IN ALL ENVIRONMENTS
-- =============================================================================

SELECT create_environment_tables('news_data_dev');
SELECT create_environment_tables('news_data_test');
SELECT create_environment_tables('news_data_prod');

-- =============================================================================
-- SAMPLE DATA FOR TESTING
-- Insert into all environment schemas
-- =============================================================================

-- Insert the current news sources into each environment
DO $$
BEGIN
    -- Development environment
    INSERT INTO news_data_dev.news_sources (name, base_url, enabled, scraper_class, parser_class) VALUES
        ('Slate.fr', 'https://www.slate.fr', true, 'scrapers.slate_fr_scraper.SlateFrURLScraper', 'parsers.database_slate_fr_parser.DatabaseSlateFrArticleParser'),
        ('FranceInfo.fr', 'https://www.franceinfo.fr', true, 'scrapers.france_info_scraper.FranceInfoURLScraper', 'parsers.database_france_info_parser.DatabaseFranceInfoArticleParser'),
        ('TF1 Info', 'https://www.tf1info.fr', true, 'scrapers.tf1_info_scraper.TF1InfoURLScraper', 'parsers.database_tf1_info_parser.DatabaseTF1InfoArticleParser'),
        ('Depeche.fr', 'https://www.ladepeche.fr', true, 'scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper', 'parsers.database_ladepeche_fr_parser.DatabaseLadepecheFrArticleParser')
    ON CONFLICT (name) DO NOTHING;

    -- Test environment
    INSERT INTO news_data_test.news_sources (name, base_url, enabled, scraper_class, parser_class) VALUES
        ('Slate.fr', 'https://www.slate.fr', true, 'scrapers.slate_fr_scraper.SlateFrURLScraper', 'parsers.database_slate_fr_parser.DatabaseSlateFrArticleParser'),
        ('FranceInfo.fr', 'https://www.franceinfo.fr', true, 'scrapers.france_info_scraper.FranceInfoURLScraper', 'parsers.database_france_info_parser.DatabaseFranceInfoArticleParser'),
        ('TF1 Info', 'https://www.tf1info.fr', true, 'scrapers.tf1_info_scraper.TF1InfoURLScraper', 'parsers.database_tf1_info_parser.DatabaseTF1InfoArticleParser'),
        ('Depeche.fr', 'https://www.ladepeche.fr', true, 'scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper', 'parsers.database_ladepeche_fr_parser.DatabaseLadepecheFrArticleParser')
    ON CONFLICT (name) DO NOTHING;

    -- Production environment
    INSERT INTO news_data_prod.news_sources (name, base_url, enabled, scraper_class, parser_class) VALUES
        ('Slate.fr', 'https://www.slate.fr', true, 'scrapers.slate_fr_scraper.SlateFrURLScraper', 'parsers.database_slate_fr_parser.DatabaseSlateFrArticleParser'),
        ('FranceInfo.fr', 'https://www.franceinfo.fr', true, 'scrapers.france_info_scraper.FranceInfoURLScraper', 'parsers.database_france_info_parser.DatabaseFranceInfoArticleParser'),
        ('TF1 Info', 'https://www.tf1info.fr', true, 'scrapers.tf1_info_scraper.TF1InfoURLScraper', 'parsers.database_tf1_info_parser.DatabaseTF1InfoArticleParser'),
        ('Depeche.fr', 'https://www.ladepeche.fr', true, 'scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper', 'parsers.database_ladepeche_fr_parser.DatabaseLadepecheFrArticleParser')
    ON CONFLICT (name) DO NOTHING;
END $$;

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERMISSIONS FOR ALL SCHEMAS
-- =============================================================================

-- Grant necessary permissions to the news_user for all schemas
DO $$
DECLARE
    schema_name text;
BEGIN
    FOR schema_name IN VALUES ('news_data_dev'), ('news_data_test'), ('news_data_prod'), ('dbt_staging'), ('dbt_test'), ('dbt_prod')
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
    RAISE NOTICE '  • news_data_dev   (development)';
    RAISE NOTICE '  • news_data_test  (testing)'; 
    RAISE NOTICE '  • news_data_prod  (production)';
    RAISE NOTICE '';
    RAISE NOTICE 'dbt Schemas Created:';
    RAISE NOTICE '  • dbt_staging     (dev target)';
    RAISE NOTICE '  • dbt_test        (test target)';
    RAISE NOTICE '  • dbt_prod        (prod target)';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables: news_sources, articles, word_frequencies, processing_logs';
    RAISE NOTICE 'Ready for Python + dbt integration!';
    RAISE NOTICE '';
END $$;