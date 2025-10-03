-- Migration 001: Complete initial schema for French news scraper
-- Clean, schema-free approach with all required tables
-- Works identically in both dev and test databases

-- Raw articles table - stores scraped HTML content with metadata
CREATE TABLE IF NOT EXISTS raw_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL,
    raw_html TEXT NOT NULL,
    site TEXT NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    response_status INTEGER,
    content_length INTEGER,
    -- Trafilatura extracted fields
    extracted_text TEXT,
    title TEXT,
    author TEXT,
    date_published TIMESTAMP WITH TIME ZONE,
    language VARCHAR(10),
    summary TEXT,
    keywords TEXT,
    extraction_status VARCHAR(20) DEFAULT 'pending',
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Word events table - stores individual word occurrences from articles
CREATE TABLE IF NOT EXISTS word_events (
    event_id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    article_id UUID NOT NULL REFERENCES raw_articles(id) ON DELETE CASCADE,
    position_in_article INTEGER NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Stop words table - French stop words for filtering
CREATE TABLE IF NOT EXISTS stop_words (
    word TEXT PRIMARY KEY,
    language VARCHAR(10) DEFAULT 'fr',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes for raw_articles
CREATE INDEX IF NOT EXISTS idx_raw_articles_site ON raw_articles(site);
CREATE INDEX IF NOT EXISTS idx_raw_articles_scraped_at ON raw_articles(scraped_at);
CREATE INDEX IF NOT EXISTS idx_raw_articles_extraction_status ON raw_articles(extraction_status);

-- Performance indexes for word_events
CREATE INDEX IF NOT EXISTS idx_word_events_word ON word_events(word);
CREATE INDEX IF NOT EXISTS idx_word_events_article ON word_events(article_id);
CREATE INDEX IF NOT EXISTS idx_word_events_scraped ON word_events(scraped_at);
CREATE INDEX IF NOT EXISTS idx_word_events_word_time ON word_events(word, scraped_at);

-- Performance index for stop_words
CREATE INDEX IF NOT EXISTS idx_stop_words_word ON stop_words(word);

-- Populate stop words table with French stop words
INSERT INTO stop_words (word, language) VALUES
('a', 'fr'), ('an', 'fr'), ('and', 'fr'), ('are', 'fr'), ('as', 'fr'), ('at', 'fr'),
('be', 'fr'), ('but', 'fr'), ('by', 'fr'), ('for', 'fr'), ('if', 'fr'), ('in', 'fr'),
('into', 'fr'), ('is', 'fr'), ('it', 'fr'), ('no', 'fr'), ('not', 'fr'), ('of', 'fr'),
('on', 'fr'), ('or', 'fr'), ('s', 'fr'), ('such', 'fr'), ('t', 'fr'), ('that', 'fr'),
('the', 'fr'), ('their', 'fr'), ('then', 'fr'), ('there', 'fr'), ('these', 'fr'),
('they', 'fr'), ('this', 'fr'), ('to', 'fr'), ('was', 'fr'), ('will', 'fr'), ('with', 'fr'),
('au', 'fr'), ('aux', 'fr'), ('avec', 'fr'), ('ce', 'fr'), ('ces', 'fr'), ('dans', 'fr'),
('de', 'fr'), ('des', 'fr'), ('du', 'fr'), ('elle', 'fr'), ('en', 'fr'), ('et', 'fr'),
('eux', 'fr'), ('il', 'fr'), ('je', 'fr'), ('la', 'fr'), ('le', 'fr'), ('leur', 'fr'),
('lui', 'fr'), ('ma', 'fr'), ('mais', 'fr'), ('me', 'fr'), ('même', 'fr'), ('mes', 'fr'),
('moi', 'fr'), ('mon', 'fr'), ('ne', 'fr'), ('nos', 'fr'), ('notre', 'fr'), ('nous', 'fr'),
('on', 'fr'), ('ou', 'fr'), ('par', 'fr'), ('pas', 'fr'), ('pour', 'fr'), ('qu', 'fr'),
('que', 'fr'), ('qui', 'fr'), ('sa', 'fr'), ('se', 'fr'), ('ses', 'fr'), ('son', 'fr'),
('sur', 'fr'), ('ta', 'fr'), ('te', 'fr'), ('tes', 'fr'), ('toi', 'fr'), ('ton', 'fr'),
('tu', 'fr'), ('un', 'fr'), ('une', 'fr'), ('vos', 'fr'), ('votre', 'fr'), ('vous', 'fr'),
('c', 'fr'), ('d', 'fr'), ('j', 'fr'), ('l', 'fr'), ('à', 'fr'), ('m', 'fr'),
('n', 'fr'), ('y', 'fr'), ('été', 'fr'), ('étée', 'fr'), ('étées', 'fr'), ('étés', 'fr'),
('étant', 'fr'), ('suis', 'fr'), ('es', 'fr'), ('est', 'fr'), ('sommes', 'fr'),
('êtes', 'fr'), ('sont', 'fr'), ('serai', 'fr'), ('seras', 'fr'), ('sera', 'fr'),
('serons', 'fr'), ('serez', 'fr'), ('seront', 'fr'), ('serais', 'fr'), ('serait', 'fr'),
('serions', 'fr'), ('seriez', 'fr'), ('seraient', 'fr'), ('étais', 'fr'), ('était', 'fr'),
('étions', 'fr'), ('étiez', 'fr'), ('étaient', 'fr'), ('fus', 'fr'), ('fut', 'fr'),
('fûmes', 'fr'), ('fûtes', 'fr'), ('furent', 'fr'), ('sois', 'fr'), ('soit', 'fr'),
('soyons', 'fr'), ('soyez', 'fr'), ('soient', 'fr'), ('fusse', 'fr'), ('fusses', 'fr'),
('fût', 'fr'), ('fussions', 'fr'), ('fussiez', 'fr'), ('fussent', 'fr'), ('ayant', 'fr'),
('eu', 'fr'), ('eue', 'fr'), ('eues', 'fr'), ('eus', 'fr'), ('ai', 'fr'), ('as', 'fr'),
('avons', 'fr'), ('avez', 'fr'), ('ont', 'fr'), ('aurai', 'fr'), ('auras', 'fr'),
('aura', 'fr'), ('aurons', 'fr'), ('aurez', 'fr'), ('auront', 'fr'), ('aurais', 'fr'),
('aurait', 'fr'), ('aurions', 'fr'), ('auriez', 'fr'), ('auraient', 'fr'), ('avais', 'fr'),
('avait', 'fr'), ('avions', 'fr'), ('aviez', 'fr'), ('avaient', 'fr'), ('eut', 'fr'),
('eûmes', 'fr'), ('eûtes', 'fr'), ('eurent', 'fr'), ('aie', 'fr'), ('aies', 'fr'),
('ait', 'fr'), ('ayons', 'fr'), ('ayez', 'fr'), ('aient', 'fr'), ('eusse', 'fr'),
('eusses', 'fr'), ('eût', 'fr'), ('eussions', 'fr'), ('eussiez', 'fr'), ('eussent', 'fr'),
('ceci', 'fr'), ('celà', 'fr'), ('cet', 'fr'), ('cette', 'fr'), ('ici', 'fr'), ('ils', 'fr'),
('les', 'fr'), ('leurs', 'fr'), ('quel', 'fr'), ('quels', 'fr'), ('quelle', 'fr'),
('quelles', 'fr'), ('sans', 'fr'), ('soi', 'fr')
ON CONFLICT (word) DO NOTHING;