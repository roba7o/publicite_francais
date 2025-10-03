"""
Unit tests for component factory - testing real dynamic class loading.

Tests actual component creation, error handling, and class import functionality.
"""

import pytest
from core.component_factory import ComponentFactory
from core.components.url_collectors.slate_fr_url_collector import SlateFrUrlCollector
from core.components.soup_validators.slate_fr_soup_validator import SlateFrSoupValidator


class TestComponentFactory:
    """Test ComponentFactory dynamic loading capabilities."""

    def test_create_real_collector_from_config(self):
        """Test creating real URL collector from configuration."""
        factory = ComponentFactory()

        config = {
            "site": "slate.fr",
            "url_collector_class": "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector",
            "url_collector_kwargs": {}
        }

        collector = factory.create_collector(config)

        # Verify it's the correct type and has expected methods
        assert isinstance(collector, SlateFrUrlCollector)
        assert hasattr(collector, 'get_article_urls')
        assert callable(collector.get_article_urls)

    def test_create_real_validator_from_config(self):
        """Test creating real soup validator from configuration."""
        factory = ComponentFactory()

        config = {
            "site": "slate.fr",
            "soup_validator_class": "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator",
            "soup_validator_kwargs": {}
        }

        validator = factory.create_validator(config)

        # Verify it's the correct type and has expected methods
        assert isinstance(validator, SlateFrSoupValidator)
        assert hasattr(validator, 'validate_and_extract')
        assert hasattr(validator, 'get_soup_from_url')
        assert callable(validator.validate_and_extract)

    def test_create_all_real_collectors(self):
        """Test creating all actual collector types used in the system."""
        factory = ComponentFactory()

        collector_configs = [
            {
                "site": "slate.fr",
                "url_collector_class": "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector",
                "url_collector_kwargs": {}
            },
            {
                "site": "franceinfo.fr",
                "url_collector_class": "core.components.url_collectors.france_info_url_collector.FranceInfoUrlCollector",
                "url_collector_kwargs": {}
            },
            {
                "site": "tf1info.fr",
                "url_collector_class": "core.components.url_collectors.tf1_info_url_collector.TF1InfoUrlCollector",
                "url_collector_kwargs": {}
            },
            {
                "site": "ladepeche.fr",
                "url_collector_class": "core.components.url_collectors.ladepeche_fr_url_collector.LadepecheFrUrlCollector",
                "url_collector_kwargs": {}
            }
        ]

        for config in collector_configs:
            collector = factory.create_collector(config)
            assert collector is not None
            assert hasattr(collector, 'get_article_urls')

    def test_create_all_real_validators(self):
        """Test creating all actual validator types used in the system."""
        factory = ComponentFactory()

        validator_configs = [
            {
                "site": "slate.fr",
                "soup_validator_class": "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator",
                "soup_validator_kwargs": {}
            },
            {
                "site": "franceinfo.fr",
                "soup_validator_class": "core.components.soup_validators.france_info_soup_validator.FranceInfoSoupValidator",
                "soup_validator_kwargs": {}
            },
            {
                "site": "tf1info.fr",
                "soup_validator_class": "core.components.soup_validators.tf1_info_soup_validator.Tf1InfoSoupValidator",
                "soup_validator_kwargs": {}
            },
            {
                "site": "ladepeche.fr",
                "soup_validator_class": "core.components.soup_validators.ladepeche_fr_soup_validator.LadepecheFrSoupValidator",
                "soup_validator_kwargs": {}
            }
        ]

        for config in validator_configs:
            validator = factory.create_validator(config)
            assert validator is not None
            assert hasattr(validator, 'validate_and_extract')

    def test_missing_collector_class_error(self):
        """Test error handling when collector class is missing from config."""
        factory = ComponentFactory()

        config = {
            "site": "test.fr",
            # Missing url_collector_class
            "url_collector_kwargs": {}
        }

        with pytest.raises(ValueError, match="No url_collector_class specified"):
            factory.create_collector(config)

    def test_missing_validator_class_error(self):
        """Test error handling when validator class is missing from config."""
        factory = ComponentFactory()

        config = {
            "site": "test.fr",
            # Missing soup_validator_class
            "soup_validator_kwargs": {}
        }

        with pytest.raises(ValueError, match="No soup_validator_class specified"):
            factory.create_validator(config)

    def test_invalid_collector_class_path(self):
        """Test error handling for invalid collector class path."""
        factory = ComponentFactory()

        config = {
            "site": "test.fr",
            "url_collector_class": "nonexistent.module.NonexistentClass",
            "url_collector_kwargs": {}
        }

        with pytest.raises(ImportError):
            factory.create_collector(config)

    def test_invalid_validator_class_path(self):
        """Test error handling for invalid validator class path."""
        factory = ComponentFactory()

        config = {
            "site": "test.fr",
            "soup_validator_class": "nonexistent.module.NonexistentClass",
            "soup_validator_kwargs": {}
        }

        with pytest.raises(ImportError):
            factory.create_validator(config)

    def test_malformed_class_path_no_dots(self):
        """Test error handling for malformed class path without dots."""
        factory = ComponentFactory()

        with pytest.raises(ImportError, match="Invalid class path.*Expected format"):
            factory.import_class("JustAClassName")

    def test_class_exists_but_wrong_name(self):
        """Test error handling when module exists but class name is wrong."""
        factory = ComponentFactory()

        config = {
            "site": "test.fr",
            "url_collector_class": "core.components.url_collectors.slate_fr_url_collector.WrongClassName",
            "url_collector_kwargs": {}
        }

        with pytest.raises(ImportError):
            factory.create_collector(config)


