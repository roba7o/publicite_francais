{{ config(materialized='table') }}

select 
    word_clean,
    count(distinct article_id) as articles_containing_word,
    sum(frequency_in_article) as total_frequency,
    round(avg(frequency_in_article), 2) as avg_frequency_per_article,
    
    -- Best example sentence (shortest one for clarity)
    (
        select sentence_text 
        from {{ ref('words') }} w2 
        where w2.word_clean = wfa.word_clean
        order by length(sentence_text) 
        limit 1
    ) as example_sentence

from {{ ref('word_frequency_by_article') }} wfa

group by word_clean

having count(distinct article_id) >= 2  -- Word must appear in at least 2 articles
   and sum(frequency_in_article) >= 3   -- Word must appear at least 3 times total

order by total_frequency desc