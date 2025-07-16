SITE_CONFIGS = {
    "slate.fr": {
        "additional_stopwords": {
            "slate",
            "article",
            "lire",
            "aussi",
            "voir",
            "copyright",
        },
        "min_word_frequency": 2,
        "min_word_length": 4,
        "max_word_length": 30,
    },
    "franceinfo.fr": {
        "additional_stopwords": {
            "franceinfo", "article", "abonnés", "premium"
        },
        "min_word_frequency": 1,
        "min_word_length": 3,
        "max_word_length": 25,
    },
    "tf1info.fr": {
        "additional_stopwords": {
            "tf1",
            "info",
            "lci",
            "vidéo",
            "reportage",
            "commenter",
            "partager",
        },
        "min_word_frequency": 1,
        "min_word_length": 3,
        "max_word_length": 30,
    },
    "ladepeche.fr": {
        "additional_stopwords": {
            "ladepeche",
            "dépêche",
            "midi",
            "toulouse",
            "actualité",
            "info",
        },
        "min_word_frequency": 2,
        "min_word_length": 4,
        "max_word_length": 30,
    },
    "default": {
        "additional_stopwords": set(),
        "min_word_frequency": 2,
        "min_word_length": 3,
        "max_word_length": 50,
    },
}


def get_site_config(domain: str) -> dict:
    """
    Get text processing configuration for a specific domain.

    Args:
        domain: Domain name (e.g., 'slate.fr')

    Returns:
        Configuration dictionary for the domain, or default config if not found

    Example:
        >>> config = get_site_config('slate.fr')
        >>> min_length = config['min_word_length']
    """
    return SITE_CONFIGS.get(domain, SITE_CONFIGS["default"])


def get_all_additional_stopwords() -> set:
    """
    Get all additional stopwords from all site configurations.

    Returns:
        Set containing all site-specific stopwords combined

    Useful for getting a comprehensive list of domain-specific
    terms that should be filtered across all sources.
    """
    all_stopwords = set()
    for config in SITE_CONFIGS.values():
        all_stopwords.update(config.get("additional_stopwords", set()))
    return all_stopwords


def is_junk_filtering_enabled(domain: str) -> bool:
    """
    Check if junk word filtering is enabled for a domain.

    Args:
        domain: Domain name to check

    Returns:
        True if junk filtering is enabled, False otherwise
    """
    config = get_site_config(domain)
    return config.get("enable_junk_filtering", True)


# Export for backward compatibility
__all__ = [
    "SITE_CONFIGS",
    "get_site_config",
    "get_all_additional_stopwords",
    "is_junk_filtering_enabled",
]
