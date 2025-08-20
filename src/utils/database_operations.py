"""
Direct database operations with proper ACID compliance.

Simple functions for database operations using the clean session management
from database.py with proper transaction handling.
"""

from uuid import uuid4

from sqlalchemy import text

from core.database import get_session
from core.models import RawArticle
from utils.schema import get_current_schema
from utils.structured_logger import get_structured_logger

logger = get_structured_logger(__name__)


def store_raw_article(raw_article: RawArticle) -> bool:
    """
    Store raw article data using ELT approach with proper ACID compliance.

    Uses the clean session management from database.py which handles:
    - Automatic commits on success
    - Automatic rollbacks on failure
    - Proper session cleanup

    Args:
        raw_article: Raw scraped data (URL, HTML, source)

    Returns:
        True if stored successfully, False otherwise
    """
    schema_name = get_current_schema()

    try:
        with get_session() as session:
            # Check for duplicates by URL
            existing = session.execute(
                text(f"SELECT id FROM {schema_name}.raw_articles WHERE url = :url"),
                {"url": raw_article.url},
            ).fetchone()

            if existing:
                logger.debug(
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
                    INSERT INTO {schema_name}.raw_articles
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
            # NOTE: No manual session.commit() here!
            # The context manager in database.py handles commit/rollback properly

            logger.info(
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
        # Exception automatically triggers rollback in database.py context manager
        logger.error(
            f"Failed to store raw article: {str(e)}",
            extra_data={
                "url": raw_article.url,
                "source": raw_article.source,
                "error": str(e),
            },
            exc_info=True,
        )
        return False
