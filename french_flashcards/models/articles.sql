{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['url'], 'unique': True},
            {'columns': ['source']},
            {'columns': ['scraped_at']}
        ]
    )
}}

-- Deduplicated articles using pure ELT approach
-- Takes latest version of each URL, extracting clean article data from raw HTML

WITH deduplicated_raw AS (
    SELECT DISTINCT ON (url) 
        id,
        url,
        raw_html,
        source,
        scraped_at,
        response_status,
        content_length
    FROM {{ source('news_data', 'raw_articles') }}
    WHERE response_status = 200
        AND content_length > 1000  -- Filter out error pages
    ORDER BY url, scraped_at DESC  -- Latest version wins
),

-- Extract clean article data from raw HTML
articles_parsed AS (
    SELECT 
        id,
        url,
        source,
        scraped_at,
        
        -- Basic HTML extraction (this would be expanded with proper parsing)
        -- For now, use simple regex/string functions as placeholder
        CASE 
            WHEN raw_html ~ '<title[^>]*>([^<]+)</title>' 
            THEN regexp_replace(
                substring(raw_html from '<title[^>]*>([^<]+)</title>'), 
                '&[a-zA-Z0-9]+;', '', 'g'
            )
            ELSE 'No Title Found'
        END as title,
        
        -- Extract text content (simplified - would use proper HTML parser in production)
        regexp_replace(
            regexp_replace(raw_html, '<[^>]*>', ' ', 'g'),  -- Remove HTML tags
            '\s+', ' ', 'g'  -- Normalize whitespace
        ) as full_text,
        
        -- Extract date from scraped_at for now
        scraped_at::date as article_date,
        
        source as source_name
        
    FROM deduplicated_raw
    WHERE raw_html IS NOT NULL 
        AND length(raw_html) > 1000
)

SELECT * FROM articles_parsed
WHERE title != 'No Title Found'
    AND length(full_text) > 500  -- Ensure meaningful content