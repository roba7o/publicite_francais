"""
Parser module for French Article Scraper.

This module contains parsers for extracting content from different French news websites.
All parsers extend the BaseParser class and return ArticleData objects.
"""

from .base_parser import BaseParser
from .slate_fr_parser import SlateFrArticleParser
from .france_info_parser import FranceInfoArticleParser
from .tf1_info_parser import TF1InfoArticleParser
from .ladepeche_fr_parser import LadepecheFrArticleParser

__all__ = [
    "BaseParser",
    "SlateFrArticleParser",
    "FranceInfoArticleParser",
    "TF1InfoArticleParser",
    "LadepecheFrArticleParser",
]
