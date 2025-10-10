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
from collections.abc import Generator  # for type hinting
from contextlib import contextmanager  # for context manager decorator

import sqlalchemy.exc
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    Session,  # type hint for DB sessions
    sessionmaker,  # factory to create new sessions
)
from sqlalchemy.pool import QueuePool  # for optimized connection pooling
from sqlalchemy.sql import column, table  # for dynamic table references

from config.environment import DATABASE_CONFIG, DEBUG, ENVIRONMENT
from database.models import RawArticle, WordFact
from utils.structured_logger import get_logger

logger = get_logger(__name__)

# Simple module-level session factory and engine
_SessionLocal: sessionmaker | None = None
_engine: Engine | None = None


def initialize_database(echo: bool | None = None) -> bool:
    """Initialize database connection with optimized connection pooling."""
    global _SessionLocal, _engine

    if _engine is not None:
        if DEBUG:
            logger.info("Database already initialized, skipping re-initialization")
        return True  # Already initialized

    try:
        # builds connection string from config
        db_config = DATABASE_CONFIG
        database_url = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

        # Allow override of echo for migrations
        if echo is None:
            echo = DEBUG

        # Determine pool parameters based on environment
        is_test = ENVIRONMENT == "test"
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

        logger.info("Database initialized with connection pooling")

        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False


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
            session = (
                _SessionLocal()
            )  # fresh session from the session factory (calling the factory)
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
        yield session  # hands session to the caller ('with' block)
        session.commit()  # attempts to commit if no exceptions
    except Exception:
        session.rollback()  # discards uncommitted changes on error
        raise
    finally:
        session.close()  # always closes the session (cleanup, returns connection to pool)


def store_article(article: RawArticle) -> bool:
    """
    Store raw article data in clean single schema.

    Args:
        article: Raw scraped data with auto-generated UUID

    Returns:
        True if stored successfully, False on error
    """
    try:
        with get_session() as session:
            # Use table() for cleaner insert - public schema only
            raw_articles_table = table(
                "raw_articles",
                column("id"),
                column("url"),
                column("raw_html"),
                column("site"),
                column("scraped_at"),
                column("response_status"),
                column("content_length"),
            )

            stmt = raw_articles_table.insert().values(
                id=article.id,
                url=article.url,
                raw_html=article.raw_html,
                site=article.site,
                scraped_at=article.scraped_at,
                response_status=article.response_status,
                content_length=article.content_length,
            )

            session.execute(stmt)

            if DEBUG:
                logger.info("Article stored successfully")
            return True

    except Exception as e:
        # Exception automatically triggers rollback in context manager
        logger.error(f"Failed to store article: {str(e)}")
        return False


def store_articles_batch(
    articles: list[RawArticle],
    max_memory_mb: int = 100,
) -> tuple[int, int]:
    """
    Store multiple articles in optimized batches using SQLAlchemy bulk operations.

    This function provides significant performance improvements over individual inserts:
    - Reduces database operations from N*2 (N inserts + N commits) to 2 (1 insert + 1 commit)
    - Eliminates connection churning by using a single session
    - Reduces disk I/O from N writes to 1 write per batch
    - Includes memory management for large article sets

    Args:
        articles: List of RawArticle objects to store
        max_memory_mb: Maximum memory usage in MB before chunking (default: 100MB)

    Returns:
        Tuple of (successful_count, failed_count)
    """
    if not articles:
        return 0, 0

    # Clean schema approach - use public schema only

    # Memory management: estimate size and chunk if needed for this batch
    estimated_size_mb = (
        sum(len(article.raw_html or "") for article in articles) / 1024 / 1024
    )

    """
    Recursively process in smaller chunks if estimated size exceeds max_memory_mb.
    If we end up with a chunk size of 1 [RawArticle], we fall back to individual inserts.
    """
    if estimated_size_mb > max_memory_mb and len(articles) > 1:
        # Process in chunks to manage memory
        chunk_size = max(1, int(len(articles) * max_memory_mb / estimated_size_mb))
        logger.info(
            f"Large batch detected ({estimated_size_mb:.1f}MB), processing in chunks of {chunk_size}"
        )

        total_successful = 0
        total_failed = 0

        for i in range(0, len(articles), chunk_size):
            chunk = articles[i : i + chunk_size]
            successful, failed = store_articles_batch(chunk, max_memory_mb)
            total_successful += successful
            total_failed += failed

        return total_successful, total_failed

    try:
        with get_session() as session:
            # Use SQLAlchemy's optimized bulk insert
            # Convert articles to dictionaries for bulk_insert_mappings
            article_dicts = [article.to_dict() for article in articles]

            # Use the raw_articles table metadata for bulk insert
            raw_articles_table = table(
                "raw_articles",
                column("id"),
                column("url"),
                column("raw_html"),
                column("site"),
                column("scraped_at"),
                column("response_status"),
                column("content_length"),
            )

            # Execute bulk insert
            """
            SQL: INSERT INTO schema.raw_articles (columns...) VALUES (...), (...), ...
            """
            session.execute(raw_articles_table.insert(), article_dicts)

            if DEBUG:
                logger.info(
                    f"Batch stored {len(articles)} articles successfully (pure ELT)"
                )

            return len(articles), 0

    except IntegrityError as e:
        # Handle unique constraint violations or other integrity issues
        logger.warning(f"Batch insert integrity error: {str(e)}")
        return _fallback_individual_inserts(articles)

    except Exception as e:
        logger.error(f"Batch insert failed: {str(e)}")
        return _fallback_individual_inserts(articles)


