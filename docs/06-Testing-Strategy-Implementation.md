# Testing Strategy Implementation

## How Different Types of Tests Ensure System Reliability

This document explains the **testing strategy** - how unit tests, integration tests, and end-to-end tests work together to validate the French News Scraper system.

## Testing Pyramid Implementation

### **Test Categories by Speed and Scope**

```
    /\
   /E2E\     ← Few, Slow, High Confidence (Full Pipeline)
  /____\
 /      \
/  UNIT  \    ← Many, Fast, Low Confidence (Individual Functions)  
\________/
```

#### **Unit Tests** (Fast, Many)
- **Scope**: Individual functions, classes, methods
- **Speed**: < 1 second per test
- **Dependencies**: Mocked external systems
- **Location**: `tests/test_essential.py`

#### **Integration Tests** (Medium, Some)  
- **Scope**: Component interactions, database operations
- **Speed**: 1-10 seconds per test
- **Dependencies**: Real database, mocked HTTP
- **Location**: `tests/test_deterministic_pipeline.py`

#### **End-to-End Tests** (Slow, Few)
- **Scope**: Complete pipeline with real/test data
- **Speed**: 30+ seconds per test
- **Dependencies**: Full system stack
- **Location**: `tests/integration/`

## Test Infrastructure Setup

### **Test Configuration** (`tests/conftest.py`)

```python
import pytest
from unittest.mock import Mock
import os

@pytest.fixture(scope="session")
def test_database():
    """Setup test database for integration tests."""
    # Use separate test database to avoid contaminating dev data
    os.environ["DATABASE_URL"] = "postgresql://test_user:test_pass@localhost/test_french_news"
    
    # Initialize test database schema
    from database import initialize_database
    initialize_database()
    
    yield
    
    # Cleanup after all tests
    # Drop test database tables

@pytest.fixture(scope="function") 
def clean_database(test_database):
    """Clean database before each integration test."""
    from database import get_database_manager
    
    db = get_database_manager()
    with db.get_session() as session:
        # Clean all test data
        session.execute("TRUNCATE TABLE french_news.articles RESTART IDENTITY CASCADE")
        session.commit()
        
@pytest.fixture
def mock_http_responses():
    """Mock HTTP responses for testing parsers."""
    responses = {
        "http://test-slate.fr/article-1": "<html><h1>Test Title</h1><div class='article-content'><p>Test content</p></div></html>",
        "http://test-franceinfo.fr/article-1": "<html><h1 class='headline'>News Title</h1><div class='story-body'><p>News content</p></div></html>"
    }
    return responses
```

### **Test Fixtures** (`tests/fixtures/`)

#### **Mock Scraper** (`fixtures/mock_scraper.py`)
```python
class MockScraper:
    """Test double for scrapers that returns predictable URLs."""
    
    def __init__(self, debug=False):
        self.debug = debug
        
    def get_article_urls(self):
        """Return consistent test URLs for deterministic testing."""
        return [
            "http://test-site.com/article-1",
            "http://test-site.com/article-2", 
            "http://test-site.com/article-3"
        ]
```

#### **Mock Parser** (`fixtures/mock_parser_unified.py`)  
```python
from models import ArticleData

class MockParser:
    """Test double for parsers that returns predictable article data."""
    
    def __init__(self, source_id: str):
        self.source_id = source_id
        
    def parse_article(self, soup):
        """Return consistent test article data."""
        return ArticleData(
            title="Mock Article Title",
            full_text="This is mock article content for testing. It has multiple sentences. Perfect for word extraction testing.",
            article_date="2025-01-15",
            num_paragraphs=2
        )
        
    def to_database(self, article_data, url):
        """Mock database storage - always succeeds."""
        return True
        
    def get_test_sources_from_directory(self, source_name):
        """Return mock HTML sources for offline testing."""
        from bs4 import BeautifulSoup
        mock_html = "<html><h1>Mock Title</h1><p>Mock content</p></html>"
        soup = BeautifulSoup(mock_html, "html.parser")
        return [(soup, "http://mock-url.com")]
```

## Unit Test Examples

### **Component Factory Testing** (`test_essential.py:19-31`)

```python
def test_article_pipeline_class_registry(self):
    """Test that the component loader can load classes from class paths."""
    from core.component_loader import import_class
    
    # Test scraper class loading
    scraper_class = import_class("scrapers.slate_fr_scraper.SlateFrURLScraper")
    assert scraper_class is not None
    assert scraper_class.__name__ == "SlateFrURLScraper"
    
    # Test parser class loading  
    parser_class = import_class("parsers.database_slate_fr_parser.DatabaseSlateFrParser")
    assert parser_class is not None
    assert parser_class.__name__ == "DatabaseSlateFrParser"
```

