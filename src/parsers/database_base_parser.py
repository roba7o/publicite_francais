"""
Database-focused base parser that stores raw article data to PostgreSQL.

This parser provides:
- HTTP session management and parsing infrastructure
- Direct database storage for articles
- Maintains the same interface for child parsers
- Stores only raw data (title, full_text, url, date)

Child parsers only need to implement parse_article().
"""

import os
import time
from abc import ABC, abstractmethod
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import DEBUG
from core.models import RawArticle


class DatabaseBaseParser(ABC):
    """
    Database-focused base parser for raw data collection.

    Child parsers implement the parse_article(soup) -> RawArticle interface.

    Features:
    - Shared HTTP session with connection pooling
    - Direct PostgreSQL storage
    - Duplicate detection based on source_id + url
    - No text processing - stores raw article content
    - Support for both live web scraping and offline testing

    Child classes must implement:
        parse_article(soup): Return raw HTML data for ELT processing
    """

    # Shared session for HTTP requests
    _session = None

    def __init__(self, site_domain: str, source_name: str, delay: float = 1.0):
        """
        Initialize database parser.

        Args:
            site_domain: Domain name for logging purposes
            source_name: Name of the source (e.g., "Slate.fr")
            delay: Request delay for rate limiting
        """
        from utils.structured_logger import get_structured_logger

        self.logger = get_structured_logger(self.__class__.__name__)
        self.site_domain = site_domain
        self.source_name = source_name  # Simple source name like "Slate.fr"
        self.delay = delay
        self.debug = DEBUG

    @classmethod
    def get_session(cls):
        """Get or create shared HTTP session (same as BaseParser)."""
        if cls._session is None:
            cls._session = requests.Session()

            # Same retry strategy as BaseParser
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )

            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,
                pool_maxsize=20,
                pool_block=False,
            )

            cls._session.mount("http://", adapter)
            cls._session.mount("https://", adapter)

            # Standard headers (same as BaseParser)
            cls._session.headers.update(
                {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
                    )
                }
            )

        return cls._session

    def get_soup_from_url(self, url: str, max_retries: int = 3) -> BeautifulSoup | None:
        """
        Fetch and parse HTML (same logic as BaseParser).
        """
        if os.getenv("TEST_MODE", "false").lower() == "true":
            self.logger.warning(
                "URL fetch attempted in offline mode",
                extra_data={"url": url, "mode": "offline"},
            )
            return None

        for attempt in range(max_retries):
            try:
                session = self.get_session()
                response = session.get(url, timeout=15)
                time.sleep(self.delay)
                response.raise_for_status()

                if len(response.content) < 100:
                    self.logger.warning(
                        "Response content too short",
                        extra_data={
                            "url": url,
                            "content_length": len(response.content),
                        },
                    )
                    continue

                return BeautifulSoup(response.content, "html.parser")

            except requests.exceptions.RequestException as e:
                self.logger.warning(
                    "URL fetch failed",
                    extra_data={"url": url, "attempt": attempt + 1, "error": str(e)},
                )

            if attempt < max_retries - 1:
                time.sleep(1 + attempt)

        self.logger.error(
            "URL fetch failed after all retries",
            extra_data={"url": url, "max_retries": max_retries},
        )
        return None

    def get_test_sources_from_directory(
        self, source_name: str
    ) -> list[tuple[BeautifulSoup | None, str]]:
        """Load test files for offline mode (same as BaseParser)."""
        current_file_dir = Path(__file__).parent
        project_root_dir = current_file_dir.parent.parent
        test_data_dir = project_root_dir / "src" / "test_data" / "raw_url_soup"
        source_dir = test_data_dir / source_name

        if not source_dir.exists():
            self.logger.warning(
                "Test directory not found",
                extra_data={
                    "source_name": source_name,
                    "directory_path": str(source_dir),
                },
            )
            return []

        soup_sources: list[tuple[BeautifulSoup | None, str]] = []
        try:
            from test_data.url_mapping import URL_MAPPING

            for file_path in source_dir.iterdir():
                if file_path.suffix in (".html", ".php"):
                    filename = file_path.name
                    original_url = URL_MAPPING.get(filename, f"test://{filename}")

                    with open(file_path, encoding="utf-8") as f:
                        soup = BeautifulSoup(f.read(), "html.parser")
                        soup_sources.append((soup, original_url))

        except Exception as e:
            self.logger.error(
                "Error reading test files",
                extra_data={"source_name": source_name, "error": str(e)},
                exc_info=True,
            )

        return soup_sources

    @abstractmethod
    def parse_article(self, soup: BeautifulSoup, url: str) -> RawArticle | None:
        """
        Create raw article data for ELT processing.

        Child parsers must implement this to return:
        - RawArticle with complete HTML content
        - All processing will be done by dbt

        Args:
            soup: BeautifulSoup object of article HTML
            url: Article URL for the RawArticle

        Returns:
            RawArticle with raw HTML or None if parsing fails
        """
        pass

    def to_database(self, raw_article: RawArticle, url: str) -> bool:
        """
        Store raw article data using ELT approach.

        Args:
            raw_article: Raw HTML data
            url: Article URL for duplicate detection

        Returns:
            True if stored successfully, False otherwise
        """
        from utils.database_operations import store_raw_article

        return store_raw_article(raw_article)
