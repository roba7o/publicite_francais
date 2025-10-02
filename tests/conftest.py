"""
Pytest configuration and shared fixtures for the test suite.

This file contains pytest configuration, shared fixtures, and utilities
used across all test modules. It sets up the test environment and provides
common test data and mock objects.
"""

import os
import shutil
import sys
import tempfile
from unittest.mock import Mock

import pytest

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import after path setup
# ScraperConfig removed - using dictionary configurations
from core.orchestrator import ArticleOrchestrator
from utils.structured_logger import get_logger


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to the test data directory."""
    return os.path.join(os.path.dirname(__file__), "fixtures", "test_html")


@pytest.fixture(scope="session")
def raw_test_files_dir(test_data_dir):
    """Path to the raw HTML test files."""
    return test_data_dir


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp(prefix="test_scraper_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_french_text():
    """Sample French text for testing text processing."""
    return """
    Le gouvernement français annonce des réformes importantes pour l'avenir.
    Ces changements concernent la sécurité sociale et les politiques publiques.
    Les citoyens français attendent ces modifications avec intérêt.
    Cette nouvelle politique devrait améliorer la situation économique du pays.
    """


@pytest.fixture
def sample_article_data():
    """Sample article data structure for testing."""
    return {
        "title": "Test Article Title",
        "full_text": "Ceci est un article de test en français avec du contenu significatif.",
        "article_date": "2025-07-13",
        "date_scraped": "2025-07-13 17:00:00",
        "url": "https://example.com/test-article",
    }


@pytest.fixture
def mock_scraper_config():
    """Mock scraper configuration for testing."""
    return {
        "name": "TestSource",
        "enabled": True,
        "scraper_class": "tests.fixtures.mock_scraper.MockScraper",
        "parser_class": "tests.fixtures.mock_parser_unified.MockDatabaseParser",
        "scraper_kwargs": {"debug": True},
        "parser_kwargs": {},
    }


@pytest.fixture
def scraper_configs():
    """All scraper configurations for testing."""
    from config.site_configs import SCRAPER_CONFIGS

    return SCRAPER_CONFIGS


@pytest.fixture
def article_pipeline():
    """Database processor for testing database operations."""
    return ArticleOrchestrator


@pytest.fixture
def test_logger():
    """Test logger instance."""
    return get_logger("test_logger")


@pytest.fixture
def mock_requests_response():
    """Mock requests response for HTTP testing."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = (
        b"<html><body><h1>Test Article</h1><p>Test content</p></body></html>"
    )
    mock_response.raise_for_status.return_value = None
    return mock_response


# Enhanced fixtures for your existing 16 HTML test files
@pytest.fixture(scope="session")
def test_html_files(raw_test_files_dir):
    """
    Access to your existing 16 HTML test files organized by news source.

    Returns a dictionary mapping source names to their test file paths.
    This fixture makes it easy to access your existing test data.
    """
    from pathlib import Path

    base_dir = Path(raw_test_files_dir)
    test_files = {}

    # Map your actual directory names to standardized source names
    source_mapping = {
        "Slate.fr": "slate.fr",
        "FranceInfo.fr": "franceinfo.fr",
        "TF1 Info": "tf1info.fr",
        "Depeche.fr": "ladepeche.fr",
    }

    for actual_dir, source_name in source_mapping.items():
        source_dir = base_dir / actual_dir
        if source_dir.exists():
            # Get all HTML and PHP files
            files = list(source_dir.glob("*.html")) + list(source_dir.glob("*.php"))
            test_files[source_name] = files
        else:
            test_files[source_name] = []

    return test_files


@pytest.fixture
def slate_test_files(test_html_files):
    """List of Slate.fr test files."""
    return test_html_files.get("slate.fr", [])


@pytest.fixture
def franceinfo_test_files(test_html_files):
    """List of FranceInfo.fr test files."""
    return test_html_files.get("franceinfo.fr", [])


@pytest.fixture
def tf1_test_files(test_html_files):
    """List of TF1Info.fr test files."""
    return test_html_files.get("tf1info.fr", [])


@pytest.fixture
def ladepeche_test_files(test_html_files):
    """List of LaDepeche.fr test files."""
    return test_html_files.get("ladepeche.fr", [])


@pytest.fixture
def all_test_files(test_html_files):
    """All test files organized by source - uses your existing 16 HTML files."""
    return test_html_files


