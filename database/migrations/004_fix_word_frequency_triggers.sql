-- Migration 004: Fix word frequency triggers to be schema-aware
-- The previous triggers failed because they didn't include schema prefixes

-- Drop existing triggers first
DROP TRIGGER IF EXISTS trigger_dev_word_frequency ON news_data_dev.word_occurrences;
DROP TRIGGER IF EXISTS trigger_test_word_frequency ON news_data_test.word_occurrences;
DROP TRIGGER IF EXISTS trigger_prod_word_frequency ON news_data_prod.word_occurrences;

-- Drop existing function
DROP FUNCTION IF EXISTS update_word_frequency();

-- Create schema-specific trigger functions
CREATE OR REPLACE FUNCTION update_word_frequency_dev()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Update total_frequency and document_frequency for the word
        UPDATE news_data_dev.words SET
            total_frequency = total_frequency + 1,
            last_seen = NEW.scraped_at,
            updated_at = CURRENT_TIMESTAMP
        WHERE word_id = NEW.word_id;

        -- Update first_seen if this is the first occurrence
        UPDATE news_data_dev.words SET first_seen = NEW.scraped_at
        WHERE word_id = NEW.word_id AND first_seen IS NULL;

        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        -- Decrease frequency when occurrence is deleted
        UPDATE news_data_dev.words SET
            total_frequency = GREATEST(total_frequency - 1, 0),
            updated_at = CURRENT_TIMESTAMP
        WHERE word_id = OLD.word_id;

        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_word_frequency_test()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE news_data_test.words SET
            total_frequency = total_frequency + 1,
            last_seen = NEW.scraped_at,
            updated_at = CURRENT_TIMESTAMP
        WHERE word_id = NEW.word_id;

        UPDATE news_data_test.words SET first_seen = NEW.scraped_at
        WHERE word_id = NEW.word_id AND first_seen IS NULL;

        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE news_data_test.words SET
            total_frequency = GREATEST(total_frequency - 1, 0),
            updated_at = CURRENT_TIMESTAMP
        WHERE word_id = OLD.word_id;

        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_word_frequency_prod()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE news_data_prod.words SET
            total_frequency = total_frequency + 1,
            last_seen = NEW.scraped_at,
            updated_at = CURRENT_TIMESTAMP
        WHERE word_id = NEW.word_id;

        UPDATE news_data_prod.words SET first_seen = NEW.scraped_at
        WHERE word_id = NEW.word_id AND first_seen IS NULL;

        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE news_data_prod.words SET
            total_frequency = GREATEST(total_frequency - 1, 0),
            updated_at = CURRENT_TIMESTAMP
        WHERE word_id = OLD.word_id;

        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for each environment with correct functions
CREATE TRIGGER trigger_dev_word_frequency
    AFTER INSERT OR DELETE ON news_data_dev.word_occurrences
    FOR EACH ROW EXECUTE FUNCTION update_word_frequency_dev();

CREATE TRIGGER trigger_test_word_frequency
    AFTER INSERT OR DELETE ON news_data_test.word_occurrences
    FOR EACH ROW EXECUTE FUNCTION update_word_frequency_test();

CREATE TRIGGER trigger_prod_word_frequency
    AFTER INSERT OR DELETE ON news_data_prod.word_occurrences
    FOR EACH ROW EXECUTE FUNCTION update_word_frequency_prod();