class TestComponentFactoryHelperMethods:
    """Test ComponentFactory static helper methods."""

    def test_import_class_direct(self):
        """Test direct class import functionality."""
        class_path = "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector"

        imported_class = ComponentFactory.import_class(class_path)

        assert imported_class == SlateFrUrlCollector
        assert callable(imported_class)

    def test_create_component_direct(self):
        """Test direct component creation with arguments."""
        class_path = "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator"
        site_name = "test.fr"

        component = ComponentFactory.create_component(class_path, site_name)

        assert isinstance(component, SlateFrSoupValidator)
        assert hasattr(component, 'validate_and_extract')

    def test_create_component_with_kwargs(self):
        """Test component creation with keyword arguments."""
        class_path = "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector"

        # URL collectors don't currently take kwargs, but test the mechanism
        component = ComponentFactory.create_component(class_path)

        assert isinstance(component, SlateFrUrlCollector)

    def test_import_builtin_class(self):
        """Test importing built-in Python classes."""
        imported_class = ComponentFactory.import_class("collections.defaultdict")

        from collections import defaultdict
        assert imported_class == defaultdict

    def test_import_class_error_propagation(self):
        """Test that import errors are properly propagated."""
        with pytest.raises(ImportError, match="Failed to import"):
            ComponentFactory.import_class("completely.fake.module.FakeClass")


def test_factory_integration_with_real_site_config():
    """Test factory with realistic site configuration structure."""
    factory = ComponentFactory()

    # Simulate real site config structure
    slate_config = {
        "site": "slate.fr",
        "base_url": "https://www.slate.fr",
        "enabled": True,
        "url_collector_class": "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector",
        "soup_validator_class": "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator",
        "url_collector_kwargs": {},
        "soup_validator_kwargs": {}
    }

    # Should create both components successfully
    collector = factory.create_collector(slate_config)
    validator = factory.create_validator(slate_config)

    # Verify they're working instances
    assert hasattr(collector, 'get_article_urls')
    assert hasattr(validator, 'validate_and_extract')

    # Verify site name is passed correctly to validator
    assert hasattr(validator, 'site_name') or hasattr(validator, 'domain')


def test_factory_handles_missing_kwargs_gracefully():
    """Test factory handles missing kwargs dictionaries gracefully."""
    factory = ComponentFactory()

    # Config without explicit kwargs
    config = {
        "site": "slate.fr",
        "url_collector_class": "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector",
        "soup_validator_class": "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator"
        # No kwargs specified
    }

    # Should work with default empty kwargs
    collector = factory.create_collector(config)
    validator = factory.create_validator(config)

    assert collector is not None
    assert validator is not None
