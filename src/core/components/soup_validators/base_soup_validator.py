"""
Pure ELT base soup validator for storing raw HTML to PostgreSQL.

Provides:
- HTTP session management for web scraping
- Database storage for raw HTML content
- Abstract contract for child soup validators
- Support for live and offline modes

Child soup validators implement domain-specific HTML validation logic.
"""

import time
from abc import ABC, abstractmethod
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from config.environment import DEBUG, TEST_MODE
from core.components.enhanced_web_mixin import EnhancedWebMixin
from database.models import RawArticle


class BaseSoupValidator(EnhancedWebMixin, ABC):
    """
    Abstract base soup validator for pure ELT raw data collection.

    Each child soup validator handles domain-specific HTML structure but stores
    only raw HTML content. All text processing happens downstream in dbt.

    Contract:
    - Child classes MUST implement: validate_and_extract(soup, url) -> RawArticle | None
    - Child classes handle domain-specific HTML validation
    - Base class provides HTTP session management and database storage
    """

    def __init__(self, site_domain: str, site_name: str, delay: float = 1.0):
        """
        Initialize soup validator with domain-specific configuration.

        Args:
            site_domain: Domain name for logging (e.g., "slate.fr")
            site_name: Human readable source name (e.g., "Slate.fr")
            delay: Request delay in seconds for rate limiting
        """
        from utils.structured_logger import Logger

        self.logger = Logger(self.__class__.__name__)
        self.site_domain = site_domain
        self.site_name = site_name
        self.delay = delay
        self.debug = DEBUG

    def get_soup_from_url(self, url: str, max_retries: int = 3) -> BeautifulSoup | None:
        """Fetch and parse HTML from URL with retry logic."""
        if TEST_MODE:
            self.logger.warning("URL fetch attempted in offline mode")
            return None

        for attempt in range(max_retries):
            try:
                response = self.get_with_session(url, timeout=15)
                time.sleep(self.delay)
                response.raise_for_status()

                if len(response.content) < 100:
                    self.logger.warning(f"Response content too short: {len(response.content)} bytes")
                    continue

                return self.parse_html_fast(response.content)

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"URL fetch failed (attempt {attempt + 1}): {str(e)}")

            if attempt < max_retries - 1:
                time.sleep(1 + attempt)

        self.logger.error(f"URL fetch failed after {max_retries} retries")
        return None

    def get_test_sources_from_directory(
        self, site_name: str
    ) -> list[tuple[BeautifulSoup | None, str]]:
        """Load test HTML files for offline mode testing."""
        current_file_dir = Path(__file__).parent
        project_root_dir = current_file_dir.parent.parent.parent.parent
        test_data_dir = project_root_dir / "src" / "test_data" / "raw_url_soup"

        # Map config source names to directory names
        source_dir_mapping = {
            "slate.fr": "Slate.fr",
            "franceinfo.fr": "FranceInfo.fr",
            "tf1info.fr": "TF1 Info",
            "ladepeche.fr": "Depeche.fr",
        }
        dir_name = source_dir_mapping.get(site_name, site_name)
        source_dir = test_data_dir / dir_name

        if not source_dir.exists():
            self.logger.warning(f"Test directory not found: {source_dir}")
            return []

        soup_sources = []
        try:
            from test_data.url_mapping import URL_MAPPING

            for file_path in source_dir.iterdir():
                if file_path.suffix in (".html", ".php"):
                    filename = file_path.name
                    original_url = URL_MAPPING.get(filename, f"test://{filename}")

                    with open(file_path, encoding="utf-8") as f:
                        soup = self.parse_html_fast(f.read().encode('utf-8'))
                        soup_sources.append((soup, original_url))

        except Exception as e:
            self.logger.error(f"Error reading test files: {str(e)}")

        return soup_sources

    @abstractmethod
    def validate_and_extract(self, soup: BeautifulSoup, url: str) -> RawArticle | None:
        """
        Validate domain-specific article content and create RawArticle.

        This is the ONLY method child soup validators need to implement.
        Each child handles the unique HTML structure of their domain.

        Args:
            soup: BeautifulSoup object of the article page HTML
            url: Article URL for the RawArticle record

        Returns:
            RawArticle with raw HTML content or None if validation fails

        Implementation Notes:
        - Store the ENTIRE HTML content in raw_html field
        - Set source to the domain name (e.g., "slate.fr")
        - Let dbt handle all text processing downstream
        - No title/content extraction here - pure raw storage
        """
        pass

    def store_to_database(self, raw_article: RawArticle) -> bool:
        """
        Store raw article using pure ELT approach.

        Args:
            raw_article: Complete raw HTML article data

        Returns:
            True if stored successfully, False otherwise
        """
        from database.database import store_raw_article

        return store_raw_article(raw_article)
