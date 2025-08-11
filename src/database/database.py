"""
Simple database connection for French news scraper.

Provides straightforward SQLAlchemy session management.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config.settings import DATABASE_CONFIG

# Simple module-level session factory
_SessionLocal = None


def initialize_database() -> bool:
    """Initialize database connection with simple session factory."""
    global _SessionLocal
    
    try:
        database_url = (
            f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
            f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
        )
        
        engine = create_engine(database_url, echo=False)
        _SessionLocal = sessionmaker(bind=engine)
        
        # Test connection
        with get_session() as session:
            session.execute(text("SELECT 1"))
            
        return True
        
    except Exception:
        return False


@contextmanager  
def get_session() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup."""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
        
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Backwards compatibility for existing code
def get_database_manager():
    """Backwards compatibility shim."""
    class SimpleManager:
        def get_session(self):
            return get_session()
    return SimpleManager()
