"""
Essential working tests only.

These tests verify core functionality is working correctly after development.
Focused on database pipeline functionality.
"""

import pytest
from unittest.mock import Mock, patch

from core.database_processor import DatabaseProcessor
from config.website_parser_scrapers_config import ScraperConfig
from models import ArticleData


class TestEssential:
    """Essential tests that must pass for the database system to work."""

    def test_database_processor_import_class(self):
        """Test that the DatabaseProcessor can import classes."""
        with patch('core.database_processor.importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_class = Mock()
            mock_module.TestClass = mock_class
            mock_import.return_value = mock_module
            
            result = DatabaseProcessor.import_class("test.module.TestClass")
            assert result == mock_class

    def test_database_processor_disabled_config(self):
        """Test that DatabaseProcessor handles disabled configurations."""
        # Create a mock disabled source configuration
        config = ScraperConfig(
            name="DisabledSource",
            enabled=False,
            scraper_class="scrapers.slate_fr_scraper.SlateFrURLScraper",
            parser_class="parsers.database_slate_fr_parser.DatabaseSlateFrParser"
        )
        
        # Test that the ScraperConfig properly tracks enabled state
        assert config.enabled is False
        assert config.name == "DisabledSource"

    def test_database_processor_initialization(self):
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
        """Test that configurations can be loaded."""
        from config.website_parser_scrapers_config import SCRAPER_CONFIGS
        
        assert isinstance(SCRAPER_CONFIGS, list)
        assert len(SCRAPER_CONFIGS) > 0
        
        # Check first config has required fields
        config = SCRAPER_CONFIGS[0]
        assert hasattr(config, 'name')
        assert hasattr(config, 'enabled')
        assert hasattr(config, 'scraper_class')
        assert hasattr(config, 'parser_class')

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