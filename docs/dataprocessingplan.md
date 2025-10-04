# LLM Implementation Instructions: Clean Architecture

## Context
You are implementing a clean architecture for a French news scraper. The user wants to eliminate all legacy code, separate concerns properly, and create a simple, understandable system.

## Core Principles
- **No backwards compatibility** - Remove all legacy patterns completely
- **Clean separation** - Articles and word processing are separate concerns
- **Simple to understand** - Prioritize clarity over performance
- **Single environment variable** - Use `ENVIRONMENT` only, remove `TEST_MODE`
- **Fail gracefully** - If word extraction fails, continue without word facts
- **NO ARTIFICIAL TEST FIXES** - Fix root cause issues, don't make tests pass artificially
- **NO LEGACY ACCOMMODATION** - Don't rewrite logic to support old patterns
- **FIX SOURCE CODE** - Change the actual implementation, not workarounds

## Implementation Order

### 0. Remove Multi-Schema Environment Logic (FIRST - BEFORE ANYTHING ELSE)
**Goal:** Eliminate all logic that uses one environment with multiple schema-level environments

**Problem Pattern to Remove:**
```python
# BAD - Multiple schemas in one environment
if test_mode:
    schema = "test_schema"
else:
    schema = "public"

# BAD - Schema switching logic
def get_table_name(base_name):
    schema = "test" if TEST_MODE else "public"
    return f"{schema}.{base_name}"

# BAD - Conditional schema references
CREATE TABLE IF NOT EXISTS {schema}.raw_articles ...
```

**Actions Required:**
1. **Search and destroy** all schema-switching logic
2. **Remove** any `schema` parameters in database operations
3. **Delete** any conditional table naming based on environment
4. **Eliminate** multi-schema configuration patterns
5. **Standardize** on single `public` schema for all environments

**Files to Clean:**
- `src/database/database.py` - Remove schema parameters
- `src/database/models.py` - Remove schema logic from table definitions
- `database/migrations/*.sql` - Remove schema conditionals
- Any configuration files with schema switching

**Example Cleanup:**
```python
# REMOVE THIS PATTERN COMPLETELY
def store_article(article, schema="public"):
    table_name = f"{schema}.raw_articles"  # DELETE THIS LOGIC

# REPLACE WITH CLEAN SINGLE SCHEMA
def store_article(article: RawArticle) -> bool:
    # Always use public schema - no conditionals
```

**Validation:**
- ✅ No `schema` variables anywhere in codebase
- ✅ No conditional table naming
- ✅ No schema parameters in functions
- ✅ All SQL references standard table names without schema prefixes

### 1. Environment Configuration (SECOND)
**Goal:** Single source of truth for environment handling

**File:** `src/config/environment.py`
```python
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
VALID_ENVIRONMENTS = {"development", "test", "production"}
IS_TEST = ENVIRONMENT == "test"
DEBUG = ENVIRONMENT == "development"

DATABASE_CONFIG = {
    "development": {...},
    "test": {...},
    "production": {...}
}[ENVIRONMENT]
```

**Remove everywhere:** All references to `TEST_MODE`
**Update imports:** Change `TEST_MODE` to `IS_TEST` in all files

### 2. Data Model Separation (THIRD)
**Goal:** Clean separation between articles and word facts

**File:** `src/database/models.py`
```python
@dataclass
class RawArticle:
    """Article data only - no word processing"""
    url: str
    raw_html: str
    site: str
    # Remove: word_events field
    # Remove: _extract_french_words method

@dataclass
class WordFact:
    """Separate vocabulary fact"""
    word: str
    article_id: str
    position_in_article: int
    scraped_at: str
```

### 3. Word Extraction Service (FOURTH)
**Goal:** Dedicated service for word processing

**Create:** `src/services/word_extractor.py`
```python
class WordExtractor:
    def extract_words_from_article(self, article: RawArticle) -> list[WordFact]:
        """Extract French words, log failures and return empty list"""
        try:
            # Move word extraction logic here
        except Exception as e:
            logger.warning(f"Failed to extract words from article {article.id}: {e}")
            return []  # Fail gracefully but log the issue
```

### 4. Database Operations (FIFTH)
**Goal:** Separate storage operations with retry logic

**File:** `src/database/database.py`
```python
def store_article(article: RawArticle) -> bool:
    """Store single article with exponential backoff retry"""

def store_articles_batch(articles: list[RawArticle], batch_size=100) -> tuple[int, int]:
    """Store multiple articles with retry logic"""

def store_word_fact(word_fact: WordFact) -> bool:
    """Store single word fact with exponential backoff retry"""

def store_word_facts_batch(word_facts: list[WordFact], batch_size=500) -> tuple[int, int]:
    """Store multiple word facts with retry logic"""
```

