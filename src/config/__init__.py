"""
Configuration module for French Article Scraper.

This module contains all configuration settings, including:
- Website scraper and parser configurations
- Text processing settings
- Junk word filters
- Application settings
"""

from .settings import DEBUG, OFFLINE
from .website_parser_scrapers_config import SCRAPER_CONFIGS, ScraperConfig
from .text_processing_config import (
    SITE_CONFIGS,
    get_site_config,
    get_all_additional_stopwords,
    is_junk_filtering_enabled,
)
from .junk_words_config import get_junk_patterns, is_junk_word

__all__ = [
    "DEBUG",
    "OFFLINE",
    "SCRAPER_CONFIGS",
    "ScraperConfig",
    "SITE_CONFIGS",
    "get_site_config",
    "get_all_additional_stopwords",
    "is_junk_filtering_enabled",
    "get_junk_patterns",
    "is_junk_word",
]
