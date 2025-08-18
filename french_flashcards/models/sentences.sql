{{ config(materialized='table') }}

-- Extract individual sentences from articles
select 
    {{ dbt_utils.generate_surrogate_key(['id', 'sentence_position']) }} as sentence_id,
    id as article_id,
    source_name,
    title as article_title,
    url,
    sentence_position,
    sentence_text,
    length(sentence_text) as sentence_length
    
from (
    select 
        id,
        source_name,
        title,
        url,
        row_number() over (partition by id order by id) as sentence_position,
        trim(sentence) as sentence_text
    from (
        select 
            id,
            source_name,
            title,
            url,
            unnest(string_to_array(
                regexp_replace(full_text, '<[^>]*>', '', 'g'), -- Strip HTML
                '.'
            )) as sentence
        from {{ source('news_data', 'articles') }}
        where full_text is not null 
          and length(trim(full_text)) > 200
          and full_text ~ '[àâäçéèêëïîôûùüÿñæœ]'  -- Contains French characters
    ) sentence_splits
) sentence_data

where length(sentence_text) >= 10  -- Minimum sentence length
  and sentence_text ~ '[àâäçéèêëïîôûùüÿñæœ]'  -- Must contain French characters  
  and sentence_text !~ '^[[:space:]]*$'  -- Not just whitespace
  and sentence_text ~ '[a-zA-ZàâäçéèêëïîôûùüÿñæœÀÂÄÇÉÈÊËÏÎÔÛÙÜŸÑÆŒ]'  -- Contains actual letters