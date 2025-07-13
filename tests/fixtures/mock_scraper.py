"""
Mock scraper implementations for testing.

These mock scrapers simulate real scraper behavior without making
actual HTTP requests, allowing for reliable and fast testing.
"""

from typing import List
from unittest.mock import Mock


class MockScraper:
    """Mock URL scraper for testing."""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = Mock()
        
    def get_article_urls(self) -> List[str]:
        """Return mock article URLs."""
        return [
            "https://test.example.com/article-1",
            "https://test.example.com/article-2", 
            "https://test.example.com/article-3"
        ]


class MockFailingScraper:
    """Mock scraper that simulates failures."""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = Mock()
        
    def get_article_urls(self) -> List[str]:
        """Simulate scraper failure."""
        raise ConnectionError("Mock connection failure")


class MockSlowScraper:
    """Mock scraper that simulates slow responses."""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = Mock()
        
    def get_article_urls(self) -> List[str]:
        """Return URLs after simulated delay."""
        import time
        time.sleep(0.1)  # Short delay for testing
        return ["https://slow.example.com/article-1"]


class MockEmptyScraper:
    """Mock scraper that returns no URLs."""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = Mock()
        
    def get_article_urls(self) -> List[str]:
        """Return empty list."""
        return []