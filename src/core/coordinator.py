import os
import time
from typing import Any

from bs4 import BeautifulSoup

from database.models import RawArticle


class ArticleCoordinator:
    """
    Article processing coordinator focused on orchestration workflow.

    Coordinates the complete pipeline: content acquisition → article processing → storage.
    Uses ComponentFactory for component creation to maintain single responsibility.
    """

    def __init__(self):
        """Initialize processor with default dependencies."""
        from core.component_factory import ComponentFactory
        from utils.terminal_output import output
        self.output = output
        self.component_factory = ComponentFactory()

    def acquire_content(
        self, url_collector: Any, soup_validator: Any, source_name: str
    ) -> list[tuple[BeautifulSoup, str]]:
        """
            Acquire content sources based on mode
            a) Offline mode: read from local files (handled by soup_validator)
            b) Live mode: scrape from web (handled by _get_live_sources)
            NOTE! Uses the same soup_validator for both modes to maintain consistency

            returns:
                List of tuples (BeautifulSoup, source_identifier[url or file path])
        Check if running in offline mode (TEST_MODE)
        """
        if os.getenv("TEST_MODE", "false").lower() == "true":
            return soup_validator.get_test_sources_from_directory(source_name)
        else:
            return self._get_live_sources(url_collector, soup_validator, source_name)

    # Logic for acquiring live sources from web scraping
    def _get_live_sources(
        self, url_collector: Any, soup_validator: Any, source_name: str
    ) -> list[tuple[BeautifulSoup, str]]:
        """Get live sources from web scraping."""
        urls = url_collector.get_article_urls()
        if not urls:
            self.output.warning(
                "URL discovery returned no results",
                extra_data={"source": source_name, "operation": "url_discovery"},
            )
            return []

        sources = []

        # Process first 5 URLs for testing (can expand later)
        # Pure ELT: collect raw URLs without validation - let dbt handle validation
        for url in urls[:5]:
            try:
                soup = soup_validator.get_soup_from_url(url)
                if soup:
                    sources.append((soup, url))

            except Exception as e:
                self.output.warning(
                    "URL processing error",
                    extra_data={
                        "url": url,
                        "source": source_name,
                        "error": str(e),
                        "operation": "url_processing",
                    },
                )
                continue

        return sources

    def process_article(
        self, soup_validator, soup: BeautifulSoup, url: str, source_name: str
    ) -> bool:
        """Process single article - validate and store to database."""
        try:
            # Log article processing start with shortened URL
            # NOTE! does not affect the logic, just improves readability in logs
            url_display = (
                url.split("/")[-1][:50] + "..."
                if len(url.split("/")[-1]) > 50
                else url.split("/")[-1]
            )
            self.output.info(
                f"Processing: {url_display}",
                extra_data={
                    "source": source_name,
                    "url": url,
                    "operation": "article_start",
                },
            )

            # Validate article (ELT approach - raw HTML only in form of RawArticle)
            raw_article: RawArticle | None = soup_validator.validate_and_extract(soup, url)
            if not raw_article:
                self.output.warning(
                    f"Failed to validate: {url_display}",
                    extra_data={
                        "source": source_name,
                        "url": url,
                        "operation": "validation_failed",
                    },
                )
                return False

            # Store raw data directly to database
            success = soup_validator.store_to_database(raw_article)
            if success:
                self.output.success(
                    f"Stored: {url_display}",
                    extra_data={
                        "source": source_name,
                        "url": url,
                        "content_length": raw_article.content_length,
                        "approach": "ELT",
                        "operation": "article_complete",
                    },
                )
            return success

        except Exception as e:
            self.output.error(
                "Article processing failed",
                extra_data={
                    "source": source_name,
                    "url": url,
                    "error": str(e),
                    "operation": "article_processing",
                },
            )
            return False

    def process_source(self, config: dict) -> tuple[int, int]:
        """
        Process a single source - database version.

        Uses your existing scraper but Database parser + database storage.
        """
        if not config.get("enabled", True):
            self.output.info(
                "Source processing skipped - disabled",
                extra_data={"source": config["domain"], "reason": "disabled"},
            )
            return 0, 0

        # Database is always enabled (no CSV fallback)

        self.output.process_start(
            f"source_processing_{config['domain']}",
            extra_data={
                "source": config["domain"],
                "url_collector_class": config["url_collector_class"],
            },
        )
        start_time = time.time()

        try:
            # Create url collector
            url_collector = self.component_factory.create_scraper(config)

            # Create soup validator - much simpler, no database lookup needed!
            soup_validator = self.component_factory.create_parser(config)

        except (ValueError, ImportError) as e:
            self.output.error(
                "Component initialization failed",
                extra_data={
                    "source": config["domain"],
                    "error": str(e),
                    "operation": "initialization",
                },
            )
            return 0, 0
        except Exception as e:
            self.output.error(
                "Unexpected error during component initialization",
                extra_data={
                    "source": config["domain"],
                    "error": str(e),
                    "operation": "initialization",
                },
            )
            return 0, 0

        # Acquire content sources
        sources = self.acquire_content(url_collector, soup_validator, config["domain"])

        mode_str = (
            "offline" if os.getenv("TEST_MODE", "false").lower() == "true" else "live"
        )
        self.output.info(
            f"Found {len(sources)} sources for {config['domain']} (mode: {mode_str})",
            extra_data={
                "source": config["domain"],
                "sources_found": len(sources),
                "mode": mode_str,
            },
        )

        if not sources:
            self.output.warning(
                "No content sources found",
                extra_data={
                    "source": config["domain"],
                    "mode": mode_str,
                    "sources_count": 0,
                },
            )
            return 0, 0

        processed_count = 0
        total_attempted = len(sources)

        # Process each article for database storage
        for soup, source_identifier in sources:
            if soup:
                success = self.process_article(
                    soup_validator, soup, source_identifier, config["domain"]
                )
                if success:
                    processed_count += 1

        elapsed_time = time.time() - start_time
        success_rate = (
            (processed_count / total_attempted * 100) if total_attempted > 0 else 0
        )

        # Complete source processing with consolidated output
        self.output.process_complete(
            f"source_processing_{config['domain']}",
            extra_data={
                "source": config["domain"],
                "articles_stored": processed_count,
                "articles_attempted": total_attempted,
                "success_rate_percent": round(success_rate, 1),
                "processing_time_seconds": round(elapsed_time, 2),
            },
        )

        self.output.success(
            f"Source '{config['domain']}' processing completed",
            extra_data={"source": config["domain"], "status": "completed"},
        )

        return processed_count, total_attempted

    def process_all_sources(self, source_configs: list[dict]) -> tuple[int, int]:
        """
        Process all sources - database version.
        """
        total_processed = 0
        total_attempted = 0

        enabled_sources = [
            config for config in source_configs if config.get("enabled", True)
        ]

        mode_str = (
            "offline" if os.getenv("TEST_MODE", "false").lower() == "true" else "live"
        )
        self.output.process_start(
            "database_processing",
            extra_data={
                "total_sources": len(source_configs),
                "enabled_sources": len(enabled_sources),
                "database_required": True,
                "mode": mode_str,
            },
        )

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
                "processing_complete": True,
            },
        )

        self.output.process_complete(
            "database_processing",
            extra_data={
                "total_articles_stored": total_processed,
                "total_articles_attempted": total_attempted,
                "success_rate_percent": round(success_rate, 1),
            },
        )

        return total_processed, total_attempted
