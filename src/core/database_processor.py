"""
Database-focused processor that stores raw article data to PostgreSQL.

This is the database equivalent of ArticleProcessor that:
- Uses your existing scrapers (unchanged)
- Uses Database parsers (extends DatabaseBaseParser)
- Stores raw data directly to database via to_database()
- NO word frequencies, NO text analysis

All text processing is moved to dbt/SQL.
"""

import time
from typing import Any, List, Tuple

from bs4 import BeautifulSoup

from config.settings import DATABASE_ENABLED, OFFLINE
from core.class_registry import get_scraper_class, get_parser_class, extract_class_name
from database import ArticleRepository
from utils.consolidated_output import ConsolidatedOutput
from utils.validators import DataValidator


class DatabaseProcessor:
    """
    Database-focused processor for raw data collection only.

    This replaces the complex ArticleProcessor with:
    - Raw data extraction only
    - Direct database storage via DatabaseBaseParser
    - No text processing pipeline
    - Uses your existing scrapers
    """

    def get_scraper_class_safe(self, class_path: str) -> Any:
        """Get scraper class from registry with error handling."""
        class_name = extract_class_name(class_path)
        scraper_class = get_scraper_class(class_name)
        if not scraper_class:
            raise ImportError(f"Scraper class not found: {class_name}")
        return scraper_class
    
    def get_parser_class_safe(self, class_path: str) -> Any:
        """Get parser class from registry with error handling."""
        class_name = extract_class_name(class_path)
        parser_class = get_parser_class(class_name)
        if not parser_class:
            raise ImportError(f"Parser class not found: {class_name}")
        return parser_class

    def __init__(self):
        """Initialize processor with database repository."""
        self.article_repo = ArticleRepository()
        self.output = ConsolidatedOutput("database_processor")
    
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
            # Use your existing scraper (unchanged)
            ScraperClass = self.get_scraper_class_safe(config["scraper_class"])
            scraper = ScraperClass(**(config.get("scraper_kwargs", {})))

            # Get source ID from database
            source_id = self.get_source_id(config["name"])
            if not source_id:
                self.output.error(f"Could not get source ID for {config['name']}",
                                 extra_data={"source": config["name"], "operation": "get_source_id"})
                return 0, 0

            # Create database parser using dynamic class loading
            database_parser = self._create_database_parser(config, source_id)
            if not database_parser:
                self.output.error(f"Could not create database parser for {config['name']}",
                                 extra_data={"source": config["name"], "operation": "create_parser"})
                return 0, 0

        except Exception as e:
            self.output.error("Component initialization failed",
                             extra_data={"source": config["name"], "error": str(e), "operation": "initialization"})
            return 0, 0

        # Get content sources (same logic as ArticleProcessor)
        sources = (
            self._get_test_sources(database_parser, config["name"])
            if OFFLINE
            else self._get_live_sources(scraper, database_parser, config["name"])
        )

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
                success = self._process_article(
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

    def _create_database_parser(self, config: dict, source_id: str):
        """Create database parser using dynamic class loading from config."""
        parser_class_path = config.get("parser_class")
        if not parser_class_path:
            self.output.error(f"No parser_class specified in config for source: {config['name']}",
                             extra_data={"source": config['name'], "operation": "create_parser"})
            return None

        try:
            # Registry-based class loading (more robust!)
            ParserClass = self.get_parser_class_safe(parser_class_path)

            # Create parser with source_id (database parsers use different signature)
            parser_kwargs = config.get("parser_kwargs", {})
            return ParserClass(source_id, **parser_kwargs)
        except Exception as e:
            self.output.error(f"Failed to create database parser {parser_class_path}: {e}",
                             extra_data={"parser_class": parser_class_path, "error": str(e), "operation": "create_parser"})
            return None

    def _get_test_sources(self, parser, source_name: str) -> List[Tuple[BeautifulSoup, str]]:
        """Get test sources for offline mode."""
        return parser.get_test_sources_from_directory(source_name)  # type: ignore

    def _get_live_sources(
        self, scraper: Any, parser, source_name: str
    ) -> List[Tuple[BeautifulSoup, str]]:
        """Get live sources (simplified - no complex concurrency for now)."""
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

    def _process_article(
        self, parser, soup: BeautifulSoup, url: str, source_name: str
    ) -> bool:
        """Process single article - database version."""
        try:
            # Parse article (no text processing)
            article_data = parser.parse_article(soup)
            if not article_data:
                return False

            # Store raw data directly to database
            return parser.to_database(article_data, url)  # type: ignore

        except Exception as e:
            self.output.error("Article processing failed",
                             extra_data={"source": source_name, "url": url, "error": str(e), "operation": "article_processing"})
            return False

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
