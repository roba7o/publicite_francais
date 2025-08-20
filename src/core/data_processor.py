"""
Data processor for database operations.

Handles all database interactions for article data by providing
a clean interface for storing and retrieving article information.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import text

from core.models import ArticleData


class DataProcessor:
    """Processor for article database operations."""

    def __init__(self):
        """Initialize processor with default dependencies."""
        from core.database import get_database_manager
        from utils.structured_logger import get_structured_logger

        self.db = get_database_manager()
        self.logger = get_structured_logger(__name__)
        # Dynamic schema evaluation to support test mode
        self.schema_name = self._get_current_schema()

    def _get_current_schema(self) -> str:
        """Get current schema name dynamically based on environment."""
        import os

        # Replicate settings.py logic but evaluate dynamically
        database_env = os.getenv("DATABASE_ENV") or (
            "test" if os.getenv("TEST_MODE", "false").lower() == "true" else "dev"
        )

        schema_config = {
            "test": os.getenv("NEWS_DATA_TEST_SCHEMA", "news_data_test"),
            "dev": os.getenv("NEWS_DATA_DEV_SCHEMA", "news_data_dev"),
            "prod": os.getenv("NEWS_DATA_PROD_SCHEMA", "news_data_prod"),
        }

        return schema_config[database_env]

    def _parse_article_date(self, date_str: str) -> str | None:
        """
        Parse article date string to valid YYYY-MM-DD format or None.

        Args:
            date_str: Date string from parser (could be "Unknown date", "2025-01-01", etc.)

        Returns:
            Valid date string in YYYY-MM-DD format or None for invalid dates
        """
        if not date_str or date_str.lower() in [
            "unknown date",
            "no date found",
            "unknown",
            "",
        ]:
            return None

        # If already in YYYY-MM-DD format, validate and return
        if len(date_str) == 10 and date_str.count("-") == 2:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                pass

        # Try to parse other common formats
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in date_formats:
            try:
                # Split on T and space to handle datetime strings
                clean_date = date_str.split("T")[0].split(" ")[0]
                dt = datetime.strptime(clean_date, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # If we can't parse it, log a warning and return None
        self.logger.warning(
            f"Could not parse article date: '{date_str}', storing as NULL"
        )
        return None

    def store_article(
        self, article_data: ArticleData, url: str, source_name: str
    ) -> bool:
        """
        Store raw article data directly to database.

        Simple storage: source_name + url + article data.
        Duplicate detection by URL only.

        Args:
            article_data: Parsed article content
            url: Article URL for duplicate detection
            source_name: Name of the source (e.g., "Slate.fr")

        Returns:
            True if stored successfully, False otherwise
        """
        # Database is always enabled (no CSV fallback)

        if not article_data or not article_data.full_text:
            self.logger.debug("No article data to store")
            return False

        try:
            # Parse article date to valid format or None
            parsed_article_date = self._parse_article_date(article_data.article_date)

            with self.db.get_session() as session:
                # Simple URL-only duplicate check
                existing_url = session.execute(
                    text(f"""
                    SELECT id FROM {self.schema_name}.articles
                    WHERE url = :url
                """),
                    {"url": url},
                ).fetchone()

                if existing_url:
                    self.logger.debug(
                        "Article already exists (duplicate URL)",
                        extra_data={"url": url, "existing_id": str(existing_url[0])},
                    )
                    return False

                # Insert raw article data - much simpler!
                article_id = uuid4()
                session.execute(
                    text(f"""
                    INSERT INTO {self.schema_name}.articles
                    (id, title, url, source_name, article_date, scraped_at, full_text, num_paragraphs)
                    VALUES (:id, :title, :url, :source_name, :article_date, :scraped_at, :full_text, :num_paragraphs)
                """),
                    {
                        "id": str(article_id),
                        "title": article_data.title,
                        "url": url,
                        "source_name": source_name,
                        "article_date": parsed_article_date,
                        "scraped_at": datetime.now(),
                        "full_text": article_data.full_text,
                        "num_paragraphs": article_data.num_paragraphs,
                    },
                )

                session.commit()  # Commit the transaction explicitly

                self.logger.info(
                    "Article stored successfully",
                    extra_data={
                        "article_id": str(article_id),
                        "source_name": source_name,
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
                "Failed to store article",
                extra_data={"url": url, "source_name": source_name, "error": str(e)},
                exc_info=True,
            )
            return False
