"""
Configuration for news source scrapers in database architecture.

This module defines which news sources to process using the consolidated
database-focused scraper architecture. Text processing is handled by dbt/SQL.
"""

from typing import Dict, List


def get_scraper_configs() -> List[Dict]:
    """Get list of scraper configurations as simple dictionaries."""
    from utils.lazy_imports import get_debug_setting
    
    DEBUG = get_debug_setting()

    return [
        {
            "name": "Slate.fr",
            "enabled": True,
            "scraper_class": "scrapers.slate_fr_scraper.SlateFrURLScraper",
            "parser_class": "parsers.database_slate_fr_parser.DatabaseSlateFrParser",
            "scraper_kwargs": {"debug": DEBUG},
            "parser_kwargs": {},
        },
        {
            "name": "FranceInfo.fr", 
            "enabled": True,
            "scraper_class": "scrapers.france_info_scraper.FranceInfoURLScraper",
            "parser_class": "parsers.database_france_info_parser.DatabaseFranceInfoParser",
            "scraper_kwargs": {"debug": DEBUG},
            "parser_kwargs": {},
        },
        {
            "name": "TF1 Info",
            "enabled": True,
            "scraper_class": "scrapers.tf1_info_scraper.TF1InfoURLScraper", 
            "parser_class": "parsers.database_tf1_info_parser.DatabaseTF1InfoParser",
            "scraper_kwargs": {"debug": DEBUG},
            "parser_kwargs": {},
        },
        {
            "name": "Depeche.fr",
            "enabled": True,
            "scraper_class": "scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper",
            "parser_class": "parsers.database_ladepeche_fr_parser.DatabaseLadepecheFrParser", 
            "scraper_kwargs": {"debug": DEBUG},
            "parser_kwargs": {},
        },
    ]


# Static list for backward compatibility (tests)
SCRAPER_CONFIGS = get_scraper_configs()
