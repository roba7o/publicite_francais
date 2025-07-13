from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class ScraperConfig:
    name: str
    enabled: bool
    scraper_class: str
    parser_class: str
    live_mode: bool = True
    test_files: Optional[List[str]] = None
    scraper_kwargs: Optional[Dict] = None
    parser_kwargs: Optional[Dict] = None


SCRAPER_CONFIGS = [
    ScraperConfig(
        name="Slate.fr",
        enabled=True,
        scraper_class="article_scrapers.scrapers.slate_fr_scraper.SlateFrURLScraper",
        parser_class="article_scrapers.parsers.slate_fr_parser.SlateFrArticleParser",
        live_mode=True,
        scraper_kwargs={"debug": True},
    ),
    ScraperConfig(
        name="FranceInfo.fr",
        enabled=True,
        scraper_class="article_scrapers.scrapers.france_info_scraper.FranceInfoURLScraper",
        parser_class="article_scrapers.parsers.france_info_parser.FranceInfoArticleParser",
        live_mode=True,
        scraper_kwargs={"debug": True},
    ),
    ScraperConfig(
        name="TF1 Info",
        enabled=True,
        scraper_class="article_scrapers.scrapers.tf1_info_scraper.TF1InfoURLScraper",
        parser_class="article_scrapers.parsers.tf1_info_parser.TF1InfoArticleParser",
        live_mode=True,
        scraper_kwargs={"debug": True},
    ),
    ScraperConfig(
        name="Depeche.fr",
        enabled=True,
        scraper_class="article_scrapers.scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper",
        parser_class="article_scrapers.parsers.ladepeche_fr_parser.LadepecheFrArticleParser",
        live_mode=True,
        scraper_kwargs={"debug": True},
    ),
]
