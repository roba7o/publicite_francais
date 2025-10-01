-- Migration 003: Add French word analysis tables
-- Creates normalized word dimension and fact tables for word frequency analysis
-- Preserves all raw data while providing stop word reference for logic

-- =====================================================
-- French Stop Words Reference Table
-- =====================================================
-- This table stores French stop words for reference (not filtering)
-- Used by flashcard logic to skip common words, but raw data remains intact

CREATE TABLE IF NOT EXISTS news_data_dev.french_stop_words (
    stop_word_id SERIAL PRIMARY KEY,
    word TEXT UNIQUE NOT NULL,
    word_type VARCHAR(50), -- 'article', 'pronoun', 'conjunction', 'preposition', etc.
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS news_data_test.french_stop_words (
    LIKE news_data_dev.french_stop_words INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS news_data_prod.french_stop_words (
    LIKE news_data_dev.french_stop_words INCLUDING ALL
);

-- =====================================================
-- Words Dimension Table
-- =====================================================
-- Central repository of all unique words found in articles
-- No filtering - contains every word, with stop word flagging for reference

CREATE TABLE IF NOT EXISTS news_data_dev.words (
    word_id SERIAL PRIMARY KEY,
    word TEXT UNIQUE NOT NULL,
    word_length INTEGER NOT NULL,
    total_frequency INTEGER DEFAULT 0,
    document_frequency INTEGER DEFAULT 0, -- how many articles contain this word
    is_stop_word BOOLEAN DEFAULT FALSE, -- reference flag, doesn't filter data
    first_seen TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS news_data_test.words (
    LIKE news_data_dev.words INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS news_data_prod.words (
    LIKE news_data_dev.words INCLUDING ALL
);

-- =====================================================
-- Word Occurrences Fact Table
-- =====================================================
-- Every instance of every word in every article
-- Complete raw data preservation for analysis

CREATE TABLE IF NOT EXISTS news_data_dev.word_occurrences (
    occurrence_id SERIAL PRIMARY KEY,
    word_id INTEGER NOT NULL REFERENCES news_data_dev.words(word_id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES news_data_dev.raw_articles(id) ON DELETE CASCADE,
    sentence_number INTEGER, -- which sentence in the article (1, 2, 3...)
    position_in_sentence INTEGER, -- which word in the sentence (1, 2, 3...)
    position_in_article INTEGER, -- which word in the entire article (1, 2, 3...)
    context_sentence TEXT, -- the full sentence containing this word
    scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS news_data_test.word_occurrences (
    occurrence_id SERIAL PRIMARY KEY,
    word_id INTEGER NOT NULL REFERENCES news_data_test.words(word_id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES news_data_test.raw_articles(id) ON DELETE CASCADE,
    sentence_number INTEGER,
    position_in_sentence INTEGER,
    position_in_article INTEGER,
    context_sentence TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS news_data_prod.word_occurrences (
    occurrence_id SERIAL PRIMARY KEY,
    word_id INTEGER NOT NULL REFERENCES news_data_prod.words(word_id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES news_data_prod.raw_articles(id) ON DELETE CASCADE,
    sentence_number INTEGER,
    position_in_sentence INTEGER,
    position_in_article INTEGER,
    context_sentence TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- Performance Indexes
-- =====================================================

-- French stop words indexes
CREATE INDEX IF NOT EXISTS idx_dev_french_stop_words_word ON news_data_dev.french_stop_words(word);
CREATE INDEX IF NOT EXISTS idx_dev_french_stop_words_type ON news_data_dev.french_stop_words(word_type);

CREATE INDEX IF NOT EXISTS idx_test_french_stop_words_word ON news_data_test.french_stop_words(word);
CREATE INDEX IF NOT EXISTS idx_test_french_stop_words_type ON news_data_test.french_stop_words(word_type);

CREATE INDEX IF NOT EXISTS idx_prod_french_stop_words_word ON news_data_prod.french_stop_words(word);
CREATE INDEX IF NOT EXISTS idx_prod_french_stop_words_type ON news_data_prod.french_stop_words(word_type);

-- Words table indexes
CREATE INDEX IF NOT EXISTS idx_dev_words_word ON news_data_dev.words(word);
CREATE INDEX IF NOT EXISTS idx_dev_words_frequency ON news_data_dev.words(total_frequency DESC);
CREATE INDEX IF NOT EXISTS idx_dev_words_stop_word ON news_data_dev.words(is_stop_word);
CREATE INDEX IF NOT EXISTS idx_dev_words_length ON news_data_dev.words(word_length);

CREATE INDEX IF NOT EXISTS idx_test_words_word ON news_data_test.words(word);
CREATE INDEX IF NOT EXISTS idx_test_words_frequency ON news_data_test.words(total_frequency DESC);
CREATE INDEX IF NOT EXISTS idx_test_words_stop_word ON news_data_test.words(is_stop_word);
CREATE INDEX IF NOT EXISTS idx_test_words_length ON news_data_test.words(word_length);

CREATE INDEX IF NOT EXISTS idx_prod_words_word ON news_data_prod.words(word);
CREATE INDEX IF NOT EXISTS idx_prod_words_frequency ON news_data_prod.words(total_frequency DESC);
CREATE INDEX IF NOT EXISTS idx_prod_words_stop_word ON news_data_prod.words(is_stop_word);
CREATE INDEX IF NOT EXISTS idx_prod_words_length ON news_data_prod.words(word_length);

-- Word occurrences indexes (for fast lookups and analysis)
CREATE INDEX IF NOT EXISTS idx_dev_word_occurrences_word_id ON news_data_dev.word_occurrences(word_id);
CREATE INDEX IF NOT EXISTS idx_dev_word_occurrences_article_id ON news_data_dev.word_occurrences(article_id);
CREATE INDEX IF NOT EXISTS idx_dev_word_occurrences_scraped_at ON news_data_dev.word_occurrences(scraped_at);
CREATE INDEX IF NOT EXISTS idx_dev_word_occurrences_sentence ON news_data_dev.word_occurrences(sentence_number);

CREATE INDEX IF NOT EXISTS idx_test_word_occurrences_word_id ON news_data_test.word_occurrences(word_id);
CREATE INDEX IF NOT EXISTS idx_test_word_occurrences_article_id ON news_data_test.word_occurrences(article_id);
CREATE INDEX IF NOT EXISTS idx_test_word_occurrences_scraped_at ON news_data_test.word_occurrences(scraped_at);
CREATE INDEX IF NOT EXISTS idx_test_word_occurrences_sentence ON news_data_test.word_occurrences(sentence_number);

CREATE INDEX IF NOT EXISTS idx_prod_word_occurrences_word_id ON news_data_prod.word_occurrences(word_id);
CREATE INDEX IF NOT EXISTS idx_prod_word_occurrences_article_id ON news_data_prod.word_occurrences(article_id);
CREATE INDEX IF NOT EXISTS idx_prod_word_occurrences_scraped_at ON news_data_prod.word_occurrences(scraped_at);
CREATE INDEX IF NOT EXISTS idx_prod_word_occurrences_sentence ON news_data_prod.word_occurrences(sentence_number);

-- =====================================================
-- Triggers for maintaining word statistics
-- =====================================================

-- Function to update word frequency counts
CREATE OR REPLACE FUNCTION update_word_frequency()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Update total_frequency and document_frequency for the word
        UPDATE words SET
            total_frequency = total_frequency + 1,
            last_seen = NEW.scraped_at,
            updated_at = CURRENT_TIMESTAMP
        WHERE word_id = NEW.word_id;

        -- Update first_seen if this is the first occurrence
        UPDATE words SET first_seen = NEW.scraped_at
        WHERE word_id = NEW.word_id AND first_seen IS NULL;

        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        -- Decrease frequency when occurrence is deleted
        UPDATE words SET
            total_frequency = GREATEST(total_frequency - 1, 0),
            updated_at = CURRENT_TIMESTAMP
        WHERE word_id = OLD.word_id;

        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for each environment
CREATE TRIGGER trigger_dev_word_frequency
    AFTER INSERT OR DELETE ON news_data_dev.word_occurrences
    FOR EACH ROW EXECUTE FUNCTION update_word_frequency();

CREATE TRIGGER trigger_test_word_frequency
    AFTER INSERT OR DELETE ON news_data_test.word_occurrences
    FOR EACH ROW EXECUTE FUNCTION update_word_frequency();

CREATE TRIGGER trigger_prod_word_frequency
    AFTER INSERT OR DELETE ON news_data_prod.word_occurrences
    FOR EACH ROW EXECUTE FUNCTION update_word_frequency();