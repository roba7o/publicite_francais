"""
Database connection module for French news scraper.

This module provides database connectivity infrastructure without modifying
existing CSV-based scraper logic. It sets up connection pooling, provides
connection management, and includes basic health checking functionality.

Usage:
    from database.database import DatabaseManager
    
    db = DatabaseManager()
    if db.test_connection():
        print("Database connected successfully!")
"""

import logging
from contextlib import contextmanager
from typing import Optional, Generator
import time

import psycopg2
from psycopg2 import pool, OperationalError
from sqlalchemy import create_engine, text, MetaData, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

from utils.structured_logger import get_structured_logger


class DatabaseManager:
    """
    Manages database connections for the French news scraper.
    
    Provides both raw psycopg2 connections and SQLAlchemy sessions
    for different use cases. Includes connection pooling, health checks,
    and proper error handling.
    
    Attributes:
        connection_pool: psycopg2 connection pool for raw SQL
        engine: SQLAlchemy engine for ORM operations
        SessionLocal: SQLAlchemy session factory
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize database manager with configuration.
        
        Args:
            config: Database configuration dict. If None, uses default config.
        """
        self.logger = get_structured_logger(self.__class__.__name__)
        
        # Load configuration from settings
        from config.settings import DATABASE_CONFIG
        default_config = DATABASE_CONFIG
        
        self.config = {**default_config, **(config or {})}
        
        # Initialize connection infrastructure - will be set during initialize()
        self._connection_pool: Optional[pool.AbstractConnectionPool] = None
        self._engine: Optional[Engine] = None
        self._session_local: Optional[sessionmaker] = None
        self._metadata: Optional[MetaData] = None
        
        # Connection status
        self._initialized = False
        self._last_health_check = 0
        self._health_check_interval = 300  # 5 minutes
        
    def initialize(self) -> bool:
        """
        Initialize database connections and pools.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
            
        try:
            self._setup_connection_pool()
            self._setup_sqlalchemy()
            self._initialized = True
            
            self.logger.info(
                "Database manager initialized successfully",
                extra_data={
                    'host': self.config['host'],
                    'port': self.config['port'],
                    'database': self.config['database'],
                    'pool_size': f"{self.config['min_connections']}-{self.config['max_connections']}"
                }
            )
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize database manager",
                extra_data={
                    'error': str(e),
                    'config': {k: v for k, v in self.config.items() if k != 'password'}
                },
                exc_info=True
            )
            return False
    
    def _setup_connection_pool(self) -> None:
        """Setup psycopg2 connection pool for raw SQL operations."""
        connection_string = (
            f"host={self.config['host']} "
            f"port={self.config['port']} "
            f"dbname={self.config['database']} "
            f"user={self.config['user']} "
            f"password={self.config['password']}"
        )
        
        self._connection_pool = pool.ThreadedConnectionPool(
            minconn=self.config['min_connections'],
            maxconn=self.config['max_connections'],
            dsn=connection_string,
            connect_timeout=self.config['connection_timeout']
        )
        
    def _setup_sqlalchemy(self) -> None:
        """Setup SQLAlchemy engine and session factory."""
        database_url = (
            f"postgresql://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )
        
        self._engine = create_engine(
            database_url,
            pool_size=self.config['min_connections'],
            max_overflow=self.config['max_connections'] - self.config['min_connections'],
            pool_timeout=self.config['connection_timeout'],
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False  # Set to True for SQL query logging
        )
        
        self._session_local = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine
        )
        
        self._metadata = MetaData()
    
    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """
        Context manager for raw psycopg2 database connections.
        
        Yields:
            psycopg2 database connection
            
        Raises:
            RuntimeError: If database manager is not initialized
            
        Example:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM news_data.news_sources")
                results = cursor.fetchall()
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("Database manager not initialized")
        
        # Type guard: After initialization, connection_pool should not be None
        assert self._connection_pool is not None, "Connection pool not initialized"
                
        connection = None
        try:
            connection = self._connection_pool.getconn()
            yield connection
            connection.commit()
            
        except Exception as e:
            if connection:
                connection.rollback()
            self.logger.error(
                "Database connection error",
                extra_data={'error': str(e)},
                exc_info=True
            )
            raise
            
        finally:
            if connection:
                self._connection_pool.putconn(connection)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for SQLAlchemy database sessions.
        
        Yields:
            SQLAlchemy database session
            
        Raises:
            RuntimeError: If database manager is not initialized
            
        Example:
            with db.get_session() as session:
                sources = session.execute(text("SELECT * FROM news_data.news_sources"))
                for row in sources:
                    print(row)
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("Database manager not initialized")
        
        # Type guard: After initialization, SessionLocal should not be None
        assert self._session_local is not None, "Session factory not initialized"
                
        session = self._session_local()
        try:
            yield session
            session.commit()
            
        except Exception as e:
            session.rollback()
            self.logger.error(
                "Database session error", 
                extra_data={'error': str(e)},
                exc_info=True
            )
            raise
            
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """
        Test database connectivity and basic operations.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test raw connection
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                
                if result[0] != 1:
                    return False
            
            # Test SQLAlchemy connection
            with self.get_session() as session:
                result = session.execute(text("SELECT COUNT(*) FROM news_data.news_sources"))
                count = result.scalar()
                
            self.logger.info(
                "Database connection test successful",
                extra_data={
                    'news_sources_count': count,
                    'connection_type': 'both_raw_and_sqlalchemy'
                }
            )
            return True
            
        except Exception as e:
            self.logger.error(
                "Database connection test failed",
                extra_data={'error': str(e)},
                exc_info=True
            )
            return False
    
    def health_check(self) -> dict:
        """
        Comprehensive database health check.
        
        Returns:
            Dict with health status and metrics
        """
        current_time = time.time()
        
        # Skip if recent health check exists
        if (current_time - self._last_health_check) < self._health_check_interval:
            return {'status': 'cached', 'message': 'Recent health check exists'}
        
        health_status = {
            'status': 'unknown',
            'timestamp': current_time,
            'connection_pool_status': 'unknown',
            'sqlalchemy_status': 'unknown',
            'news_sources_count': 0,
            'errors': []
        }
        
        try:
            # Test connection pool
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                health_status['postgresql_version'] = version
                health_status['connection_pool_status'] = 'healthy'
                cursor.close()
                
        except Exception as e:
            health_status['connection_pool_status'] = 'error'
            health_status['errors'].append(f"Connection pool: {str(e)}")
        
        try:
            # Test SQLAlchemy
            with self.get_session() as session:
                result = session.execute(text("SELECT COUNT(*) FROM news_data.news_sources"))
                health_status['news_sources_count'] = result.scalar()
                health_status['sqlalchemy_status'] = 'healthy'
                
        except Exception as e:
            health_status['sqlalchemy_status'] = 'error'
            health_status['errors'].append(f"SQLAlchemy: {str(e)}")
        
        # Overall status
        if not health_status['errors']:
            health_status['status'] = 'healthy'
        else:
            health_status['status'] = 'degraded' if len(health_status['errors']) == 1 else 'unhealthy'
        
        self._last_health_check = current_time
        
        self.logger.info(
            "Database health check completed",
            extra_data=health_status
        )
        
        return health_status
    
    def close(self) -> None:
        """Clean up database connections and pools."""
        if self._connection_pool:
            self._connection_pool.closeall()
            self.logger.info("Connection pool closed")
            
        if self._engine:
            self._engine.dispose()
            self.logger.info("SQLAlchemy engine disposed")
            
        self._initialized = False


# Global database manager instance
# Will be configured by the config system later
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
        
    return _db_manager


def initialize_database() -> bool:
    """
    Initialize the global database manager.
    
    Returns:
        True if successful, False otherwise
    """
    db = get_database_manager()
    return db.initialize()