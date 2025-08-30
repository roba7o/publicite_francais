"""
Component factory for creating scrapers and parsers from configuration.

Separates component creation concerns from orchestration logic.
"""

import importlib


class ComponentFactory:
    """Factory for creating scrapers and parsers from configuration dictionaries."""

    # -----helper functions----

    # Both seperated to allow importing without instantiation
    # (e.g. for testing)

    @staticmethod
    def import_class(class_path: str):
        if "." not in class_path:
            raise ImportError(
                f"Invalid class path: {class_path}. Expected format: 'module.class'"
            )
        module_path, class_name = class_path.rsplit(".", 1)
        try:
            module = importlib.import_module(module_path)  # loads module into memory
            return getattr(module, class_name)  # returns class object
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Failed to import {class_path}: {e}") from e

    @staticmethod
    def create_component(class_path: str, *args, **kwargs):
        """
        Create component from the full class path definined in site_configs.py

        Args:
            class_path: Full module path
            *args: Positional arguments for component constructor (not used currently
            as we have config as dictionary -> may used in future)
            **kwargs: Keyword arguments for component constructor

        Returns:
            Component instance
        """
        component_class = ComponentFactory.import_class(class_path)  # get class
        return component_class(*args, **kwargs)  # Calls constructor (__init__)

    def create_scraper(self, config: dict):
        """Create url collector from configuration."""
        class_path = config.get("url_collector_class")
        if not class_path:
            raise ValueError(
                f"No url_collector_class specified in config for source: {config['site']}"
            )

        kwargs = config.get("url_collector_kwargs", {})
        return self.create_component(class_path, **kwargs)

    def create_parser(self, config: dict):
        """Create soup validator from configuration."""
        class_path = config.get("soup_validator_class")
        if not class_path:
            raise ValueError(
                f"No soup_validator_class specified in config for source: {config['site']}"
            )

        # Soup validator gets site_name from config - much simpler!
        kwargs = config.get("soup_validator_kwargs", {})
        return self.create_component(class_path, config["site"], **kwargs)
