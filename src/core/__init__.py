"""
Database module for French news scraper.

Provides database connectivity infrastructure without modifying existing
scraper logic.
"""

from .data_processor import DataProcessor
from .database import get_session, initialize_database

__all__ = [
    "initialize_database",
    "get_session",
    "DataProcessor",
]
