# Integration Tests

This directory contains integration tests that verify how different components work together in the French News Scraper system.

## Test Structure

### `test_article_pipeline.py`
**Complete End-to-End Pipeline Testing**

- **`TestHtmlTestDataIntegrity`**: Validates your 16 HTML test files are intact and readable
- **`TestArticleOrchestrator`**: Tests the main orchestrator component integration  
- **`TestDeterministicPipeline`**: Ensures consistent, repeatable results from the pipeline using test HTML files

Key features:
- Uses your existing 16 HTML test files for deterministic testing
- Verifies article distribution across all 4 sources (Slate.fr, FranceInfo.fr, TF1Info.fr, LaDepeche.fr)
- Tests pipeline idempotency (no duplicates on repeated runs)

### `test_database_integration.py`
**Database Infrastructure & Operations**

- **`TestDatabaseConnectivity`**: Basic database connection and schema access
- **`TestDatabaseOperations`**: Model creation, uniqueness constraints, bulk operations
- **`TestSchemaOperations`**: Table structure validation and permissions testing

Key features:
- Tests with environment-specific schemas (`news_data_test`, etc.)
- Validates RawArticle model operations
- Ensures proper database permissions and constraints

### `test_component_integration.py`
**Component Architecture Integration**

- **`TestComponentFactory`**: Validates dynamic component creation from configurations
- **`TestCollectorValidatorIntegration`**: Tests URL collector and soup validator pairing
- **`TestOrchestratorIntegration`**: Verifies orchestrator uses components correctly
- **`TestEndToEndFlow`**: Complete processing flow validation

Key features:
- Tests all 4 URL collectors and 4 soup validators work with ComponentFactory
- Validates component configuration handling (enabled/disabled sources)
- Tests error handling and graceful degradation

## Test Data Usage

All integration tests use your existing test data structure:
```
src/test_data/raw_url_soup/
├── Slate.fr/          # 4 HTML files
├── FranceInfo.fr/      # 4 HTML files  
├── TF1 Info/           # 4 HTML files
└── Depeche.fr/         # 4 PHP/HTML files
```

## Key Integration Points Tested

1. **Configuration → Component Creation**: `site_configs.py` → `ComponentFactory` → Components
2. **Component Interaction**: URL Collectors → Soup Validators → Database Models
3. **Pipeline Flow**: Test HTML Files → Processing → Database Storage
4. **Error Handling**: Invalid configs, network issues, parsing failures
5. **Data Integrity**: URL uniqueness, schema validation, proper storage

## Running Integration Tests

```bash
# All integration tests
make test-integration
# or
PYTHONPATH=src ./venv/bin/python -m pytest tests/integration/ -v

# Specific test file
PYTHONPATH=src ./venv/bin/python -m pytest tests/integration/test_article_pipeline.py -v

# With database cleanup
PYTHONPATH=src ./venv/bin/python -m pytest tests/integration/ -v --tb=short
```

## Database Requirements

Integration tests require:
- PostgreSQL container running (`make db-start`)
- Test database schema (`news_data_test`)
- Proper database permissions for CRUD operations

The `clean_test_database` fixture automatically handles database cleanup between tests.

## Expected Results

**Deterministic Testing**: These tests should produce identical results on every run because they use fixed HTML test files rather than live web scraping.

**Typical Results**:
- 16 HTML files processed (4 per source)
- ~14-18 articles successfully extracted (allows for parsing variations)
- All 4 news sources represented in database
- No duplicate URLs due to uniqueness constraints

## Maintenance

When adding new news sources:
1. Add configuration to `site_configs.py`
2. Add corresponding HTML test files to `src/test_data/raw_url_soup/`
3. Update expected counts in `test_article_pipeline.py`
4. Add new source to component integration tests