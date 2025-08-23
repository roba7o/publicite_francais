-- Migration: Add article tags functionality (EXAMPLE)
-- Created: 2025-08-22
-- Description: Adds tags table and relationship to articles for categorization
--
-- This is an EXAMPLE migration to demonstrate rollback functionality.
-- To rollback: make db-rollback TARGET=002

-- Add tags table and article_tags relationship
DO $$
DECLARE
    schema_name text;
BEGIN
    FOR schema_name IN VALUES ('news_data_dev'), ('news_data_test'), ('news_data_prod')
    LOOP
        -- Create tags table
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.article_tags (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                description TEXT,
                color VARCHAR(7), -- hex color code
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )', schema_name);

        -- Create article-tags relationship table
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.raw_articles_tags (
                article_id UUID NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (article_id, tag_id),
                FOREIGN KEY (article_id) REFERENCES %I.raw_articles(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES %I.article_tags(id) ON DELETE CASCADE
            )', schema_name, schema_name, schema_name);

        -- Insert some sample tags
        EXECUTE format('
            INSERT INTO %I.article_tags (name, description, color) VALUES 
            (''breaking'', ''Breaking news articles'', ''#FF0000''),
            (''analysis'', ''In-depth analysis pieces'', ''#0066CC''),
            (''local'', ''Local news stories'', ''#00AA00'')
            ON CONFLICT (name) DO NOTHING
        ', schema_name);

        -- Create indexes for performance
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_article_tags_name ON %I.article_tags(name)', 
                       replace(schema_name, '_', ''), schema_name);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_raw_articles_tags_article ON %I.raw_articles_tags(article_id)', 
                       replace(schema_name, '_', ''), schema_name);
                       
        RAISE NOTICE 'Added article tags functionality to schema: %', schema_name;
    END LOOP;
END $$;