"""
Database-focused base parser that stores raw article data to PostgreSQL.

This is the database equivalent of BaseParser that:
- Keeps all the HTTP session management and parsing infrastructure
- Replaces CSV/text processing with direct database storage
- Maintains the same interface for child parsers
- Stores only raw data (title, full_text, url, date)

Child parsers only need to implement parse_article() - same as BaseParser.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import DATABASE_ENABLED, DEBUG, OFFLINE
from database import get_database_manager
from models import ArticleData
from utils.structured_logger import get_structured_logger


class DatabaseBaseParser(ABC):
    """
    Database-focused base parser for raw data collection.

    This mirrors BaseParser but stores data to PostgreSQL instead of CSV.
    Child parsers implement the same parse_article(soup) -> ArticleData interface.

    Features:
    - Shared HTTP session with connection pooling (same as BaseParser)
    - Direct PostgreSQL storage instead of CSV output
    - Duplicate detection based on source_id + url
    - No text processing - stores raw article content
    - Support for both live web scraping and offline testing

    Child classes must implement:
        parse_article(soup): Extract title, full_text, date from HTML
    """

    # Shared session for HTTP requests (same as BaseParser)
    _session = None

    def __init__(self, site_domain: str, source_id: str, delay: float = 1.0):
        """
        Initialize database parser.

        Args:
            site_domain: Domain name for logging purposes
            source_id: UUID of the news source in database
            delay: Request delay for rate limiting
        """
        self.logger = get_structured_logger(self.__class__.__name__)
        self.site_domain = site_domain
        self.source_id = source_id  # UUID from news_sources table
        self.delay = delay
        self.debug = DEBUG

        # Initialize database connection if enabled
        if DATABASE_ENABLED:
            self.db = get_database_manager()

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

    def get_soup_from_url(
        self, url: str, max_retries: int = 3
    ) -> Optional[BeautifulSoup]:
        """
        Fetch and parse HTML (same logic as BaseParser).
        """
        if OFFLINE:
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
    ) -> List[Tuple[Optional[BeautifulSoup], str]]:
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

        soup_sources: List[Tuple[Optional[BeautifulSoup], str]] = []
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
    def parse_article(self, soup: BeautifulSoup) -> Optional[ArticleData]:
        """
        Extract raw article data from HTML.

        Child parsers must implement this to extract:
        - title: Article headline
        - full_text: Complete article content
        - article_date: Publication date (optional)
        - num_paragraphs: Paragraph count

        NO text processing - just extract the raw content.
        Text analysis will be done in dbt/SQL.

        Args:
            soup: BeautifulSoup object of article HTML

        Returns:
            ArticleData with raw content or None if parsing fails
        """
        pass

    def to_database(self, article_data: ArticleData, url: str) -> bool:
        """
        Store raw article data directly to database.

        This replaces BaseParser's to_csv() method with database storage.
        NO text processing, NO word frequencies - just raw data.

        Args:
            article_data: Parsed article content
            url: Article URL for duplicate detection

        Returns:
            True if stored successfully, False otherwise
        """
        if not DATABASE_ENABLED:
            self.logger.warning("Database not enabled - article not stored")
            return False

        if not article_data or not article_data.full_text:
            self.logger.debug("No article data to store")
            return False

        try:
            with self.db.get_session() as session:
                from sqlalchemy import text

                # Check for duplicate
                existing = session.execute(
                    text("""
                    SELECT id FROM news_data.articles
                    WHERE source_id = :source_id AND url = :url
                """),
                    {"source_id": self.source_id, "url": url},
                ).fetchone()

                if existing:
                    self.logger.debug(
                        "Article already exists",
                        extra_data={"url": url, "existing_id": str(existing[0])},
                    )
                    return False

                # Insert raw article data
                article_id = uuid4()
                session.execute(
                    text("""
                    INSERT INTO news_data.articles
                    (id, source_id, title, url, article_date, scraped_at, full_text, num_paragraphs)
                    VALUES (:id, :source_id, :title, :url, :article_date, :scraped_at, :full_text, :num_paragraphs)
                """),
                    {
                        "id": str(article_id),
                        "source_id": self.source_id,
                        "title": article_data.title,
                        "url": url,
                        "article_date": article_data.article_date,
                        "scraped_at": datetime.now(),
                        "full_text": article_data.full_text,
                        "num_paragraphs": article_data.num_paragraphs,
                    },
                )

                self.logger.info(
                    "Raw article stored successfully",
                    extra_data={
                        "article_id": str(article_id),
                        "title": article_data.title[:50] + "..."
                        if len(article_data.title) > 50
                        else article_data.title,
                        "url": url,
                        "text_length": len(article_data.full_text),
                    },
                )
                return True

        except Exception as e:
            self.logger.error(
                "Failed to store raw article",
                extra_data={"url": url, "error": str(e)},
                exc_info=True,
            )
            return False
