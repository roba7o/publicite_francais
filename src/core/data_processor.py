"""
Data processor for database operations.

Handles all database interactions for article data by providing
a clean interface for storing and retrieving article information.
"""

from uuid import uuid4

from sqlalchemy import text

from core.models import RawArticle


class DataProcessor:
    """Processor for article database operations."""

    def __init__(self):
        """Initialize processor with default dependencies."""
        from core.database import get_session
        from utils.structured_logger import get_structured_logger

        self.get_session = get_session
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

    def store_raw_article(self, raw_article: RawArticle) -> bool:
        """
        Store raw article data using ELT approach.

        Stores unprocessed HTML for later processing by dbt.

        Args:
            raw_article: Raw scraped data (URL, HTML, source)

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            with self.get_session() as session:
                # Check for duplicates by URL
                existing = session.execute(
                    text(
                        f"SELECT id FROM {self.schema_name}.raw_articles WHERE url = :url"
                    ),
                    {"url": raw_article.url},
                ).fetchone()

                if existing:
                    self.logger.debug(
                        "Raw article already exists, skipping",
                        extra_data={
                            "url": raw_article.url,
                            "source": raw_article.source,
                        },
                    )
                    return False

                # Insert new raw article
                session.execute(
                    text(f"""
                        INSERT INTO {self.schema_name}.raw_articles
                        (id, url, raw_html, source, scraped_at, response_status, content_length)
                        VALUES (:id, :url, :raw_html, :source, :scraped_at, :response_status, :content_length)
                    """),
                    {
                        "id": str(uuid4()),
                        "url": raw_article.url,
                        "raw_html": raw_article.raw_html,
                        "source": raw_article.source,
                        "scraped_at": raw_article.scraped_at,
                        "response_status": raw_article.response_status,
                        "content_length": raw_article.content_length,
                    },
                )
                session.commit()

                self.logger.info(
                    "Raw article stored successfully",
                    extra_data={
                        "url": raw_article.url,
                        "source": raw_article.source,
                        "content_length": raw_article.content_length,
                        "approach": "ELT",
                    },
                )
                return True

        except Exception as e:
            self.logger.error(
                f"Failed to store raw article: {str(e)}",
                extra_data={
                    "url": raw_article.url,
                    "source": raw_article.source,
                    "error": str(e),
                },
                exc_info=True,
            )
            return False
