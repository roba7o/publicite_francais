"""
Configuration module for French Article Scraper.

This module contains all configuration settings, including:
- Website scraper and parser configurations
- Application settings

Note: Text processing and filtering is now handled by dbt/SQL.
Stopwords and junk word configurations are in french_flashcards/config/ as JSON files.
"""

from .settings import DEBUG, OFFLINE
from .source_configs import SCRAPER_CONFIGS

__all__ = [
    "DEBUG",
    "OFFLINE",
    "SCRAPER_CONFIGS",
]
