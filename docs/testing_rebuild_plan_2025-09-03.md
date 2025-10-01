# Testing Rebuild Plan - Learning Project

## Project Structure
```
tests/
├── conftest.py              # Global fixtures and SQLite test database
├── unit/                    # Fast isolated tests (Stage 1)
├── integration/             # Component interaction tests with SQLite (Stage 1) 
├── config/                  # Configuration validation tests (Stage 2)
├── essential/               # Critical path smoke tests (Stage 2)
├── performance/             # Benchmarks and load tests (Stage 3)
└── fixtures/                # Test data and utilities
    ├── test_html/ (existing)
    └── mock_components.py
```

---

## STAGE 1: Core Testing Foundation

### Unit Tests (`tests/unit/`)

**Pytest Concepts to Learn:**
- Basic test functions (`test_*` naming)
- Assertions (`assert`, `pytest.raises`)
- Fixtures (`@pytest.fixture`, `scope` parameter)
- Mocking (`unittest.mock.Mock`, `@patch` decorator)
- Parametrized tests (`@pytest.mark.parametrize`)

**Critical Tests (Must Have):**
- `test_component_factory.py`
  - Test dynamic class importing (`import_class()`)
  - Test component creation with valid/invalid configs
  - Test error handling for missing classes
  
- `test_soup_validators.py`
  - Test HTML parsing with BeautifulSoup
  - Test article extraction from real HTML fixtures
  - Test validation logic (title/content existence)
  - Test error handling for malformed HTML
  
- `test_url_collectors.py`
  - Test URL pattern matching
  - Test filtering logic
  - Test HTTP request mocking
  - Test timeout handling
  
- `test_database_models.py`
  - Test data validation
  - Test type conversion
  - Test required field validation

**Nice to Have:**
- `test_structured_logger.py` - Log formatting, levels
- `test_url_mapping.py` - URL normalization
- `test_web_mixin.py` - HTTP utilities

**Make Command:** `test-unit`

---

### Integration Tests (`tests/integration/`)

**Pytest Concepts to Learn:**
- **SQLite fixtures** (in-memory database setup)
- **Database schema initialization** 
- **Test isolation** (fresh database per test)
- **SQLAlchemy dialect switching** (PostgreSQL → SQLite)
- **Subprocess testing** (`subprocess.run`)

**Critical Tests (Must Have):**
- `test_database_operations.py`
  - Test article storage to SQLite (in-memory)
  - Test batch operations with SQLite
  - Test transaction handling
  - Test connection error recovery
  
- `test_orchestrator_integration.py`
  - Test multi-site processing
  - Test component integration with real HTML fixtures
  - Test error aggregation
  - Test TEST_MODE vs live mode switching

**Nice to Have:**
- `test_pipeline_end_to_end.py` - Full scraper → SQLite workflow
- `test_offline_mode.py` - Test fixture processing with SQLite storage

**Make Command:** `test-integration`

**SQLite Setup:**
```python
# In conftest.py
@pytest.fixture(scope="function")
def test_database():
    """SQLite in-memory database per test"""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    # Initialize schema, yield, auto-cleanup
```

---

## STAGE 2: Advanced Testing Infrastructure

### Config Tests (`tests/config/`)

**Pytest Concepts to Learn:**
- **Environment variable mocking** (`monkeypatch.setenv`)
- **Configuration validation patterns**
- **File system mocking** (missing .env files)
- **Error message testing** (`pytest.raises`)

**Critical Tests (Must Have):**
- `test_environment_loading.py`
  - Test .env file parsing
  - Test missing environment variables
  - Test development vs production modes
  - Test database connection strings
  
- `test_site_configs_validation.py`
  - Test configuration schema validation
  - Test enabled/disabled site handling
  - Test missing required fields
  - Test invalid class paths

**Nice to Have:**
- `test_settings_override.py` - Runtime configuration changes
- `test_config_migration.py` - Backward compatibility

**Make Command:** `test-config`

---

### Essential Tests (`tests/essential/`)

**Pytest Concepts to Learn:**
- **Smoke testing strategies**
- **Test ordering and dependencies**
- **Critical path identification**
- **Fast feedback loops**

**Critical Tests (Must Have):**
- `test_smoke_tests.py`
  - Test application starts without errors
  - Test database connection works (SQLite)
  - Test basic component creation
  - Test configuration loading
  
- `test_critical_paths.py`
  - Test happy path: URL → Soup → Article → Database
  - Test error paths: Network failures, parsing errors
  - Test data integrity end-to-end with HTML fixtures

**Nice to Have:**
- `test_deployment_readiness.py` - Production environment checks
- `test_regression_prevention.py` - Known bug prevention

**Make Command:** `test-essential`

---

## STAGE 3: Performance & Load Testing

### Performance Tests (`tests/performance/`)

**Pytest Concepts to Learn:**
- **Time measurement** (`time.time()`, `timeit`)
- **Memory profiling basics** (`tracemalloc`)
- **Performance assertions** (thresholds)
- **Load testing patterns**
- **Test timeouts and markers**

