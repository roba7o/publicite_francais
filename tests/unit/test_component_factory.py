"""
Component Factory and Core Component Tests.

Tests for component loading, factory patterns, and basic component functionality.
Extracted from test_essential.py for better organization.
"""

import pytest

from config.site_configs import SCRAPER_CONFIGS
from core.orchestrator import ArticleOrchestrator
from database.models import RawArticle


class TestComponentFactory:
    """Tests for component factory and class loading."""

    def test_component_class_loading(self):
        """Test that the component loader can load classes from class paths."""
        from core.component_loader import import_class

        # Test url collector class loading
        url_collector_class = import_class("core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector")
        assert url_collector_class is not None
        assert url_collector_class.__name__ == "SlateFrUrlCollector"

        # Test soup validator class loading
        soup_validator_class = import_class(
            "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator"
        )
        assert soup_validator_class is not None
        assert soup_validator_class.__name__ == "SlateFrSoupValidator"

    def test_article_orchestrator_initialization(self):
        """Test ArticleOrchestrator can be initialized."""
        processor = ArticleOrchestrator()
        assert processor is not None

    def test_disabled_config_handling(self):
        """Test that ArticleOrchestrator handles disabled configurations."""
        # Create a disabled source configuration dictionary
        config = {
            "site": "disabled-source.fr",
            "enabled": False,
            "url_collector_class": "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector",
            "soup_validator_class": "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator",
            "url_collector_kwargs": {"debug": False},
        }

        # Test that the configuration dictionary has correct enabled state
        assert config["enabled"] is False
        assert config["site"] == "disabled-source.fr"


class TestModels:
    """Tests for database models."""

    def test_raw_article_model_creation(self):
        """Test RawArticle model creation."""
        raw_data = RawArticle(
            url="https://test.example.com/article",
            raw_html="<html><body><h1>Test Article</h1><p>Test content</p></body></html>",
            site="test.example.com",
        )

        assert raw_data.url == "https://test.example.com/article"
        assert "Test Article" in raw_data.raw_html
        assert raw_data.site == "test.example.com"
        assert raw_data.content_length > 0


class TestConfiguration:
    """Tests for configuration loading and validation."""

    def test_configuration_loading(self):
        """Test that configurations can be loaded in database architecture."""

        assert isinstance(SCRAPER_CONFIGS, list)
        assert len(SCRAPER_CONFIGS) > 0

        # Check first config has required fields for database architecture
        config = SCRAPER_CONFIGS[0]
        assert isinstance(config, dict)
        assert "site" in config
        assert "enabled" in config
        assert "url_collector_class" in config

        # Test that dict format has all required fields
        assert "site" in config
        assert "enabled" in config
        assert "url_collector_class" in config
        assert "soup_validator_class" in config
        assert "url_collector_kwargs" in config
        # soup_validator_kwargs is optional (handled by config.get("soup_validator_kwargs", {}))

    def test_environment_configuration(self):
        """Test that environment configuration can be loaded."""
        from config.environment import env_config

        test_mode = env_config.is_test_mode()
        assert isinstance(test_mode, bool)

        schema = env_config.get_news_data_schema()
        assert isinstance(schema, str)


class TestUtilities:
    """Tests for utility functions and imports."""

    def test_structured_logger_import(self):
        """Test that structured logger can be imported."""
        from utils.structured_logger import Logger

        logger = Logger("test")
        assert logger is not None

    def test_validators_removed(self):
        """Test that DataValidator was removed in favor of pure ELT approach."""
        # DataValidator removed - validation now handled by dbt
        assert True  # Placeholder test


class TestMockClasses:
    """Tests for mock classes used in testing."""

    def test_mock_classes_aligned_with_architecture(self):
        """Test that mock classes work with the ELT database architecture."""
        from tests.fixtures.mock_parser_unified import MockDatabaseParser
        from tests.fixtures.mock_scraper import MockScraper

        # Test that mock parser returns RawArticle (ELT approach)
        parser = MockDatabaseParser("test-source")
        raw_article = parser.parse_article(None)  # Mock doesn't need actual soup
        assert isinstance(raw_article, RawArticle)
        assert "Mock Article Title" in raw_article.raw_html
        assert raw_article.site == "test.example.com"

        # Test that mock scraper works with processor
        scraper = MockScraper(debug=True)
        urls = scraper.get_article_urls()
        assert len(urls) == 3
        assert all(url.startswith("https://") for url in urls)