**Implementation Pattern:**
```python
def retry_with_exponential_backoff(func, max_retries=3):
    """Retry database operations with exponential backoff"""
    import time
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            logger.warning(f"Database operation failed, retrying in {wait_time}s: {e}")
            time.sleep(wait_time)
```

**Remove:** `store_raw_article`, `store_word_events`

### 5. Database Schema (SIXTH)
**Goal:** Clean fact table design for normalized word processing

**Context:** Main branch stores raw articles as unprocessed HTML. This branch processes articles into normalized word facts for vocabulary learning.

**File:** `database/migrations/001_initial_schema.sql`
```sql
-- Keep raw articles table (main branch pattern)
CREATE TABLE raw_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL UNIQUE,
    raw_html TEXT NOT NULL,
    site TEXT NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- NEW: Add normalized word facts table
CREATE TABLE word_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word TEXT NOT NULL,
    article_id UUID NOT NULL REFERENCES raw_articles(id) ON DELETE CASCADE,
    position_in_article INTEGER NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Indexes for word analysis queries
CREATE INDEX idx_word_facts_word ON word_facts(word);
CREATE INDEX idx_word_facts_article_id ON word_facts(article_id);
CREATE INDEX idx_word_facts_scraped_at ON word_facts(scraped_at);
```

**Migration Strategy:**
- Drop existing `word_events` table if it exists
- Start fresh with normalized `word_facts` design
- Main branch compatibility: Keep `raw_articles` structure but add word processing layer

### 6. Pipeline Orchestration (SEVENTH)
**Goal:** Clean separation in processing pipeline

**File:** `src/core/orchestrator.py`
```python
class ArticleOrchestrator:
    def __init__(self):
        self.word_extractor = WordExtractor()

    def process_site(self, config):
        # 1. Process articles
        articles = [...]
        store_articles_batch(articles)

        # 2. Extract word facts separately
        word_facts = []
        for article in articles:
            word_facts.extend(self.word_extractor.extract_words_from_article(article))

        # 3. Store word facts separately
        if word_facts:
            store_word_facts_batch(word_facts)
```

### 7. Docker Environment (EIGHTH)
**Goal:** Clean environment separation

**File:** `docker-compose.yml`
```yaml
services:
  postgres-dev:
    container_name: french_news_dev_db
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

  postgres-test:
    container_name: french_news_test_db
    tmpfs:
      - /var/lib/postgresql/data  # Fast in-memory
```

### 8. Clean Tests (NINTH)
**Goal:** Environment-based testing with static HTML test data

**File:** `tests/conftest.py`
```python
os.environ["ENVIRONMENT"] = "test"

@pytest.fixture
def clean_database():
    with get_session() as session:
        session.execute(text("TRUNCATE raw_articles CASCADE;"))
        session.execute(text("TRUNCATE word_facts CASCADE;"))
```

**Testing Strategy:**
- **E2E Tests:** Use existing static HTML files from main branch
- **Integration Tests:** Real database operations with test data
- **Unit Tests:** Mock external HTTP calls, test core logic
- **Focus:** End-to-end pipeline testing with known HTML content

**No External HTTP in Tests:**
- Use static HTML test files that main branch already provides
- Test word extraction against known French content
- Validate database operations with predictable data

## Key Implementation Rules

0. **Remove multi-schema logic FIRST:** Eliminate all schema-switching before implementing clean environment
1. **Log word extraction failures:** Always log when word parsing fails, then continue gracefully
2. **Exponential backoff:** Use retry logic with exponential backoff for database operations
3. **Single responsibility:** Each class/function has one clear purpose
4. **No mixed concerns:** Articles handle content, word facts handle vocabulary
5. **Environment-based:** Use `IS_TEST` for test checks, not `TEST_MODE`
6. **Static test data:** Use existing static HTML files, no external HTTP in tests
7. **Clean imports:** Update all import statements to use new function names
8. **Remove legacy:** Delete old functions, don't rename them
9. **Single schema only:** All environments use `public` schema - no conditional schemas
10. **Main branch compatibility:** Keep raw articles structure, add word processing layer

## CRITICAL: What NOT to Do

### ❌ DO NOT Make Tests Artificially Pass
```python
# WRONG - Artificial test fix
def test_word_events_generation():
    if hasattr(article, 'word_events'):  # Accommodation code
        assert article.word_events
    else:
        pytest.skip("Legacy test")  # Artificial skip

# RIGHT - Fix the actual test
def test_word_extraction_service():
    extractor = WordExtractor()
    word_facts = extractor.extract_words_from_article(article)
    assert len(word_facts) > 0
```

