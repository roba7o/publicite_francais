"""
Component factory for creating scrapers and parsers from configuration.

Separates component creation concerns from orchestration logic.
"""

from typing import Any

from core.component_loader import create_component


class ComponentFactory:
    """Factory for creating scrapers and parsers from configuration dictionaries."""

    def create_scraper(self, config: dict) -> Any:
        """Create scraper from configuration."""
        class_path = config.get("scraper_class")
        if not class_path:
            raise ValueError(
                f"No scraper_class specified in config for source: {config['name']}"
            )

        kwargs = config.get("scraper_kwargs", {})
        return create_component(class_path, **kwargs)

    def create_parser(self, config: dict) -> Any:
        """Create database parser from configuration."""
        class_path = config.get("parser_class")
        if not class_path:
            raise ValueError(
                f"No parser_class specified in config for source: {config['name']}"
            )

        # Parser gets source_name from config - much simpler!
        kwargs = config.get("parser_kwargs", {})
        return create_component(class_path, config["domain"], **kwargs)
