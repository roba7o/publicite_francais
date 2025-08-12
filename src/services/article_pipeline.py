"""
Database-focused processor that stores raw article data to PostgreSQL.

Simplified processor that handles:
- Scraper/parser creation
- Content acquisition (live/offline)
- Article processing and storage
- Database operations

All text processing is moved to dbt/SQL.
"""

import time
from typing import Any, List, Tuple
from bs4 import BeautifulSoup

from config.settings import DATABASE_ENABLED, OFFLINE
from utils.validators import DataValidator


class DatabaseProcessor:
    """
    Database pipeline orchestrator focused on processing workflow.
    
    Orchestrates the complete pipeline: content acquisition → article processing → storage.
    Uses ComponentFactory for component creation to maintain single responsibility.
    """

    def __init__(self):
        """Initialize processor with default dependencies."""
        from database import ArticleRepository
        from utils.terminal_output import output
        from core.component_factory import ComponentFactory
        
        self.article_repo = ArticleRepository()
        self.output = output
        self.component_factory = ComponentFactory()

    def acquire_content(self, scraper: Any, parser: Any, source_name: str) -> List[Tuple[BeautifulSoup, str]]:
        """Get content sources based on mode (offline/live)."""
        if OFFLINE:
            return parser.get_test_sources_from_directory(source_name)
        else:
            return self._get_live_sources(scraper, parser, source_name)
    
    def _get_live_sources(self, scraper: Any, parser: Any, source_name: str) -> List[Tuple[BeautifulSoup, str]]:
        """Get live sources from web scraping."""
        urls = scraper.get_article_urls()
        if not urls:
            self.output.warning("URL discovery returned no results", 
                               extra_data={"source": source_name, "operation": "url_discovery"})
            return []

        sources = []

        # Process first 5 URLs for testing (can expand later)
        for url in urls[:5]:
            try:
                validated_url = DataValidator.validate_url(url)
                if not validated_url:
                    continue

                soup = parser.get_soup_from_url(validated_url)
                if soup:
                    sources.append((soup, validated_url))

            except Exception as e:
                self.output.warning("URL processing error",
                                   extra_data={"url": url, "source": source_name, "error": str(e), "operation": "url_processing"})
                continue

        return sources

    def process_article(self, parser, soup: BeautifulSoup, url: str, source_name: str) -> bool:
        """Process single article - parse and store to database."""
        try:
            # Parse article (no text processing)
            article_data = parser.parse_article(soup)
            if not article_data:
                return False

            # Store raw data directly to database
            return parser.to_database(article_data, url)

        except Exception as e:
            self.output.error("Article processing failed",
                             extra_data={"source": source_name, "url": url, "error": str(e), "operation": "article_processing"})
            return False

    def get_source_id(self, source_name: str) -> str:
        """Get source ID from database."""
        source_id = self.article_repo.get_source_id(source_name)
        if not source_id:
            self.output.error(f"Source not found in database: {source_name}",
                             extra_data={"source_name": source_name, "operation": "get_source_id"})
            return ""
        return source_id

    def process_source(self, config: dict) -> Tuple[int, int]:
        """
        Process a single source - database version.

        Uses your existing scraper but Database parser + database storage.
        """
        if not config.get("enabled", True):
            self.output.info("Source processing skipped - disabled",
                            extra_data={"source": config["name"], "reason": "disabled"})
            return 0, 0

        if not DATABASE_ENABLED:
            self.output.warning("Database not enabled - skipping source",
                               extra_data={"source": config["name"], "database_enabled": False})
            return 0, 0

        self.output.process_start(f"source_processing_{config['name']}", 
                                 extra_data={
                                     "source": config["name"],
                                     "scraper_class": config["scraper_class"],
                                 })
        start_time = time.time()

        try:
            # Create scraper
            scraper = self.component_factory.create_scraper(config)

            # Get source ID from database
            source_id = self.get_source_id(config["name"])
            if not source_id:
                return 0, 0

            # Create database parser
            database_parser = self.component_factory.create_parser(config, source_id)

        except (ValueError, ImportError) as e:
            self.output.error("Component initialization failed",
                             extra_data={"source": config["name"], "error": str(e), "operation": "initialization"})
            return 0, 0
        except Exception as e:
            self.output.error("Unexpected error during component initialization",
                             extra_data={"source": config["name"], "error": str(e), "operation": "initialization"})
            return 0, 0

        # Acquire content sources  
        sources = self.acquire_content(scraper, database_parser, config["name"])

        mode_str = 'offline' if OFFLINE else 'live'
        self.output.info(f"Found {len(sources)} sources for {config['name']} (mode: {mode_str})",
                        extra_data={"source": config["name"], "sources_found": len(sources), "mode": mode_str})

        if not sources:
            self.output.warning("No content sources found",
                               extra_data={"source": config["name"], "mode": mode_str, "sources_count": 0})
            return 0, 0

        processed_count = 0
        total_attempted = len(sources)

        # Process each article for database storage
        for soup, source_identifier in sources:
            if soup:
                success = self.process_article(
                    database_parser, soup, source_identifier, config["name"]
                )
                if success:
                    processed_count += 1

        elapsed_time = time.time() - start_time
        success_rate = (
            (processed_count / total_attempted * 100) if total_attempted > 0 else 0
        )

        # Complete source processing with consolidated output
        self.output.process_complete(f"source_processing_{config['name']}", 
                                    extra_data={
                                        "source": config["name"],
                                        "articles_stored": processed_count,
                                        "articles_attempted": total_attempted,
                                        "success_rate_percent": round(success_rate, 1),
                                        "processing_time_seconds": round(elapsed_time, 2),
                                    })

        self.output.success(f"Source '{config['name']}' processing completed",
                           extra_data={"source": config["name"], "status": "completed"})

        return processed_count, total_attempted


    def process_all_sources(self, source_configs: List[dict]) -> Tuple[int, int]:
        """
        Process all sources - database version.
        """
        total_processed = 0
        total_attempted = 0

        enabled_sources = [
            config for config in source_configs if config.get("enabled", True)
        ]

        mode_str = "offline" if OFFLINE else "live"
        self.output.process_start("database_processing", 
                                 extra_data={
                                     "total_sources": len(source_configs),
                                     "enabled_sources": len(enabled_sources),
                                     "database_enabled": DATABASE_ENABLED,
                                     "mode": mode_str,
                                 })

        # Process sources sequentially for now (simpler)
        for config in enabled_sources:
            processed, attempted = self.process_source(config)
            total_processed += processed
            total_attempted += attempted

        success_rate = (
            (total_processed / total_attempted * 100) if total_attempted > 0 else 0
        )
        
        # Display completion summary with consolidated output
        self.output.completion_summary(
            "Database Processing Complete",
            {
                "Articles Stored": total_processed,
                "Articles Attempted": total_attempted,
                "Success Rate": f"{round(success_rate, 1)}%",
            },
            extra_data={
                "total_articles_stored": total_processed,
                "total_articles_attempted": total_attempted,
                "success_rate_percent": round(success_rate, 1),
                "processing_complete": True
            }
        )

        self.output.process_complete("database_processing",
                                   extra_data={
                                       "total_articles_stored": total_processed,
                                       "total_articles_attempted": total_attempted,
                                       "success_rate_percent": round(success_rate, 1),
                                   })

        return total_processed, total_attempted
