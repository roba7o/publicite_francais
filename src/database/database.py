"""
Database connection and session management for French news scraper.

Provides:
1. Database connection setup using SQLAlchemy
2. Session factory for database operations
3. Context manager for safe transaction handling

The main purpose is to create the session factory, which is used by repository
classes to get database sessions with proper transaction handling.
"""

from collections.abc import Generator
from contextlib import contextmanager
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config.environment import env_config
from database.models import RawArticle
from utils.structured_logger import get_structured_logger

logger = get_structured_logger(__name__)

# Simple module-level session factory
_SessionLocal = None


def initialize_database() -> bool:
    """Initialize database connection with simple session factory."""
    global _SessionLocal

    try:
        # builds connection string from config
        db_config = env_config.get_database_config()
        database_url = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        # this engine manages connections to database
        engine = create_engine(database_url, echo=env_config.is_debug_mode())

        # create session factory bound to this engine
        _SessionLocal = sessionmaker(bind=engine)

        # Tests the connection by creating a session and executing a simple query
        with get_session() as session:
            session.execute(text("SELECT 1"))

        return True

    except Exception:
        return False


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Provides a database session for safe transaction handling.

    This is a context manager that automatically handles:
    - Session creation
    - Transaction commits (on success)
    - Transaction rollbacks (on errors)
    - Session cleanup (always)

    Usage:
        with get_session() as session:
            # Use the session for database operations
            session.execute(text("SELECT 1"))
            # Session will auto-commit if no errors occur

    Features:
    - Creates a new database session when entering the 'with' block
    - Yields the session for your database operations
    - Commits all changes if the block completes successfully
    - Rolls back all changes if any exceptions occur
    - Always closes the session properly, even during failures

    Example (successful operation):
        with get_session() as s:
            s.execute(text("UPDATE users SET active = True"))
            # Auto-committed when block exits

    Example (failed operation):
        with get_session() as s:
            s.execute(text("INVALID SQL"))  # Raises exception
            # Auto-rolled back, then exception propagates
    """
    if _SessionLocal is None:
        raise RuntimeError(
            "Database not initialized. Call initialize_database() first."
        )

    session = _SessionLocal()  # fresh session from the session factory
    try:
        yield session  # hands session to the caller
        session.commit()  # saves
    except Exception:
        session.rollback()  # discards
        raise
    finally:
        session.close()  # always closes the session


def store_raw_article(raw_article: RawArticle) -> bool:
    """
    Store raw article data using pure ELT approach with proper ACID compliance.

    Pure ELT: Stores ALL scraped data including duplicates.
    Deduplication is handled downstream by dbt for better separation of concerns.

    Uses the clean session management which handles:
    - Automatic commits on success
    - Automatic rollbacks on failure
    - Proper session cleanup

    Args:
        raw_article: Raw scraped data (URL, HTML, site)

    Returns:
        True if stored successfully, False otherwise
    """
    schema_name = env_config.get_news_data_schema()

    try:
        with get_session() as session:
            # Pure ELT: Insert ALL data, let dbt handle deduplication
            session.execute(
                text(f"""
                    INSERT INTO {schema_name}.raw_articles
                    (id, url, raw_html, site, scraped_at, response_status, content_length,
                     extracted_text, title, author, date_published, language, summary, keywords, extraction_status)
                    VALUES (:id, :url, :raw_html, :site, :scraped_at, :response_status, :content_length,
                            :extracted_text, :title, :author, :date_published, :language, :summary, :keywords, :extraction_status)
                """),
                {
                    "id": str(uuid4()),
                    "url": raw_article.url,
                    "raw_html": raw_article.raw_html,
                    "site": raw_article.site,
                    "scraped_at": raw_article.scraped_at,
                    "response_status": raw_article.response_status,
                    "content_length": raw_article.content_length,
                    "extracted_text": raw_article.extracted_text,
                    "title": raw_article.title,
                    "author": raw_article.author,
                    "date_published": raw_article.date_published,
                    "language": raw_article.language,
                    "summary": raw_article.summary,
                    "keywords": raw_article.keywords,
                    "extraction_status": raw_article.extraction_status,
                },
            )

            logger.info(
                "Raw article stored successfully (pure ELT)",
                extra_data={
                    "url": raw_article.url,
                    "site": raw_article.site,
                    "content_length": raw_article.content_length,
                    "approach": "pure_ELT",
                    "deduplication": "handled_by_dbt",
                },
            )
            return True

    except Exception as e:
        # Exception automatically triggers rollback in context manager
        logger.error(
            f"Failed to store raw article: {str(e)}",
            extra_data={
                "url": raw_article.url,
                "site": raw_article.site,
                "error": str(e),
            },
            exc_info=True,
        )
        return False
