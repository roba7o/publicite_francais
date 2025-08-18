"""
Abstract base scraper class defining the contract for all news site scrapers.

This module provides the BaseScraper abstract base class that defines the
interface all scrapers must implement. It ensures consistency across
different news site scrapers and makes it easier to add new sources.
"""

from abc import ABC, abstractmethod

import requests

from config.settings import DEBUG
from utils.structured_logger import get_structured_logger


class BaseScraper(ABC):
    """
    Abstract base class for news site scrapers.

    This class defines the contract that all scrapers must implement and
    provides common functionality like logging, headers, and debug mode.

    When creating a new scraper:
    1. Inherit from BaseScraper
    2. Set self.base_url in __init__
    3. Implement get_article_urls() method
    4. Optionally override default headers

    Example:
        class MyNewsScraper(BaseScraper):
            def __init__(self, debug=None):
                super().__init__(debug)
                self.base_url = "https://example.com"

            def get_article_urls(self) -> List[str]:
                # Implementation here
                return ["url1", "url2"]
    """

    def __init__(self, debug: bool | None = None) -> None:
        """
        Initialize the base scraper.

        Args:
            debug: Enable debug logging. If None, uses DEBUG from config.
        """
        self.logger = get_structured_logger(self.__class__.__name__)
        self.debug = debug if debug is not None else DEBUG
        self.base_url = ""  # Must be set by subclasses

        # Default headers - can be overridden by subclasses
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    @abstractmethod
    def get_article_urls(self) -> list[str]:
        """
        Extract article URLs from the news site.

        This method must be implemented by all subclasses to extract
        article URLs from their respective news sites.

        Returns:
            List of article URLs as strings

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement get_article_urls()")

    def _make_request(self, url: str, timeout: int = 10) -> requests.Response:
        """
        Make HTTP request with error handling.

        Provides consistent request handling across all scrapers with
        proper error logging and timeout management.

        Args:
            url: URL to request
            timeout: Request timeout in seconds

        Returns:
            Response object

        Raises:
            requests.RequestException: If request fails
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"Request failed for {url}",
                extra_data={
                    "url": url,
                    "error": str(e),
                    "scraper": self.__class__.__name__,
                },
            )
            raise

    def _log_results(self, urls: list[str]) -> None:
        """
        Log scraping results consistently.

        Args:
            urls: List of URLs found
        """
        if self.debug:
            self.logger.info(
                f"Found {len(urls)} article URLs",
                extra_data={
                    "scraper": self.__class__.__name__,
                    "url_count": len(urls),
                    "base_url": self.base_url,
                },
            )
            for i, url in enumerate(urls, 1):
                self.logger.debug(f"URL {i}: {url}")
