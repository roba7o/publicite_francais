"""
Simple unit tests for component factory.

Tests basic component creation.
"""

import pytest
from core.component_factory import ComponentFactory


def test_factory_with_valid_config():
    """Test factory with a simple valid config."""
    factory = ComponentFactory()

    config = {
        "site": "test.fr",
        "url_collector_class": "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector",
        "soup_validator_class": "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator",
        "url_collector_kwargs": {},
        "soup_validator_kwargs": {}
    }

    # Should not raise an error
    collector = factory.create_collector(config)
    validator = factory.create_validator(config)

    assert collector is not None
    assert validator is not None