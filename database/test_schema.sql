-- Test database schema for CI/CD testing
-- This creates minimal schema needed for integration tests

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create test schemas
CREATE SCHEMA IF NOT EXISTS news_data_test;
CREATE SCHEMA IF NOT EXISTS dbt_test;

-- Create news sources table for testing
CREATE TABLE IF NOT EXISTS news_data_test.news_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create articles table for testing (matching production schema)
CREATE TABLE IF NOT EXISTS news_data_test.articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES news_data_test.news_sources(id),
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    article_date DATE,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    full_text TEXT,
    num_paragraphs INTEGER,
    UNIQUE(source_id, url),
    UNIQUE(source_id, title, article_date)
);

-- Insert test data (matching exact config names)
INSERT INTO news_data_test.news_sources (name, base_url, enabled) VALUES
    ('Slate.fr', 'https://slate.fr', true),
    ('FranceInfo.fr', 'https://franceinfo.fr', true),
    ('TF1 Info', 'https://tf1info.fr', true),
    ('Depeche.fr', 'https://ladepeche.fr', false)
ON CONFLICT (name) DO NOTHING;

-- Create indexes for performance (matching production schema)
CREATE INDEX IF NOT EXISTS idx_articles_source_id ON news_data_test.articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_url ON news_data_test.articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_article_date ON news_data_test.articles(article_date);
CREATE INDEX IF NOT EXISTS idx_articles_scraped_at ON news_data_test.articles(scraped_at);

-- Grant permissions (for CI/CD user)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ci_test_user') THEN
        GRANT USAGE ON SCHEMA news_data_test TO ci_test_user;
        GRANT USAGE ON SCHEMA dbt_test TO ci_test_user;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA news_data_test TO ci_test_user;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dbt_test TO ci_test_user;
    END IF;
END
$$;