"""
Schema utilities for database operations.

Simple utilities for getting the correct database schema based on environment.
"""

from config.environment import get_news_data_schema


def get_current_schema() -> str:
    """Get current schema name dynamically based on environment."""
    return get_news_data_schema()
