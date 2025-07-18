"""
Pytest configuration and shared fixtures for the test suite.

This file contains pytest configuration, shared fixtures, and utilities
used across all test modules. It sets up the test environment and provides
common test data and mock objects.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import after path setup
from utils.structured_logger import get_structured_logger
from utils.french_text_processor import FrenchTextProcessor
from utils.csv_writer import DailyCSVWriter
from config.website_parser_scrapers_config import ScraperConfig
from core.processor import ArticleProcessor


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to the test data directory."""
    return os.path.join(os.path.dirname(__file__), '..', 'src', 'test_data')


@pytest.fixture(scope="session") 
def raw_test_files_dir(test_data_dir):
    """Path to the raw HTML test files."""
    return os.path.join(test_data_dir, 'raw_url_soup')


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp(prefix='test_scraper_')
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
        'title': 'Test Article Title',
        'full_text': 'Ceci est un article de test en français avec du contenu significatif.',
        'article_date': '2025-07-13',
        'date_scraped': '2025-07-13 17:00:00',
        'url': 'https://example.com/test-article'
    }


@pytest.fixture
def mock_scraper_config():
    """Mock scraper configuration for testing."""
    return ScraperConfig(
        name="TestSource",
        enabled=True,
        scraper_class="tests.fixtures.mock_scraper.MockScraper",
        parser_class="tests.fixtures.mock_parser.MockParser",
        scraper_kwargs={"debug": True}
    )


@pytest.fixture
def french_text_processor():
    """Initialized French text processor for testing."""
    return FrenchTextProcessor()


@pytest.fixture
def csv_writer(temp_output_dir):
    """CSV writer with temporary output directory."""
    return DailyCSVWriter(output_dir=temp_output_dir, debug=True)


@pytest.fixture
def test_logger():
    """Test logger instance."""
    return get_structured_logger('test_logger')


@pytest.fixture
def mock_requests_response():
    """Mock requests response for HTTP testing."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"<html><body><h1>Test Article</h1><p>Test content</p></body></html>"
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def slate_test_files(raw_test_files_dir):
    """List of Slate.fr test files."""
    slate_dir = os.path.join(raw_test_files_dir, 'slate_fr')
    if os.path.exists(slate_dir):
        return [f for f in os.listdir(slate_dir) if f.endswith('.html')]
    return []


@pytest.fixture
def depeche_test_files(raw_test_files_dir):
    """List of Depeche.fr test files."""
    depeche_dir = os.path.join(raw_test_files_dir, 'depeche_fr')
    if os.path.exists(depeche_dir):
        return [f for f in os.listdir(depeche_dir) if f.endswith(('.html', '.php'))]
    return []


@pytest.fixture
def tf1_test_files(raw_test_files_dir):
    """List of TF1 test files."""
    tf1_dir = os.path.join(raw_test_files_dir, 'tf1_fr')
    if os.path.exists(tf1_dir):
        return [f for f in os.listdir(tf1_dir) if f.endswith('.html')]
    return []


@pytest.fixture
def lemonde_test_files(raw_test_files_dir):
    """List of LeMonde test files."""
    lemonde_dir = os.path.join(raw_test_files_dir, 'lemonde_fr')
    if os.path.exists(lemonde_dir):
        return [f for f in os.listdir(lemonde_dir) if f.endswith('.html')]
    return []


@pytest.fixture
def all_test_files(slate_test_files, depeche_test_files, tf1_test_files, lemonde_test_files):
    """Combined list of all test files."""
    return {
        'slate_fr': slate_test_files,
        'depeche_fr': depeche_test_files, 
        'tf1_fr': tf1_test_files,
        'lemonde_fr': lemonde_test_files
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment with proper settings."""
    # Force offline mode for tests
    monkeypatch.setenv('OFFLINE', 'True')
    monkeypatch.setenv('DEBUG', 'True')
    
    # Patch settings if already imported
    with patch('config.settings.OFFLINE', True):
        with patch('config.settings.DEBUG', True):
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
        'small': "Ceci est un petit texte français pour les tests.",
        'medium': " ".join([
            "Ceci est un texte de taille moyenne pour les tests de performance.",
            "Il contient plusieurs phrases avec du vocabulaire français varié.",
            "Le système doit traiter ce texte efficacement et rapidement.",
            "Nous testons la vitesse de traitement du texte français."
        ] * 10),
        'large': " ".join([
            "Ceci est un texte volumineux pour les tests de performance intensive.",
            "Il contient de nombreuses phrases avec un vocabulaire français étendu.",
            "Le système doit traiter ce texte volumineux de manière efficace.",
            "Nous testons les limites de performance du processeur de texte français.",
            "Cette analyse inclut la tokenisation, le nettoyage et le comptage.",
        ] * 100)
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
        "<html><body>🚫💥⚠️</body></html>",  # Special characters
    ]


@pytest.fixture
def mock_network_errors():
    """Mock various network error scenarios."""
    from requests.exceptions import ConnectionError, Timeout, HTTPError
    
    return {
        'connection_error': ConnectionError("Connection failed"),
        'timeout': Timeout("Request timed out"),
        'http_404': HTTPError("404 Not Found"),
        'http_500': HTTPError("500 Internal Server Error"),
    }


# Test data validation fixtures
@pytest.fixture
def expected_word_counts():
    """Expected word counts for test validation."""
    return {
        'slate_fr': {'min_words': 50, 'max_words': 1000},
        'depeche_fr': {'min_words': 30, 'max_words': 800},
        'tf1_fr': {'min_words': 40, 'max_words': 600},
        'lemonde_fr': {'min_words': 60, 'max_words': 1200},
    }


# Configuration for different test modes
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


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