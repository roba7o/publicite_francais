"""
Utilities module for French Article Scraper.

This module contains utility functions and classes for:
- Data validation
- Logging configuration
- HTML downloading

Note: Text processing is now handled by downstream processing for better performance.
"""

from .structured_logger import get_logger

__all__ = [
    "get_logger",
]
