"""
Performance Tests for Concurrent Processing.

These tests measure performance of concurrent operations including URL fetching,
HTML parsing, and database storage. They help identify performance bottlenecks
and ensure the system scales appropriately.

Run with: make test-performance
"""

import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from database.database import store_articles_batch
from database.models import RawArticle


class TestConcurrentProcessing:
    """Performance tests for concurrent URL fetching and processing."""

    @pytest.mark.performance
    def test_concurrent_html_parsing_performance(self, test_html_files):
        """Test performance of concurrent HTML parsing using existing test files."""
        if not any(test_html_files.values()):
            pytest.skip("No test HTML files available for performance testing")
        
        # Get all available HTML files
        all_files = []
        for files in test_html_files.values():
            all_files.extend(files)
        
        # Take first 8 files for testing (enough for concurrency)
        test_files = all_files[:8]
        
        def parse_html_file(file_path):
            """Parse a single HTML file and return processing time."""
            start_time = time.perf_counter()
            
            # Read and process the HTML file
            html_content = file_path.read_text(encoding='utf-8')
            
            # Simulate HTML parsing (using BeautifulSoup like the validators do)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract some basic information (similar to validators)
            title = soup.find('title')
            text_content = soup.get_text()
            
            processing_time = time.perf_counter() - start_time
            return {
                'file': file_path.name,
                'size_kb': len(html_content) / 1024,
                'title_found': title is not None,
                'content_length': len(text_content),
                'processing_time': processing_time
            }
        
        # Test sequential processing
        sequential_start = time.perf_counter()
        sequential_results = []
        for file_path in test_files:
            result = parse_html_file(file_path)
            sequential_results.append(result)
        sequential_time = time.perf_counter() - sequential_start
        
        # Test concurrent processing
        concurrent_start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=4) as executor:
            concurrent_results = list(executor.map(parse_html_file, test_files))
        concurrent_time = time.perf_counter() - concurrent_start
        
        # Performance assertions
        assert len(sequential_results) == len(test_files), "Sequential processing should handle all files"
        assert len(concurrent_results) == len(test_files), "Concurrent processing should handle all files"
        
        # Concurrent should be faster for multiple files (with some tolerance)
        if len(test_files) >= 4:
            speedup_ratio = sequential_time / concurrent_time
            assert speedup_ratio > 1.2, f"Concurrent processing should be faster. Speedup: {speedup_ratio:.2f}x"
        
        # Report performance metrics
        avg_file_size = sum(r['size_kb'] for r in sequential_results) / len(sequential_results)
        print(f"\n=== HTML Parsing Performance ===")
        print(f"Files processed: {len(test_files)}")
        print(f"Average file size: {avg_file_size:.1f} KB")
        print(f"Sequential time: {sequential_time:.3f}s")
        print(f"Concurrent time: {concurrent_time:.3f}s")
        print(f"Speedup: {sequential_time/concurrent_time:.2f}x")

    @pytest.mark.performance
    def test_database_bulk_insert_performance(self, clean_test_database):
        """Test performance of database bulk insert operations."""
        # Create test articles of varying sizes
        test_sizes = [10, 50, 100]
        
        for batch_size in test_sizes:
            # Generate test articles
            articles = []
            for i in range(batch_size):
                # Create articles with realistic content sizes
                html_size = "x" * (1000 + i * 100)  # Varying sizes
                article = RawArticle(
                    url=f"https://performance-test.com/batch-{batch_size}-article-{i}",
                    raw_html=f"<html><body><h1>Performance Test {i}</h1><p>{html_size}</p></body></html>",
                    site="performance-test.com"
                )
                articles.append(article)
            
            # Measure bulk insert performance
            start_time = time.perf_counter()
            successful, attempted = store_articles_batch(articles)
            insert_time = time.perf_counter() - start_time
            
            # Performance assertions
            assert successful == batch_size, f"All {batch_size} articles should be inserted"
            assert attempted >= 0, f"Should have non-negative attempted count"
            
            # Performance should be reasonable (< 100ms per article for bulk operations)
            time_per_article = insert_time / batch_size
            assert time_per_article < 0.1, f"Bulk insert too slow: {time_per_article:.3f}s per article"
            
            # Report performance
            total_size_kb = sum(len(a.raw_html) for a in articles) / 1024
            print(f"\n=== Database Bulk Insert Performance ===")
            print(f"Batch size: {batch_size} articles")
            print(f"Total data: {total_size_kb:.1f} KB")
            print(f"Insert time: {insert_time:.3f}s")
            print(f"Time per article: {time_per_article*1000:.1f}ms")
            print(f"Throughput: {batch_size/insert_time:.1f} articles/second")

    @pytest.mark.performance
    def test_orchestrator_processing_performance(self, clean_test_database):
        """Test performance of the complete ArticleOrchestrator processing."""
        from core.orchestrator import ArticleOrchestrator
        from config.site_configs import SCRAPER_CONFIGS
        
        # Find one enabled config for testing
        test_config = None
        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                test_config = config
                break
        
        if not test_config:
            pytest.skip("No enabled source config available for performance testing")
        
        orchestrator = ArticleOrchestrator()
        
        # Measure processing performance
        start_time = time.perf_counter()
        processed, attempted = orchestrator.process_site(test_config)
        processing_time = time.perf_counter() - start_time
        
        if attempted > 0:  # Only test if there was content to process
            # Performance assertions
            assert processed >= 0, "Should have non-negative processed count"
            assert attempted >= processed, "Attempted should be >= processed"
            
            # Processing should be reasonably fast
            time_per_attempt = processing_time / attempted
            assert time_per_attempt < 2.0, f"Processing too slow: {time_per_attempt:.3f}s per article"
            
            # Report performance
            success_rate = (processed / attempted) * 100 if attempted > 0 else 0
            print(f"\n=== Orchestrator Processing Performance ===")
            print(f"Source: {test_config['site']}")
            print(f"Processed: {processed}/{attempted} articles")
            print(f"Success rate: {success_rate:.1f}%")
            print(f"Total time: {processing_time:.3f}s")
            print(f"Time per attempt: {time_per_attempt*1000:.1f}ms")
            if processed > 0:
                print(f"Time per success: {(processing_time/processed)*1000:.1f}ms")

    @pytest.mark.performance  
    def test_concurrent_database_operations(self, clean_test_database):
        """Test performance of concurrent database operations."""
        # Create articles for concurrent testing
        num_threads = 4
        articles_per_thread = 5
        
        def store_articles_batch_wrapper(thread_id):
            """Store a batch of articles for one thread."""
            articles = []
            for i in range(articles_per_thread):
                article = RawArticle(
                    url=f"https://concurrent-test.com/thread-{thread_id}-article-{i}",
                    raw_html=f"<html><body><h1>Thread {thread_id} Article {i}</h1></body></html>",
                    site="concurrent-test.com"
                )
                articles.append(article)
            
            start_time = time.perf_counter()
            successful, attempted = store_articles_batch(articles)
            thread_time = time.perf_counter() - start_time
            
            return {
                'thread_id': thread_id,
                'successful': successful,
                'attempted': attempted,
                'time': thread_time
            }
        
        # Test concurrent database operations
        start_time = time.perf_counter()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            thread_results = list(executor.map(store_articles_batch_wrapper, range(num_threads)))
        total_time = time.perf_counter() - start_time
        
        # Verify results
        total_successful = sum(r['successful'] for r in thread_results)
        total_attempted = sum(r['attempted'] for r in thread_results)
        expected_total = num_threads * articles_per_thread
        
        assert total_successful == expected_total, f"Should have stored all {expected_total} articles"
        assert total_attempted >= 0, f"Should have non-negative attempted count"
        
        # Performance metrics
        avg_thread_time = sum(r['time'] for r in thread_results) / num_threads
        
        print(f"\n=== Concurrent Database Operations Performance ===")
        print(f"Threads: {num_threads}")
        print(f"Articles per thread: {articles_per_thread}")
        print(f"Total articles: {expected_total}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Average thread time: {avg_thread_time:.3f}s")
        print(f"Throughput: {expected_total/total_time:.1f} articles/second")
        print(f"Concurrency efficiency: {avg_thread_time/total_time:.1f}")


