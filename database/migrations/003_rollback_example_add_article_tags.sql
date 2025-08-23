-- Rollback Migration: Remove article tags functionality (EXAMPLE)
-- Created: 2025-08-22
-- Description: Removes article tags tables and relationships
--
-- This rollback undoes migration 003_example_add_article_tags.sql

-- Remove article tags functionality
DO $$
DECLARE
    schema_name text;
BEGIN
    FOR schema_name IN VALUES ('news_data_dev'), ('news_data_test'), ('news_data_prod')
    LOOP
        -- Drop relationship table first (foreign key constraints)
        EXECUTE format('DROP TABLE IF EXISTS %I.raw_articles_tags CASCADE', schema_name);
        
        -- Drop tags table
        EXECUTE format('DROP TABLE IF EXISTS %I.article_tags CASCADE', schema_name);
                       
        RAISE NOTICE 'Removed article tags functionality from schema: %', schema_name;
    END LOOP;
END $$;