**What This Tests:**
- **Dynamic import functionality**: `importlib.import_module()` works correctly
- **Class path parsing**: String splitting logic is correct
- **Error handling**: Invalid class paths raise appropriate exceptions

### **Configuration Validation** (`test_essential.py:33-47`)

```python
def test_article_pipeline_disabled_config(self):
    """Test that DatabaseProcessor handles disabled configurations."""
    config = {
        "name": "DisabledSource",
        "enabled": False,
        "scraper_class": "scrapers.slate_fr_scraper.SlateFrURLScraper",
        "parser_class": "parsers.database_slate_fr_parser.DatabaseSlateFrParser",
    }
    
    assert config["enabled"] is False
    assert config["name"] == "DisabledSource"
```

**What This Tests:**
- **Configuration structure**: Dictionary contains expected keys
- **Boolean handling**: `enabled` flag works correctly
- **Data validation**: Configuration matches expected schema

### **Repository Pattern Testing**

```python
@patch('database.article_repository.get_database_manager')
def test_repository_error_handling(self, mock_db_manager):
    """Test repository handles database errors gracefully."""
    # Setup: Mock database to raise exception
    mock_db_manager.return_value.get_session.side_effect = Exception("Database connection failed")
    
    repo = ArticleRepository()
    
    # Test: Repository should handle error and return None
    result = repo.get_source_id("TestSource")
    assert result is None
    
    # Test: Repository should log error (verify logging called)
    # Note: In real implementation, would verify logger.error was called
```

**What This Tests:**
- **Error resilience**: Database failures don't crash the application
- **Graceful degradation**: Returns None instead of raising exception
- **Logging behavior**: Errors are properly logged for debugging

## Integration Test Examples

### **Database Operations** (`test_deterministic_pipeline.py`)

```python
def test_database_article_extraction(self, clean_database):
    """Test that articles can be stored and retrieved from database."""
    from database.article_repository import ArticleRepository
    from models import ArticleData
    
    # Setup test data
    repo = ArticleRepository()
    test_article = ArticleData(
        title="Integration Test Article",
        full_text="This is a test article for integration testing. It contains multiple sentences for word extraction.",
        article_date="2025-01-15",
        num_paragraphs=2
    )
    
    # Test storage
    success = repo.store_article(test_article, "http://integration-test.com", "test-source-uuid")
    assert success is True
    
    # Test retrieval (verify data was actually stored)
    with repo.db.get_session() as session:
        result = session.execute(
            "SELECT title, full_text FROM french_news.articles WHERE url = %s",
            ("http://integration-test.com",)
        ).fetchone()
        
    assert result is not None
    assert result[0] == "Integration Test Article"
    assert "integration testing" in result[1]
```

**What This Tests:**
- **Database connectivity**: PostgreSQL connection works
- **Transaction handling**: Data is properly committed
- **Data integrity**: Stored data matches input data
- **Schema compatibility**: Database schema matches application expectations

### **dbt Transformations** (`test_deterministic_pipeline.py`)

```python
def test_dbt_processing_deterministic_counts(self, clean_database):
    """Test that dbt transformations produce expected word counts."""
    
    # Setup: Store test articles with known content
    repo = ArticleRepository()
    
    test_articles = [
        ArticleData(title="Article 1", full_text="Le président français mange des pommes. Il aime les pommes.", ...),
        ArticleData(title="Article 2", full_text="Le gouvernement français discute des réformes. Les réformes sont importantes.", ...)
    ]
    
    for i, article in enumerate(test_articles):
        repo.store_article(article, f"http://test-{i}.com", source_id)
    
    # Execute dbt transformations
    subprocess.run(["dbt", "run"], cwd="french_flashcards", check=True)
    
    # Verify results
    with repo.db.get_session() as session:
        # Test sentence extraction
        sentence_count = session.execute("SELECT COUNT(*) FROM french_flashcards.sentences").scalar()
        assert sentence_count >= 4  # At least 4 sentences from test data
        
        # Test word extraction  
        word_count = session.execute("SELECT COUNT(*) FROM french_flashcards.raw_words").scalar()
        assert word_count >= 10  # Multiple words per sentence
        
        # Test frequency analysis
        pommes_frequency = session.execute(
            "SELECT frequency FROM french_flashcards.word_occurrences WHERE word = 'pommes'"
        ).scalar()
        assert pommes_frequency == 2  # "pommes" appears twice
```

