{{ config(materialized='table') }}

-- Junction table: Many-to-many relationship between sentences and words
select 
    {{ dbt_utils.generate_surrogate_key(['sentence_id', 'word_id', 'word_position']) }} as occurrence_id,
    sentences.sentence_id,
    words.word_id,
    sentences.article_id,
    sentences.source_name,
    words.word_clean,
    sentences.sentence_text,
    word_positions.word_position
    
from {{ ref('sentences') }} sentences

cross join lateral (
    -- Extract words from each sentence with positions
    select 
        lower(trim(word)) as word_clean,
        row_number() over () as word_position
    from unnest(string_to_array(
        regexp_replace(sentences.sentence_text, '[^\w\sàâäçéèêëïîôûùüÿñæœ]', ' ', 'g'),
        ' '
    )) as word
    where length(trim(word)) >= 3
      and trim(word) !~ '^[0-9]+$'
) word_positions

inner join {{ ref('raw_words') }} words 
    on words.word_clean = word_positions.word_clean
    and not words.is_stopword 
    and not words.is_junk_word 
    and not words.too_short 
    and not words.is_numeric 
    and not words.mostly_numeric
    and words.frequency >= 2  -- Quality filter