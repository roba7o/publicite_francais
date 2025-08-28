"""
French Article Scraper - Main package.

This package provides tools for scraping French articles from various news websites,
processing the text, and extracting vocabulary with frequency analysis.
"""

from .database.models import RawArticle

__all__ = ["RawArticle"]
