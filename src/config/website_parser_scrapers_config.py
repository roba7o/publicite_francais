"""
Configuration for news source scrapers in database architecture.

This module defines which news sources to process using the consolidated
database-focused scraper architecture. Text processing is handled by dbt/SQL.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ScraperConfig:
    """Configuration for a single news source with dynamic class loading."""

    name: str  # Display name of the news source
    enabled: bool  # Whether to process this source
    scraper_class: str  # Full path to scraper class
    parser_class: str  # Full path to database parser class
    scraper_kwargs: Optional[Dict] = None  # Arguments to pass to scraper
    parser_kwargs: Optional[Dict] = None  # Arguments to pass to parser

    def to_dict(self) -> Dict:
        """Convert to dict format for DatabaseProcessor compatibility."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "scraper_class": self.scraper_class,
            "parser_class": self.parser_class,
            "scraper_kwargs": self.scraper_kwargs or {},
            "parser_kwargs": self.parser_kwargs or {}
        }


def get_scraper_configs() -> list[ScraperConfig]:
    """Get list of scraper configurations with dynamic class loading."""
    from config.settings import DEBUG
    
    return [
        ScraperConfig(
            name="Slate.fr",
            enabled=True,
            scraper_class="scrapers.slate_fr_scraper.SlateFrURLScraper",
            parser_class="parsers.database_slate_fr_parser.DatabaseSlateFrParser",
            scraper_kwargs={"debug": DEBUG},
        ),
        ScraperConfig(
            name="FranceInfo.fr",
            enabled=True,
            scraper_class="scrapers.france_info_scraper.FranceInfoURLScraper", 
            parser_class="parsers.database_france_info_parser.DatabaseFranceInfoParser",
            scraper_kwargs={"debug": DEBUG},
        ),
        ScraperConfig(
            name="TF1 Info",
            enabled=True,
            scraper_class="scrapers.tf1_info_scraper.TF1InfoURLScraper",
            parser_class="parsers.database_tf1_info_parser.DatabaseTF1InfoParser",
            scraper_kwargs={"debug": DEBUG},
        ),
        ScraperConfig(
            name="Depeche.fr",
            enabled=True,
            scraper_class="scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper",
            parser_class="parsers.database_ladepeche_fr_parser.DatabaseLadepecheFrParser",
            scraper_kwargs={"debug": DEBUG},
        ),
    ]


# Static list for backward compatibility (tests)
SCRAPER_CONFIGS = get_scraper_configs()
