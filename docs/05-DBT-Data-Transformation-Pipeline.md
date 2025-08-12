# dbt Data Transformation Pipeline

## How Raw Articles Become Flashcard Data Through SQL Transformations

This document explains the **dbt (data build tool)** implementation - how raw article data is transformed into structured vocabulary data for flashcards through declarative SQL transformations.

## dbt Architecture Overview

### **Why Use dbt for Text Processing?**
- **SQL is better than Python** for large-scale text transformations
- **Declarative approach**: Describe *what* you want, not *how* to get it
- **Version controlled transformations**: All changes tracked in Git
- **Easy testing and validation**: Built-in data quality checks
- **Incremental processing**: Only process new articles

### **Data Flow Pipeline**
```
Raw Articles (Python) → dbt Models → Analytics Tables (Django)
```

## dbt Project Structure

### **Configuration** (`dbt_project.yml`)
```yaml
name: 'french_flashcards'
version: '1.0.0'
profile: 'french_flashcards'

model-paths: ["models"]
analysis-paths: ["analyses"] 
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]

models:
  french_flashcards:
    +materialized: table  # Create physical tables, not views
```

### **Database Connection** (`profiles.yml`)
```yaml
french_flashcards:
  outputs:
    dev:
      type: postgres
      host: localhost
      user: news_user
      password: news_pass
      port: 5432
      dbname: french_news
      schema: french_flashcards
      threads: 4
      keepalives_idle: 0
```

## Transformation Pipeline Deep Dive

### **1. Source Definition** (`models/sources.yml`)

```yaml
version: 2

sources:
  - name: news_data
    description: "Raw article data from Python scraper"
    tables:
      - name: articles
        description: "Raw articles with title, full_text, and metadata"
        columns:
          - name: id
            description: "Primary key (UUID)"
          - name: source_id  
            description: "Foreign key to news_sources table"
          - name: title
            description: "Article headline"
          - name: full_text
            description: "Complete article content"
          - name: article_date
            description: "Publication date (YYYY-MM-DD or NULL)"
          - name: scraped_at
            description: "When article was scraped"
```

**Source Benefits:**
- **Documentation**: Clear data lineage from Python to dbt
- **Testing**: Validate source data quality
- **Freshness**: Monitor when source data was last updated

### **2. Sentence Extraction** (`models/sentences.sql`)

```sql
{{ config(materialized='table') }}

SELECT 
    id as article_id,
    ROW_NUMBER() OVER (PARTITION BY id ORDER BY sentence_num) as sentence_id,
    TRIM(sentence_text) as sentence_text,
    LENGTH(TRIM(sentence_text)) as sentence_length,
    article_date,
    source_id,
    scraped_at
FROM (
    SELECT 
        id,
        unnest(string_to_array(full_text, '. ')) as sentence_text,
        ROW_NUMBER() OVER (PARTITION BY id ORDER BY position) as sentence_num,
        article_date,
        source_id,
        scraped_at
    FROM {{ source('news_data', 'articles') }}
    WHERE full_text IS NOT NULL 
      AND LENGTH(full_text) > 100  -- Filter out short articles
) sentences
WHERE LENGTH(TRIM(sentence_text)) > 20  -- Filter out short sentences
  AND TRIM(sentence_text) NOT LIKE '%@%'  -- Filter out email addresses
  AND TRIM(sentence_text) NOT LIKE 'http%'  -- Filter out URLs
```

**Sentence Processing Logic:**
- **Split on periods**: `string_to_array(full_text, '. ')`
- **Generate IDs**: `ROW_NUMBER()` creates unique sentence identifiers
- **Quality filters**: Remove short sentences, emails, URLs
- **Preserve context**: Keep article metadata for each sentence

**Output Structure:**
```
sentence_id | article_id | sentence_text | sentence_length | article_date | source_id
     1      |   uuid-1   | "Le président français..." |      45        | 2025-01-15 | uuid-src
     2      |   uuid-1   | "Cette décision marque..." |      38        | 2025-01-15 | uuid-src
```

### **3. Word Extraction** (`models/raw_words.sql`)

