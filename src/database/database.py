"""
Database connection and session management for French news scraper.

Provides:
1. Database connection setup using SQLAlchemy
2. Session factory for database operations
3. Context manager for safe transaction handling

The main purpose is to create the session factory, which is used by repository
classes to get database sessions with proper transaction handling.
"""

import time
from collections.abc import Generator
from contextlib import contextmanager

import sqlalchemy.exc
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import column, table

from config.environment import env_config
from database.models import RawArticle
from utils.structured_logger import Logger

logger = Logger(__name__)

# Simple module-level session factory and engine
_SessionLocal = None
_engine = None


def initialize_database(echo: bool = None) -> bool:
    """Initialize database connection with optimized connection pooling."""
    global _SessionLocal, _engine

    try:
        # builds connection string from config
        db_config = env_config.get_database_config()
        database_url = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

        # Allow override of echo for migrations
        if echo is None:
            echo = env_config.is_debug_mode()

        # Determine pool parameters based on environment
        is_test = env_config.is_test_mode()
        pool_size = 5 if is_test else 10
        max_overflow = 10 if is_test else 20

        # Create engine with optimized connection pooling
        _engine = create_engine(
            database_url,
            echo=echo,
            poolclass=QueuePool,
            pool_size=pool_size,  # Keep N connections in pool
            max_overflow=max_overflow,  # Allow N extra connections
            pool_timeout=30,  # Wait 30s for connection
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Verify connection health before use
            connect_args={
                "connect_timeout": 10,
                "application_name": "french_news_scraper",
            },
        )

        # create session factory bound to this engine
        _SessionLocal = sessionmaker(bind=_engine)

        # Tests the connection by creating a session and executing a simple query
        with get_session() as session:
            session.execute(text("SELECT 1"))

        logger.info(
            "Database initialized with connection pooling",
            extra_data={
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_timeout": 30,
                "pool_recycle": 3600,
            },
        )

        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False


def log_pool_status() -> None:
    """Log current database connection pool status for monitoring."""
    if _engine is None:
        logger.warning("Cannot log pool status: database not initialized")
        return

    try:
        if hasattr(_engine, "pool"):
            pool = _engine.pool
            status_data = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }

            # Add invalidated count if available
            if hasattr(pool, "invalidated"):
                status_data["invalidated"] = pool.invalidated()

            logger.info("Database connection pool status", extra_data=status_data)
        else:
            logger.warning("Pool status unavailable: engine has no pool attribute")
    except Exception as e:
        logger.error(f"Failed to log pool status: {str(e)}")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Provides a database session with connection pool exhaustion handling.

    This is a context manager that automatically handles:
    - Session creation with retry logic for pool exhaustion
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
    - Handles connection pool exhaustion with retry logic

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

    max_retries = 3
    retry_delay = 1.0
    session = None

    for attempt in range(max_retries):
        try:
            session = _SessionLocal()  # fresh session from the session factory
            break
        except sqlalchemy.exc.TimeoutError:
            if attempt == max_retries - 1:
                logger.error("Connection pool exhausted after max retries")
                raise
            logger.warning(
                f"Connection pool exhausted, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})"
            )
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
        except Exception:
            # For non-timeout errors, don't retry
            raise

    if session is None:
        raise RuntimeError("Failed to create database session")

    try:
        yield session  # hands session to the caller
        session.commit()  # saves
    except Exception:
        session.rollback()  # discards
        raise
    finally:
        session.close()  # always closes the session


def _execute_operation(operation: str, params: dict = None) -> bool:
    """Private helper to DRY up database operations."""
    try:
        with get_session() as session:
            session.execute(text(operation), params or {})
            return True
    except Exception as e:
        logger.error(f"Database operation failed: {str(e)}")
        return False


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
            # Ensure schema exists (simple, idempotent check)
            session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

            # Use table() for cleaner insert
            raw_articles_table = table(
                "raw_articles",
                column("id"),
                column("url"),
                column("raw_html"),
                column("site"),
                column("scraped_at"),
                column("response_status"),
                column("content_length"),
                column("extracted_text"),
                column("title"),
                column("author"),
                column("date_published"),
                column("language"),
                column("summary"),
                column("keywords"),
                column("extraction_status"),
                schema=schema_name,
            )

            stmt = raw_articles_table.insert().values(
                id=raw_article.id,
                url=raw_article.url,
                raw_html=raw_article.raw_html,
                site=raw_article.site,
                scraped_at=raw_article.scraped_at,
                response_status=raw_article.response_status,
                content_length=raw_article.content_length,
                extracted_text=raw_article.extracted_text,
                title=raw_article.title,
                author=raw_article.author,
                date_published=raw_article.date_published,
                language=raw_article.language,
                summary=raw_article.summary,
                keywords=raw_article.keywords,
                extraction_status=raw_article.extraction_status,
            )

            session.execute(stmt)

            if env_config.is_debug_mode():
                logger.info("Raw article stored successfully (pure ELT)")
            return True

    except Exception as e:
        # Exception automatically triggers rollback in context manager
        logger.error(f"Failed to store raw article: {str(e)}")
        return False
