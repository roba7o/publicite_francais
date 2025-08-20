"""
Database package for French news scraper.

Provides database connection, models, and utilities.
"""

from database.database import get_session, initialize_database, store_raw_article
from database.models import RawArticle
from database.schema import get_current_schema

__all__ = [
    "get_session",
    "initialize_database", 
    "store_raw_article",
    "RawArticle",
    "get_current_schema",
]