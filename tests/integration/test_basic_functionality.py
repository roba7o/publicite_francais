"""
Basic integration tests to verify the main functionality works.

These tests verify that the core components can work together correctly
after the directory restructuring and configuration changes.
"""

import pytest
import tempfile
import os
from pathlib import Path
from models import ArticleData
from utils.french_text_processor import FrenchTextProcessor
from utils.csv_writer import DailyCSVWriter
from utils.logging_config_enhanced import setup_logging


class TestBasicFunctionality:
    """Test basic functionality of core components."""
    
    def test_logging_setup(self):
        """Test that logging can be set up without errors."""
        # Use the consolidated logs directory
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
        log_directory = os.path.join(project_root, "src", "logs")
        setup_logging(log_directory=log_directory)
        # If we get here without errors, logging setup worked
        assert True
    
    def test_french_text_processor_basic(self):
        """Test basic French text processing functionality."""
        processor = FrenchTextProcessor()
        
        # Test with simple French text
        french_text = "Voici un texte français simple pour tester le processeur de texte."
        
        # Test validation
        validated = processor.validate_text(french_text)
        assert validated is not None
        assert len(validated) > 0
        
        # Test word frequency counting
        word_freq = processor.count_word_frequency(french_text)
        assert isinstance(word_freq, dict)
        assert len(word_freq) > 0
        
        # Should contain some French words
        words = list(word_freq.keys())
        assert len(words) > 3  # Should have multiple meaningful words
    
    def test_csv_writer_basic(self, tmp_path):
        """Test basic CSV writer functionality."""
        writer = DailyCSVWriter(output_dir=str(tmp_path))
        
        # Verify the writer was created with correct output directory
        assert str(tmp_path) in str(writer.output_dir)
        
        # Test writing an article
        article_data = ArticleData(
            title='Test Article français',
            full_text='Contenu de test français avec suffisamment de mots pour analyser.',
            article_date='2025-07-13',
            date_scraped='2025-07-13 17:00:00'
        )
        
        word_frequencies = {'français': 2, 'test': 3, 'contenu': 1, 'analyser': 1}
        word_contexts = {
            'français': 'Test Article français avec contenu',
            'test': 'Test Article avec contenu de test',
            'contenu': 'Contenu de test français',
            'analyser': 'suffisamment de mots pour analyser'
        }
        
        # This should not raise an error
        writer.write_article(article_data, "https://test.com/article", word_frequencies, word_contexts)
        
        # Check that a CSV file was created
        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1
        
        # Verify the file has content
        csv_file = csv_files[0]
        assert csv_file.stat().st_size > 0
    
    def test_text_processing_pipeline(self, tmp_path):
        """Test the complete text processing pipeline."""
        processor = FrenchTextProcessor()
        writer = DailyCSVWriter(output_dir=str(tmp_path))
        
        # Simulate processing a French article
        article_text = """
        Le gouvernement français annonce de nouvelles mesures économiques importantes.
        Ces décisions politiques auront un impact significatif sur la population française.
        Les experts analysent attentivement ces changements gouvernementaux majeurs.
        Cette politique française modernise le système économique national actuel.
        """
        
        article_data = ArticleData(
            title='Mesures Économiques Françaises',
            full_text=article_text,
            article_date='2025-07-13',
            date_scraped='2025-07-13 17:00:00'
        )
        
        # Process the text
        word_frequencies = processor.count_word_frequency(article_text)
        assert len(word_frequencies) > 5  # Should extract multiple words
        
        # Get top words
        top_words = processor.get_top_words(article_text, n=10)
        assert len(top_words) > 0
        assert all(isinstance(item, tuple) and len(item) == 2 for item in top_words)
        
        # Extract contexts
        top_word_list = [word for word, _ in top_words[:5]]
        contexts = processor.extract_sentences_with_words(article_text, top_word_list)
        
        # Write to CSV
        writer.write_article(article_data, "https://test.com/mesures", word_frequencies, contexts)
        
        # Verify output
        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1
        
        # Read and verify CSV content
        import csv
        with open(csv_files[0], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0
            
            # Check that we have French words
            french_words_found = sum(1 for row in rows if 'français' in row.get('word', '').lower() or 
                                   'économique' in row.get('word', '').lower() or
                                   'politique' in row.get('word', '').lower())
            assert french_words_found > 0
    
    def test_output_directory_structure(self):
        """Test that output directories are correctly configured."""
        processor = FrenchTextProcessor()
        writer = DailyCSVWriter()
        
        # Check that the writer uses the expected output directory structure
        output_path = str(writer.output_dir)
        assert 'src' in output_path
        assert output_path.endswith('output')
        
        # Verify the directory exists
        assert os.path.exists(writer.output_dir)
        assert os.path.isdir(writer.output_dir)
    
    def test_logging_directory_structure(self):
        """Test that logging is configured to use the correct directory."""
        # Use the consolidated logs directory
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
        log_directory = os.path.join(project_root, "src", "logs")
        setup_logging(log_directory=log_directory)
        
        # The logging should be set up to use src/logs
        # We can't easily test the exact path without accessing logging internals,
        # but we can verify setup completes without errors
        assert True  # If we got here, logging setup worked
    
    def test_french_text_quality(self):
        """Test French text processing quality with real French content."""
        processor = FrenchTextProcessor()
        
        # Real French text with various characteristics
        real_french_text = """
        L'économie française traverse une période de transformation majeure avec de 
        nombreuses réformes structurelles. Le gouvernement français développe des 
        stratégies innovantes pour moderniser les institutions nationales. Ces 
        changements politiques reflètent l'évolution de la société française 
        contemporaine vers une approche plus durable et équitable.
        """
        
        # Process the text
        word_frequencies = processor.count_word_frequency(real_french_text)
        
        # Should extract meaningful French words
        assert len(word_frequencies) >= 10
        
        # Check for presence of expected French words
        words = list(word_frequencies.keys())
        expected_words = ['française', 'français', 'économie', 'gouvernement', 'société', 'politique']
        found_expected = sum(1 for expected in expected_words 
                           if any(expected in word for word in words))
        
        assert found_expected >= 2  # Should find at least 2 expected French words
        
        # Test context extraction
        top_words = processor.get_top_words(real_french_text, n=5)
        top_word_list = [word for word, _ in top_words]
        contexts = processor.extract_sentences_with_words(real_french_text, top_word_list)
        
        # Should have meaningful contexts
        assert len(contexts) > 0
        context_values = list(contexts.values())
        assert all(len(context) > 10 for context in context_values)  # Non-trivial contexts
    
    def test_concurrent_processing_basic(self, tmp_path):
        """Test basic concurrent processing doesn't break."""
        import threading
        import time
        
        processor = FrenchTextProcessor()
        results = []
        errors = []
        
        def process_text(text_id):
            try:
                text = f"Texte français numéro {text_id} pour tester le traitement concurrent."
                word_freq = processor.count_word_frequency(text)
                results.append((text_id, len(word_freq)))
            except Exception as e:
                errors.append((text_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_text, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert all(word_count > 0 for _, word_count in results)