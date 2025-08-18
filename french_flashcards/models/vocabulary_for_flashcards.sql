{{ config(materialized='table') }}

-- Aggregated vocabulary with frequency data for flashcard creation
select 
    words.word_id,
    words.word_clean as french_word,
    
    -- Frequency metrics
    count(distinct occurrences.article_id) as appears_in_articles,
    count(distinct occurrences.sentence_id) as appears_in_sentences,  
    count(*) as total_occurrences,
    
    -- Context examples
    (
        select sentence_text 
        from {{ ref('word_occurrences') }} wo2
        where wo2.word_id = words.word_id
        order by length(sentence_text) asc  -- Shortest sentence first
        limit 1
    ) as shortest_example,
    
    (
        select sentence_text 
        from {{ ref('word_occurrences') }} wo3
        where wo3.word_id = words.word_id
        order by length(sentence_text) desc  -- Longest sentence 
        limit 1
    ) as longest_example,
    
    -- Source variety
    count(distinct occurrences.source_name) as appears_in_sources

from {{ ref('raw_words') }} words

inner join {{ ref('word_occurrences') }} occurrences 
    on occurrences.word_id = words.word_id

where not words.is_stopword 
  and not words.is_junk_word 
  and not words.too_short 
  and not words.is_numeric 
  and not words.mostly_numeric
  and words.frequency >= 2

group by words.word_id, words.word_clean

-- Filter for quality vocabulary words
having count(distinct occurrences.article_id) >= 2  -- Must appear in multiple articles
   and count(*) >= 3  -- Must appear at least 3 times total
   
order by total_occurrences desc, appears_in_articles desc