# Enhanced database fixtures for better test isolation
@pytest.fixture
def clean_test_database():
    """
    Ensure clean database state for integration tests.

    This fixture initializes the database and ensures tables are clean
    before each test that needs database operations.
    """
    from sqlalchemy import text

    from database.database import get_session, initialize_database

    # Initialize database
    initialize_database()

    # Clean the test tables (schema-free approach)
    with get_session() as session:
        session.execute(text("TRUNCATE raw_articles CASCADE;"))
        session.commit()

    yield

    # Optional cleanup after test (if needed)


@pytest.fixture
def mock_article_orchestrator():
    """
    Mock ArticleOrchestrator using your existing mock classes.

    This provides a test-friendly orchestrator that uses your existing
    MockScraper and MockDatabaseParser for isolated unit testing.
    """
    from unittest.mock import Mock

    from tests.fixtures.mock_parser_unified import MockDatabaseParser
    from tests.fixtures.mock_scraper import MockScraper

    # Create mock orchestrator
    mock_orchestrator = Mock()
    mock_orchestrator.component_factory = Mock()

    # Configure factory to return your existing mocks
    mock_orchestrator.component_factory.create_collector.return_value = MockScraper(
        debug=True
    )
    mock_orchestrator.component_factory.create_validator.return_value = (
        MockDatabaseParser("test-source")
    )

    return mock_orchestrator


@pytest.fixture
def sample_site_config():
    """
    Sample site configuration matching your actual site_configs.py structure.

    This provides a realistic test configuration that matches your actual
    configuration format for testing component factory and orchestrator.
    """
    from config.environment import DEBUG

    return {
        "site": "test-site.fr",
        "enabled": True,
        "url_collector_class": "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector",
        "soup_validator_class": "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator",
        "url_collector_kwargs": {"debug": DEBUG},
        "soup_validator_kwargs": {"debug": DEBUG},
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment with proper settings."""
    # Force test mode for tests
    monkeypatch.setenv("TEST_MODE", "True")
    monkeypatch.setenv("DEBUG", "True")

    # No longer needed - using direct imports

    yield


@pytest.fixture
def disable_logging():
    """Disable logging during tests to reduce noise."""
    import logging

    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


# Performance test fixtures
@pytest.fixture
def performance_sample_texts():
    """Sample texts of varying sizes for performance testing."""
    return {
        "small": "Ceci est un petit texte français pour les tests.",
        "medium": " ".join(
            [
                "Ceci est un texte de taille moyenne pour les tests de performance.",
                "Il contient plusieurs phrases avec du vocabulaire français varié.",
                "Le système doit traiter ce texte efficacement et rapidement.",
                "Nous testons la vitesse de traitement du texte français.",
            ]
            * 10
        ),
        "large": " ".join(
            [
                "Ceci est un texte volumineux pour les tests de performance intensive.",
                "Il contient de nombreuses phrases avec un vocabulaire français étendu.",
                "Le système doit traiter ce texte volumineux de manière efficace.",
                "Nous testons les limites de performance du processeur de texte français.",
                "Cette analyse inclut la tokenisation, le nettoyage et le comptage.",
            ]
            * 100
        ),
    }


# Error testing fixtures
@pytest.fixture
def invalid_html_content():
    """Invalid HTML content for error testing."""
    return [
        "",  # Empty content
        "<html><body>",  # Incomplete HTML
        "Not HTML at all",  # Plain text
        "<html><body>" + "x" * 10000 + "</body></html>",  # Very large content
        "<html><body>×※⚠</body></html>",  # Special characters
    ]


@pytest.fixture
def mock_network_errors():
    """Mock various network error scenarios."""
    from requests.exceptions import ConnectionError, HTTPError, Timeout

    return {
        "connection_error": ConnectionError("Connection failed"),
        "timeout": Timeout("Request timed out"),
        "http_404": HTTPError("404 Not Found"),
        "http_500": HTTPError("500 Internal Server Error"),
    }


# Test data validation fixtures
@pytest.fixture
def expected_word_counts():
    """Expected word counts for test validation."""
    return {
        "slate_fr": {"min_words": 50, "max_words": 1000},
        "depeche_fr": {"min_words": 30, "max_words": 800},
        "tf1_fr": {"min_words": 40, "max_words": 600},
        "lemonde_fr": {"min_words": 60, "max_words": 1200},
    }


# Configuration for different test modes
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark slow tests
        if "performance" in item.nodeid or "large" in item.nodeid:
            item.add_marker(pytest.mark.slow)

        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark e2e tests
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)

        # Mark performance tests
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
