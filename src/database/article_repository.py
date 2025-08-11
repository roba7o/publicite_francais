"""
Article repository for database operations.

Separates database concerns from business logic by providing
a clean interface for article-related database operations.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import text

from config.settings import DATABASE_ENABLED, NEWS_DATA_SCHEMA
from models import ArticleData


class ArticleRepository:
    """Repository for article database operations."""
    
    def __init__(self):
        """Initialize repository with default dependencies."""
        from database import get_database_manager
        from utils.structured_logger import get_structured_logger
        
        self.db = get_database_manager()
        self.logger = get_structured_logger(__name__)
        self.schema_name = NEWS_DATA_SCHEMA
    
    def get_source_id(self, source_name: str) -> Optional[str]:
        """Get source ID from database by name."""
        try:
            with self.db.get_session() as session:
                result = session.execute(
                    text(f"""
                    SELECT id FROM {self.schema_name}.news_sources
                    WHERE name = :name
                """),
                    {"name": source_name},
                )
                
                row = result.fetchone()
                return str(row[0]) if row else None
                
        except Exception as e:
            self.logger.error(
                "Failed to get source ID",
                extra_data={"source_name": source_name, "error": str(e)}
            )
            return None

    def _parse_article_date(self, date_str: str) -> Optional[str]:
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

    def store_article(self, article_data: ArticleData, url: str, source_id: str) -> bool:
        """
        Store raw article data directly to database.

        NO text processing, NO word frequencies - just raw data.

        Args:
            article_data: Parsed article content
            url: Article URL for duplicate detection
            source_id: UUID of the news source

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
            # Parse article date to valid format or None
            parsed_article_date = self._parse_article_date(article_data.article_date)

            with self.db.get_session() as session:
                # Check for duplicates on both unique constraints
                existing_url = session.execute(
                    text(f"""
                    SELECT id FROM {self.schema_name}.articles
                    WHERE source_id = :source_id AND url = :url
                """),
                    {"source_id": source_id, "url": url},
                ).fetchone()

                if existing_url:
                    self.logger.debug(
                        "Article already exists (duplicate URL)",
                        extra_data={"url": url, "existing_id": str(existing_url[0])},
                    )
                    return False

                # Check for duplicate title+date combination
                if parsed_article_date:  # Only check if we have a valid date
                    existing_title_date = session.execute(
                        text(f"""
                        SELECT id FROM {self.schema_name}.articles
                        WHERE source_id = :source_id AND title = :title AND article_date = :article_date
                    """),
                        {
                            "source_id": source_id,
                            "title": article_data.title,
                            "article_date": parsed_article_date,
                        },
                    ).fetchone()

                    if existing_title_date:
                        self.logger.debug(
                            "Article already exists (duplicate title+date)",
                            extra_data={
                                "title": article_data.title[:50] + "..."
                                if len(article_data.title) > 50
                                else article_data.title,
                                "article_date": parsed_article_date,
                                "existing_id": str(existing_title_date[0]),
                            },
                        )
                        return False

                # Insert raw article data (duplicates already handled above)
                article_id = uuid4()
                session.execute(
                    text(f"""
                    INSERT INTO {self.schema_name}.articles
                    (id, source_id, title, url, article_date, scraped_at, full_text, num_paragraphs)
                    VALUES (:id, :source_id, :title, :url, :article_date, :scraped_at, :full_text, :num_paragraphs)
                """),
                    {
                        "id": str(article_id),
                        "source_id": source_id,
                        "title": article_data.title,
                        "url": url,
                        "article_date": parsed_article_date,  # Now properly parsed or NULL
                        "scraped_at": datetime.now(),  # When we scraped it (current timestamp)
                        "full_text": article_data.full_text,
                        "num_paragraphs": article_data.num_paragraphs,
                    },
                )

                session.commit()  # Commit the transaction explicitly

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