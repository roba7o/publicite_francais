"""
Component factory for creating scrapers and parsers from configuration.

Separates component creation concerns from orchestration logic.
"""

from core.component_loader import create_component


class ComponentFactory:
    """Factory for creating scrapers and parsers from configuration dictionaries."""

    def create_scraper(self, config: dict):
        """Create url collector from configuration."""
        class_path = config.get("url_collector_class")
        if not class_path:
            raise ValueError(
                f"No url_collector_class specified in config for source: {config['site']}"
            )

        kwargs = config.get("url_collector_kwargs", {})
        return create_component(class_path, **kwargs)

    def create_parser(self, config: dict):
        """Create soup validator from configuration."""
        class_path = config.get("soup_validator_class")
        if not class_path:
            raise ValueError(
                f"No soup_validator_class specified in config for source: {config['site']}"
            )

        # Soup validator gets site_name from config - much simpler!
        kwargs = config.get("soup_validator_kwargs", {})
        return create_component(class_path, config["site"], **kwargs)
