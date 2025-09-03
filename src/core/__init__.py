"""
Core module for French news scraper.

Provides orchestration and component management for the scraping pipeline.
"""

from .component_factory import ComponentFactory
from .orchestrator import ArticleOrchestrator

__all__ = [
    "ComponentFactory",
    "ArticleOrchestrator",
]
