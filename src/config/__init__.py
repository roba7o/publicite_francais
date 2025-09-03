"""
Configuration module for French Article Scraper.

This module contains all configuration settings, including:
- Website scraper and parser configurations
- Application settings using centralized environment management

Note: Text processing and filtering is now handled by dbt/SQL.
Stopwords and junk word configurations are in french_flashcards/config/ as JSON files.
"""

from .environment import (
    DEBUG,
    TEST_MODE,
    DATABASE_CONFIG,
    get_news_data_schema,
    CONCURRENT_FETCHERS,
    FETCH_TIMEOUT,
)
from .site_configs import SCRAPER_CONFIGS

__all__ = [
    "DEBUG",
    "TEST_MODE",
    "DATABASE_CONFIG",
    "get_news_data_schema",
    "CONCURRENT_FETCHERS",
    "FETCH_TIMEOUT",
    "SCRAPER_CONFIGS",
]
