-- =============================================================================
-- French News Scraper Database Schema
-- =============================================================================
-- Star Schema Design:
--   - dim_articles: Dimension table (metadata only, no HTML storage)
--   - word_facts: Fact table (one row per word occurrence)
--
-- Processing flow:
-- 1. Scrape HTML (transient, not stored)
-- 2. Extract words immediately
-- 3. Store dim_articles metadata + word_facts
--
-- Uses standard public schema for all environments
-- =============================================================================

-- Dimension Table: Article Metadata
-- Stores metadata only (no HTML content)
CREATE TABLE IF NOT EXISTS dim_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL UNIQUE,              -- Unique constraint: one article per URL
    site TEXT NOT NULL,                    -- News site identifier (e.g., "slate.fr")
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,  -- When article was scraped
    response_status INTEGER,                -- HTTP response status (e.g., 200)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fact Table: Word Facts
-- Denormalized vocabulary table for French language learning
-- One row per word occurrence (no deduplication)
CREATE TABLE IF NOT EXISTS word_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word TEXT NOT NULL,                     -- French word (normalized, lowercase)
    article_id UUID NOT NULL                -- Foreign key to dim_articles
        REFERENCES dim_articles(id)
        ON DELETE CASCADE,
    position_in_article INTEGER NOT NULL,   -- Position of word in article (0-indexed)
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL  -- When word was extracted
);

-- =============================================================================
-- Performance Indexes
-- =============================================================================

-- Dimension Articles indexes
CREATE INDEX IF NOT EXISTS idx_dim_articles_site
    ON dim_articles(site);

CREATE INDEX IF NOT EXISTS idx_dim_articles_scraped_at
    ON dim_articles(scraped_at);

-- Word Facts indexes (for vocabulary queries)
CREATE INDEX IF NOT EXISTS idx_word_facts_word
    ON word_facts(word);

CREATE INDEX IF NOT EXISTS idx_word_facts_article_id
    ON word_facts(article_id);

CREATE INDEX IF NOT EXISTS idx_word_facts_scraped_at
    ON word_facts(scraped_at);

