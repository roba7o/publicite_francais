-- =============================================================================
-- MINIMAL DBT MODELS FOR FRENCH WORD FREQUENCY ANALYSIS
-- =============================================================================

-- FILE: models/sources.yml
-- =============================================================================
version: 2

sources:
  - name: news_data
    schema: news_data
    tables:
      - name: articles
        description: Raw scraped French articles
        columns:
          - name: id
          - name: url
          - name: title  
          - name: full_text
          - name: article_date
          - name: source_id

-- =============================================================================
-- FILE: models/cleaned_articles.sql
-- =============================================================================
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

-- =============================================================================
-- FILE: models/sentences.sql  
-- =============================================================================
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

-- =============================================================================
-- FILE: models/words.sql
-- =============================================================================  
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

-- =============================================================================
-- FILE: models/word_frequency_by_article.sql
-- =============================================================================
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

-- =============================================================================  
-- FILE: models/word_frequency_overall.sql
-- =============================================================================
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