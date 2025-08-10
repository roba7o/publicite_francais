-- =============================================================================
-- TEST ENVIRONMENT TABLES  
-- =============================================================================

-- News sources configuration table (test)
CREATE TABLE IF NOT EXISTS news_data_test.news_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    scraper_class VARCHAR(200),
    parser_class VARCHAR(200),
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Articles metadata table (test)
CREATE TABLE IF NOT EXISTS news_data_test.articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES news_data_test.news_sources(id),
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    article_date DATE,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    full_text TEXT,
    num_paragraphs INTEGER,
    UNIQUE(source_id, url),
    UNIQUE(source_id, title, article_date)
);

-- Word frequencies table (test)
CREATE TABLE IF NOT EXISTS news_data_test.word_frequencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES news_data_test.articles(id) ON DELETE CASCADE,
    word VARCHAR(100) NOT NULL,
    frequency INTEGER NOT NULL CHECK (frequency > 0),
    context TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Processing logs table (test)
CREATE TABLE IF NOT EXISTS news_data_test.processing_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES news_data_test.news_sources(id),
    run_type VARCHAR(20) NOT NULL CHECK (run_type IN ('live', 'offline', 'test')),
    articles_attempted INTEGER DEFAULT 0,
    articles_processed INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT
);

-- Indexes for test tables
CREATE INDEX IF NOT EXISTS idx_test_articles_source_id ON news_data_test.articles(source_id);
CREATE INDEX IF NOT EXISTS idx_test_articles_scraped_at ON news_data_test.articles(scraped_at);
CREATE INDEX IF NOT EXISTS idx_test_word_frequencies_article_id ON news_data_test.word_frequencies(article_id);

-- Insert test sources
INSERT INTO news_data_test.news_sources (name, base_url, enabled, scraper_class, parser_class) VALUES
    ('Slate.fr', 'https://www.slate.fr', true, 'scrapers.slate_fr_scraper.SlateFrURLScraper', 'parsers.slate_fr_parser.SlateFrArticleParser'),
    ('FranceInfo.fr', 'https://www.franceinfo.fr', true, 'scrapers.france_info_scraper.FranceInfoURLScraper', 'parsers.france_info_parser.FranceInfoArticleParser'),
    ('TF1 Info', 'https://www.tf1info.fr', true, 'scrapers.tf1_info_scraper.TF1InfoURLScraper', 'parsers.tf1_info_parser.TF1InfoArticleParser'),
    ('Depeche.fr', 'https://www.ladepeche.fr', true, 'scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper', 'parsers.ladepeche_fr_parser.LadepecheFrArticleParser')
ON CONFLICT (name) DO NOTHING;

-- Grant permissions
GRANT USAGE ON SCHEMA news_data_test TO news_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA news_data_test TO news_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA news_data_test TO news_user;