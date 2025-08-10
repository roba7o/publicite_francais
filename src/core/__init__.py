"""
Core processing module for French Article Scraper.

This module contains the main article processing logic,
including coordination between scrapers and parsers.
"""

from .database_processor import DatabaseProcessor

__all__ = ["DatabaseProcessor"]
