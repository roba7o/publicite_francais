{{ config(materialized='table') }}

select 
    {{ dbt_utils.generate_surrogate_key(['sentence_id', 'word_position']) }} as word_occurrence_id,
    sentence_id,
    article_id, 
    source_id,
    word_position,
    word_clean,
    sentence_text

from (
    select 
        sentence_id,
        article_id,
        source_id,
        sentence_text,
        lower(trim(word)) as word_clean,
        row_number() over (partition by sentence_id order by sentence_id) as word_position
        
    from (
        select 
            sentence_id,
            article_id,
            source_id, 
            sentence_text,
            unnest(string_to_array(
                regexp_replace(sentence_text, '[^\w\sàâäçéèêëïîôûùüÿñæœ]', ' ', 'g'),  -- Keep only letters and French chars
                ' '
            )) as word
        from {{ ref('sentences') }}
    ) word_splits
) word_positions

where length(word_clean) >= 3  -- Minimum word length
  and word_clean !~ '^[0-9]+$'  -- Not just numbers
  and word_clean not in ('les', 'des', 'une', 'dans', 'avec', 'pour', 'que', 'qui', 'est', 'son', 'sont', 'ont', 'par', 'sur', 'aux')  -- Basic stopwords