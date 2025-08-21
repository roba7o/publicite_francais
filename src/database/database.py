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

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config.environment import env_config
from database.models import RawArticle
from utils.structured_logger import Logger

logger = Logger(__name__)

# Simple module-level session factory
_SessionLocal = None


def initialize_database(echo: bool = None) -> bool:
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
        # Allow override of echo for migrations
        if echo is None:
            echo = env_config.is_debug_mode()
        engine = create_engine(database_url, echo=echo)

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
    Store raw article data with UUID-based uniqueness.

    Each article gets a unique UUID, allowing duplicate URLs to be stored
    as separate entries. This follows pure ELT approach where all scraped
    data is preserved and deduplication is handled downstream by dbt.

    Args:
        raw_article: Raw scraped data with auto-generated UUID

    Returns:
        True if stored successfully, False on error
    """
    schema_name = env_config.get_news_data_schema()

    try:
        with get_session() as session:
            # Insert article with UUID from model (allows duplicate URLs)
            session.execute(
                text(f"""
                    INSERT INTO {schema_name}.raw_articles
                    (id, url, raw_html, site, scraped_at, response_status, content_length,
                     extracted_text, title, author, date_published, language, summary, keywords, extraction_status)
                    VALUES (:id, :url, :raw_html, :site, :scraped_at, :response_status, :content_length,
                            :extracted_text, :title, :author, :date_published, :language, :summary, :keywords, :extraction_status)
                """),
                {
                    "id": raw_article.id,
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

            # Only log detailed storage info in debug mode
            if env_config.is_debug_mode():
                logger.info("Raw article stored successfully (pure ELT)")
            return True

    except Exception as e:
        # Exception automatically triggers rollback in context manager
        logger.error(f"Failed to store raw article: {str(e)}")
        return False
