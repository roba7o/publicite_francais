{{ config(materialized='table') }}

select 
    {{ dbt_utils.generate_surrogate_key(['article_id', 'sentence_number']) }} as sentence_id,
    article_id,
    source_id,
    sentence_number,
    sentence_text,
    length(sentence_text) as sentence_length

from (
    select 
        article_id,
        source_id,
        trim(unnest(string_to_array(
            regexp_replace(text_clean, '[.!?]+', '|', 'g'),  -- Replace sentence endings with |
            '|'
        ))) as sentence_text,
        row_number() over (partition by article_id order by article_id) as sentence_number
        
    from {{ ref('cleaned_articles') }}
) sentences

where length(trim(sentence_text)) > 20  -- Filter very short sentences
  and sentence_text != ''