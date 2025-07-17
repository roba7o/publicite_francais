"""
Utilities module for French Article Scraper.

This module contains utility functions and classes for:
- Text processing and analysis
- CSV output writing
- Data validation
- Logging configuration
- HTML downloading
"""

from .french_text_processor import FrenchTextProcessor
from .csv_writer import DailyCSVWriter, CSVWriter
from .validators import DataValidator
from .structured_logger import get_structured_logger
from .html_downloader import download_html

__all__ = [
    "FrenchTextProcessor",
    "DailyCSVWriter",
    "CSVWriter",
    "DataValidator",
    "get_structured_logger",
    "download_html",
]