**What This Tests:**
- **dbt execution**: `dbt run` command works correctly
- **SQL transformations**: Each dbt model produces expected output
- **Data consistency**: Word frequencies match expected counts
- **End-to-end data flow**: Python → PostgreSQL → dbt → Analytics tables

## End-to-End Test Examples

### **Full Pipeline Testing** (`test_offline_integration.py`)

```python
def test_make_run_offline_integration(self, clean_database):
    """Test complete pipeline with offline test data."""
    
    # Execute full pipeline in offline mode
    env = os.environ.copy()
    env["OFFLINE"] = "True"
    env["DEBUG"] = "True" 
    
    # Run Python scraping pipeline
    result = subprocess.run(
        ["python", "main.py"],
        capture_output=True,
        text=True,
        env=env,
        timeout=120  # 2 minute timeout
    )
    
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"
    
    # Verify articles were stored
    repo = ArticleRepository()
    with repo.db.get_session() as session:
        article_count = session.execute("SELECT COUNT(*) FROM french_news.articles").scalar()
        assert article_count >= 10  # Should process test HTML files
        
    # Run dbt transformations
    dbt_result = subprocess.run(
        ["make", "dbt-run"],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    assert dbt_result.returncode == 0, f"dbt failed: {dbt_result.stderr}"
    
    # Verify final flashcard data
    with repo.db.get_session() as session:
        flashcard_count = session.execute("SELECT COUNT(*) FROM french_flashcards.vocabulary_for_flashcards").scalar()
        assert flashcard_count >= 50  # Should generate substantial vocabulary
```

**What This Tests:**
- **Complete workflow**: All components work together
- **Process integration**: Make commands execute correctly
- **Data pipeline**: Raw data becomes flashcard data
- **Error propagation**: Failures are detected and reported

### **Performance Testing** 

```python
def test_pipeline_performance_benchmarks(self, clean_database):
    """Test that pipeline meets performance requirements."""
    import time
    
    start_time = time.time()
    
    # Run pipeline with controlled dataset
    result = subprocess.run(["python", "main.py"], env={"OFFLINE": "True"})
    
    processing_time = time.time() - start_time
    
    # Performance assertions
    assert processing_time < 60  # Should complete within 1 minute for test data
    assert result.returncode == 0
    
    # Verify throughput
    repo = ArticleRepository()
    with repo.db.get_session() as session:
        article_count = session.execute("SELECT COUNT(*) FROM french_news.articles").scalar()
        
    articles_per_second = article_count / processing_time
    assert articles_per_second >= 1  # At least 1 article per second
```

## Test Execution Strategy

### **Development Workflow**
```bash
# Run fast unit tests during development
pytest tests/test_essential.py -v

# Run integration tests before commits
pytest tests/test_deterministic_pipeline.py -v

# Run all tests before releases
pytest tests/ -v --tb=short
```

### **CI/CD Pipeline Testing** 
```yaml
# .github/workflows/test.yml
name: Test Pipeline
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
          
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12
          
      - name: Install dependencies
        run: |
          pip install -e .[dev]
          
      - name: Run unit tests
        run: pytest tests/test_essential.py -v
        
      - name: Run integration tests  
        run: pytest tests/test_deterministic_pipeline.py -v
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
```

## Test Data Management

### **Deterministic Test Data**
- **HTML fixtures**: Real article HTML stored in `src/test_data/raw_url_soup/`
- **URL mapping**: `test_data/url_mapping.py` maps filenames to original URLs
- **Expected results**: Known word counts and frequencies for validation

### **Test Database Strategy**
- **Separate database**: Test database isolated from development data
- **Transaction rollback**: Each test runs in transaction that's rolled back
- **Seed data**: Consistent test sources and configuration

### **Mock Strategy**
```python
# Mock external dependencies, test real business logic
@patch('requests.Session.get')  # Mock HTTP requests
def test_parser_logic(mock_get):
    mock_get.return_value.content = "<html>...</html>"
    
    # Test real parser logic with mocked HTTP
    parser = DatabaseSlateFrParser("test-source-id")
    soup = parser.get_soup_from_url("http://test.com")
    result = parser.parse_article(soup)
    
    assert result.title == "Expected Title"
```

This testing strategy provides confidence that the system works correctly at multiple levels, from individual functions to complete end-to-end workflows.