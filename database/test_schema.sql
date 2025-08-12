-- Test database schema for CI/CD testing
-- This creates minimal schema needed for integration tests

-- Create test schemas
CREATE SCHEMA IF NOT EXISTS news_data_test;
CREATE SCHEMA IF NOT EXISTS dbt_test;

-- Create news sources table for testing
CREATE TABLE IF NOT EXISTS news_data_test.news_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create articles table for testing
CREATE TABLE IF NOT EXISTS news_data_test.articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT,
    url VARCHAR(1000) NOT NULL UNIQUE,
    published_date DATE,
    source_id UUID REFERENCES news_data_test.news_sources(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert test data
INSERT INTO news_data_test.news_sources (name, base_url, enabled) VALUES
    ('slate.fr', 'https://slate.fr', true),
    ('franceinfo.fr', 'https://franceinfo.fr', true),
    ('tf1info.fr', 'https://tf1info.fr', true),
    ('ladepeche.fr', 'https://ladepeche.fr', false)
ON CONFLICT (name) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_articles_source_id ON news_data_test.articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_url ON news_data_test.articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_published_date ON news_data_test.articles(published_date);

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