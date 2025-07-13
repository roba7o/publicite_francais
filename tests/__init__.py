"""
Test suite for French Article Scraper.

This test suite provides comprehensive coverage including:
- Unit tests for individual components
- Integration tests for processing pipelines  
- End-to-end tests using real test data
- Performance benchmarks
- Error scenario testing

Test Structure:
- tests/unit/ - Individual component tests
- tests/integration/ - Multi-component workflow tests
- tests/e2e/ - Full system tests with test data
- tests/fixtures/ - Shared test data and utilities
- tests/performance/ - Performance and load tests

Usage:
    pytest tests/                    # Run all tests
    pytest tests/unit/              # Unit tests only
    pytest tests/e2e/               # E2E tests only
    pytest -v --tb=short            # Verbose with short tracebacks
    pytest -k "test_text_processing" # Run specific test patterns
"""