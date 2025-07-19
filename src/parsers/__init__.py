"""
Parser module for French Article Scraper.

This module contains parsers for extracting content from different French news websites.
All parsers extend the BaseParser class and return ArticleData objects.
"""

from .base_parser import BaseParser
from .france_info_parser import FranceInfoArticleParser
from .ladepeche_fr_parser import LadepecheFrArticleParser
from .slate_fr_parser import SlateFrArticleParser
from .tf1_info_parser import TF1InfoArticleParser

__all__ = [
    "BaseParser",
    "SlateFrArticleParser",
    "FranceInfoArticleParser",
    "TF1InfoArticleParser",
    "LadepecheFrArticleParser",
]
