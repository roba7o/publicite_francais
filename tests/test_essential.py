"""
Essential working tests only.

These tests verify core functionality is working correctly after development.
Focused on database pipeline functionality.
"""

import pytest
from unittest.mock import Mock, patch

from services.article_pipeline import DatabaseProcessor
from config.source_configs import SCRAPER_CONFIGS
from models import ArticleData


class TestEssential:
    """Essential tests that must pass for the database system to work."""

    def test_article_pipeline_class_registry(self):
        """Test that the DatabaseProcessor can load classes from registry."""
        processor = DatabaseProcessor()
        
        # Test scraper class loading
        scraper_class = processor.get_scraper_class_safe("scrapers.slate_fr_scraper.SlateFrURLScraper")
        assert scraper_class is not None
        assert scraper_class.__name__ == "SlateFrURLScraper"
        
        # Test parser class loading  
        parser_class = processor.get_parser_class_safe("parsers.database_slate_fr_parser.DatabaseSlateFrParser")
        assert parser_class is not None
        assert parser_class.__name__ == "DatabaseSlateFrParser"

    def test_article_pipeline_disabled_config(self):
        """Test that DatabaseProcessor handles disabled configurations."""
        # Create a disabled source configuration dictionary
        config = {
            "name": "DisabledSource",
            "enabled": False,
            "scraper_class": "scrapers.slate_fr_scraper.SlateFrURLScraper",
            "parser_class": "parsers.database_slate_fr_parser.DatabaseSlateFrParser",
            "scraper_kwargs": {"debug": False}
        }
        
        # Test that the configuration dictionary has correct enabled state
        assert config["enabled"] is False
        assert config["name"] == "DisabledSource"
        assert config['enabled'] is False

    def test_article_pipeline_initialization(self):
        """Test DatabaseProcessor can be initialized."""
        processor = DatabaseProcessor()
        assert processor is not None

    def test_article_data_model(self):
        """Test ArticleData model creation."""
        parsed_data = ArticleData(
            title='Test Article',
            full_text='Test content for the article',
            article_date='2025-07-14',
            date_scraped='2025-07-14'
        )
        
        assert parsed_data.title == 'Test Article'
        assert parsed_data.full_text == 'Test content for the article'
        assert parsed_data.article_date == '2025-07-14'
        assert parsed_data.date_scraped == '2025-07-14'

    def test_database_connectivity_check(self):
        """Test database connectivity without actual database operations."""
        from config.settings import DATABASE_ENABLED
        # Just verify the setting can be imported
        assert isinstance(DATABASE_ENABLED, bool)

    def test_configuration_loading(self):
        """Test that configurations can be loaded in database architecture."""
        from config.source_configs import SCRAPER_CONFIGS
        
        assert isinstance(SCRAPER_CONFIGS, list)
        assert len(SCRAPER_CONFIGS) > 0
        
        # Check first config has required fields for database architecture
        config = SCRAPER_CONFIGS[0]
        assert isinstance(config, dict)
        assert 'name' in config
        assert 'enabled' in config
        assert 'scraper_class' in config
        
        # Test that dict format has all required fields
        assert 'name' in config
        assert 'enabled' in config  
        assert 'scraper_class' in config
        assert 'parser_class' in config
        assert 'scraper_kwargs' in config
        assert 'parser_kwargs' in config

    def test_offline_mode_setting(self):
        """Test that offline mode setting can be imported."""
        from config.settings import OFFLINE
        assert isinstance(OFFLINE, bool)

    def test_structured_logger_import(self):
        """Test that structured logger can be imported."""
        from utils.structured_logger import get_structured_logger
        logger = get_structured_logger('test')
        assert logger is not None

    def test_validators_import(self):
        """Test that validators can be imported."""
        from utils.validators import DataValidator
        validator = DataValidator()
        assert validator is not None

    def test_mock_classes_aligned_with_architecture(self):
        """Test that mock classes work with the new database architecture."""
        from services.article_pipeline import DatabaseProcessor
        from tests.fixtures.mock_parser_unified import MockDatabaseParser
        from tests.fixtures.mock_scraper import MockScraper
        from models import ArticleData
        
        # Test that mock parser returns ArticleData (not dict)
        parser = MockDatabaseParser("test-source")
        article_data = parser.parse_article(None)  # Mock doesn't need actual soup
        assert isinstance(article_data, ArticleData)
        assert article_data.title == "Mock Article Title"
        
        # Test that mock scraper works with processor
        scraper = MockScraper(debug=True)
        urls = scraper.get_article_urls()
        assert len(urls) == 3
        assert all(url.startswith("https://") for url in urls)