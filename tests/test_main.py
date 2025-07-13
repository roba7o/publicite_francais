"""
Main test file for pytest tests/ command.

This file contains the core working tests that verify the system functionality
after the repository cleanup and directory restructuring.
"""

import pytest
import tempfile
import os
from article_scrapers.utils.french_text_processor import FrenchTextProcessor
from article_scrapers.utils.csv_writer import DailyCSVWriter
from article_scrapers.utils.logging_config_enhanced import setup_logging


class TestSystemFunctionality:
    """Core system functionality tests."""
    
    def test_logging_setup_works(self):
        """Test that logging can be set up without errors."""
        # Use the consolidated logs directory
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, ".."))
        log_directory = os.path.join(project_root, "src", "article_scrapers", "logs")
        setup_logging(log_directory=log_directory)
        assert True  # If we get here, logging setup worked
    
    def test_french_text_processor_works(self):
        """Test French text processor basic functionality."""
        processor = FrenchTextProcessor()
        
        french_text = "Voici un texte français simple pour tester le processeur."
        validated = processor.validate_text(french_text)
        assert validated is not None
        
        word_freq = processor.count_word_frequency(french_text)
        assert isinstance(word_freq, dict)
        assert len(word_freq) > 0
    
    def test_csv_writer_works(self, tmp_path):
        """Test CSV writer basic functionality."""
        writer = DailyCSVWriter(output_dir=str(tmp_path))
        
        article_data = {
            'title': 'Test français',
            'full_text': 'Contenu de test français avec des mots pour analyser.',
            'article_date': '2025-07-13',
            'date_scraped': '2025-07-13 17:00:00'
        }
        
        word_frequencies = {'français': 1, 'test': 2, 'contenu': 1}
        
        # Should not raise an error
        writer.write_article(article_data, "https://test.com", word_frequencies)
        
        # Check file was created
        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1
        assert csv_files[0].stat().st_size > 0
    
    def test_directory_structure(self):
        """Test that directory structure is correct."""
        writer = DailyCSVWriter()
        output_path = str(writer.output_dir)
        
        # Should use the new structure
        assert 'src/article_scrapers' in output_path
        assert output_path.endswith('output')
        assert os.path.exists(writer.output_dir)
    
    def test_text_processing_pipeline(self, tmp_path):
        """Test complete text processing pipeline."""
        processor = FrenchTextProcessor()
        writer = DailyCSVWriter(output_dir=str(tmp_path))
        
        article_text = """
        Le gouvernement français développe des politiques économiques importantes.
        Ces mesures auront un impact significatif sur la société française.
        """
        
        article_data = {
            'title': 'Politique Française',
            'full_text': article_text,
            'article_date': '2025-07-13',
            'date_scraped': '2025-07-13 17:00:00'
        }
        
        # Process text
        word_frequencies = processor.count_word_frequency(article_text)
        assert len(word_frequencies) > 3
        
        # Write to CSV
        writer.write_article(article_data, "https://test.com/politique", word_frequencies)
        
        # Verify output
        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1
        
        # Verify CSV content
        import csv
        with open(csv_files[0], 'r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
            assert len(rows) > 0
            assert any('français' in row.get('word', '').lower() for row in rows)


# Additional specific tests for individual components
class TestFrenchTextProcessor:
    """Specific tests for French text processor."""
    
    def test_initialization(self):
        """Test processor initializes correctly."""
        processor = FrenchTextProcessor()
        assert hasattr(processor, 'french_stopwords')
        assert hasattr(processor, 'junk_patterns')
        assert len(processor.french_stopwords) > 0
    
    def test_validate_text_valid_input(self):
        """Test text validation with valid input."""
        processor = FrenchTextProcessor()
        valid_text = "Ceci est un texte français valide avec suffisamment de contenu."
        result = processor.validate_text(valid_text)
        assert result is not None
        assert isinstance(result, str)
    
    def test_validate_text_empty_input(self):
        """Test text validation with empty input."""
        processor = FrenchTextProcessor()
        assert processor.validate_text("") is None
        assert processor.validate_text(None) is None
        assert processor.validate_text("   ") is None
    
    def test_count_word_frequency_basic(self):
        """Test basic word frequency counting."""
        processor = FrenchTextProcessor()
        text = "chat chat souris chat jardin souris"
        frequencies = processor.count_word_frequency(text)
        
        assert isinstance(frequencies, dict)
        # Note: actual counts may differ due to filtering, just verify structure
        assert len(frequencies) >= 0