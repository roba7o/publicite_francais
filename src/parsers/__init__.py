"""
Parser module for French Article Scraper.

This module contains database-focused parsers for extracting content from different French news websites.
All parsers extend the DatabaseBaseParser class and return ArticleData objects for database storage.
"""

from .database_base_parser import DatabaseBaseParser
from .database_france_info_parser import DatabaseFranceInfoParser
from .database_ladepeche_fr_parser import DatabaseLadepecheFrParser
from .database_slate_fr_parser import DatabaseSlateFrParser
from .database_tf1_info_parser import DatabaseTF1InfoParser

__all__ = [
    "DatabaseBaseParser",
    "DatabaseSlateFrParser", 
    "DatabaseFranceInfoParser",
    "DatabaseTF1InfoParser",
    "DatabaseLadepecheFrParser",
]
