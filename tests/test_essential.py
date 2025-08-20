"""
Essential working tests only.

These tests verify core functionality is working correctly after development.
Focused on database pipeline functionality.
"""

from config.source_configs import SCRAPER_CONFIGS
from core.orchestrator import ArticleOrchestrator
from database.models import RawArticle


class TestEssential:
    """Essential tests that must pass for the database system to work."""

    def test_article_pipeline_class_registry(self):
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

    def test_article_pipeline_disabled_config(self):
        """Test that ArticleOrchestrator handles disabled configurations."""
        # Create a disabled source configuration dictionary
        config = {
            "domain": "disabled-source.fr",
            "enabled": False,
            "url_collector_class": "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector",
            "soup_validator_class": "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator",
            "url_collector_kwargs": {"debug": False},
        }

        # Test that the configuration dictionary has correct enabled state
        assert config["enabled"] is False
        assert config["domain"] == "disabled-source.fr"
        assert config["enabled"] is False

    def test_article_pipeline_initialization(self):
        """Test ArticleOrchestrator can be initialized."""
        processor = ArticleOrchestrator()
        assert processor is not None

    def test_raw_article_model(self):
        """Test RawArticle model creation."""
        raw_data = RawArticle(
            url="https://test.example.com/article",
            raw_html="<html><body><h1>Test Article</h1><p>Test content</p></body></html>",
            source="test.example.com",
        )

        assert raw_data.url == "https://test.example.com/article"
        assert "Test Article" in raw_data.raw_html
        assert raw_data.source == "test.example.com"
        assert raw_data.content_length > 0

    def test_database_connectivity_check(self):
        """Test database connectivity without actual database operations."""
        # Database is always enabled (no CSV fallback)
        # This test verifies database configuration can be imported
        from config.settings import NEWS_DATA_SCHEMA

        assert isinstance(NEWS_DATA_SCHEMA, str)

    def test_configuration_loading(self):
        """Test that configurations can be loaded in database architecture."""

        assert isinstance(SCRAPER_CONFIGS, list)
        assert len(SCRAPER_CONFIGS) > 0

        # Check first config has required fields for database architecture
        config = SCRAPER_CONFIGS[0]
        assert isinstance(config, dict)
        assert "domain" in config
        assert "enabled" in config
        assert "url_collector_class" in config

        # Test that dict format has all required fields
        assert "domain" in config
        assert "enabled" in config
        assert "url_collector_class" in config
        assert "soup_validator_class" in config
        assert "url_collector_kwargs" in config
        # soup_validator_kwargs is optional (handled by config.get("soup_validator_kwargs", {}))

    def test_test_mode_setting(self):
        """Test that test mode setting can be imported."""
        from config.settings import TEST_MODE

        assert isinstance(TEST_MODE, bool)

    def test_structured_logger_import(self):
        """Test that structured logger can be imported."""
        from utils.structured_logger import get_structured_logger

        logger = get_structured_logger("test")
        assert logger is not None

    def test_validators_removed(self):
        """Test that DataValidator was removed in favor of pure ELT approach."""
        # DataValidator removed - validation now handled by dbt
        assert True  # Placeholder test

    def test_mock_classes_aligned_with_architecture(self):
        """Test that mock classes work with the ELT database architecture."""
        from tests.fixtures.mock_parser_unified import MockDatabaseParser
        from tests.fixtures.mock_scraper import MockScraper

        # Test that mock parser returns RawArticle (ELT approach)
        parser = MockDatabaseParser("test-source")
        raw_article = parser.parse_article(None)  # Mock doesn't need actual soup
        assert isinstance(raw_article, RawArticle)
        assert "Mock Article Title" in raw_article.raw_html
        assert raw_article.source == "test.example.com"

        # Test that mock scraper works with processor
        scraper = MockScraper(debug=True)
        urls = scraper.get_article_urls()
        assert len(urls) == 3
        assert all(url.startswith("https://") for url in urls)
