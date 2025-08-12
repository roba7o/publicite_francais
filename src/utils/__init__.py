"""
Utilities module for French Article Scraper.

This module contains utility functions and classes for:
- Data validation
- Logging configuration
- HTML downloading

Note: Text processing is now handled by dbt/SQL for better performance.
"""

from .structured_logger import get_structured_logger
from .validators import DataValidator

__all__ = [
    "DataValidator",
    "get_structured_logger",
]