```sql
{{ config(materialized='table') }}

SELECT 
    LOWER(
        regexp_replace(
            word_raw,
            '[^\w\sÀ-ÿ]',  -- Remove punctuation, keep French accents
            '', 
            'g'
        )
    ) as word,
    sentence_id,
    article_id,
    article_date,
    source_id
FROM (
    SELECT 
        regexp_split_to_table(sentence_text, '\s+') as word_raw,
        sentence_id,
        article_id, 
        article_date,
        source_id
    FROM {{ ref('sentences') }}
    WHERE sentence_text IS NOT NULL
) word_extraction
WHERE LENGTH(word_raw) > 2          -- Filter short words (le, la, de)
  AND word_raw NOT LIKE '%@%'       -- Filter email fragments
  AND word_raw NOT LIKE 'http%'     -- Filter URL fragments
  AND word_raw !~ '^[0-9]+$'        -- Filter pure numbers
```

**Word Processing Logic:**
- **Split on whitespace**: `regexp_split_to_table(sentence_text, '\s+')`
- **Clean punctuation**: `regexp_replace()` removes non-word characters
- **Preserve French accents**: `À-ÿ` range keeps accented characters
- **Normalize case**: `LOWER()` for consistent word matching
- **Quality filters**: Remove numbers, email fragments, URLs

**Output Structure:**
```
word      | sentence_id | article_id | article_date | source_id
"président" |     1      |   uuid-1   | 2025-01-15   | uuid-src
"français"  |     1      |   uuid-1   | 2025-01-15   | uuid-src
"décision"  |     2      |   uuid-1   | 2025-01-15   | uuid-src
```

### **4. Word Frequency Analysis** (`models/word_occurrences.sql`)

```sql
{{ config(materialized='table') }}

WITH word_stats AS (
    SELECT 
        word,
        COUNT(*) as frequency,
        COUNT(DISTINCT article_id) as article_count,
        COUNT(DISTINCT source_id) as source_count,
        MIN(article_date) as first_seen,
        MAX(article_date) as last_seen
    FROM {{ ref('raw_words') }}
    WHERE word IS NOT NULL
      AND LENGTH(word) >= 3
    GROUP BY word
),

word_examples AS (
    SELECT 
        w.word,
        array_agg(
            DISTINCT s.sentence_text 
            ORDER BY s.sentence_text 
            LIMIT 3
        ) as example_sentences
    FROM {{ ref('raw_words') }} w
    JOIN {{ ref('sentences') }} s ON w.sentence_id = s.sentence_id
    GROUP BY w.word
)

SELECT 
    ws.word,
    ws.frequency,
    ws.article_count,
    ws.source_count,
    ws.first_seen,
    ws.last_seen,
    we.example_sentences,
    
    -- Calculate difficulty/priority scores
    CASE 
        WHEN ws.frequency >= 50 THEN 'very_common'
        WHEN ws.frequency >= 20 THEN 'common'
        WHEN ws.frequency >= 10 THEN 'moderate'
        WHEN ws.frequency >= 5  THEN 'uncommon'
        ELSE 'rare'
    END as frequency_category,
    
    -- Diversity score: appears in multiple articles/sources
    ROUND(
        (ws.article_count::float / ws.frequency * 100), 2
    ) as diversity_score

FROM word_stats ws
JOIN word_examples we ON ws.word = we.word
WHERE ws.frequency >= 3  -- Only words appearing 3+ times
ORDER BY ws.frequency DESC, ws.word
```

**Analytics Features:**
- **Frequency counting**: How often each word appears
- **Distribution analysis**: Across how many articles/sources
- **Example sentences**: Context for learning
- **Difficulty categorization**: Common vs rare words
- **Diversity scoring**: Words in many articles vs repeated in few

**Output Structure:**
```
word      | frequency | article_count | source_count | example_sentences | frequency_category
"président" |    45    |      12       |      3       | ["Le président...", "..."] | very_common
"économie"  |    23    |       8       |      2       | ["L'économie...", "..."]   | common
"réforme"   |    15    |       5       |      2       | ["Cette réforme...", "..."] | moderate
```

### **5. Flashcard Data Preparation** (`models/vocabulary_for_flashcards.sql`)

