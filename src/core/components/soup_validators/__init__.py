"""
Soup Validators package for French news scraper.

Contains soup validators for different news sources.
"""

from .base_soup_validator import BaseSoupValidator
from .france_info_soup_validator import FranceInfoSoupValidator
from .ladepeche_fr_soup_validator import LadepecheFrSoupValidator
from .slate_fr_soup_validator import SlateFrSoupValidator
from .tf1_info_soup_validator import Tf1InfoSoupValidator

__all__ = [
    "BaseSoupValidator",
    "FranceInfoSoupValidator",
    "LadepecheFrSoupValidator",
    "SlateFrSoupValidator",
    "Tf1InfoSoupValidator",
]
