"""
Simple integration tests for ArticleOrchestrator.
"""

import pytest
from unittest.mock import patch, MagicMock

from core.orchestrator import ArticleOrchestrator
from database.models import RawArticle


@pytest.fixture
def orchestrator():
    """Create orchestrator instance for testing."""
    return ArticleOrchestrator()


@pytest.fixture
def mock_site_config():
    """Mock site configuration for testing."""
    return {
        "site": "test-site.fr",
        "enabled": True,
        "url_collector_class": "mock.url_collector",
        "soup_validator_class": "mock.soup_validator",
        "url_collector_kwargs": {},
        "soup_validator_kwargs": {},
    }


@pytest.fixture
def sample_raw_article():
    """Sample raw article for testing."""
    return RawArticle(
        url="https://test-site.fr/article-123",
        raw_html="<html><h1>Test Article</h1><p>Test content</p></html>",
        site="test-site.fr",
    )


class TestArticleOrchestrator:
    """Test cases for ArticleOrchestrator integration."""

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes correctly."""
        assert orchestrator.logger is not None
        assert orchestrator.component_factory is not None

    @patch("core.orchestrator.TEST_MODE", True)
    def test_process_site_test_mode(self, orchestrator, mock_site_config, sample_raw_article):
        """Test processing site in TEST_MODE."""
        mock_collector = MagicMock()
        mock_validator = MagicMock()

        # Mock validator methods
        mock_validator.get_test_sources_from_directory.return_value = [
            ("<html><h1>Test</h1></html>", "test-file.html")
        ]
        mock_validator.validate_and_extract.return_value = sample_raw_article

        with patch.object(orchestrator.component_factory, 'create_collector', return_value=mock_collector), \
             patch.object(orchestrator.component_factory, 'create_validator', return_value=mock_validator), \
             patch("database.store_articles_batch", return_value=(1, 0)) as mock_store:

            processed, attempted = orchestrator.process_site(mock_site_config)

            assert processed == 1
            assert attempted == 1

            # Verify component creation was called
            orchestrator.component_factory.create_collector.assert_called_once_with(mock_site_config)
            orchestrator.component_factory.create_validator.assert_called_once_with(mock_site_config)

            # Verify test sources were fetched
            mock_validator.get_test_sources_from_directory.assert_called_once_with("test-site.fr")

            # Verify validation was called
            mock_validator.validate_and_extract.assert_called_once()

            # Verify storage was called
            mock_store.assert_called_once()

    @patch("core.orchestrator.TEST_MODE", False)
    def test_process_site_live_mode(self, orchestrator, mock_site_config, sample_raw_article):
        """Test processing site in live mode."""
        mock_collector = MagicMock()
        mock_validator = MagicMock()

        # Mock collector methods
        mock_collector.get_article_urls.return_value = ["https://test-site.fr/article-1"]

        # Mock validator methods
        mock_validator.get_soup_from_url.return_value = "<html><h1>Test</h1></html>"
        mock_validator.validate_and_extract.return_value = sample_raw_article

        with patch.object(orchestrator.component_factory, 'create_collector', return_value=mock_collector), \
             patch.object(orchestrator.component_factory, 'create_validator', return_value=mock_validator), \
             patch("database.store_articles_batch", return_value=(1, 0)) as mock_store:

            processed, attempted = orchestrator.process_site(mock_site_config)

            assert processed == 1
            assert attempted == 1

            # Verify URL collection was called
            mock_collector.get_article_urls.assert_called_once()

            # Verify soup fetching was called
            mock_validator.get_soup_from_url.assert_called()

            # Verify validation was called
            mock_validator.validate_and_extract.assert_called_once()

            # Verify storage was called
            mock_store.assert_called_once()

    def test_process_site_disabled(self, orchestrator):
        """Test processing disabled site returns zeros."""
        disabled_config = {"site": "disabled.fr", "enabled": False}

        processed, attempted = orchestrator.process_site(disabled_config)

        assert processed == 0
        assert attempted == 0

    def test_process_site_component_failure(self, orchestrator, mock_site_config):
        """Test handling component creation failure."""
        with patch.object(orchestrator.component_factory, 'create_collector', side_effect=Exception("Component error")):
            processed, attempted = orchestrator.process_site(mock_site_config)

            assert processed == 0
            assert attempted == 0

    def test_process_site_no_urls(self, orchestrator, mock_site_config):
        """Test handling when no URLs are found."""
        mock_collector = MagicMock()
        mock_validator = MagicMock()

        # Mock empty URL list
        mock_collector.get_article_urls.return_value = []

        with patch.object(orchestrator.component_factory, 'create_collector', return_value=mock_collector), \
             patch.object(orchestrator.component_factory, 'create_validator', return_value=mock_validator), \
             patch("core.orchestrator.TEST_MODE", False):

            processed, attempted = orchestrator.process_site(mock_site_config)

            assert processed == 0
            assert attempted == 0

    def test_process_all_sites(self, orchestrator):
        """Test processing multiple sites."""
        site_configs = [
            {"site": "site1.fr", "enabled": True},
            {"site": "site2.fr", "enabled": True},
            {"site": "site3.fr", "enabled": False},  # This should be skipped
        ]

        with patch.object(orchestrator, 'process_site') as mock_process:
            # Mock returns: (processed, attempted)
            mock_process.side_effect = [(2, 3), (1, 2)]  # Only 2 calls for enabled sites

            total_processed, total_attempted = orchestrator.process_all_sites(site_configs)

            assert total_processed == 3  # 2 + 1
            assert total_attempted == 5  # 3 + 2
            assert mock_process.call_count == 2  # Only enabled sites

    def test_process_all_sites_empty_list(self, orchestrator):
        """Test processing empty site list."""
        total_processed, total_attempted = orchestrator.process_all_sites([])

        assert total_processed == 0
        assert total_attempted == 0

    @patch("core.orchestrator.TEST_MODE", True)
    def test_process_site_no_test_sources(self, orchestrator, mock_site_config):
        """Test handling when no test sources are found."""
        mock_collector = MagicMock()
        mock_validator = MagicMock()

        # Mock empty test sources
        mock_validator.get_test_sources_from_directory.return_value = []

        with patch.object(orchestrator.component_factory, 'create_collector', return_value=mock_collector), \
             patch.object(orchestrator.component_factory, 'create_validator', return_value=mock_validator):

            processed, attempted = orchestrator.process_site(mock_site_config)

            assert processed == 0
            assert attempted == 0

    @patch("core.orchestrator.TEST_MODE", True)
    def test_process_site_validation_failure(self, orchestrator, mock_site_config):
        """Test handling when validation fails."""
        mock_collector = MagicMock()
        mock_validator = MagicMock()

        # Mock test sources but validation fails
        mock_validator.get_test_sources_from_directory.return_value = [
            ("<html><h1>Test</h1></html>", "test-file.html")
        ]
        mock_validator.validate_and_extract.return_value = None  # Validation failure

        with patch.object(orchestrator.component_factory, 'create_collector', return_value=mock_collector), \
             patch.object(orchestrator.component_factory, 'create_validator', return_value=mock_validator):

            processed, attempted = orchestrator.process_site(mock_site_config)

            assert processed == 0
            assert attempted == 1  # One source attempted
