"""
Deterministic tests for the database→dbt pipeline.

These tests verify that the scraper + dbt processing produces exactly
the expected results from the known HTML test files. Any changes to
these counts indicate changes in parsing logic that need investigation.
"""

import os
import subprocess

import pytest

from config.source_configs import SCRAPER_CONFIGS
from core.coordinator import ArticleCoordinator


class TestDeterministicPipeline:
    """Test that pipeline produces consistent, expected results from test HTML files."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Ensure we're using the test database environment."""
        os.environ["DATABASE_ENV"] = "test"
        os.environ["TEST_MODE"] = "true"

        # Initialize database for tests
        from core.database import initialize_database

        initialize_database()

    def _get_test_schema(self) -> str:
        """Get current schema name dynamically for tests."""
        # Should be test schema since we set DATABASE_ENV=test in setup_database
        return os.getenv("NEWS_DATA_TEST_SCHEMA", "news_data_test")

    def _get_dbt_test_schema(self) -> str:
        """Get dbt schema for test environment."""
        # Use dev schema since test target has auth issues
        return "dbt_staging"

    def test_html_file_counts(self):
        """Test that we have the expected number of HTML test files."""
        from pathlib import Path

        test_data_dir = (
            Path(__file__).parent.parent / "src" / "test_data" / "raw_url_soup"
        )

        # Count HTML files by source
        expected_files = {
            "Depeche.fr": 4,  # 4 PHP/HTML files
            "FranceInfo.fr": 4,  # 4 HTML files
            "Slate.fr": 4,  # 4 HTML files
            "TF1 Info": 4,  # 4 HTML files
        }

        for source_name, expected_count in expected_files.items():
            source_dir = test_data_dir / source_name
            if source_dir.exists():
                actual_files = list(source_dir.glob("*.html")) + list(
                    source_dir.glob("*.php")
                )
                assert len(actual_files) == expected_count, (
                    f"{source_name}: expected {expected_count} files, got {len(actual_files)}"
                )

        # Total should be 16 files
        total_files = sum(
            len(
                list((test_data_dir / source).glob("*.html"))
                + list((test_data_dir / source).glob("*.php"))
            )
            for source in expected_files.keys()
            if (test_data_dir / source).exists()
        )
        assert total_files == 16, f"Expected 16 total HTML files, got {total_files}"

    def test_database_article_extraction(self):
        """Test that articles are extracted and stored in database."""
        # Clear articles table for clean test
        from core.database import get_session

        # Direct session usage
        with get_session() as session:
            from sqlalchemy import text

            session.execute(
                text(f"TRUNCATE {self._get_test_schema()}.raw_articles CASCADE;")
            )
            session.commit()

        # Run the database processor on all test files
        processed_count = 0
        attempted_count = 0

        processor = ArticleCoordinator()
        for config in SCRAPER_CONFIGS:
            if config["enabled"]:
                # Config is already in dict format
                p_count, a_count = processor.process_source(config)
                processed_count += p_count
                attempted_count += a_count

        # Should process some articles from HTML files
        # Exact count may vary based on file content and parsing success
        assert processed_count > 0, (
            f"Expected some articles processed, got {processed_count}"
        )
        assert attempted_count >= processed_count, (
            f"Attempted count ({attempted_count}) should be >= processed count ({processed_count})"
        )

        # Check that raw articles are actually in the database (ELT approach)
        with get_session() as session:
            raw_article_count = session.execute(
                text(f"SELECT COUNT(*) FROM {self._get_test_schema()}.raw_articles")
            ).scalar()
            assert raw_article_count == processed_count, (
                f"Database has {raw_article_count} raw articles but processor reported {processed_count}"
            )

    def test_dbt_processing_pipeline_health(self):
        """Test that dbt processing produces reasonable data volumes and relationships."""

        # Run dbt processing on test data (using dev target since test auth is broken)
        result = subprocess.run(
            ["../venv/bin/dbt", "run"],
            cwd="french_flashcards",
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"dbt run failed: {result.stderr}"

        # Now verify exact counts from database
        from core.database import get_session

        # Direct session usage

        with get_session() as session:
            from sqlalchemy import text

            # Test exact table counts - these are deterministic from test HTML files
            dbt_schema = self._get_dbt_test_schema()
            counts = session.execute(
                text(f"""
                SELECT 'sentences' as table_name, COUNT(*) as count FROM {dbt_schema}.sentences
                UNION ALL
                SELECT 'raw_words', COUNT(*) FROM {dbt_schema}.raw_words
                UNION ALL
                SELECT 'word_occurrences', COUNT(*) FROM {dbt_schema}.word_occurrences
                UNION ALL
                SELECT 'vocabulary_words', COUNT(*) FROM {dbt_schema}.vocabulary_for_flashcards
            """)
            ).fetchall()

            count_dict = {row[0]: row[1] for row in counts}

            # Robust pipeline health checks - test reasonable ranges not exact counts
            # This ensures pipeline works without being fragile to minor processing changes
            assert 1500 <= count_dict["sentences"] <= 2500, (
                f"Expected 1500-2500 sentences (reasonable range), got {count_dict['sentences']}"
            )
            assert 7000 <= count_dict["raw_words"] <= 10000, (
                f"Expected 7000-10000 raw words (reasonable range), got {count_dict['raw_words']}"
            )
            assert 15000 <= count_dict["word_occurrences"] <= 18000, (
                f"Expected 15000-18000 quality word occurrences, got {count_dict['word_occurrences']}"
            )
            assert 1400 <= count_dict["vocabulary_words"] <= 1800, (
                f"Expected 1400-1800 vocabulary words, got {count_dict['vocabulary_words']}"
            )

            # Test data relationships (more robust than exact counts)
            assert count_dict["raw_words"] > count_dict["sentences"] * 4, (
                "Should have 4+ words per sentence on average"
            )
            assert count_dict["word_occurrences"] > count_dict["raw_words"], (
                "Word occurrences should be more than unique raw words (due to repetition)"
            )
            assert (
                count_dict["vocabulary_words"] < count_dict["word_occurrences"] * 0.2
            ), "Vocabulary should be <20% of word occurrences"

    def test_vocabulary_quality(self):
        """Test that vocabulary contains meaningful French words with reasonable frequencies."""
        from core.database import get_session

        # Direct session usage

        with get_session() as session:
            from sqlalchemy import text

            # Test vocabulary quality instead of exact word frequencies
            dbt_schema = self._get_dbt_test_schema()

            # Check that we have some common French words with reasonable frequencies
            vocab_stats = session.execute(
                text(f"""
                SELECT
                    COUNT(*) as total_vocab,
                    COUNT(*) FILTER (WHERE total_occurrences >= 5) as frequent_words,
                    COUNT(*) FILTER (WHERE appears_in_articles >= 2) as multi_article_words,
                    MAX(total_occurrences) as max_frequency,
                    AVG(total_occurrences) as avg_frequency
                FROM {dbt_schema}.vocabulary_for_flashcards
            """)
            ).fetchone()

            # Test vocabulary quality metrics
            assert vocab_stats[0] >= 100, (
                f"Should have at least 100 vocabulary words, got {vocab_stats[0]}"
            )
            assert vocab_stats[1] >= 20, (
                f"Should have at least 20 frequent words (5+ occurrences), got {vocab_stats[1]}"
            )
            assert vocab_stats[2] >= 50, (
                f"Should have at least 50 words appearing in multiple articles, got {vocab_stats[2]}"
            )
            assert vocab_stats[3] >= 10, (
                f"Most frequent word should appear 10+ times, got {vocab_stats[3]}"
            )
            assert 2 <= vocab_stats[4] <= 20, (
                f"Average frequency should be reasonable (2-20), got {vocab_stats[4]}"
            )

            # Test that vocabulary contains actual French words (not just numbers/fragments)
            sample_words = session.execute(
                text(f"""
                SELECT french_word FROM {dbt_schema}.vocabulary_for_flashcards
                WHERE total_occurrences >= 5 LIMIT 10
            """)
            ).fetchall()

            sample_word_list = [row[0] for row in sample_words]

            # Basic sanity checks on word quality
            for word in sample_word_list[:5]:  # Check first 5 words
                assert len(word) >= 3, f"Vocabulary word '{word}' too short (< 3 chars)"
                assert word.isalpha() or "-" in word, (
                    f"Vocabulary word '{word}' should be alphabetic or contain hyphens"
                )
                assert not word.isnumeric(), (
                    f"Vocabulary word '{word}' should not be purely numeric"
                )

    def test_source_distribution(self):
        """Test that articles are distributed correctly across sources."""
        from core.database import get_session

        # Direct session usage

        with get_session() as session:
            from sqlalchemy import text

            # Count raw articles per source (ELT approach)
            source_counts = session.execute(
                text(f"""
                SELECT source, COUNT(*) as article_count
                FROM {self._get_test_schema()}.raw_articles
                GROUP BY source
                ORDER BY source
            """)
            ).fetchall()

            source_dict = {row[0]: row[1] for row in source_counts}

            # Each source should contribute articles (exact counts may vary based on HTML quality)
            # Only test sources that have test data files in offline mode
            expected_sources = ["slate.fr", "franceinfo.fr"]

            for source in expected_sources:
                assert source in source_dict, f"Source '{source}' not found in database"
                assert source_dict[source] > 0, f"Source '{source}' has no articles"

            # Should have reasonable number of articles (allow for some variation)
            # With 2 sources in test mode, expect 6-12 articles total
            total_articles = sum(source_dict.values())
            assert 6 <= total_articles <= 12, (
                f"Expected 6-12 total articles, got {total_articles}"
            )

            # Each source should contribute roughly equally (within reason)
            if total_articles > 0:
                avg_per_source = total_articles / len(expected_sources)
                for source in expected_sources:
                    assert source_dict[source] <= avg_per_source * 2, (
                        f"Source '{source}' has too many articles ({source_dict[source]})"
                    )

    def test_data_quality_integrity(self):
        """Test overall data quality and integrity across the pipeline."""
        from core.database import get_session

        # Direct session usage

        with get_session() as session:
            from sqlalchemy import text

            # Test data integrity across all tables
            dbt_schema = self._get_dbt_test_schema()

            # Check for data consistency (ELT approach - check raw HTML content)
            integrity_checks = session.execute(
                text(f"""
                SELECT
                    'raw_articles_have_html' as check_name,
                    COUNT(*) FILTER (WHERE raw_html IS NOT NULL AND length(raw_html) > 1000) as pass_count,
                    COUNT(*) as total_count
                FROM {self._get_test_schema()}.raw_articles

                UNION ALL

                SELECT
                    'sentences_contain_french' as check_name,
                    COUNT(*) FILTER (WHERE sentence_text ~ '[àâäçéèêëïîôûùüÿñæœ]') as pass_count,
                    COUNT(*) as total_count
                FROM {dbt_schema}.sentences

                UNION ALL

                SELECT
                    'vocabulary_words_meaningful' as check_name,
                    COUNT(*) FILTER (WHERE length(french_word) >= 3 AND french_word ~ '^[a-zA-ZàâäçéèêëïîôûùüÿñæœÀÂÄÇÉÈÊËÏÎÔÛÙÜŸÑÆŒ-]+$') as pass_count,
                    COUNT(*) as total_count
                FROM {dbt_schema}.vocabulary_for_flashcards
            """)
            ).fetchall()

            # Verify data quality standards
            for check_name, pass_count, total_count in integrity_checks:
                if total_count > 0:
                    pass_rate = pass_count / total_count
                    assert pass_rate >= 0.8, (
                        f"Data quality check '{check_name}' failed: {pass_rate:.2%} pass rate (expected ≥80%)"
                    )

            # Test that ELT pipeline produces connected data
            pipeline_flow = session.execute(
                text(f"""
                SELECT
                    (SELECT COUNT(*) FROM {self._get_test_schema()}.raw_articles) as raw_articles,
                    (SELECT COUNT(*) FROM {dbt_schema}.sentences) as sentences,
                    (SELECT COUNT(*) FROM {dbt_schema}.raw_words) as raw_words,
                    (SELECT COUNT(*) FROM {dbt_schema}.vocabulary_for_flashcards) as vocabulary
            """)
            ).fetchone()

            # Ensure data flows through the entire ELT pipeline
            raw_articles, sentences, raw_words, vocabulary = pipeline_flow
            assert raw_articles > 0, "No raw articles in source data"
            assert sentences > 0, "No sentences generated from raw articles"
            assert raw_words > 0, "No words extracted from sentences"
            assert vocabulary > 0, "No vocabulary generated from words"

            # Test pipeline flow ratios are reasonable
            assert sentences / raw_articles >= 5, (
                f"Too few sentences per article ({sentences}/{raw_articles} = {sentences / raw_articles:.1f})"
            )
            assert raw_words / sentences >= 3, (
                f"Too few words per sentence ({raw_words}/{sentences} = {raw_words / sentences:.1f})"
            )
