"""
Contains the full path to url_collectors/soup_validators for the database architecture.

"""


def get_site_configs() -> list[dict]:
    """Get list of URL collector and soup validator configurations for news sites."""
    from config.environment import DEBUG

    return [
        {
            "site": "slate.fr",  # News site identifier
            "enabled": True,
            "url_collector_class": "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector",
            "soup_validator_class": "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator",
            "url_collector_kwargs": {"debug": DEBUG},
            "soup_validator_kwargs": {"debug": DEBUG},
        },
        {
            "site": "franceinfo.fr",  # News site identifier
            "enabled": True,
            "url_collector_class": "core.components.url_collectors.france_info_url_collector.FranceInfoUrlCollector",
            "soup_validator_class": "core.components.soup_validators.france_info_soup_validator.FranceInfoSoupValidator",
            "url_collector_kwargs": {"debug": DEBUG},
            "soup_validator_kwargs": {"debug": DEBUG},
        },
        {
            "site": "tf1info.fr",  # News site identifier
            "enabled": True,
            "url_collector_class": "core.components.url_collectors.tf1_info_url_collector.TF1InfoUrlCollector",
            "soup_validator_class": "core.components.soup_validators.tf1_info_soup_validator.Tf1InfoSoupValidator",
            "url_collector_kwargs": {"debug": DEBUG},
            "soup_validator_kwargs": {"debug": DEBUG},
        },
        {
            "site": "ladepeche.fr",  # News site identifier
            "enabled": True,
            "url_collector_class": "core.components.url_collectors.ladepeche_fr_url_collector.LadepecheFrUrlCollector",
            "soup_validator_class": "core.components.soup_validators.ladepeche_fr_soup_validator.LadepecheFrSoupValidator",
            "url_collector_kwargs": {"debug": DEBUG},
            "soup_validator_kwargs": {"debug": DEBUG},
        },
    ]
