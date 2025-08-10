{{ config(materialized='table') }}

select 
    {{ dbt_utils.generate_surrogate_key(['article_id', 'word_clean']) }} as word_article_id,
    article_id,
    source_id,
    word_clean,
    count(*) as frequency_in_article,
    
    -- Sample sentences where this word appears in this article
    string_agg(distinct sentence_text, ' | ' order by sentence_text) as example_sentences

from {{ ref('words') }}

group by article_id, source_id, word_clean