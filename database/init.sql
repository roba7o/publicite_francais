-- French News Database Initialization Script
-- This script sets up the basic schema structure for future use
-- Run automatically when the PostgreSQL container starts for the first time

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas for different environments
CREATE SCHEMA IF NOT EXISTS news_data_dev;
CREATE SCHEMA IF NOT EXISTS news_data_test;  
CREATE SCHEMA IF NOT EXISTS news_data_prod;

-- Set search path to include our schemas
SET search_path TO news_data_dev, news_data_test, news_data_prod, public;

-- =============================================================================
-- TABLES FOR FUTURE IMPLEMENTATION
-- These tables are created for the upcoming refactor but not used yet
-- =============================================================================

-- =============================================================================
-- DEVELOPMENT ENVIRONMENT TABLES
-- =============================================================================

-- News sources configuration table (dev)
CREATE TABLE IF NOT EXISTS news_data_dev.news_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    scraper_class VARCHAR(200),
    parser_class VARCHAR(200),
    config JSONB, -- Store scraper/parser specific config
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Articles metadata table (dev)
CREATE TABLE IF NOT EXISTS news_data_dev.articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES news_data_dev.news_sources(id),
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    article_date DATE,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    full_text TEXT,
    num_paragraphs INTEGER,
    -- Prevent duplicate articles from same source
    UNIQUE(source_id, url),
    UNIQUE(source_id, title, article_date)
);

-- Word frequencies table (dev)  
CREATE TABLE IF NOT EXISTS news_data_dev.word_frequencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES news_data_dev.articles(id) ON DELETE CASCADE,
    word VARCHAR(100) NOT NULL,
    frequency INTEGER NOT NULL CHECK (frequency > 0),
    context TEXT, -- Sentence context where the word appears
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Processing logs table for monitoring (dev)
CREATE TABLE IF NOT EXISTS news_data_dev.processing_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES news_data_dev.news_sources(id),
    run_type VARCHAR(20) NOT NULL CHECK (run_type IN ('live', 'offline', 'test')),
    articles_attempted INTEGER DEFAULT 0,
    articles_processed INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Articles indexes (dev)
CREATE INDEX IF NOT EXISTS idx_dev_articles_source_id ON news_data_dev.articles(source_id);
CREATE INDEX IF NOT EXISTS idx_dev_articles_scraped_at ON news_data_dev.articles(scraped_at);
CREATE INDEX IF NOT EXISTS idx_dev_articles_article_date ON news_data_dev.articles(article_date);
CREATE INDEX IF NOT EXISTS idx_dev_articles_url ON news_data_dev.articles(url);

-- Word frequencies indexes (dev)
CREATE INDEX IF NOT EXISTS idx_dev_word_frequencies_article_id ON news_data_dev.word_frequencies(article_id);
CREATE INDEX IF NOT EXISTS idx_dev_word_frequencies_word ON news_data_dev.word_frequencies(word);
CREATE INDEX IF NOT EXISTS idx_dev_word_frequencies_frequency ON news_data_dev.word_frequencies(frequency);

-- Processing logs indexes (dev)
CREATE INDEX IF NOT EXISTS idx_dev_processing_logs_source_id ON news_data_dev.processing_logs(source_id);
CREATE INDEX IF NOT EXISTS idx_dev_processing_logs_started_at ON news_data_dev.processing_logs(started_at);
CREATE INDEX IF NOT EXISTS idx_dev_processing_logs_status ON news_data_dev.processing_logs(status);

-- =============================================================================
-- SAMPLE DATA FOR TESTING
-- =============================================================================

-- Insert the current news sources (dev)
INSERT INTO news_data_dev.news_sources (name, base_url, enabled, scraper_class, parser_class) VALUES
    ('Slate.fr', 'https://www.slate.fr', true, 'scrapers.slate_fr_scraper.SlateFrURLScraper', 'parsers.slate_fr_parser.SlateFrArticleParser'),
    ('FranceInfo.fr', 'https://www.franceinfo.fr', true, 'scrapers.france_info_scraper.FranceInfoURLScraper', 'parsers.france_info_parser.FranceInfoArticleParser'),
    ('TF1 Info', 'https://www.tf1info.fr', true, 'scrapers.tf1_info_scraper.TF1InfoURLScraper', 'parsers.tf1_info_parser.TF1InfoArticleParser'),
    ('Depeche.fr', 'https://www.ladepeche.fr', true, 'scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper', 'parsers.ladepeche_fr_parser.LadepecheFrArticleParser')
ON CONFLICT (name) DO NOTHING;

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
$$ language 'plpgsql';

-- Trigger to automatically update updated_at for news_sources
CREATE TRIGGER update_news_sources_updated_at 
    BEFORE UPDATE ON news_sources 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- PERMISSIONS
-- =============================================================================

-- Grant necessary permissions to the news_user
GRANT USAGE ON SCHEMA news_data_dev TO news_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA news_data_dev TO news_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA news_data_dev TO news_user;
GRANT USAGE ON SCHEMA news_data_test TO news_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA news_data_test TO news_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA news_data_test TO news_user;
GRANT USAGE ON SCHEMA news_data_prod TO news_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA news_data_prod TO news_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA news_data_prod TO news_user;

-- Print confirmation message
DO $$
BEGIN
    RAISE NOTICE 'French News Database initialized successfully!';
    RAISE NOTICE 'Schemas: news_data_dev, news_data_test, news_data_prod';
    RAISE NOTICE 'Tables created: news_sources, articles, word_frequencies, processing_logs';
    RAISE NOTICE 'Ready for future Python integration';
END $$;