"""
Utilities module for French Article Scraper.

This module contains utility functions and classes for:
- Text processing and analysis
- Data validation
- Logging configuration
- HTML downloading
"""

from .french_text_processor import FrenchTextProcessor
from .html_downloader import download_html
from .structured_logger import get_structured_logger
from .validators import DataValidator

__all__ = [
    "FrenchTextProcessor",
    "DataValidator",
    "get_structured_logger",
    "download_html",
]