class TestPerformanceUtilities:
    """Utility tests for performance measurement infrastructure."""

    @pytest.mark.performance
    def test_timing_accuracy(self):
        """Test that timing measurements are accurate."""
        # Test short timing
        start = time.perf_counter()
        time.sleep(0.01)  # 10ms
        duration = time.perf_counter() - start
        
        # Should be approximately 10ms (with some tolerance)
        assert 0.008 < duration < 0.015, f"Timing measurement inaccurate: {duration:.3f}s"
        
        # Test longer timing
        start = time.perf_counter()
        time.sleep(0.05)  # 50ms
        duration = time.perf_counter() - start
        
        assert 0.045 < duration < 0.065, f"Longer timing measurement inaccurate: {duration:.3f}s"

    @pytest.mark.performance
    def test_memory_usage_awareness(self):
        """Test awareness of memory usage during operations."""
        import sys
        
        # Baseline memory
        baseline_objects = len(sys.modules)
        
        # Create some objects
        large_list = [RawArticle(
            url=f"https://memory-test.com/article-{i}",
            raw_html="<html>" + "x" * 1000 + "</html>",
            site="memory-test.com"
        ) for i in range(100)]
        
        # Check that objects were created
        assert len(large_list) == 100, "Should create 100 test objects"
        
        # Clean up
        del large_list
        
        # This test mainly serves as documentation that we're aware of memory considerations
        print(f"\nBaseline modules: {baseline_objects}")
        print("Memory usage awareness test completed")