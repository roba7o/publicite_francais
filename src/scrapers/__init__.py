"""
Scraper module for French Article Scraper.

This module contains scrapers for fetching URLs from different French news websites.
All scrapers provide methods to get article URLs for processing.
"""

from .france_info_scraper import FranceInfoURLScraper
from .ladepeche_fr_scraper import LadepecheFrURLScraper
from .slate_fr_scraper import SlateFrURLScraper
from .tf1_info_scraper import TF1InfoURLScraper

__all__ = [
    "SlateFrURLScraper",
    "FranceInfoURLScraper",
    "TF1InfoURLScraper",
    "LadepecheFrURLScraper",
]
