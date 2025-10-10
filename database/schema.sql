-- =============================================================================
-- French News Scraper Database Schema
-- =============================================================================
-- Star Schema Design:
--   - raw_articles: Dimension table (one row per unique article URL)
--     - scraped_at: When the HTML was scraped from the web
--   - word_facts: Fact table (one row per word occurrence)
--     - scraped_at: When the word was extracted from HTML
--     - Links to raw_articles via article_id foreign key
--
-- Note: The two scraped_at timestamps may differ because articles are scraped
-- first, then words are extracted in a separate processing step.
--
-- Uses standard public schema for all environments
-- =============================================================================

-- Dimension Table: Raw Articles
-- Stores unique articles by URL
CREATE TABLE IF NOT EXISTS raw_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL UNIQUE,              -- Unique constraint: one article per URL
    raw_html TEXT NOT NULL,                -- Complete HTML content
    site TEXT NOT NULL,                    -- News site identifier (e.g., "slate.fr")
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,  -- When HTML was fetched from web
    response_status INTEGER,                -- HTTP response status (e.g., 200)
    content_length INTEGER,                 -- Length of raw_html
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fact Table: Word Facts
-- Denormalized vocabulary table for French language learning
-- One row per word occurrence (no deduplication)
CREATE TABLE IF NOT EXISTS word_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word TEXT NOT NULL,                     -- French word (normalized, lowercase)
    article_id UUID NOT NULL                -- Foreign key to raw_articles
        REFERENCES raw_articles(id)
        ON DELETE CASCADE,
    position_in_article INTEGER NOT NULL,   -- Position of word in article (0-indexed)
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL  -- When word was extracted (may differ from article scraped_at)
);

-- =============================================================================
-- Performance Indexes
-- =============================================================================

-- Raw Articles indexes
CREATE INDEX IF NOT EXISTS idx_raw_articles_site
    ON raw_articles(site);

CREATE INDEX IF NOT EXISTS idx_raw_articles_scraped_at
    ON raw_articles(scraped_at);

-- Word Facts indexes (for vocabulary queries)
CREATE INDEX IF NOT EXISTS idx_word_facts_word
    ON word_facts(word);

CREATE INDEX IF NOT EXISTS idx_word_facts_article_id
    ON word_facts(article_id);

CREATE INDEX IF NOT EXISTS idx_word_facts_scraped_at
    ON word_facts(scraped_at);

