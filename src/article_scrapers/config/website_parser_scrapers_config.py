# article_scrapers/config/scraper_configs.py

"""
Configuration for various web scrapers.

This module defines the ScraperConfig dataclass and a list of configurations
for different news websites, specifying their respective scraper and parser classes,
and other operational parameters.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class ScraperConfig:
    """
    Defines the configuration for a single web scraper.

    Attributes:
        name (str): A human-readable name for the scraper (e.g., "Slate.fr").
        enabled (bool): Whether this scraper configuration is active.
        scraper_class (str): The full import path to the scraper class.
        parser_class (str): The full import path to the parser class.
        live_mode (bool): If True, the scraper will fetch content from live URLs.
                          If False, it will use local test files. Defaults to True.
        test_files (Optional[List[str]]): A list of local HTML file paths to use
                                           when live_mode is False. Defaults to None.
        scraper_kwargs (Optional[Dict]): Additional keyword arguments to pass to
                                         the scraper's constructor. Defaults to None.
        parser_kwargs (Optional[Dict]): Additional keyword arguments to pass to
                                        the parser's constructor. Defaults to None.
    """
    name: str
    enabled: bool
    scraper_class: str
    parser_class: str
    live_mode: bool = True
    test_files: Optional[List[str]] = None
    scraper_kwargs: Optional[Dict] = None
    parser_kwargs: Optional[Dict] = None


# Update the class paths to match your actual module structure if different
SCRAPER_CONFIGS: List[ScraperConfig] = [
    ScraperConfig(
        name="Slate.fr",
        enabled=True,
        scraper_class="article_scrapers.scrapers.slate_fr_scraper.SlateFrURLScraper",
        parser_class="article_scrapers.parsers.slate_fr_parser.SlateFrArticleParser",
        live_mode=True,
        test_files=["test1.html", "test2.html"],
        scraper_kwargs={"debug": True},
        parser_kwargs={}
    ),
    ScraperConfig(
        name="FranceInfo.fr",
        enabled=True,
        scraper_class="article_scrapers.scrapers.france_info_scraper.FranceInfoURLScraper",
        parser_class="article_scrapers.parsers.france_info_parser.FranceInfoArticleParser",
        live_mode=True,
        scraper_kwargs={"debug": True},
        parser_kwargs={}
    ),
    ScraperConfig(
        name="TF1 Info",
        enabled=True,
        scraper_class="article_scrapers.scrapers.tf1_info_scraper.TF1InfoURLScraper",
        parser_class="article_scrapers.parsers.tf1_info_parser.TF1InfoArticleParser",
        live_mode=True,
        scraper_kwargs={"debug": True},
        parser_kwargs={}
    ),
    ScraperConfig(
        name="Depeche.fr",
        enabled=True,
        scraper_class="article_scrapers.scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper",
        parser_class="article_scrapers.parsers.ladepeche_fr_parser.LadepecheFrArticleParser",
        live_mode=True,
        scraper_kwargs={"debug": True},
        parser_kwargs={}
    )
]