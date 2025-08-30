"""
Component Integration Tests.

Tests how different components work together: ComponentFactory, URL Collectors,
Soup Validators, and the ArticleOrchestrator. These tests verify that the
component architecture works correctly end-to-end.
"""

import pytest

from config.site_configs import SCRAPER_CONFIGS
from core.component_factory import ComponentFactory
from core.orchestrator import ArticleOrchestrator
from database.models import RawArticle


class TestComponentFactory:
    """Test ComponentFactory integration with actual configurations."""

    def test_component_factory_creates_all_collectors(self):
        """Test that ComponentFactory can create all configured URL collectors."""
        factory = ComponentFactory()

        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                collector = factory.create_collector(config)
                assert collector is not None, (
                    f"Should create collector for {config['site']}"
                )
                assert hasattr(collector, "get_article_urls"), (
                    "Collector should have get_article_urls method"
                )

    def test_component_factory_creates_all_validators(self):
        """Test that ComponentFactory can create all configured soup validators."""
        factory = ComponentFactory()

        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                validator = factory.create_validator(config)
                assert validator is not None, (
                    f"Should create validator for {config['site']}"
                )
                assert hasattr(validator, "validate_and_extract"), (
                    "Validator should have validate_and_extract method"
                )

    def test_component_factory_handles_invalid_config(self):
        """Test that ComponentFactory handles invalid configurations gracefully."""
        factory = ComponentFactory()

        # Test missing url_collector_class
        invalid_config = {
            "site": "invalid.test",
            "enabled": True,
            "soup_validator_class": "some.valid.Class",
        }

        with pytest.raises(ValueError, match="No url_collector_class specified"):
            factory.create_collector(invalid_config)

        # Test missing soup_validator_class
        invalid_config2 = {
            "site": "invalid.test",
            "enabled": True,
            "url_collector_class": "some.valid.Class",
        }

        with pytest.raises(ValueError, match="No soup_validator_class specified"):
            factory.create_validator(invalid_config2)


class TestCollectorValidatorIntegration:
    """Test integration between URL collectors and soup validators."""

    def test_collector_validator_pairing(self):
        """Test that each collector has a matching validator."""
        factory = ComponentFactory()

        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                # Both should be creatable
                collector = factory.create_collector(config)
                validator = factory.create_validator(config)

                assert collector is not None
                assert validator is not None

                # Validator should be configured for the same site
                # Note: Validator site_domain should match the config site
                assert validator.site_domain == config["site"], (
                    f"Validator domain should match config site for {config['site']}"
                )

    def test_validator_processes_real_content(self, test_html_files):
        """Test that validators can process content from their corresponding HTML files."""
        factory = ComponentFactory()

        # Map config sites to test file sources
        site_to_test_mapping = {
            "slate.fr": "slate.fr",
            "franceinfo.fr": "franceinfo.fr",
            "tf1info.fr": "tf1info.fr",
            "ladepeche.fr": "ladepeche.fr",
        }

        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True) and config["site"] in site_to_test_mapping:
                validator = factory.create_validator(config)
                test_source = site_to_test_mapping[config["site"]]

                if test_source in test_html_files and test_html_files[test_source]:
                    # Test with first available HTML file
                    test_file = test_html_files[test_source][0]
                    html_content = test_file.read_text(encoding="utf-8")

                    # Parse and validate
                    soup = validator.parse_html_fast(html_content)
                    test_url = f"https://{config['site']}/test-article"
                    result = validator.validate_and_extract(soup, test_url)

                    # Should either return RawArticle or None (both are valid)
                    if result is not None:
                        assert isinstance(result, RawArticle), (
                            f"Validator for {config['site']} should return RawArticle"
                        )
                        assert result.raw_html is not None
                        assert result.site is not None


class TestOrchestratorIntegration:
    """Test ArticleOrchestrator integration with components."""

    def test_orchestrator_uses_component_factory(self):
        """Test that orchestrator properly uses ComponentFactory."""
        orchestrator = ArticleOrchestrator()
        assert hasattr(orchestrator, "component_factory")
        assert orchestrator.component_factory is not None

    def test_orchestrator_processes_enabled_sources(self, clean_test_database):
        """Test that orchestrator processes all enabled sources."""
        orchestrator = ArticleOrchestrator()
        processed_sources = []

        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                processed, attempted = orchestrator.process_site(config)
                if attempted > 0:  # Only count sources that had content to process
                    processed_sources.append(config["site"])

        # Should process multiple sources
        assert len(processed_sources) > 0, (
            "Should process at least some enabled sources"
        )

        # All enabled sources should be attempted (in test mode)
        enabled_sources = [
            config["site"] for config in SCRAPER_CONFIGS if config.get("enabled", True)
        ]
        for source in enabled_sources:
            assert source in processed_sources, (
                f"Should have processed enabled source: {source}"
            )

    def test_orchestrator_handles_disabled_sources(self):
        """Test that orchestrator properly skips disabled sources."""
        orchestrator = ArticleOrchestrator()

        # Create a disabled config
        disabled_config = {
            "site": "disabled.test",
            "enabled": False,
            "url_collector_class": "core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector",
            "soup_validator_class": "core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator",
            "url_collector_kwargs": {"debug": True},
            "soup_validator_kwargs": {"debug": True},
        }

        processed, attempted = orchestrator.process_site(disabled_config)
        assert processed == 0, "Disabled sources should not process any articles"
        assert attempted == 0, "Disabled sources should not attempt any processing"


class TestEndToEndFlow:
    """Test complete end-to-end component flow."""

    def test_complete_processing_flow(self, clean_test_database):
        """Test the complete flow from configuration to database storage."""
        orchestrator = ArticleOrchestrator()

        # Process one enabled source completely
        test_config = None
        for config in SCRAPER_CONFIGS:
            if config.get("enabled", True):
                test_config = config
                break

        assert test_config is not None, (
            "Should have at least one enabled config for testing"
        )

        # Process the source
        processed, attempted = orchestrator.process_site(test_config)

        if attempted > 0:  # Only verify if we had content to process
            # Should have processed some articles
            assert processed >= 0, "Should have non-negative processed count"
            assert attempted >= processed, "Attempted should be >= processed"

            # Check database storage
            from sqlalchemy import text

            from config.environment import get_news_data_schema
            from database.database import get_session

            with get_session() as session:
                schema = get_news_data_schema()
                count = session.execute(
                    text(
                        f"SELECT COUNT(*) FROM {schema}.raw_articles WHERE site = :site"
                    ),
                    {"site": test_config["site"]},
                ).scalar()

                assert count == processed, (
                    f"Database should have {processed} articles for {test_config['site']}"
                )

    def test_error_handling_in_pipeline(self):
        """Test that pipeline handles errors gracefully."""
        orchestrator = ArticleOrchestrator()

        # Create config with invalid class path
        invalid_config = {
            "site": "error.test",
            "enabled": True,
            "url_collector_class": "non.existent.Class",
            "soup_validator_class": "also.non.existent.Class",
            "url_collector_kwargs": {},
            "soup_validator_kwargs": {},
        }

        # Should handle errors gracefully (return 0, 0)
        processed, attempted = orchestrator.process_site(invalid_config)
        assert processed == 0, "Invalid config should result in 0 processed"
        assert attempted == 0, "Invalid config should result in 0 attempted"
