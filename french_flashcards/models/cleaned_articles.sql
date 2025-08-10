{{ config(materialized='view') }}

select 
    id as article_id,
    url,
    source_id,
    article_date,
    
    -- Clean title and text
    lower(trim(title)) as title_clean,
    regexp_replace(full_text, '<[^>]*>', '', 'g') as text_clean,  -- Strip HTML
    
    -- Basic filtering
    length(regexp_replace(full_text, '<[^>]*>', '', 'g')) as text_length

from {{ source('news_data', 'articles') }}

where full_text is not null 
  and length(trim(full_text)) > 200  -- Minimum content threshold
  and full_text ~ '[àâäçéèêëïîôûùüÿñæœ]'  -- Contains French characters