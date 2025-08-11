"""
Database-focused processor that stores raw article data to PostgreSQL.

This is the database equivalent of ArticleProcessor that:
- Uses your existing scrapers (unchanged)
- Uses Database parsers (extends DatabaseBaseParser)
- Stores raw data directly to database via to_database()
- NO word frequencies, NO text analysis

All text processing is moved to dbt/SQL.
"""

import importlib
import time
from typing import Any, List, Tuple, Type

from bs4 import BeautifulSoup

from config.settings import DATABASE_ENABLED, OFFLINE, DATABASE_ENV
from database import get_database_manager
from utils.structured_logger import get_structured_logger
from utils.validators import DataValidator

logger = get_structured_logger(__name__)


class DatabaseProcessor:
    """
    Database-focused processor for raw data collection only.

    This replaces the complex ArticleProcessor with:
    - Raw data extraction only
    - Direct database storage via DatabaseBaseParser
    - No text processing pipeline
    - Uses your existing scrapers
    """

    @staticmethod
    def import_class(class_path: str) -> Type[Any]:
        """Import class from string path (same as ArticleProcessor)."""
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls  # type: ignore

    @classmethod
    def get_source_id(cls, source_name: str) -> str:
        """Get source ID from database."""
        db = get_database_manager()
        # Use appropriate schema based on environment
        schema_name = f"news_data_{DATABASE_ENV}"
        try:
            with db.get_session() as session:
                from sqlalchemy import text

                result = session.execute(
                    text(f"""
                    SELECT id FROM {schema_name}.news_sources
                    WHERE name = :name
                """),
                    {"name": source_name},
                )

                row = result.fetchone()
                if row:
                    return str(row[0])
                else:
                    logger.error(f"Source not found in database: {source_name}")
                    return ""

        except Exception as e:
            logger.error(f"Failed to get source ID: {e}")
            return ""

    @classmethod
    def process_source(cls, config: dict) -> Tuple[int, int]:
        """
        Process a single source - database version.

        Uses your existing scraper but Database parser + database storage.
        """
        if not config.get("enabled", True):
            logger.info(
                "Source processing skipped",
                extra_data={"source": config["name"], "reason": "disabled"},
            )
            return 0, 0

        if not DATABASE_ENABLED:
            logger.warning(
                "Database not enabled - skipping source",
                extra_data={"source": config["name"]},
            )
            return 0, 0

        logger.info(
            "Starting database source processing",
            extra_data={
                "source": config["name"],
                "scraper_class": config["scraper_class"],
            },
        )
        start_time = time.time()

        try:
            # Use your existing scraper (unchanged)
            ScraperClass = cls.import_class(config["scraper_class"])
            scraper = ScraperClass(**(config.get("scraper_kwargs", {})))

            # Get source ID from database
            source_id = cls.get_source_id(config["name"])
            if not source_id:
                logger.error(f"Could not get source ID for {config['name']}")
                return 0, 0

            # Create database parser using dynamic class loading
            database_parser = cls._create_database_parser(config, source_id)
            if not database_parser:
                logger.error(f"Could not create database parser for {config['name']}")
                return 0, 0

        except Exception as e:
            logger.error(
                "Component initialization failed",
                extra_data={"source": config["name"], "error": str(e)},
                exc_info=True,
            )
            return 0, 0

        # Get content sources (same logic as ArticleProcessor)
        sources = (
            cls._get_test_sources(database_parser, config["name"])
            if OFFLINE
            else cls._get_live_sources(scraper, database_parser, config["name"])
        )

        logger.info(
            f"Found {len(sources)} sources for {config['name']} (mode: {'offline' if OFFLINE else 'live'})"
        )

        if not sources:
            logger.warning(
                "No content sources found",
                extra_data={
                    "source": config["name"],
                    "mode": "offline" if OFFLINE else "live",
                },
            )
            return 0, 0

        processed_count = 0
        total_attempted = len(sources)

        # Process each article for database storage
        for soup, source_identifier in sources:
            if soup:
                success = cls._process_article(
                    database_parser, soup, source_identifier, config["name"]
                )
                if success:
                    processed_count += 1

        elapsed_time = time.time() - start_time
        success_rate = (
            (processed_count / total_attempted * 100) if total_attempted > 0 else 0
        )

        # Clean completion message  
        from utils.cli_output import success
        success(f"Source '{config['name']}' processing completed")
        
        logger.info(
            "Database source processing completed",
            extra_data={
                "source": config["name"],
                "articles_stored": processed_count,
                "articles_attempted": total_attempted,
                "success_rate_percent": round(success_rate, 1),
                "processing_time_seconds": round(elapsed_time, 2),
            },
        )

        return processed_count, total_attempted

    @classmethod
    def _create_database_parser(cls, config: dict, source_id: str):
        """Create database parser using dynamic class loading from config."""
        parser_class_path = config.get("parser_class")
        if not parser_class_path:
            logger.error(f"No parser_class specified in config for source: {config['name']}")
            return None

        try:
            # Dynamic class loading (like your old system!)
            ParserClass = cls.import_class(parser_class_path)
            
            # Create parser with source_id (database parsers use different signature)
            parser_kwargs = config.get("parser_kwargs", {})
            return ParserClass(source_id, **parser_kwargs)
        except Exception as e:
            logger.error(f"Failed to create database parser {parser_class_path}: {e}")
            return None

    @staticmethod
    def _get_test_sources(parser, source_name: str) -> List[Tuple[BeautifulSoup, str]]:
        """Get test sources for offline mode."""
        return parser.get_test_sources_from_directory(source_name)  # type: ignore

    @staticmethod
    def _get_live_sources(
        scraper: Any, parser, source_name: str
    ) -> List[Tuple[BeautifulSoup, str]]:
        """Get live sources (simplified - no complex concurrency for now)."""
        urls = scraper.get_article_urls()
        if not urls:
            logger.warning(
                "URL discovery returned no results", extra_data={"source": source_name}
            )
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
                logger.warning(
                    "URL processing error",
                    extra_data={"url": url, "source": source_name, "error": str(e)},
                )
                continue

        return sources

    @staticmethod
    def _process_article(
        parser, soup: BeautifulSoup, url: str, source_name: str
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
            logger.error(
                "Article processing failed",
                extra_data={"source": source_name, "url": url, "error": str(e)},
                exc_info=True,
            )
            return False

    @classmethod
    def process_all_sources(cls, source_configs: List[dict]) -> Tuple[int, int]:
        """
        Process all sources - database version.
        """
        total_processed = 0
        total_attempted = 0

        enabled_sources = [
            config for config in source_configs if config.get("enabled", True)
        ]

        logger.info(
            "Starting database processing",
            extra_data={
                "total_sources": len(source_configs),
                "enabled_sources": len(enabled_sources),
                "database_enabled": DATABASE_ENABLED,
                "mode": "offline" if OFFLINE else "live",
            },
        )

        # Process sources sequentially for now (simpler)
        for config in enabled_sources:
            processed, attempted = cls.process_source(config)
            total_processed += processed
            total_attempted += attempted

        success_rate = (
            (total_processed / total_attempted * 100) if total_attempted > 0 else 0
        )
        # Clean completion summary using CLI package
        from utils.cli_output import completion_summary
        completion_summary("Database Processing Complete", {
            "Articles Stored": total_processed,
            "Articles Attempted": total_attempted, 
            "Success Rate": f"{round(success_rate, 1)}%"
        })
        
        logger.info(
            "Database processing completed",
            extra_data={
                "total_articles_stored": total_processed,
                "total_articles_attempted": total_attempted,
                "success_rate_percent": round(success_rate, 1),
            },
        )

        return total_processed, total_attempted
