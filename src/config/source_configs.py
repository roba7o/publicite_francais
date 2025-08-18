"""
Contains the full path to scraper/parsers for the database architecture.

"""


def get_scraper_configs() -> list[dict]:
    """Get list of scraper configurations as simple dictionaries."""
    from config.settings import DEBUG

    return [
        {
            "name": "Slate.fr",
            "source_id": "1fce7432-58de-4295-a3dc-54ed7801bac1",
            "enabled": True,
            "scraper_class": "scrapers.slate_fr_scraper.SlateFrURLScraper",
            "parser_class": "parsers.database_slate_fr_parser.DatabaseSlateFrParser",
            "scraper_kwargs": {"debug": DEBUG},
        },
        {
            "name": "FranceInfo.fr",
            "source_id": "022d09f8-0fe5-4990-b520-f7f70e49865b",
            "enabled": True,
            "scraper_class": "scrapers.france_info_scraper.FranceInfoURLScraper",
            "parser_class": "parsers.database_france_info_parser.DatabaseFranceInfoParser",
            "scraper_kwargs": {"debug": DEBUG},
        },
        {
            "name": "TF1 Info",
            "source_id": "2298bfb1-122c-4731-bef3-a421420aa2a1",
            "enabled": True,
            "scraper_class": "scrapers.tf1_info_scraper.TF1InfoURLScraper",
            "parser_class": "parsers.database_tf1_info_parser.DatabaseTF1InfoParser",
            "scraper_kwargs": {"debug": DEBUG},
        },
        {
            "name": "Depeche.fr",
            "source_id": "8dae0a48-5dea-45f8-bd4b-1b903ec8e7a6",
            "enabled": True,
            "scraper_class": "scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper",
            "parser_class": "parsers.database_ladepeche_fr_parser.DatabaseLadepecheFrParser",
            "scraper_kwargs": {"debug": DEBUG},
        },
    ]


# Static list for backward compatibility (tests)
SCRAPER_CONFIGS = get_scraper_configs()
