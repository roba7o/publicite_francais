-- Stage 2: Basic staging model that selects from raw articles
-- This is the first dbt transformation - just cleaning up the raw data

{{ config(materialized='view') }}

select 
    id as article_id,
    source_id,
    title,
    url,
    article_date,
    scraped_at,
    full_text,
    num_paragraphs,
    
    -- Add some basic cleaning
    lower(trim(title)) as title_clean,
    length(full_text) as text_length,
    
    -- Calculate days since publication
    current_date - article_date::date as days_since_published

from {{ source('news_data', 'articles') }}

-- Only include articles with actual content
where full_text is not null 
  and length(trim(full_text)) > 100