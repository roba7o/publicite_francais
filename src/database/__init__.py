"""
Database module for French news scraper.

Provides database connectivity infrastructure without modifying existing
scraper logic.
"""

from .database import get_database_manager, initialize_database, get_session
from .article_repository import ArticleRepository

__all__ = ["get_database_manager", "initialize_database", "get_session", "ArticleRepository"]
