import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from bs4 import BeautifulSoup

from config.environment import env_config, is_test_mode
from database.models import RawArticle


class ArticleOrchestrator:
    """
    Article processing orchestrator focused on orchestration workflow.

    Orchestrates the complete pipeline: content acquisition → article processing → storage.
    Uses ComponentFactory for component creation to maintain single responsibility.
    """

    def __init__(self):
        """Initialize processor with default dependencies."""
        from core.component_factory import ComponentFactory
        from utils.terminal_output import output

        self.output = output
        self.component_factory = ComponentFactory()

    def acquire_content(
        self, url_collector: Any, soup_validator: Any, site_name: str
    ) -> list[tuple[BeautifulSoup, str]]:
        """
            Acquire content sites based on mode
            a) Offline mode: read from local files (handled by soup_validator)
            b) Live mode: scrape from web (handled by _get_live_sources)
            NOTE! Uses the same soup_validator for both modes to maintain consistency

            returns:
                List of tuples (BeautifulSoup, site_identifier[url or file path])
        Check if running in offline mode (TEST_MODE)
        """
        if is_test_mode():
            return soup_validator.get_test_sources_from_directory(site_name)
        else:
            return self._get_live_sources(url_collector, soup_validator, site_name)

    # Logic for acquiring live sources from web scraping
    def _get_live_sources(
        self, url_collector: Any, soup_validator: Any, site_name: str
    ) -> list[tuple[BeautifulSoup, str]]:
        """Get live sites from web scraping using concurrent processing."""
        urls = url_collector.get_article_urls()
        if not urls:
            self.output.warning(
                "URL discovery returned no results",
                extra_data={"site": site_name, "operation": "url_discovery"},
            )
            return []

        # Process first 5 URLs for testing (can expand later)
        target_urls = urls[:5]
        sites = []

        # Get concurrent processing configuration
        max_workers = env_config.get_concurrent_fetchers()
        fetch_timeout = env_config.get_fetch_timeout()

        self.output.info(
            f"Fetching {len(target_urls)} URLs concurrently",
            extra_data={
                "site": site_name,
                "url_count": len(target_urls),
                "max_workers": max_workers,
                "timeout": fetch_timeout,
                "operation": "concurrent_fetch_start",
            },
        )

        # Use ThreadPoolExecutor for concurrent URL fetching
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all URL fetch tasks
            future_to_url = {
                executor.submit(soup_validator.get_soup_from_url, url): url
                for url in target_urls
            }

            # Collect results as they complete
            for future in as_completed(future_to_url, timeout=fetch_timeout):
                url = future_to_url[future]
                try:
                    soup = future.result()
                    if soup:
                        sites.append((soup, url))
                        self.output.success(
                            f"Successfully fetched: {url}",
                            extra_data={
                                "site": site_name,
                                "url": url,
                                "operation": "url_fetch_success",
                            },
                        )
                    else:
                        self.output.warning(
                            f"Empty response for: {url}",
                            extra_data={
                                "site": site_name,
                                "url": url,
                                "operation": "url_fetch_empty",
                            },
                        )
                except Exception as e:
                    self.output.warning(
                        "URL processing error",
                        extra_data={
                            "url": url,
                            "site": site_name,
                            "error": str(e),
                            "operation": "url_processing",
                        },
                    )
                    continue

        self.output.info(
            f"Concurrent fetch completed: {len(sites)}/{len(target_urls)} successful",
            extra_data={
                "site": site_name,
                "successful": len(sites),
                "attempted": len(target_urls),
                "success_rate": (len(sites) / len(target_urls) * 100) if target_urls else 0,
                "operation": "concurrent_fetch_complete",
            },
        )

        return sites

    def process_article(
        self, soup_validator, soup: BeautifulSoup, url: str, site_name: str
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
                    "site": site_name,
                    "url": url,
                    "operation": "article_start",
                },
            )

            # Validate article (ELT approach - raw HTML only in form of RawArticle)
            raw_article: RawArticle | None = soup_validator.validate_and_extract(
                soup, url
            )
            if not raw_article:
                self.output.warning(
                    f"Failed to validate: {url_display}",
                    extra_data={
                        "site": site_name,
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
                        "site": site_name,
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
                    "site": site_name,
                    "url": url,
                    "error": str(e),
                    "operation": "article_processing",
                },
            )
            return False

    def process_site(self, config: dict) -> tuple[int, int]:
        """
        Process a single site - database version.

        Uses your existing scraper but Database parser + database storage.
        """
        if not config.get("enabled", True):
            self.output.info(
                "Site processing skipped - disabled",
                extra_data={"site": config["site"], "reason": "disabled"},
            )
            return 0, 0

        # Database is always enabled (no CSV fallback)

        self.output.process_start(
            f"site_processing_{config['site']}",
            extra_data={
                "site": config["site"],
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
                    "site": config["site"],
                    "error": str(e),
                    "operation": "initialization",
                },
            )
            return 0, 0
        except Exception as e:
            self.output.error(
                "Unexpected error during component initialization",
                extra_data={
                    "site": config["site"],
                    "error": str(e),
                    "operation": "initialization",
                },
            )
            return 0, 0

        # Acquire content sites
        sites = self.acquire_content(url_collector, soup_validator, config["site"])

        mode_str = "offline" if is_test_mode() else "live"
        self.output.info(
            f"Found {len(sites)} sites for {config['site']} (mode: {mode_str})",
            extra_data={
                "site": config["site"],
                "sites_found": len(sites),
                "mode": mode_str,
            },
        )

        if not sites:
            self.output.warning(
                "No content sites found",
                extra_data={
                    "site": config["site"],
                    "mode": mode_str,
                    "sites_count": 0,
                },
            )
            return 0, 0

        processed_count = 0
        total_attempted = len(sites)

        # Process each article for database storage
        for soup, site_identifier in sites:
            if soup:
                success = self.process_article(
                    soup_validator, soup, site_identifier, config["site"]
                )
                if success:
                    processed_count += 1

        elapsed_time = time.time() - start_time
        success_rate = (
            (processed_count / total_attempted * 100) if total_attempted > 0 else 0
        )

        # Complete site processing with consolidated output
        self.output.process_complete(
            f"site_processing_{config['site']}",
            extra_data={
                "site": config["site"],
                "articles_stored": processed_count,
                "articles_attempted": total_attempted,
                "success_rate_percent": round(success_rate, 1),
                "processing_time_seconds": round(elapsed_time, 2),
            },
        )

        self.output.success(
            f"Site '{config['site']}' processing completed",
            extra_data={"site": config["site"], "status": "completed"},
        )

        return processed_count, total_attempted

    def process_all_sites(self, site_configs: list[dict]) -> tuple[int, int]:
        """
        Process all sites - database version.
        """
        total_processed = 0
        total_attempted = 0

        enabled_sites = [
            config for config in site_configs if config.get("enabled", True)
        ]

        mode_str = "offline" if is_test_mode() else "live"
        self.output.process_start(
            "database_processing",
            extra_data={
                "total_sites": len(site_configs),
                "enabled_sites": len(enabled_sites),
                "database_required": True,
                "mode": mode_str,
            },
        )

        # Process sites sequentially for now (simpler)
        for config in enabled_sites:
            processed, attempted = self.process_site(config)
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
