"""
Simple database connection for French news scraper.

1. Sets up a connection to a PostgreSQL database using SQLAlchemy.
2. creates sessions for database operations.
3. ensures sessions are cleaned up - committed or rolled back as needed.


The main purpose of this module is to create the session factory (which uses engine config). Much later when
articles are processed, repository.store_artticle() calls 'with self.db.get_session() as session:' to get a session.
context mananger auto commits (or rolls back) the session, then clsoes it.

so main.py calls initialize_database() to set up the session factory, but never creates the session directly.

"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config.settings import DATABASE_CONFIG, DEBUG

# Simple module-level session factory
_SessionLocal = None


def initialize_database() -> bool:
    """Initialize database connection with simple session factory."""
    global _SessionLocal

    try:
        # builds connection string from config
        database_url = (
            f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
            f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
        )
        # this engine manages connections to database
        engine = create_engine(database_url, echo=DEBUG)

        # create session factory bound to this engine
        _SessionLocal = sessionmaker(bind=engine)

        # Tests the connection by creating a session (using the session factory _SessionLocal Callable) and executing a simple query
        with get_session() as session:
            session.execute(text("SELECT 1"))

        return True

    except Exception:
        return False


# Note: this is a context manager that provides a session for database operations.
# main.py does not use this: the heavy lifting is done in the repository layer
# where its using the factory that main .py created.

# context manager is used here to ensure sessions are cleaned up properly


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
    NEEDS WITH AS ITS A CONTEXT MANAGER!!!!!!
    The context manager's __enter__() and __exit__() methods only trigger inside a with block.
        with get_session() as s:
            s.execute(text("UPDATE users SET active = True"))
            # Auto-committed when block exits

    Example wrong usage:
    session = get_session()  #  WRONG - returns a generator, not a usable session
    session.execute(...)     #  Fails - (no execute() method on the generator)


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
        yield session  # hands session to the caller, the with statement can now use it. Fucntion pauses.
        session.commit()  # saves
    except Exception:
        session.rollback()  # discards
        raise
    finally:
        session.close()  # always closes the session, even if there was an error


# Backwards compatibility for existing code (technical debt can be refactored later)
def get_database_manager():
    """
    Backwards compatibility shim for old database manager pattern.

    This function exists to maintain compatibility with existing code that was written
    before the database architecture was simplified. It provides the same interface
    as the old database manager but delegates to the new simplified get_session() function.

    Legacy Pattern (what existing code expects):
        from database import get_database_manager
        manager = get_database_manager()
        with manager.get_session() as session:
            session.execute(text("SELECT 1"))

    Modern Pattern (preferred for new code):
        from database import get_session
        with get_session() as session:
            session.execute(text("SELECT 1"))

    Currently Used In:
        - src/database/article_repository.py (line 27):
          self.db = get_database_manager()
        - tests/test_deterministic_pipeline.py (multiple locations):
          db = get_database_manager()
          with db.get_session() as session: ...
        - tests/test_database_connection.py:
          Similar database manager usage pattern

    Migration Path:
        1. Update article_repository.py to use get_session() directly
        2. Update test files to use get_session() directly
        3. Remove this backwards compatibility function

    Returns:
        SimpleManager: Object with get_session() method that delegates to the
                      modern get_session() context manager function

    Note:
        This is technical debt that should be removed once all existing code
        has been migrated to use the direct get_session() function.
    """

    class SimpleManager:
        def get_session(self):
            return get_session()

    return SimpleManager()
