{{ config(materialized='table') }}

-- Extract unique words (vocabulary)
select distinct
    {{ dbt_utils.generate_surrogate_key(['word_clean']) }} as word_id,
    word_clean,
    length(word_clean) as word_length
    
from (
    select 
        lower(trim(word)) as word_clean
    from (
        select 
            unnest(string_to_array(
                regexp_replace(sentence_text, '[^\w\sàâäçéèêëïîôûùüÿñæœ]', ' ', 'g'),
                ' '
            )) as word
        from {{ ref('sentences') }}
    ) word_splits
) words

where length(word_clean) >= 3  -- Minimum word length
  and word_clean !~ '^[0-9]+$'  -- Not just numbers
  and word_clean not in (
      'les', 'des', 'une', 'dans', 'avec', 'pour', 'que', 'qui', 'est', 'son', 
      'sont', 'ont', 'par', 'sur', 'aux', 'mais', 'tout', 'tous', 'cette', 
      'ces', 'leur', 'leurs', 'bien', 'très', 'plus', 'moins', 'comme', 'aussi',
      'elle', 'ils', 'nous', 'vous', 'elles'
  )  -- Basic French stopwords