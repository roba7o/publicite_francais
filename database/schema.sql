-- French News Scraper Database Schema
-- Single source of truth for database structure
-- Uses standard public schema for all environments

-- Raw articles table for storing scraped content
CREATE TABLE IF NOT EXISTS raw_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL UNIQUE,
    raw_html TEXT NOT NULL,
    site TEXT NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    response_status INTEGER,
    content_length INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Word facts table for normalized vocabulary processing
CREATE TABLE IF NOT EXISTS word_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word TEXT NOT NULL,
    article_id UUID NOT NULL REFERENCES raw_articles(id) ON DELETE CASCADE,
    position_in_article INTEGER NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_raw_articles_site ON raw_articles(site);
CREATE INDEX IF NOT EXISTS idx_raw_articles_scraped_at ON raw_articles(scraped_at);
CREATE INDEX IF NOT EXISTS idx_word_facts_word ON word_facts(word);
CREATE INDEX IF NOT EXISTS idx_word_facts_article_id ON word_facts(article_id);
CREATE INDEX IF NOT EXISTS idx_word_facts_scraped_at ON word_facts(scraped_at);