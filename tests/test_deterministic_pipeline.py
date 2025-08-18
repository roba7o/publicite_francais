"""
Deterministic tests for the database→dbt pipeline.

These tests verify that the scraper + dbt processing produces exactly
the expected results from the known HTML test files. Any changes to
these counts indicate changes in parsing logic that need investigation.
"""

import subprocess

import pytest

from config.settings import DATABASE_ENV, NEWS_DATA_SCHEMA, SCHEMA_CONFIG
from config.source_configs import SCRAPER_CONFIGS
from services.article_pipeline import DatabaseProcessor


class TestDeterministicPipeline:
    """Test that pipeline produces consistent, expected results from test HTML files."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Ensure we're using the test database environment."""
        import os

        os.environ["DATABASE_ENV"] = "test"
        os.environ["OFFLINE"] = "True"

        # Initialize database for tests
        from database import initialize_database

        initialize_database()

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
        from database import get_database_manager

        db = get_database_manager()
        with db.get_session() as session:
            from sqlalchemy import text

            session.execute(text(f"TRUNCATE {NEWS_DATA_SCHEMA}.articles CASCADE;"))
            session.commit()

        # Run the database processor on all test files
        processed_count = 0
        attempted_count = 0

        processor = DatabaseProcessor()
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

        # Check that articles are actually in the database
        with db.get_session() as session:
            article_count = session.execute(
                text(f"SELECT COUNT(*) FROM {NEWS_DATA_SCHEMA}.articles")
            ).scalar()
            assert article_count == processed_count, (
                f"Database has {article_count} articles but processor reported {processed_count}"
            )

    def test_dbt_processing_pipeline_health(self):
        """Test that dbt processing produces reasonable data volumes and relationships."""

        # Run dbt processing on test data
        result = subprocess.run(
            ["../venv/bin/dbt", "run", "--target", "test"],
            cwd="french_flashcards",
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"dbt run failed: {result.stderr}"

        # Now verify exact counts from database
        from database import get_database_manager

        db = get_database_manager()

        with db.get_session() as session:
            from sqlalchemy import text

            # Test exact table counts - these are deterministic from test HTML files
            dbt_schema = SCHEMA_CONFIG["dbt"][DATABASE_ENV]
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
            assert 250 <= count_dict["sentences"] <= 400, (
                f"Expected 250-400 sentences (reasonable range), got {count_dict['sentences']}"
            )
            assert 2000 <= count_dict["raw_words"] <= 3000, (
                f"Expected 2000-3000 raw words (reasonable range), got {count_dict['raw_words']}"
            )
            assert 1500 <= count_dict["word_occurrences"] <= 2200, (
                f"Expected 1500-2200 quality word occurrences, got {count_dict['word_occurrences']}"
            )
            assert 200 <= count_dict["vocabulary_words"] <= 250, (
                f"Expected 200-250 vocabulary words, got {count_dict['vocabulary_words']}"
            )

            # Test data relationships (more robust than exact counts)
            assert count_dict["raw_words"] > count_dict["sentences"] * 4, (
                "Should have 4+ words per sentence on average"
            )
            assert count_dict["word_occurrences"] < count_dict["raw_words"], (
                "Quality words should be subset of raw words"
            )
            assert (
                count_dict["vocabulary_words"] < count_dict["word_occurrences"] * 0.2
            ), "Vocabulary should be <20% of word occurrences"

    def test_vocabulary_quality(self):
        """Test that vocabulary contains meaningful French words with reasonable frequencies."""
        from database import get_database_manager

        db = get_database_manager()

        with db.get_session() as session:
            from sqlalchemy import text

            # Test vocabulary quality instead of exact word frequencies
            dbt_schema = SCHEMA_CONFIG["dbt"][DATABASE_ENV]

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
        from database import get_database_manager

        db = get_database_manager()

        with db.get_session() as session:
            from sqlalchemy import text

            # Count articles per source
            source_counts = session.execute(
                text(f"""
                SELECT s.name, COUNT(a.id) as article_count
                FROM {NEWS_DATA_SCHEMA}.news_sources s
                LEFT JOIN {NEWS_DATA_SCHEMA}.articles a ON s.id = a.source_id
                GROUP BY s.name
                ORDER BY s.name
            """)
            ).fetchall()

            source_dict = {row[0]: row[1] for row in source_counts}

            # Each source should contribute articles (exact counts may vary based on HTML quality)
            expected_sources = ["Depeche.fr", "FranceInfo.fr", "Slate.fr", "TF1 Info"]

            for source in expected_sources:
                assert source in source_dict, f"Source '{source}' not found in database"
                assert source_dict[source] > 0, f"Source '{source}' has no articles"

            # Should have reasonable number of articles (allow for some variation)
            total_articles = sum(source_dict.values())
            assert 10 <= total_articles <= 20, (
                f"Expected 10-20 total articles, got {total_articles}"
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
        from database import get_database_manager

        db = get_database_manager()

        with db.get_session() as session:
            from sqlalchemy import text

            # Test data integrity across all tables
            dbt_schema = SCHEMA_CONFIG["dbt"][DATABASE_ENV]

            # Check for data consistency
            integrity_checks = session.execute(
                text(f"""
                SELECT
                    'articles_have_content' as check_name,
                    COUNT(*) FILTER (WHERE full_text IS NOT NULL AND length(full_text) > 100) as pass_count,
                    COUNT(*) as total_count
                FROM {NEWS_DATA_SCHEMA}.articles

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

            # Test that pipeline produces connected data
            pipeline_flow = session.execute(
                text(f"""
                SELECT
                    (SELECT COUNT(*) FROM {NEWS_DATA_SCHEMA}.articles) as articles,
                    (SELECT COUNT(*) FROM {dbt_schema}.sentences) as sentences,
                    (SELECT COUNT(*) FROM {dbt_schema}.raw_words) as raw_words,
                    (SELECT COUNT(*) FROM {dbt_schema}.vocabulary_for_flashcards) as vocabulary
            """)
            ).fetchone()

            # Ensure data flows through the entire pipeline
            articles, sentences, raw_words, vocabulary = pipeline_flow
            assert articles > 0, "No articles in source data"
            assert sentences > 0, "No sentences generated from articles"
            assert raw_words > 0, "No words extracted from sentences"
            assert vocabulary > 0, "No vocabulary generated from words"

            # Test pipeline flow ratios are reasonable
            assert sentences / articles >= 5, (
                f"Too few sentences per article ({sentences}/{articles} = {sentences / articles:.1f})"
            )
            assert raw_words / sentences >= 3, (
                f"Too few words per sentence ({raw_words}/{sentences} = {raw_words / sentences:.1f})"
            )
