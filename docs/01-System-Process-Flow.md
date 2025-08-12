# System Process Flow: French News Scraper

## Overview: Complete Pipeline Execution

This document traces the **exact execution flow** when you run `python main.py` or `make pipeline`.

## High-Level Data Flow

```
main.py → DatabaseProcessor → ComponentFactory → [Scraper+Parser] → ArticleRepository → PostgreSQL → dbt → Flashcard Tables
```

## Detailed Execution Trace

### 1. **Pipeline Initialization** (`main.py:13-60`)

```python
def main():
    # Step 1: Load environment and setup logging
    setup_logging()
    configure_debug_mode(DEBUG)
    
    # Step 2: Initialize database connection
    initialize_database()  # Creates tables if needed
    
    # Step 3: Load source configurations
    source_configs = get_scraper_configs()  # Returns 4 news sources
    
    # Step 4: Create main processor
    processor = DatabaseProcessor()
```

**What happens here:**
- Environment variables loaded from `.env` or system
- Database connection tested and tables created if missing
- Configuration loaded: 4 news sources (Slate.fr, FranceInfo.fr, TF1 Info, Depeche.fr)
- Main orchestrator (`DatabaseProcessor`) initialized

---

### 2. **Source Processing Loop** (`article_pipeline.py:188-241`)

```python
def process_all_sources(source_configs):
    for config in enabled_sources:
        processed, attempted = self.process_source(config)  # Process each source
```

**For each news source, the system:**

#### 2.1 **Component Creation** (`article_pipeline.py:124-133`)
```python
# Create scraper (finds article URLs)
scraper = self.component_factory.create_scraper(config)

# Get database source ID 
source_id = self.get_source_id(config["name"])  # UUID from news_sources table

# Create parser (extracts article content)
database_parser = self.component_factory.create_parser(config, source_id)
```

#### 2.2 **Content Acquisition** (`article_pipeline.py:39-72`)
```python
def acquire_content(scraper, parser, source_name):
    if OFFLINE:
        return parser.get_test_sources_from_directory(source_name)  # Load test HTML files
    else:
        return self._get_live_sources(scraper, parser, source_name)  # Scrape live web
```

**Live Mode Process:**
1. Scraper visits news site homepage
2. Finds article URLs using CSS selectors
3. Parser fetches first 5 article URLs
4. Returns list of `(BeautifulSoup, URL)` tuples

**Offline Mode Process:**
1. Parser loads HTML files from `src/test_data/raw_url_soup/[SourceName]/`
2. Maps filenames to original URLs using `url_mapping.py`
3. Returns same format: `(BeautifulSoup, URL)` tuples

#### 2.3 **Article Processing Loop** (`article_pipeline.py:159-166`)
```python
for soup, source_identifier in sources:
    success = self.process_article(database_parser, soup, source_identifier, config["name"])
```

**For each article:**

1. **Parse Article** (`database_base_parser.py:189-209`)
   ```python
   article_data = parser.parse_article(soup)  # Site-specific implementation
   # Returns: ArticleData(title, full_text, article_date, num_paragraphs)
   ```

2. **Store to Database** (`database_base_parser.py:211-222`)
   ```python
   success = parser.to_database(article_data, url)
   # Calls repository.store_article()
   ```

---

### 3. **Database Storage Process** (`article_repository.py:101-212`)

```python
def store_article(article_data, url, source_id):
    # Step 1: Parse and validate article date
    parsed_date = self._parse_article_date(article_data.article_date)
    
    with self.db.get_session() as session:
        # Step 2: Check for duplicates (URL-based)
        existing_url = session.execute("SELECT id FROM articles WHERE source_id = :source_id AND url = :url")
        
        # Step 3: Check for duplicates (title+date-based)  
        existing_title_date = session.execute("SELECT id FROM articles WHERE source_id = :source_id AND title = :title AND article_date = :article_date")
        
        # Step 4: Insert new article if no duplicates
        article_id = uuid4()
        session.execute("INSERT INTO articles (id, source_id, title, url, article_date, scraped_at, full_text, num_paragraphs) VALUES (...)")
        session.commit()
```

**Database Operations:**
- **Duplicate Detection**: Prevents same article from being stored twice
- **Date Parsing**: Handles various date formats, stores as YYYY-MM-DD or NULL
- **Transaction Safety**: All-or-nothing database operations
- **UUID Generation**: Each article gets unique identifier

---

