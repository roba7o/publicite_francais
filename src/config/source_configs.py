"""
Contains the full path to url_collectors/soup_validators for the database architecture.

"""


def get_scraper_configs() -> list[dict]:
    """Get list of URL collector and soup validator configurations using domain-based naming."""
    from config.settings import DEBUG

    return [
        {
            "domain": "slate.fr",  # Standardized domain identifier
            "enabled": True,
            "url_collector_class": "url_collectors.slate_fr_url_collector.SlateFrUrlCollector",
            "soup_validator_class": "soup_validators.slate_fr_soup_validator.SlateFrSoupValidator",
            "url_collector_kwargs": {"debug": DEBUG},
            "soup_validator_kwargs": {"debug": DEBUG},
        },
        {
            "domain": "franceinfo.fr",  # Standardized domain identifier
            "enabled": True,
            "url_collector_class": "url_collectors.france_info_url_collector.FranceInfoUrlCollector",
            "soup_validator_class": "soup_validators.france_info_soup_validator.FranceInfoSoupValidator",
            "url_collector_kwargs": {"debug": DEBUG},
            "soup_validator_kwargs": {"debug": DEBUG},
        },
        {
            "domain": "tf1info.fr",  # Standardized domain identifier
            "enabled": True,
            "url_collector_class": "url_collectors.tf1_info_url_collector.TF1InfoUrlCollector",
            "soup_validator_class": "soup_validators.tf1_info_soup_validator.TF1InfoSoupValidator",
            "url_collector_kwargs": {"debug": DEBUG},
            "soup_validator_kwargs": {"debug": DEBUG},
        },
        {
            "domain": "ladepeche.fr",  # Standardized domain identifier
            "enabled": True,
            "url_collector_class": "url_collectors.ladepeche_fr_url_collector.LadepecheFrUrlCollector",
            "soup_validator_class": "soup_validators.ladepeche_fr_soup_validator.LadepecheFrSoupValidator",
            "url_collector_kwargs": {"debug": DEBUG},
            "soup_validator_kwargs": {"debug": DEBUG},
        },
    ]


# Static list for backward compatibility (tests)
SCRAPER_CONFIGS = get_scraper_configs()