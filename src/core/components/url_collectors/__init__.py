"""
URL Collectors package for French news scraper.

Contains URL collectors for different news sources.
"""

from .base_url_collector import BaseUrlCollector
from .france_info_url_collector import FranceInfoUrlCollector
from .ladepeche_fr_url_collector import LadepecheFrUrlCollector
from .slate_fr_url_collector import SlateFrUrlCollector
from .tf1_info_url_collector import TF1InfoUrlCollector

__all__ = [
    "BaseUrlCollector",
    "FranceInfoUrlCollector",
    "LadepecheFrUrlCollector",
    "SlateFrUrlCollector",
    "TF1InfoUrlCollector",
]
