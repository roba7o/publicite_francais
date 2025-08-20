"""
Contains the full path to scraper/parsers for the database architecture.

"""


def get_scraper_configs() -> list[dict]:
    """Get list of scraper configurations using domain-based naming."""
    from config.settings import DEBUG

    return [
        {
            "domain": "slate.fr",  # Standardized domain identifier
            "enabled": True,
            "scraper_class": "scrapers.slate_fr_scraper.SlateFrURLScraper",
            "parser_class": "parsers.database_slate_fr_parser.DatabaseSlateFrParser",
            "scraper_kwargs": {"debug": DEBUG},
            "parser_kwargs": {"debug": DEBUG},
        },
        {
            "domain": "franceinfo.fr",  # Standardized domain identifier
            "enabled": True,
            "scraper_class": "scrapers.france_info_scraper.FranceInfoURLScraper",
            "parser_class": "parsers.database_france_info_parser.DatabaseFranceInfoParser",
            "scraper_kwargs": {"debug": DEBUG},
            "parser_kwargs": {"debug": DEBUG},
        },
        {
            "domain": "tf1info.fr",  # Standardized domain identifier
            "enabled": True,
            "scraper_class": "scrapers.tf1_info_scraper.TF1InfoURLScraper",
            "parser_class": "parsers.database_tf1_info_parser.DatabaseTF1InfoParser",
            "scraper_kwargs": {"debug": DEBUG},
            "parser_kwargs": {"debug": DEBUG},
        },
        {
            "domain": "ladepeche.fr",  # Standardized domain identifier
            "enabled": True,
            "scraper_class": "scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper",
            "parser_class": "parsers.database_ladepeche_fr_parser.DatabaseLadepecheFrParser",
            "scraper_kwargs": {"debug": DEBUG},
            "parser_kwargs": {"debug": DEBUG},
        },
    ]


# Static list for backward compatibility (tests)
SCRAPER_CONFIGS = get_scraper_configs()
