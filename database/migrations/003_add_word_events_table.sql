-- Migration 003: Add simple word events table
-- Creates a clean event table for storing word occurrences from scraped articles
-- Python will populate this during scraping, dbt will analyze it later

-- =====================================================
-- Word Events Table - Simple Event Storage
-- =====================================================

CREATE TABLE IF NOT EXISTS news_data_dev.word_events (
    event_id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    article_id UUID NOT NULL REFERENCES news_data_dev.raw_articles(id) ON DELETE CASCADE,
    position_in_article INTEGER NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS news_data_test.word_events (
    event_id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    article_id UUID NOT NULL REFERENCES news_data_test.raw_articles(id) ON DELETE CASCADE,
    position_in_article INTEGER NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS news_data_prod.word_events (
    event_id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    article_id UUID NOT NULL REFERENCES news_data_prod.raw_articles(id) ON DELETE CASCADE,
    position_in_article INTEGER NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- Performance Indexes - For Fast Queries
-- =====================================================

-- Index for word frequency queries
CREATE INDEX IF NOT EXISTS idx_dev_word_events_word ON news_data_dev.word_events(word);
CREATE INDEX IF NOT EXISTS idx_test_word_events_word ON news_data_test.word_events(word);
CREATE INDEX IF NOT EXISTS idx_prod_word_events_word ON news_data_prod.word_events(word);

-- Index for article lookups
CREATE INDEX IF NOT EXISTS idx_dev_word_events_article ON news_data_dev.word_events(article_id);
CREATE INDEX IF NOT EXISTS idx_test_word_events_article ON news_data_test.word_events(article_id);
CREATE INDEX IF NOT EXISTS idx_prod_word_events_article ON news_data_prod.word_events(article_id);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_dev_word_events_scraped ON news_data_dev.word_events(scraped_at);
CREATE INDEX IF NOT EXISTS idx_test_word_events_scraped ON news_data_test.word_events(scraped_at);
CREATE INDEX IF NOT EXISTS idx_prod_word_events_scraped ON news_data_prod.word_events(scraped_at);

-- Composite index for common query patterns (word + time)
CREATE INDEX IF NOT EXISTS idx_dev_word_events_word_time ON news_data_dev.word_events(word, scraped_at);
CREATE INDEX IF NOT EXISTS idx_test_word_events_word_time ON news_data_test.word_events(word, scraped_at);
CREATE INDEX IF NOT EXISTS idx_prod_word_events_word_time ON news_data_prod.word_events(word, scraped_at);