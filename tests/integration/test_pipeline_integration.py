"""
Deterministic tests for the SCRAPE → UPLOAD RAW SOUP pipeline.

These tests verify that the UrlCollector → SoupValidator → Database pipeline
produces exactly the expected results from the known HTML test files.
Any changes to these counts indicate changes in parsing logic that need investigation.
"""

import os

import pytest

from config.environment import env_config
from config.site_configs import SCRAPER_CONFIGS
from core.orchestrator import ArticleOrchestrator


class TestScrapeUploadPipeline:
    """Test that SCRAPE → UPLOAD RAW SOUP pipeline produces consistent, expected results from test HTML files."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Ensure we're using the test database environment."""
        os.environ["DATABASE_ENV"] = "test"
        os.environ["TEST_MODE"] = "true"

        # Refresh environment config to pick up test settings
        env_config.refresh()

        # Initialize database for tests
        from database.database import initialize_database

        initialize_database()

    def _get_test_schema(self) -> str:
        """Get current schema name dynamically for tests."""
        # Should be test schema since we set DATABASE_ENV=test in setup_database
        return env_config.get('NEWS_DATA_TEST_SCHEMA')


    def test_html_file_counts(self):
        """Test that we have the expected number of HTML test files."""
        from pathlib import Path

        test_data_dir = (
            Path(__file__).parent.parent.parent / "src" / "test_data" / "raw_url_soup"
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
        from database.database import get_session

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

        processor = ArticleOrchestrator()
        for config in SCRAPER_CONFIGS:
            if config["enabled"]:
                # Config is already in dict format
                p_count, a_count = processor.process_site(config)
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


    def test_source_distribution(self):
        """Test that articles are distributed correctly across sources."""
        from database.database import get_session

        # Direct session usage

        with get_session() as session:
            from sqlalchemy import text

            # Count raw articles per source (ELT approach)
            source_counts = session.execute(
                text(f"""
                SELECT site, COUNT(*) as article_count
                FROM {self._get_test_schema()}.raw_articles
                GROUP BY site
                ORDER BY site
            """)
            ).fetchall()

            source_dict = {row[0]: row[1] for row in source_counts}

            # Each source should contribute articles (exact counts may vary based on HTML quality)
            # All sources should be working in offline mode
            expected_sources = ["slate.fr", "tf1info.fr", "ladepeche.fr", "franceinfo.fr"]  # All 4 sources working in test mode

            for source in expected_sources:
                assert source in source_dict, f"Source '{source}' not found in database"
                assert source_dict[source] > 0, f"Source '{source}' has no articles"

            # Should have reasonable number of articles (allow for some variation)
            # With 4 sources in test mode, expect 16 articles total (4 per source)
            total_articles = sum(source_dict.values())
            assert 14 <= total_articles <= 18, (
                f"Expected 14-18 total articles, got {total_articles}"
            )

            # Each working source should have exactly 4 articles (the test data files available)
            for source in expected_sources:
                if source in source_dict:
                    assert source_dict[source] == 4, (
                        f"Expected 4 {source} articles, got {source_dict[source]}"
                    )

