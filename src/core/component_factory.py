"""
Component factory for creating scrapers and parsers from configuration.

Separates component creation concerns from orchestration logic.
"""

from typing import Any, Optional

from core.component_loader import create_component


class ComponentFactory:
    """Factory for creating scrapers and parsers from configuration dictionaries."""
    
    def create_scraper(self, config: dict) -> Any:
        """Create scraper from configuration."""
        return create_component(
            config["scraper_class"], 
            **(config.get("scraper_kwargs", {}))
        )
    
    def create_parser(self, config: dict, source_id: str) -> Optional[Any]:
        """Create database parser from configuration.""" 
        parser_class_path = config.get("parser_class")
        if not parser_class_path:
            raise ValueError(f"No parser_class specified in config for source: {config['name']}")

        try:
            parser_kwargs = config.get("parser_kwargs", {})
            return create_component(parser_class_path, source_id, **parser_kwargs)
        except ImportError as e:
            raise ImportError(f"Failed to create database parser {parser_class_path}: {e}") from e