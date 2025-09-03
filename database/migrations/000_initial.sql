-- Initial schema for French news scraper
-- Creates basic table structure for raw article storage

-- Create schemas for different environments
CREATE SCHEMA IF NOT EXISTS news_data_dev;
CREATE SCHEMA IF NOT EXISTS news_data_test; 
CREATE SCHEMA IF NOT EXISTS news_data_prod;

-- Main raw articles table in dev schema
CREATE TABLE IF NOT EXISTS news_data_dev.raw_articles (
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

-- Copy table structure to test schema
CREATE TABLE IF NOT EXISTS news_data_test.raw_articles (
    LIKE news_data_dev.raw_articles INCLUDING ALL
);

-- Copy table structure to prod schema  
CREATE TABLE IF NOT EXISTS news_data_prod.raw_articles (
    LIKE news_data_dev.raw_articles INCLUDING ALL
);

-- Create basic indexes for performance
CREATE INDEX IF NOT EXISTS idx_dev_raw_articles_site ON news_data_dev.raw_articles(site);
CREATE INDEX IF NOT EXISTS idx_dev_raw_articles_scraped_at ON news_data_dev.raw_articles(scraped_at);

CREATE INDEX IF NOT EXISTS idx_test_raw_articles_site ON news_data_test.raw_articles(site);
CREATE INDEX IF NOT EXISTS idx_test_raw_articles_scraped_at ON news_data_test.raw_articles(scraped_at);

CREATE INDEX IF NOT EXISTS idx_prod_raw_articles_site ON news_data_prod.raw_articles(site);
CREATE INDEX IF NOT EXISTS idx_prod_raw_articles_scraped_at ON news_data_prod.raw_articles(scraped_at);