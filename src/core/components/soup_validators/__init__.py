"""
Soup Validators package for French news scraper.

Contains soup validators for different news sources.
"""

from .base_soup_validator import BaseSoupValidator
from .france_info_soup_validator import FranceInfoSoupValidator
from .ladepeche_fr_soup_validator import ladepechefrSoupValidator
from .slate_fr_soup_validator import SlateFrSoupValidator
from .tf1_info_soup_validator import tf1infoSoupValidator

__all__ = [
    "BaseSoupValidator",
    "FranceInfoSoupValidator",
    "ladepechefrSoupValidator",
    "SlateFrSoupValidator",
    "tf1infoSoupValidator",
]
