"""
Database module for French news scraper.

Provides database connectivity infrastructure without modifying existing
scraper logic.
"""

from .database import DatabaseManager, get_database_manager, initialize_database

__all__ = ["DatabaseManager", "get_database_manager", "initialize_database"]