def _fallback_individual_inserts(articles: list[RawArticle]) -> tuple[int, int]:
    """
    Fallback method to insert articles individually when batch insert fails.

    This handles cases where the batch insert encounters issues like:
    - Unique constraint violations
    - Memory limitations
    - Other database errors

    Args:
        articles: List of articles to store individually

    Returns:
        Tuple of (successful_count, failed_count)
    """
    successful_count = 0
    failed_count = 0

    logger.info(f"Falling back to individual inserts for {len(articles)} articles")

    for article in articles:
        try:
            if store_article(article):
                successful_count += 1
            else:
                failed_count += 1
        except Exception as e:
            logger.error(f"Individual insert failed for article {article.id}: {str(e)}")
            failed_count += 1

    logger.info(
        f"Fallback complete: {successful_count} successful, {failed_count} failed"
    )
    return successful_count, failed_count


def clear_test_database() -> bool:
    """
    Clear all data from test database using application's database layer.

    This function provides a safe way to clean the test database for testing
    isolation. Only works in test environment for safety.

    Returns:
        True if cleared successfully, False on error

    Raises:
        ValueError: If called outside test environment
    """
    if ENVIRONMENT != "test":
        raise ValueError(
            f"clear_test_database can only be called in test environment, "
            f"but ENVIRONMENT is '{ENVIRONMENT}'"
        )

    try:
        # Clean schema approach - use public schema only
        # Truncate parent table with CASCADE to automatically clear child tables

        with get_session() as session:
            # Truncate parent table (raw_articles) with CASCADE
            # This automatically truncates word_facts due to foreign key CASCADE
            session.execute(text("TRUNCATE TABLE raw_articles CASCADE"))
            # Note: get_session() context manager handles commit automatically

        if DEBUG:
            logger.info("Successfully cleared test database")

        return True

    except Exception as e:
        logger.error(f"Failed to clear test database: {e}")
        return False


def apply_schema() -> bool:
    """
    Apply database schema from schema.sql file.

    Returns:
        True if schema applied successfully, False on error
    """
    try:
        from pathlib import Path

        schema_path = Path(__file__).parent.parent.parent / "database" / "schema.sql"
        schema_sql = schema_path.read_text()

        with get_session() as session:
            session.execute(text(schema_sql))

        if DEBUG:
            logger.info("Database schema applied successfully")

        return True

    except Exception as e:
        logger.error(f"Failed to apply schema: {e}")
        return False


def store_word_fact(word_fact: WordFact) -> bool:
    """
    Store a single word fact.

    Args:
        word_fact: WordFact object to store

    Returns:
        True if stored successfully, False on error
    """
    try:
        with get_session() as session:
            word_facts_table = table(
                "word_facts",
                column("id"),
                column("word"),
                column("article_id"),
                column("position_in_article"),
                column("scraped_at"),
            )

            stmt = word_facts_table.insert().values(
                id=word_fact.id,
                word=word_fact.word,
                article_id=word_fact.article_id,
                position_in_article=word_fact.position_in_article,
                scraped_at=word_fact.scraped_at,
            )

            session.execute(stmt)

            if DEBUG:
                logger.info(f"Word fact stored: {word_fact.word}")

            return True

    except Exception as e:
        logger.error(f"Failed to store word fact: {e}")
        return False


def store_word_facts_batch(
    word_facts: list[WordFact], batch_size: int = 500
) -> tuple[int, int]:
    """
    Store multiple word facts with batch processing.

    Args:
        word_facts: List of WordFact objects to store
        batch_size: Number of word facts to process at once

    Returns:
        Tuple of (successful_count, failed_count)
    """
    if not word_facts:
        return 0, 0

    try:
        with get_session() as session:
            # Convert to dictionaries for bulk insert
            word_fact_dicts = [wf.to_dict() for wf in word_facts]

            # Process in batches to avoid memory issues
            successful_count = 0
            failed_count = 0

            for i in range(0, len(word_fact_dicts), batch_size):
                batch = word_fact_dicts[i : i + batch_size]

                try:
                    word_facts_table = table(
                        "word_facts",
                        column("id"),
                        column("word"),
                        column("article_id"),
                        column("position_in_article"),
                        column("scraped_at"),
                    )

                    session.execute(word_facts_table.insert(), batch)
                    successful_count += len(batch)

                    if DEBUG:
                        logger.info(f"Stored batch of {len(batch)} word facts")

                except IntegrityError as e:
                    # Integrity error indicates a data generation bug
                    logger.error(f"Integrity error in batch (indicates data bug): {e}")
                    failed_count += len(batch)

                except Exception as e:
                    logger.error(f"Unexpected error storing word facts batch: {e}")
                    failed_count += len(batch)

            if DEBUG:
                logger.info(
                    f"Word facts batch complete: {successful_count} successful, {failed_count} failed"
                )

            return successful_count, failed_count

    except Exception as e:
        logger.error(f"Failed to store word facts batch: {e}")
        return 0, len(word_facts)
