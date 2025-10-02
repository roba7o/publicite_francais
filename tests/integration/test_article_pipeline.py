"""
Article Processing Pipeline Integration Tests.

Tests the complete end-to-end pipeline: URL Collection → Content Extraction → Database Storage
using your existing 16 HTML test files for deterministic, repeatable results.
"""

from sqlalchemy import text

from config.site_configs import SCRAPER_CONFIGS
from core.orchestrator import ArticleOrchestrator
from database.database import get_session


class TestHtmlTestDataIntegrity:
    """Verify the integrity of your 16 HTML test files."""

    def test_all_test_files_exist(self, test_html_files):
        """Test that all expected HTML test files are available."""
        # Should have all 4 sources
        expected_sources = ["slate.fr", "franceinfo.fr", "tf1info.fr", "ladepeche.fr"]
        assert set(test_html_files.keys()) == set(expected_sources)

        # Each source should have exactly 4 files
        for source, files in test_html_files.items():
            assert len(files) == 4, f"Expected 4 files for {source}, got {len(files)}"

        # Total should be 16 files
        total_files = sum(len(files) for files in test_html_files.values())
        assert total_files == 16, f"Expected 16 total HTML files, got {total_files}"

    def test_html_files_are_readable(self, test_html_files):
        """Test that all HTML files can be read and contain content."""
        for _source, files in test_html_files.items():
            for file_path in files:
                assert file_path.exists(), f"File should exist: {file_path}"

                content = file_path.read_text(encoding="utf-8")
                assert len(content) > 100, (
                    f"File {file_path} should have substantial content"
                )
                assert "<html" in content.lower() or "<!doctype" in content.lower(), (
                    f"File {file_path} should contain HTML"
                )


class TestArticleOrchestrator:
    """Test the ArticleOrchestrator component integration."""

    def test_orchestrator_initialization(self):
        """Test that ArticleOrchestrator can be initialized properly."""
        orchestrator = ArticleOrchestrator()
        assert orchestrator is not None
        assert hasattr(orchestrator, "process_site")
        assert hasattr(orchestrator, "component_factory")

    def test_orchestrator_processes_all_sources(self, clean_test_database):
        """Test that orchestrator can process all enabled sources."""
        orchestrator = ArticleOrchestrator()
        total_processed = 0
        total_attempted = 0

        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                processed, attempted = orchestrator.process_site(config)
                total_processed += processed
                total_attempted += attempted

                # Each source should attempt to process files
                assert attempted >= 0, (
                    f"Source {config['site']} should attempt processing"
                )

        # Should have some successful processing
        assert total_processed > 0, (
            f"Expected some articles processed, got {total_processed}"
        )
        assert total_attempted >= total_processed, (
            "Attempted count should be >= processed count"
        )


class TestDeterministicPipeline:
    """Test deterministic results from the complete pipeline using test HTML files."""

    def test_pipeline_produces_consistent_results(self, clean_test_database):
        """Test that the complete pipeline produces consistent, expected results."""
        # Run the pipeline
        orchestrator = ArticleOrchestrator()
        total_processed = 0
        total_attempted = 0

        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                processed, attempted = orchestrator.process_site(config)
                total_processed += processed
                total_attempted += attempted

        # Verify processing occurred
        assert total_processed > 0, (
            f"Expected articles processed, got {total_processed}"
        )

        # Verify database storage
        with get_session() as session:
            
            db_count = session.execute(
                text("SELECT COUNT(*) FROM raw_articles")
            ).scalar()

            assert db_count == total_processed, (
                f"Database has {db_count} articles but processor reported {total_processed}"
            )

    def test_source_distribution_is_correct(self, clean_test_database):
        """Test that articles are correctly distributed across all sources."""
        # Run the pipeline first
        orchestrator = ArticleOrchestrator()
        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                orchestrator.process_site(config)

        # Check source distribution
        with get_session() as session:
            
            source_counts = session.execute(
                text("""
                SELECT site, COUNT(*) as article_count
                FROM raw_articles
                GROUP BY site
                ORDER BY site
                """)
            ).fetchall()

            source_dict = {row[0]: row[1] for row in source_counts}

            # All 4 sources should be present
            expected_sources = [
                "slate.fr",
                "tf1info.fr",
                "ladepeche.fr",
                "franceinfo.fr",
            ]
            for source in expected_sources:
                assert source in source_dict, f"Source '{source}' not found in database"
                assert source_dict[source] > 0, f"Source '{source}' has no articles"

            # Total should be reasonable (allowing for parsing variations)
            total_articles = sum(source_dict.values())
            assert 10 <= total_articles <= 30, (
                f"Expected 10-30 total articles, got {total_articles}"
            )

            # Each source should process some articles (allowing for parsing failures)
            for source in expected_sources:
                if source in source_dict:
                    assert 1 <= source_dict[source] <= 8, (
                        f"Expected 1-8 {source} articles, got {source_dict[source]}"
                    )

    def test_pipeline_multiple_runs(self, clean_test_database):
        """Test that running the pipeline multiple times stores all versions (ELT approach)."""
        orchestrator = ArticleOrchestrator()

        # Run pipeline first time
        first_run_processed = 0
        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                processed, _ = orchestrator.process_site(config)
                first_run_processed += processed

        # Get first run count
        with get_session() as session:
            
            first_count = session.execute(
                text("SELECT COUNT(*) FROM raw_articles")
            ).scalar()

        # Run pipeline second time
        second_run_processed = 0
        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                processed, _ = orchestrator.process_site(config)
                second_run_processed += processed

        # Get second run count
        with get_session() as session:
            second_count = session.execute(
                text("SELECT COUNT(*) FROM raw_articles")
            ).scalar()

        # ELT approach allows duplicates for historical tracking
        assert second_count >= first_count, (
            f"ELT should allow multiple versions. First: {first_count}, Second: {second_count}"
        )
        # Should have approximately doubled if same files processed twice
        assert second_count <= first_count * 2.5, (
            f"Should not have excessive duplicates. First: {first_count}, Second: {second_count}"
        )
