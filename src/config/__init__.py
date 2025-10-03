"""
Configuration module for French Article Scraper.

This module contains all configuration settings, including:
- Website scraper and parser configurations
- Application settings using centralized environment management
"""

from .environment import (
    DEBUG,
    ENVIRONMENT,
    DATABASE_CONFIG,
    CONCURRENT_FETCHERS,
    FETCH_TIMEOUT,
)
from .site_configs import SCRAPER_CONFIGS

__all__ = [
    "DEBUG",
    "ENVIRONMENT",
    "DATABASE_CONFIG",
    "CONCURRENT_FETCHERS",
    "FETCH_TIMEOUT",
    "SCRAPER_CONFIGS",
]
