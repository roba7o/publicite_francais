"""
Configuration for news source scrapers and parsers.

This module defines which news sources to process and how to process them,
including the scraper and parser classes to use for each source.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class ScraperConfig:
    """Configuration for a single news source."""

    name: str  # Display name of the news source
    enabled: bool  # Whether to process this source
    scraper_class: str  # Full path to scraper class
    parser_class: str  # Full path to parser class
    scraper_kwargs: Optional[Dict] = None  # Arguments to pass to scraper
    parser_kwargs: Optional[Dict] = None  # Arguments to pass to parser


# List of all configured news sources
SCRAPER_CONFIGS = [
    ScraperConfig(
        name="Slate.fr",
        enabled=True,
        scraper_class="scrapers.slate_fr_scraper.SlateFrURLScraper",
        parser_class="parsers.slate_fr_parser.SlateFrArticleParser",
        scraper_kwargs={"debug": True},
    ),
    ScraperConfig(
        name="FranceInfo.fr",
        enabled=True,
        scraper_class="scrapers.france_info_scraper.FranceInfoURLScraper",
        parser_class="parsers.france_info_parser.FranceInfoArticleParser",
        scraper_kwargs={"debug": True},
    ),
    ScraperConfig(
        name="TF1 Info",
        enabled=True,
        scraper_class="scrapers.tf1_info_scraper.TF1InfoURLScraper",
        parser_class="parsers.tf1_info_parser.TF1InfoArticleParser",
        scraper_kwargs={"debug": True},
    ),
    ScraperConfig(
        name="Depeche.fr",
        enabled=True,
        scraper_class="scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper",
        parser_class="parsers.ladepeche_fr_parser.LadepecheFrArticleParser",
        scraper_kwargs={"debug": True},
    ),
]