**Critical Tests (Must Have):**
- `test_concurrent_processing.py`
  - Test ThreadPoolExecutor performance
  - Test database connection handling under load
  - Test memory usage with large datasets
  
- `test_batch_operations.py`
  - Test database batch insert performance
  - Test HTML parsing speed with real fixtures
  - Test memory efficiency

**Nice to Have:**
- `test_soup_parsing_benchmarks.py` - BeautifulSoup speed tests
- `test_url_fetching_performance.py` - HTTP request throughput

**Make Command:** `test-performance`

---

## Testing Infrastructure Files

### `conftest.py` (Global Configuration)
```python
import pytest
import os
import tempfile
from unittest.mock import Mock

@pytest.fixture(scope="function")
def test_database():
    """SQLite in-memory database per test"""
    # Use SQLite in-memory for fast, isolated tests
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    # Initialize schema (same DDL should work for SQLite)
    from database import initialize_database
    initialize_database()
    
    yield
    # Automatic cleanup - in-memory database disappears

@pytest.fixture
def mock_http_session():
    """Mock requests.Session for HTTP tests"""
    # HTTP mocking logic for unit tests

@pytest.fixture
def sample_html_content():
    """Load test HTML from existing fixtures"""
    # Return content from tests/fixtures/test_html/
    
@pytest.fixture
def temp_database_file():
    """Temporary SQLite file for tests that need persistence"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    yield db_path
    os.unlink(db_path)
```

### `fixtures/mock_components.py`
```python
class MockURLCollector:
    """Deterministic URL collector for testing"""

class MockSoupValidator:
    """Deterministic soup validator for testing"""

class MockDatabase:
    """In-memory database for unit tests"""
```

---

## Makefile Commands to Add

```makefile
# Stage 1 Testing Commands
test-unit:  ## Run unit tests only (fast, no database)
	PYTHONPATH=$(SRC) python -m pytest tests/unit/ -v

test-integration:  ## Run integration tests (with SQLite in-memory)
	PYTHONPATH=$(SRC) python -m pytest tests/integration/ -v

# Stage 2 Testing Commands  
test-config:  ## Run configuration validation tests
	PYTHONPATH=$(SRC) python -m pytest tests/config/ -v

test-essential:  ## Run essential smoke tests
	PYTHONPATH=$(SRC) python -m pytest tests/essential/ -v

# Stage 3 Testing Commands
test-performance:  ## Run performance benchmarks (slow)
	PYTHONPATH=$(SRC) python -m pytest tests/performance/ -v -s

# Combined Commands
test-stage1:  ## Run Stage 1 tests (unit + integration)
	$(MAKE) test-unit && $(MAKE) test-integration

test-stage2:  ## Run Stage 2 tests (config + essential)
	$(MAKE) test-config && $(MAKE) test-essential

test-all:  ## Run all tests in order (all stages)
	$(MAKE) test-stage1 && $(MAKE) test-stage2 && $(MAKE) test-performance
```

---

## Learning Path Recommendations

### Recommended Learning Order:

**Stage 1: Foundation (Core Testing)**
1. **Unit Tests** - Learn pytest basics with isolated functions
2. **Integration Tests** - Learn SQLite database testing and component interaction

**Stage 2: Infrastructure (System Testing)**  
3. **Config Tests** - Learn environment and configuration testing
4. **Essential Tests** - Learn smoke testing and critical path validation

**Stage 3: Advanced (Performance Testing)**
5. **Performance Tests** - Learn benchmarking, profiling, and load testing

### Key pytest Features to Master:
- **Fixtures**: Reusable test setup/teardown
- **Mocking**: Isolate components from external dependencies  
- **Parametrization**: Test multiple scenarios efficiently
- **Markers**: Categorize and filter tests
- **Cleanup**: Proper test isolation and resource management

---

## SQLite vs PostgreSQL Strategy

**Integration Tests**: Use SQLite in-memory
- ✅ **Fast** (no network, no Docker)
- ✅ **Isolated** (fresh database per test)  
- ✅ **Simple** (no container management)
- ✅ **CI-friendly** (no external dependencies)

**Production**: Keep PostgreSQL
- Your existing schema/migrations should work with minimal changes
- SQLAlchemy handles dialect differences automatically

---

## Missing Components Analysis

**Additional Test Categories to Consider Later:**
- **Error handling tests** - Network failures, malformed HTML
- **Edge case tests** - Empty responses, timeout scenarios  
- **Security tests** - Input validation, safe HTML parsing
- **Logging tests** - Verify structured logging output
- **Regression tests** - Prevent known bugs from returning

**Test Data Strategy:**
- Your existing HTML fixtures in `tests/fixtures/test_html/` are perfect for deterministic testing
- Use these extensively in integration tests for predictable results
- Consider adding more edge-case HTML samples (empty articles, missing elements)