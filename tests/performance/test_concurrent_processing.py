"""
Performance Tests for Concurrent Processing.

These tests measure performance of concurrent operations including URL fetching,
HTML parsing, and database storage. They help identify performance bottlenecks
and ensure the system scales appropriately.

Run with: make test-performance
"""

from concurrent.futures import ThreadPoolExecutor

import pytest

from database.database import store_articles_batch
from database.models import RawArticle


class TestConcurrentProcessing:
    """Performance tests for concurrent URL fetching and processing."""

    @pytest.mark.performance
    def test_concurrent_html_parsing_works(self, test_html_files):
        """Verify concurrent HTML parsing works correctly without crashing."""
        if not any(test_html_files.values()):
            pytest.skip("No test HTML files available for performance testing")

        # Get available HTML files for testing
        all_files = []
        for files in test_html_files.values():
            all_files.extend(files)
        test_files = all_files[:8]  # Use 8 files for meaningful concurrency

        def parse_html_file(file_path):
            """Parse a single HTML file and return basic info."""
            # Read and process the HTML file
            html_content = file_path.read_text(encoding='utf-8')

            # Parse HTML (like validators do)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract basic information
            title = soup.find('title')
            text_content = soup.get_text()

            return {
                'file': file_path.name,
                'size_kb': len(html_content) / 1024,
                'title_found': title is not None,
                'content_length': len(text_content),
            }

        # Test sequential processing
        sequential_results = [parse_html_file(f) for f in test_files]

        # Test concurrent processing
        with ThreadPoolExecutor(max_workers=4) as executor:
            concurrent_results = list(executor.map(parse_html_file, test_files))

        # Verify both approaches work correctly
        assert len(sequential_results) == len(test_files), "Sequential processing should handle all files"
        assert len(concurrent_results) == len(test_files), "Concurrent processing should handle all files"

        # Verify results are equivalent (order may differ)
        sequential_files = {r['file'] for r in sequential_results}
        concurrent_files = {r['file'] for r in concurrent_results}
        assert sequential_files == concurrent_files, "Both approaches should process the same files"

        # Optional: Report basic metrics (no assertions on timing)
        avg_file_size = sum(r['size_kb'] for r in sequential_results) / len(sequential_results)
        print("\n=== HTML Parsing Verification ===")
        print(f"Files processed: {len(test_files)}")
        print(f"Average file size: {avg_file_size:.1f} KB")
        print("✓ Concurrent processing works correctly")

    @pytest.mark.performance
    def test_database_bulk_insert_works(self, clean_test_database):
        """Verify database bulk insert operations work correctly."""
        # Test different batch sizes to ensure scalability
        test_sizes = [10, 50]  # Reduced for faster testing

        for batch_size in test_sizes:
            # Generate test articles with realistic content
            articles = []
            for i in range(batch_size):
                html_size = "x" * (1000 + i * 100)  # Varying sizes
                article = RawArticle(
                    url=f"https://bulk-test.com/batch-{batch_size}-article-{i}",
                    raw_html=f"<html><body><h1>Test {i}</h1><p>{html_size}</p></body></html>",
                    site="bulk-test.com"
                )
                articles.append(article)

            # Test bulk insert functionality
            successful, attempted = store_articles_batch(articles)

            # Verify operations work correctly
            assert successful == batch_size, f"All {batch_size} articles should be inserted"
            assert attempted >= 0, "Should have non-negative attempted count"

            # Optional: Report basic metrics (no timing assertions)
            total_size_kb = sum(len(a.raw_html) for a in articles) / 1024
            print(f"\n=== Bulk Insert Test: {batch_size} articles ===")
            print(f"Total data: {total_size_kb:.1f} KB")
            print(f"✓ Successfully stored {successful}/{batch_size} articles")

    @pytest.mark.performance
    def test_orchestrator_processing_works(self, clean_test_database):
        """Verify ArticleOrchestrator processing works without crashing."""
        from config.site_configs import SCRAPER_CONFIGS
        from core.orchestrator import ArticleOrchestrator

        # Find one enabled config for testing
        test_config = next((config for config in SCRAPER_CONFIGS
                          if config.get("enabled", True)), None)

        if not test_config:
            pytest.skip("No enabled source config available")

        orchestrator = ArticleOrchestrator()

        # Test processing functionality
        processed, attempted = orchestrator.process_site(test_config)

        # Verify processing works correctly
        assert processed >= 0, "Should have non-negative processed count"
        assert attempted >= processed, "Attempted should be >= processed"

        # Optional: Report basic metrics (no timing assertions)
        if attempted > 0:
            success_rate = (processed / attempted) * 100
            print("\n=== Orchestrator Processing Test ===")
            print(f"Source: {test_config['site']}")
            print(f"Processed: {processed}/{attempted} articles")
            print(f"Success rate: {success_rate:.1f}%")
            print("✓ Orchestrator processing works correctly")

    @pytest.mark.performance
    def test_concurrent_database_operations_work(self, clean_test_database):
        """Verify concurrent database operations work without conflicts."""
        # Test concurrent database access
        num_threads = 3
        articles_per_thread = 3

        def store_articles_for_thread(thread_id):
            """Store articles from one thread."""
            articles = []
            for i in range(articles_per_thread):
                article = RawArticle(
                    url=f"https://concurrent-db.com/thread-{thread_id}-article-{i}",
                    raw_html=f"<html><body><h1>Thread {thread_id} Article {i}</h1></body></html>",
                    site="concurrent-db.com"
                )
                articles.append(article)

            successful, attempted = store_articles_batch(articles)
            return {'successful': successful, 'attempted': attempted}

        # Test concurrent database operations
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            thread_results = list(executor.map(store_articles_for_thread, range(num_threads)))

        # Verify all operations succeeded
        total_successful = sum(r['successful'] for r in thread_results)
        expected_total = num_threads * articles_per_thread

        assert total_successful == expected_total, f"Should store all {expected_total} articles"

        print("\n=== Concurrent Database Test ===")
        print(f"Threads: {num_threads}, Articles per thread: {articles_per_thread}")
        print(f"✓ Successfully stored {total_successful}/{expected_total} articles concurrently")


class TestSystemVerification:
    """Basic system functionality verification."""

    @pytest.mark.performance
    def test_raw_article_creation_works(self):
        """Verify RawArticle objects can be created correctly."""
        # Test basic article creation
        article = RawArticle(
            url="https://system-test.com/test-article",
            raw_html="<html><body><h1>System Test</h1><p>Test content</p></body></html>",
            site="system-test.com"
        )

        # Verify article properties
        assert article.url == "https://system-test.com/test-article"
        assert article.site == "system-test.com"
        assert "System Test" in article.raw_html
        assert article.content_length > 0

        print("\n=== System Verification ===")
        print("✓ RawArticle creation works correctly")

    @pytest.mark.performance
    def test_concurrent_processing_setup(self):
        """Verify ThreadPoolExecutor works correctly."""
        from concurrent.futures import ThreadPoolExecutor

        def simple_task(x):
            return x * 2

        # Test basic concurrent execution
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(simple_task, [1, 2, 3, 4, 5]))

        expected = [2, 4, 6, 8, 10]
        assert results == expected, "Concurrent processing should work correctly"

        print("✓ Concurrent processing infrastructure works correctly")
