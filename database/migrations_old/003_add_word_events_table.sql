-- Migration 003: Add simple word events table
-- Clean SQL - executed via Python migration runner
-- Creates a clean event table for storing word occurrences from scraped articles

-- Create word_events table with proper foreign key reference
CREATE TABLE IF NOT EXISTS word_events (
    event_id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    article_id UUID NOT NULL REFERENCES raw_articles(id) ON DELETE CASCADE,
    position_in_article INTEGER NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes for fast queries
-- Index for word frequency queries
CREATE INDEX IF NOT EXISTS idx_word_events_word ON word_events(word);

-- Index for article lookups
CREATE INDEX IF NOT EXISTS idx_word_events_article ON word_events(article_id);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_word_events_scraped ON word_events(scraped_at);

-- Composite index for common query patterns (word + time)
CREATE INDEX IF NOT EXISTS idx_word_events_word_time ON word_events(word, scraped_at);