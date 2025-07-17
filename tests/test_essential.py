"""
Essential working tests only.

These tests verify core functionality is working correctly after development.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from core.processor import ArticleProcessor
from config.website_parser_scrapers_config import ScraperConfig
from models import ArticleData
from utils.csv_writer import DailyCSVWriter


class TestEssential:
    """Essential tests that must pass for the system to work."""

    def test_article_processor_import_class(self):
        """Test that the ArticleProcessor can import classes."""
        with patch('core.processor.importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_class = Mock()
            mock_module.TestClass = mock_class
            mock_import.return_value = mock_module
            
            result = ArticleProcessor.import_class("test.module.TestClass")
            assert result == mock_class

    def test_article_processor_disabled_config(self):
        """Test processing with disabled configuration."""
        config = ScraperConfig(
            name="DisabledSource",
            enabled=False,
            scraper_class="scrapers.slate_fr_scraper.SlateFrURLScraper",
            parser_class="parsers.slate_fr_parser.SlateFrArticleParser"
        )
        
        processed, attempted = ArticleProcessor.process_source(config)
        assert processed == 0
        assert attempted == 0

    def test_csv_writer_initialization(self):
        """Test CSV writer can be initialized."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DailyCSVWriter(output_dir=temp_dir, debug=True)
            assert writer.output_dir == temp_dir
            assert writer.debug is True

    def test_csv_writer_filename_generation(self):
        """Test CSV filename generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DailyCSVWriter(output_dir=temp_dir)
            filename = writer._get_filename()
            assert temp_dir in filename
            assert filename.endswith('.csv')

    def test_csv_writer_basic_functionality(self):
        """Test basic CSV writing functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DailyCSVWriter(output_dir=temp_dir)
            
            parsed_data = ArticleData(
                title='Test Article',
                full_text='Test content for the article',
                article_date='2025-07-14',
                date_scraped='2025-07-14'
            )
            url = 'https://test.com/article'
            word_freqs = {'bonjour': 3, 'monde': 2}
            
            # Should not raise exceptions
            writer.write_article(parsed_data, url, word_freqs)
            
            # Check file was created
            filename = writer._get_filename()
            assert os.path.exists(filename)

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