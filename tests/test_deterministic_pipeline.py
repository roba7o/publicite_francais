"""
Deterministic tests for the database→dbt pipeline.

These tests verify that the scraper + dbt processing produces exactly
the expected results from the known HTML test files. Any changes to 
these counts indicate changes in parsing logic that need investigation.
"""

import pytest
import subprocess
from core.database_processor import DatabaseProcessor
from config.website_parser_scrapers_config import SCRAPER_CONFIGS


class TestDeterministicPipeline:
    """Test that pipeline produces consistent, expected results from test HTML files."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Ensure we're using the test database environment."""
        import os
        os.environ['DATABASE_ENV'] = 'test'
        os.environ['OFFLINE'] = 'True'
        
    def test_html_file_counts(self):
        """Test that we have the expected number of HTML test files."""
        from pathlib import Path
        
        test_data_dir = Path(__file__).parent.parent / 'src' / 'test_data' / 'raw_url_soup'
        
        # Count HTML files by source
        expected_files = {
            'Depeche.fr': 4,      # 4 PHP/HTML files
            'FranceInfo.fr': 4,   # 4 HTML files  
            'Slate.fr': 4,        # 4 HTML files
            'TF1 Info': 4,        # 4 HTML files
        }
        
        for source_name, expected_count in expected_files.items():
            source_dir = test_data_dir / source_name
            if source_dir.exists():
                actual_files = list(source_dir.glob('*.html')) + list(source_dir.glob('*.php'))
                assert len(actual_files) == expected_count, f"{source_name}: expected {expected_count} files, got {len(actual_files)}"
        
        # Total should be 16 files
        total_files = sum(
            len(list((test_data_dir / source).glob('*.html')) + list((test_data_dir / source).glob('*.php')))
            for source in expected_files.keys()
            if (test_data_dir / source).exists()
        )
        assert total_files == 16, f"Expected 16 total HTML files, got {total_files}"
    
    def test_database_article_extraction(self):
        """Test that exactly 14 articles are extracted and stored in database."""
        # Clear database first to ensure clean test
        import subprocess
        subprocess.run(['make', 'dbt-clean-test'], check=True, capture_output=True)
        
        # Clear articles table
        from database import get_database_manager
        db = get_database_manager()
        with db.get_session() as session:
            from sqlalchemy import text
            session.execute(text("TRUNCATE news_data_test.articles CASCADE;"))
            session.commit()
        
        # Run the database processor on all test files
        processed_count = 0
        attempted_count = 0
        
        for config in SCRAPER_CONFIGS:
            if config.enabled:
                # Convert to dict format for processor
                config_dict = {
                    'name': config.name,
                    'enabled': config.enabled,
                    'scraper_class': config.scraper_class,
                    'scraper_kwargs': config.scraper_kwargs or {}
                }
                
                p_count, a_count = DatabaseProcessor.process_source(config_dict)
                processed_count += p_count
                attempted_count += a_count
        
        # Should process exactly 14 articles from 16 HTML files 
        # (2 files may be malformed/empty)
        assert processed_count == 14, f"Expected 14 articles processed, got {processed_count}"
        assert attempted_count >= 14, f"Should attempt at least 14 articles, got {attempted_count}"
    
    def test_dbt_processing_deterministic_counts(self):
        """Test that dbt processing produces exactly expected table counts."""
        import subprocess
        import os
        
        # Run dbt processing on test data
        result = subprocess.run(
            ['../venv/bin/dbt', 'run', '--target', 'test'],
            cwd='french_flashcards',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"dbt run failed: {result.stderr}"
        
        # Now verify exact counts from database
        from database import get_database_manager
        db = get_database_manager()
        
        with db.get_session() as session:
            from sqlalchemy import text
            
            # Test exact table counts - these are deterministic from test HTML files
            counts = session.execute(text("""
                SELECT 'sentences' as table_name, COUNT(*) as count FROM dbt_test.sentences
                UNION ALL
                SELECT 'raw_words', COUNT(*) FROM dbt_test.raw_words  
                UNION ALL
                SELECT 'word_occurrences', COUNT(*) FROM dbt_test.word_occurrences
                UNION ALL
                SELECT 'vocabulary_words', COUNT(*) FROM dbt_test.vocabulary_for_flashcards
            """)).fetchall()
            
            count_dict = {row[0]: row[1] for row in counts}
            
            # These counts should be exactly reproducible from test HTML files
            # Updated counts reflect new raw_words table with boolean flags for filtering
            assert count_dict['sentences'] == 314, f"Expected 314 sentences, got {count_dict['sentences']}"
            assert count_dict['raw_words'] == 2506, f"Expected 2506 total raw words (with flags), got {count_dict['raw_words']}"  
            assert count_dict['word_occurrences'] == 1829, f"Expected 1829 quality word occurrences, got {count_dict['word_occurrences']}"
            assert count_dict['vocabulary_words'] == 174, f"Expected 174 vocabulary words, got {count_dict['vocabulary_words']}"
    
    def test_specific_word_frequencies(self):
        """Test that specific French words appear with expected frequencies."""
        from database import get_database_manager
        db = get_database_manager()
        
        with db.get_session() as session:
            from sqlalchemy import text
            
            # Test specific word frequencies - these should be deterministic
            # Updated to test quality words (removed 'selon' as it was correctly filtered as generic)
            word_frequencies = session.execute(text("""
                SELECT french_word, total_occurrences, appears_in_articles, appears_in_sentences
                FROM dbt_test.vocabulary_for_flashcards 
                WHERE french_word IN ('nouvelle', 'après', 'politique', 'france', 'défense')
                ORDER BY total_occurrences DESC
            """)).fetchall()
            
            frequency_dict = {row[0]: {'total': row[1], 'articles': row[2], 'sentences': row[3]} 
                            for row in word_frequencies}
            
            # These exact counts come from your test HTML files with enhanced filtering
            expected_frequencies = {
                'nouvelle': {'total': 23, 'articles': 4, 'sentences': 21},
                'après': {'total': 15, 'articles': 8, 'sentences': 15}, 
                'défense': {'total': 9, 'articles': 3, 'sentences': 9},
                'politique': {'total': 7, 'articles': 4, 'sentences': 7},
                'france': {'total': 6, 'articles': 4, 'sentences': 6},
            }
            
            for word, expected in expected_frequencies.items():
                assert word in frequency_dict, f"Word '{word}' not found in vocabulary"
                actual = frequency_dict[word]
                
                assert actual['total'] == expected['total'], \
                    f"'{word}' total occurrences: expected {expected['total']}, got {actual['total']}"
                assert actual['articles'] == expected['articles'], \
                    f"'{word}' appears in articles: expected {expected['articles']}, got {actual['articles']}"
                assert actual['sentences'] == expected['sentences'], \
                    f"'{word}' appears in sentences: expected {expected['sentences']}, got {actual['sentences']}"
    
    def test_source_distribution(self):
        """Test that articles are distributed correctly across sources."""
        from database import get_database_manager
        db = get_database_manager()
        
        with db.get_session() as session:
            from sqlalchemy import text
            
            # Count articles per source
            source_counts = session.execute(text("""
                SELECT s.name, COUNT(a.id) as article_count
                FROM news_data_test.news_sources s
                LEFT JOIN news_data_test.articles a ON s.id = a.source_id
                GROUP BY s.name
                ORDER BY s.name
            """)).fetchall()
            
            source_dict = {row[0]: row[1] for row in source_counts}
            
            # Each source should contribute articles (exact counts may vary based on HTML quality)
            expected_sources = ['Depeche.fr', 'FranceInfo.fr', 'Slate.fr', 'TF1 Info']
            
            for source in expected_sources:
                assert source in source_dict, f"Source '{source}' not found in database"
                assert source_dict[source] > 0, f"Source '{source}' has no articles"
            
            # Total should be 14 articles
            total_articles = sum(source_dict.values())
            assert total_articles == 14, f"Expected 14 total articles, got {total_articles}"
    
    def test_pipeline_consistency(self):
        """Test that running the pipeline multiple times gives identical results."""
        # Clear and run pipeline first time
        subprocess.run(['make', 'dbt-clean-test'], check=True, capture_output=True)
        
        first_run = self._run_pipeline_get_counts()
        
        # Clear and run pipeline second time  
        subprocess.run(['make', 'dbt-clean-test'], check=True, capture_output=True)
        
        second_run = self._run_pipeline_get_counts()
        
        # Results should be identical
        assert first_run == second_run, f"Pipeline results inconsistent: {first_run} vs {second_run}"
    
    def _run_pipeline_get_counts(self):
        """Helper: Run pipeline and return key counts."""
        import subprocess
        
        # Run full pipeline
        subprocess.run(['make', 'test-pipeline'], check=True, capture_output=True)
        
        # Get key counts
        from database import get_database_manager
        db = get_database_manager()
        
        with db.get_session() as session:
            from sqlalchemy import text
            
            result = session.execute(text("""
                SELECT 
                    (SELECT COUNT(*) FROM news_data_test.articles) as articles,
                    (SELECT COUNT(*) FROM dbt_test.sentences) as sentences,
                    (SELECT COUNT(*) FROM dbt_test.vocabulary_for_flashcards) as vocab_words
            """)).fetchone()
            
            return {'articles': result[0], 'sentences': result[1], 'vocab_words': result[2]}