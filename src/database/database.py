"""
Simple database connection module for French news scraper.

This module provides straightforward database connectivity for a personal project.
No complex singleton patterns or enterprise health checks - just what you need.

Usage:
    from database import get_database_manager
    
    db = get_database_manager()
    with db.get_session() as session:
        result = session.execute(text("SELECT * FROM news_data.articles"))
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from utils.structured_logger import get_structured_logger


class DatabaseManager:
    """
    Simple database manager for personal project.
    
    Provides SQLAlchemy sessions with basic error handling and logging.
    No connection pooling, health checks, or other enterprise features.
    """

    def __init__(self, config: dict = None):
        """Initialize with database configuration."""
        self.logger = get_structured_logger(self.__class__.__name__)

        # Load configuration from settings
        from config.settings import DATABASE_CONFIG

        self.config = {**DATABASE_CONFIG, **(config or {})}
        
        # Initialize SQLAlchemy components
        self._engine: Engine = None
        self._session_local: sessionmaker = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize database connection.
        
        Returns:
            True if successful, False otherwise
        """
        if self._initialized:
            return True

        try:
            database_url = (
                f"postgresql://{self.config['user']}:{self.config['password']}"
                f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
            )

            self._engine = create_engine(
                database_url,
                pool_timeout=self.config['connection_timeout'],
                pool_recycle=3600,  # Recycle connections after 1 hour
                echo=False,  # Set to True for SQL query logging
            )

            self._session_local = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self._engine
            )

            self._initialized = True
            
            self.logger.info(
                "Database initialized",
                extra_data={
                    "host": self.config["host"],
                    "database": self.config["database"],
                }
            )
            return True

        except Exception as e:
            self.logger.error(
                "Database initialization failed", 
                extra_data={"error": str(e)}, 
                exc_info=True
            )
            return False

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Example:
            with db.get_session() as session:
                result = session.execute(text("SELECT * FROM news_data.articles"))
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("Database not initialized")

        session = self._session_local()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error("Database error", extra_data={"error": str(e)}, exc_info=True)
            raise
        finally:
            session.close()

    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            self.logger.info("Database connection test successful")
            return True
        except Exception as e:
            self.logger.error("Database connection test failed", extra_data={"error": str(e)})
            return False

    def close(self) -> None:
        """Clean up database connections."""
        if self._engine:
            self._engine.dispose()
            self.logger.info("Database connection closed")
        self._initialized = False


# Simple global instance - no complex singleton pattern
_db_manager: DatabaseManager = None


def get_database_manager() -> DatabaseManager:
    """Get the database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def initialize_database() -> bool:
    """Initialize the database manager."""
    return get_database_manager().initialize()