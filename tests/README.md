# Test Suite Documentation

This directory contains a comprehensive test suite for the French article scraper project. The tests are organized by type and scope to ensure thorough coverage of all system components.

## Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and shared fixtures
├── fixtures/                     # Mock objects and test utilities
│   ├── mock_parser.py            # Mock parsers for isolated testing
│   └── mock_scraper.py           # Mock scrapers for testing
├── unit/                         # Unit tests for individual components
│   ├── test_french_text_processor.py  # Text processing functionality
│   ├── test_csv_writer.py        # CSV output handling
│   ├── test_error_recovery.py    # Circuit breaker and retry logic
│   └── test_base_parser.py       # Base parser functionality
├── integration/                  # Integration tests for component interaction
│   ├── test_text_processing_pipeline.py  # End-to-end text processing
│   └── test_error_scenarios.py   # Error handling across components
├── e2e/                         # End-to-end tests with real data
│   └── test_real_data_processing.py  # Tests using actual HTML files
├── performance/                 # Performance and scalability tests
│   └── test_performance_benchmarks.py  # System performance testing
└── README.md                   # This documentation file
```

## Test Categories

### Unit Tests (`tests/unit/`)

Test individual components in isolation using mocks and fixtures:

- **FrenchTextProcessor**: Text validation, cleaning, tokenization, word frequency analysis
- **CSVWriter**: File creation, data writing, error handling, concurrent access
- **ErrorRecovery**: Circuit breaker patterns, retry mechanisms, health monitoring
- **BaseParser**: HTML parsing, text extraction, validation

### Integration Tests (`tests/integration/`)

Test component interactions and data flow:

- **Text Processing Pipeline**: Complete flow from parsing to CSV output
- **Error Scenarios**: System behavior under various error conditions

### End-to-End Tests (`tests/e2e/`)

Test the complete system using real test data:

- **Real Data Processing**: Uses actual HTML files from `test_data/raw_url_soup/`
- **Cross-Source Comparison**: Tests processing across different news sources
- **Quality Assessment**: Validates text processing effectiveness

### Performance Tests (`tests/performance/`)

Measure system performance and scalability:

- **Benchmarks**: Performance under various load conditions
- **Memory Usage**: Memory stability during long operations
- **Concurrency**: Multi-threaded processing performance
- **Scalability**: Performance with different thread counts

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-cov psutil

# Ensure you're in the project root directory
cd /path/to/publicite_francais
```

### Basic Test Execution

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/e2e/                     # End-to-end tests only
pytest tests/performance/             # Performance tests only

# Run specific test files
pytest tests/unit/test_french_text_processor.py
pytest tests/e2e/test_real_data_processing.py
```

### Test Options

```bash
# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src/article_scrapers --cov-report=html

# Run only fast tests (exclude performance tests)
pytest tests/ -m "not slow"

# Run tests in parallel (requires pytest-xdist)
pytest tests/ -n auto

# Stop on first failure
pytest tests/ -x

# Run specific test by name pattern
pytest tests/ -k "test_french_text"
```

## Test Data

### Real Test Data

The E2E tests use actual HTML files from various French news sources:

- **Slate.fr**: `/test_data/raw_url_soup/slate_fr/`
- **France Info**: `/test_data/raw_url_soup/france_info_fr/`
- **TF1 Info**: `/test_data/raw_url_soup/tf1_fr/`
- **La Dépêche**: `/test_data/raw_url_soup/depeche_fr/`

These files contain real article HTML for testing parser accuracy and text processing quality.

### Mock Data

Unit and integration tests use mock objects that simulate real components:

- **MockParser**: Simulates article parsing without network requests
- **MockScraper**: Provides mock URL lists for testing
- **MockFailingParser**: Simulates parsing failures for error testing

## Test Configuration

### Fixtures (`conftest.py`)

Shared test fixtures available to all tests:

- `french_text_processor`: Configured FrenchTextProcessor instance
- `base_parser`: BaseParser instance for testing
- `sample_french_text`: Sample French text for testing
- `mock_article_data`: Mock article data structure

### Performance Test Configuration

Performance tests include configurable thresholds:

- **Processing Speed**: Minimum words per second
- **Memory Usage**: Maximum memory growth limits
- **Concurrent Performance**: Expected throughput with multiple threads
- **Scalability**: Performance scaling with thread count

## Expected Test Results

### Coverage Targets

- **Unit Tests**: >90% line coverage for core components
- **Integration Tests**: Critical path coverage
- **E2E Tests**: Real data processing validation
- **Performance Tests**: Baseline performance metrics

### Performance Baselines

- **Text Processing**: >1000 words/second
- **CSV Writing**: >50 articles/second
- **Concurrent Processing**: >10 articles/second total
- **Memory Stability**: <50MB growth during extended operation

## Troubleshooting

### Common Issues

1. **Missing Test Data**: E2E tests require HTML files in `test_data/` directory
2. **Permission Errors**: CSV writer tests may fail without write permissions
3. **Memory Tests**: Performance tests require `psutil` package
4. **Slow Tests**: Performance tests may take longer on slower systems

### Test Failures

```bash
# Debug specific test failure
pytest tests/unit/test_french_text_processor.py::TestFrenchTextProcessor::test_validation -v -s

# Run with Python debugger
pytest tests/unit/test_french_text_processor.py --pdb

# Capture stdout for debugging
pytest tests/integration/test_text_processing_pipeline.py -s
```

### Environment Issues

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify package imports
python -c "from article_scrapers.utils.french_text_processor import FrenchTextProcessor"

# Check test data availability
ls -la src/article_scrapers/test_data/raw_url_soup/
```

## Continuous Integration

### GitHub Actions Integration

Example CI configuration:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        pytest tests/ --cov=src/article_scrapers --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Contributing

### Adding New Tests

1. **Unit Tests**: Add to appropriate `tests/unit/test_*.py` file
2. **Integration Tests**: Add to `tests/integration/` directory
3. **Performance Tests**: Add to `tests/performance/` with appropriate benchmarks
4. **E2E Tests**: Add real data scenarios to `tests/e2e/`

### Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `TestComponentName`
- Test methods: `test_specific_functionality`
- Parametrized tests: `test_scenario_with_params`

### Mock Guidelines

- Use mocks for external dependencies (network, file system)
- Keep mocks simple and focused
- Prefer dependency injection for testability
- Document mock behavior in test docstrings

## References

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Performance Testing Best Practices](https://pytest-benchmark.readthedocs.io/)