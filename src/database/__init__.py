"""
Database package for French news scraper.

Provides database connection, models, and utilities.
"""

from database.database import (
    get_session,
    initialize_database,
    store_articles_batch,
    store_raw_article,
)
from database.models import RawArticle

__all__ = [
    "get_session",
    "initialize_database",
    "store_raw_article",
    "store_articles_batch",
    "RawArticle",
]