### ❌ DO NOT Accommodate Legacy Code
```python
# WRONG - Rewriting logic to support old patterns
def store_data(article):
    if hasattr(article, 'word_events'):  # Legacy accommodation
        return store_old_way(article)
    else:
        return store_new_way(article)

# RIGHT - Clean implementation
def store_article(article: RawArticle) -> bool:
    # Clean, single-purpose function
```

### ❌ DO NOT Use Compatibility Layers
```python
# WRONG - Wrapper to make old code work
def store_raw_article(article):  # Legacy wrapper
    return store_article(article)

# RIGHT - Remove old function, update all call sites
# Delete store_raw_article completely
# Update all callers to use store_article
```

### ✅ DO Fix Source Code Properly
```python
# RIGHT - Change the actual implementation
class RawArticle:
    # Remove word_events field completely
    # Remove _extract_french_words method completely

class WordExtractor:  # New service
    def extract_words_from_article(self, article) -> list[WordFact]:
        # Move logic here, don't wrap old logic
```

## Testing Strategy: Fix Root Causes

### ❌ WRONG: Artificial Test Fixes
- Skipping tests that fail due to architecture changes
- Adding conditional logic to make old tests pass
- Mocking new architecture to fit old test expectations
- Using `pytest.skip()` to avoid real fixes

### ✅ RIGHT: Proper Test Updates
- Rewrite tests to match new architecture
- Test the actual new functionality
- Remove tests for deleted functionality
- Create new tests for new services

Example:
```python
# Delete this test completely - don't make it pass artificially
def test_word_events_generation():  # OLD TEST - DELETE
    assert article.word_events

# Write new test for actual architecture
def test_word_extraction_service():  # NEW TEST
    extractor = WordExtractor()
    word_facts = extractor.extract_words_from_article(article)
    assert isinstance(word_facts[0], WordFact)
```

## Error Handling Pattern
```python
try:
    # Process articles first (critical path)
    articles_stored = store_articles_batch(articles)

    # Process word facts second (optional)
    word_facts = extract_words(articles)
    if word_facts:
        store_word_facts_batch(word_facts)
except Exception as e:
    logger.error(f"Article processing failed: {e}")
    # Don't fail entire pipeline for word extraction issues
```

## Files to Update/Create

**FIRST - Clean Multi-Schema Logic:**
- `src/database/database.py` (remove schema parameters)
- `src/database/models.py` (remove schema logic)
- `database/migrations/*.sql` (remove schema conditionals)
- Any config files with schema switching

**Create:**
- `src/services/word_extractor.py`
- `tests/unit/test_models.py`
- `tests/integration/test_database_clean.py`

**Update:**
- `src/config/environment.py` (complete rewrite)
- `src/database/models.py` (separate models)
- `src/database/database.py` (separate operations)
- `src/core/orchestrator.py` (inject services)
- `docker-compose.yml` (separate environments)
- `database/migrations/001_initial_schema.sql` (word_facts table)

**Remove:**
- Any file with `TEST_MODE` references
- Legacy `store_raw_article` function calls
- Mixed word/article processing logic
- **ALL SCHEMA-SWITCHING LOGIC**

## Success Criteria
- ✅ **NO MULTI-SCHEMA LOGIC** (single `public` schema everywhere)
- ✅ Single `ENVIRONMENT` variable usage
- ✅ Separated `RawArticle` and `WordFact` models
- ✅ Dedicated `WordExtractor` service
- ✅ Independent storage operations
- ✅ Clean test isolation
- ✅ No legacy backwards compatibility code
- ✅ Simple, understandable architecture
- ✅ **ALL TESTS PASS WITH REAL FUNCTIONALITY** (no artificial fixes)
- ✅ **ZERO LEGACY ACCOMMODATION** (no `if hasattr()` or compatibility layers)
- ✅ **PROPER SOURCE CODE FIXES** (change implementation, not workarounds)

## Final Validation Checklist

Before considering implementation complete, verify:

### Code Quality
- [ ] **NO SCHEMA-SWITCHING LOGIC** anywhere in codebase
- [ ] No `schema` parameters in any functions
- [ ] No conditional table naming based on environment
- [ ] No `TEST_MODE` references anywhere in codebase
- [ ] No `store_raw_article` function calls
- [ ] No `word_events` field in `RawArticle` model
- [ ] No compatibility wrappers or accommodation code
- [ ] All imports use new function names

### Test Quality
- [ ] All tests pass without `pytest.skip()`
- [ ] No conditional test logic based on old/new architecture
- [ ] Tests validate actual new functionality
- [ ] Integration tests use real database schema
- [ ] No mocked new architecture to fit old tests

### Architecture Quality
- [ ] Clean separation: articles ≠ word facts
- [ ] Single environment variable only
- [ ] Services handle business logic, models handle data
- [ ] Independent storage operations
- [ ] Graceful failure handling

If any checklist item fails, **fix the source code**, don't accommodate the failure.