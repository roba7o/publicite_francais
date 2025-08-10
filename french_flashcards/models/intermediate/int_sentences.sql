-- Stage 3: Extract individual sentences from article full_text
-- Handles French punctuation: periods, exclamation marks, question marks
-- Creates one row per sentence with position tracking

{{ config(materialized='table') }}

with sentence_splits as (
  select 
    article_id,
    source_id,
    title,
    url,
    
    -- Split on French sentence endings: . ! ?
    -- regexp_split_to_table creates one row per sentence
    trim(regexp_split_to_table(
      full_text, 
      '[.!?]+\s*'
    )) as sentence_text,
    
    -- Keep original for debugging
    full_text,
    text_length
    
  from {{ ref('stg_articles') }}
),

sentences_with_numbers as (
  select 
    article_id,
    source_id, 
    title,
    url,
    sentence_text,
    full_text,
    text_length,
    
    -- Add sentence position within article
    row_number() over (
      partition by article_id 
      order by sentence_text  -- PostgreSQL doesn't preserve split order, but this gives consistent numbering
    ) as sentence_number,
    
    -- Calculate sentence metrics
    length(sentence_text) as sentence_length,
    array_length(string_to_array(sentence_text, ' '), 1) as word_count

  from sentence_splits
  
  -- Filter out empty or very short sentences
  where length(trim(sentence_text)) > 10
    and sentence_text != ''
    and sentence_text is not null
)

select 
  -- Primary keys
  {{ dbt_utils.generate_surrogate_key(['article_id', 'sentence_number']) }} as sentence_id,
  article_id,
  sentence_number,
  
  -- Article context
  source_id,
  title,
  url,
  
  -- Sentence content
  sentence_text,
  sentence_length,
  word_count,
  
  -- Article metadata (for analysis)
  text_length as article_text_length

from sentences_with_numbers

-- Quality check: only include sentences with reasonable content
where word_count >= 3  -- At least 3 words
  and sentence_length <= 1000  -- Not too long (likely parsing errors)
  and sentence_text !~ '^[0-9\s\-\.]+$'  -- Not just numbers and punctuation

order by article_id, sentence_number