### 4. **Data Transformation (dbt)** - `make dbt-run`

After Python scraping completes, dbt processes the raw data:

#### 4.1 **Text Splitting** (`models/sentences.sql`)
```sql
SELECT 
    id as article_id,
    unnest(string_to_array(full_text, '.')) as sentence_text,
    article_date,
    source_id
FROM {{ source('news_data', 'articles') }}
WHERE full_text IS NOT NULL
```
**Result**: Each article sentence becomes a separate row

#### 4.2 **Word Extraction** (`models/raw_words.sql`)
```sql
SELECT 
    regexp_split_to_table(
        lower(regexp_replace(sentence_text, '[^\w\sÀ-ÿ]', '', 'g')), 
        '\s+'
    ) as word,
    sentence_id,
    article_id
FROM {{ ref('sentences') }}
WHERE length(word) > 2
```
**Result**: Each word becomes a separate row with sentence context

#### 4.3 **Frequency Counting** (`models/word_occurrences.sql`)
```sql
SELECT 
    word,
    count(*) as frequency,
    array_agg(DISTINCT sentence_text ORDER BY sentence_text LIMIT 3) as example_sentences
FROM {{ ref('raw_words') }} w
JOIN {{ ref('sentences') }} s ON w.sentence_id = s.id
GROUP BY word
ORDER BY frequency DESC
```
**Result**: Word frequency table with example sentences

#### 4.4 **Flashcard Preparation** (`models/vocabulary_for_flashcards.sql`)
```sql
SELECT 
    word,
    frequency,
    example_sentences[1] as primary_example,
    CASE 
        WHEN frequency >= 10 THEN 'high'
        WHEN frequency >= 5 THEN 'medium' 
        ELSE 'low'
    END as priority_level
FROM {{ ref('word_occurrences') }}
WHERE frequency >= 3  -- Only words appearing 3+ times
```
**Result**: Final flashcard data with priority levels

---

## Error Handling Throughout Pipeline

### **Graceful Degradation**
- **HTTP Failures**: Skip failed articles, continue with others
- **Parse Failures**: Log error, continue to next article  
- **Database Errors**: Rollback transaction, continue processing
- **Date Parse Errors**: Store NULL date, continue with article

### **Success Tracking**
```python
# article_pipeline.py:167-180
processed_count += 1 if success else 0
success_rate = (processed_count / total_attempted * 100)

# Warn if success rate < 50%
if success_rate < 50.0:
    output.warning(f"Low success rate ({success_rate:.1f}%)")
```

### **Comprehensive Logging**
- **Structured Logging**: Machine-readable JSON for monitoring
- **Terminal Output**: Human-readable progress updates
- **Debug Mode**: Detailed HTTP request/response logging

---

## Performance Characteristics

### **Rate Limiting**
- **HTTP Requests**: 1-second delay between requests per parser
- **Connection Pooling**: Reuse HTTP sessions across requests
- **Retry Logic**: 3 attempts for failed requests with exponential backoff

### **Memory Usage**
- **Streaming Processing**: Articles processed one at a time, not batch-loaded
- **Session Reuse**: Single HTTP session per parser class (shared across instances)
- **Database Connections**: Connection pooling via SQLAlchemy

### **Processing Speed**
- **Offline Mode**: ~50 articles/minute (no HTTP delays)
- **Live Mode**: ~30 articles/minute (rate-limited)
- **dbt Processing**: ~1000 words/second transformation

---

## Configuration Impact on Flow

### **Environment Variables**
- `OFFLINE=True`: Use test HTML files instead of live scraping
- `DEBUG=True`: Detailed logging, longer timeouts
- `DATABASE_ENABLED=False`: Skip database storage (testing only)

### **Source Configuration**
```python
# config/source_configs.py
{
    "name": "Slate.fr",
    "enabled": True,  # Skip if False
    "scraper_class": "scrapers.slate_fr_scraper.SlateFrURLScraper",
    "parser_class": "parsers.database_slate_fr_parser.DatabaseSlateFrParser",
    "scraper_kwargs": {"debug": DEBUG}
}
```

### **Database Schema**
- **Schema**: `french_news` (configurable via `NEWS_DATA_SCHEMA`)
- **Tables**: `news_sources`, `articles` (created automatically)
- **Indexes**: Unique constraints on `(source_id, url)` and `(source_id, title, article_date)`

This completes the end-to-end process flow from execution start to final flashcard data.