```sql
{{ config(materialized='table') }}

WITH filtered_words AS (
    SELECT *
    FROM {{ ref('word_occurrences') }}
    WHERE frequency >= 5                    -- Minimum frequency threshold
      AND LENGTH(word) >= 4                 -- Longer words more useful
      AND word NOT IN (                     -- Filter common stop words
          SELECT word 
          FROM {{ ref('french_stopwords') }}  -- Seed data with stop words
      )
),

difficulty_scoring AS (
    SELECT 
        *,
        -- Composite difficulty score
        CASE 
            WHEN frequency_category = 'very_common' AND diversity_score > 50 THEN 1  -- Easy
            WHEN frequency_category = 'common' AND diversity_score > 30 THEN 2       -- Medium
            WHEN frequency_category = 'moderate' THEN 3                              -- Hard
            ELSE 4  -- Very hard
        END as difficulty_level,
        
        -- Learning priority (high frequency + high diversity = priority)
        (frequency * diversity_score / 100.0) as learning_priority
        
    FROM filtered_words
)

SELECT 
    word,
    frequency,
    article_count,
    example_sentences[1] as primary_example,
    example_sentences[2] as secondary_example,
    frequency_category,
    diversity_score,
    difficulty_level,
    learning_priority,
    
    -- Prepare flashcard format
    CONCAT(
        'Word: ', word, 
        ' | Examples: ', example_sentences[1]
    ) as flashcard_front,
    
    CONCAT(
        'Frequency: ', frequency, ' occurrences',
        ' | Difficulty: ', difficulty_level,
        ' | More examples: ', example_sentences[2]
    ) as flashcard_back,
    
    -- Metadata for Django integration
    current_timestamp as created_at,
    'dbt_pipeline' as created_by

FROM difficulty_scoring
WHERE learning_priority >= 10  -- Only high-priority words
ORDER BY learning_priority DESC, frequency DESC
LIMIT 1000  -- Top 1000 words for flashcards
```

**Flashcard Features:**
- **Stop word filtering**: Remove "le", "la", "et", "dans", etc.
- **Difficulty scoring**: Based on frequency and distribution
- **Learning priority**: Composite score for study ordering
- **Flashcard formatting**: Ready-to-use front/back content
- **Django integration**: Metadata for web application

## dbt Execution Commands

### **Development Workflow**
```bash
# Run all transformations
dbt run

# Run specific model
dbt run --select sentences

# Run model and downstream dependencies  
dbt run --select sentences+

# Test data quality
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

### **Production Workflow**
```bash
# Full refresh (rebuild all tables)
dbt run --full-refresh

# Incremental processing (only new data)
dbt run --select vocabulary_for_flashcards --vars '{"incremental_strategy": "merge"}'
```

## Data Quality Testing

### **Generic Tests** (`models/schema.yml`)
```yaml
models:
  - name: sentences
    tests:
      - dbt_utils.row_count_range:
          min_value: 100  # Expect at least 100 sentences
    columns:
      - name: sentence_id
        tests:
          - unique
          - not_null
      - name: sentence_length
        tests:
          - dbt_utils.accepted_range:
              min_value: 20
              max_value: 1000

  - name: word_occurrences  
    tests:
      - dbt_utils.row_count_range:
          min_value: 50   # Expect at least 50 unique words
    columns:
      - name: word
        tests:
          - unique
          - not_null
      - name: frequency
        tests:
          - dbt_utils.accepted_range:
              min_value: 3    # All words appear at least 3 times
```

### **Custom Data Quality Tests**
```sql
-- tests/assert_no_empty_sentences.sql
SELECT sentence_id
FROM {{ ref('sentences') }}
WHERE sentence_text IS NULL 
   OR TRIM(sentence_text) = ''
   OR LENGTH(sentence_text) < 10
```

## Performance Optimizations

### **Materialization Strategy**
```sql
-- For large datasets, use incremental materialization
{{ config(
    materialized='incremental',
    unique_key='sentence_id',
    on_schema_change='fail'
) }}

{% if is_incremental() %}
  -- Only process new articles
  WHERE scraped_at > (SELECT MAX(scraped_at) FROM {{ this }})
{% endif %}
```

### **Indexing Strategy**
```sql
-- Post-hooks for performance
{{ config(
    post_hook="CREATE INDEX IF NOT EXISTS idx_word_frequency ON {{ this }} (word, frequency DESC)"
) }}
```

### **Partitioning for Scale**
```sql
-- Partition by date for large datasets
{{ config(
    materialized='table',
    post_hook="ALTER TABLE {{ this }} PARTITION BY RANGE (article_date)"
) }}
```

## Integration with Django

### **Final Output Structure**
The `vocabulary_for_flashcards` table provides a clean API for Django:

```python
# Django model can directly query dbt output
class FlashcardWord(models.Model):
    word = models.CharField(max_length=100)
    frequency = models.IntegerField()
    difficulty_level = models.IntegerField()
    learning_priority = models.FloatField()
    primary_example = models.TextField()
    flashcard_front = models.TextField()
    flashcard_back = models.TextField()
    
    class Meta:
        db_table = 'french_flashcards.vocabulary_for_flashcards'
```

This dbt pipeline transforms raw news articles into structured vocabulary data optimized for language learning, providing a clean separation between data collection (Python) and data processing (SQL).