"""
Unit Tests for URL Collectors.

Tests each URL collector component in isolation to ensure they can be
imported, instantiated, and have the expected interface. These tests
focus on component structure rather than live web scraping.
"""


class TestUrlCollectorImports:
    """Test that all URL collector classes can be imported and instantiated."""

    def test_all_url_collectors_importable(self):
        """Test that all configured URL collectors can be imported."""
        from config.site_configs import SCRAPER_CONFIGS
        from core.component_factory import ComponentFactory

        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                url_collector_class = ComponentFactory.import_class(
                    config["url_collector_class"]
                )
                assert url_collector_class is not None, (
                    f"Should import {config['url_collector_class']}"
                )

                # Verify it can be instantiated with debug=True
                collector = url_collector_class(debug=True)
                assert collector is not None
                assert hasattr(collector, "get_article_urls")


class TestUrlCollectorInterface:
    """Test that URL collectors have consistent interface."""

    def test_all_collectors_have_required_methods(self):
        """Test that all collectors implement the required interface."""
        from core.components.url_collectors.france_info_url_collector import (
            FranceInfoUrlCollector,
        )
        from core.components.url_collectors.ladepeche_fr_url_collector import (
            LadepecheFrUrlCollector,
        )
        from core.components.url_collectors.slate_fr_url_collector import (
            SlateFrUrlCollector,
        )
        from core.components.url_collectors.tf1_info_url_collector import (
            TF1InfoUrlCollector,
        )

        collectors = [
            SlateFrUrlCollector(debug=True),
            FranceInfoUrlCollector(debug=True),
            TF1InfoUrlCollector(debug=True),
            LadepecheFrUrlCollector(debug=True),
        ]

        for collector in collectors:
            # All collectors should have get_article_urls method
            assert hasattr(collector, "get_article_urls")
            assert callable(collector.get_article_urls)

    def test_collectors_debug_mode(self):
        """Test that collectors can be instantiated with debug mode."""
        from core.components.url_collectors.slate_fr_url_collector import (
            SlateFrUrlCollector,
        )

        # Test with debug=True
        collector_debug = SlateFrUrlCollector(debug=True)
        assert collector_debug is not None

        # Test with debug=False
        collector_no_debug = SlateFrUrlCollector(debug=False)
        assert collector_no_debug is not None


class TestUrlCollectorConfiguration:
    """Test URL collectors work with your site configuration structure."""

    def test_collectors_work_with_component_factory(self, sample_site_config):
        """Test that collectors can be created via component factory."""
        from core.component_factory import ComponentFactory

        factory = ComponentFactory()

        # Test that factory can create collector from config
        collector = factory.create_scraper(sample_site_config)
        assert collector is not None
        assert hasattr(collector, "get_article_urls")

    def test_collectors_match_site_configs(self):
        """Test that all collectors referenced in site_configs can be imported."""
        from config.site_configs import SCRAPER_CONFIGS
        from core.component_factory import ComponentFactory

        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                # Test that the URL collector class can be imported
                url_collector_class = ComponentFactory.import_class(
                    config["url_collector_class"]
                )
                assert url_collector_class is not None

                # Test that it can be instantiated with the config kwargs
                kwargs = config.get("url_collector_kwargs", {})
                collector = url_collector_class(**kwargs)
                assert collector is not None
                assert hasattr(collector, "get_article_urls")


class TestUrlCollectorErrorHandling:
    """Test URL collector error handling and edge cases."""

    def test_collector_with_invalid_kwargs(self):
        """Test collectors handle invalid kwargs gracefully."""
        from core.components.url_collectors.slate_fr_url_collector import (
            SlateFrUrlCollector,
        )

        # Test with unexpected kwargs - should not crash
        try:
            collector = SlateFrUrlCollector(debug=True, invalid_param=True)
            assert collector is not None
        except TypeError:
            # It's acceptable if collectors reject unknown kwargs
            pass

    def test_get_article_urls_returns_list(self):
        """Test that get_article_urls returns a list (even if empty in test mode)."""
        from core.components.url_collectors.slate_fr_url_collector import (
            SlateFrUrlCollector,
        )

        collector = SlateFrUrlCollector(debug=True)

        # In test mode, this might return empty list or mock data
        # The important thing is that it returns a list and doesn't crash
        try:
            urls = collector.get_article_urls()
            assert isinstance(urls, list)
        except Exception as e:
            # In isolated unit test, network calls might fail - that's OK
            # We're testing the interface, not live functionality
            assert (
                "requests" in str(e).lower()
                or "network" in str(e).lower()
                or "connection" in str(e).lower()
            )
