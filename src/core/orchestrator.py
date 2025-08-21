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
        from utils.structured_logger import Logger

        self.logger = Logger(__name__)
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
            self.logger.warning("URL discovery returned no results")
            return []

        self.logger.always(f"{len(urls[:5])} URLs found for {site_name}")

        # Process first 5 URLs for testing (can expand later)
        target_urls = urls[:5]
        sites = []

        # Get concurrent processing configuration
        max_workers = env_config.get_concurrent_fetchers()
        fetch_timeout = env_config.get_fetch_timeout()

        # Silent concurrent fetching

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
                except Exception:
                    continue

        # Show URL fetch results
        self.logger.always(f"{len(sites)}/{len(target_urls)} URLs successfully fetched for {site_name}")

        return sites

    def process_article(
        self, soup_validator, soup: BeautifulSoup, url: str, site_name: str
    ) -> bool:
        """Process single article - validate and store to database."""
        try:
            # Validate article (ELT approach - raw HTML only in form of RawArticle)
            raw_article: RawArticle | None = soup_validator.validate_and_extract(
                soup, url
            )
            if not raw_article:
                return False

            # Store raw data directly to database
            return soup_validator.store_to_database(raw_article)

        except Exception:
            return False

    def process_site(self, config: dict) -> tuple[int, int]:
        """
        Process a single site - database version.

        Uses your existing scraper but Database parser + database storage.
        """
        if not config.get("enabled", True):
            return 0, 0

        # Database is always enabled (no CSV fallback)

        # Process site

        try:
            # Create url collector
            url_collector = self.component_factory.create_scraper(config)

            # Create soup validator - much simpler, no database lookup needed!
            soup_validator = self.component_factory.create_parser(config)

        except Exception as e:
            self.logger.error(f"Component initialization failed: {str(e)}")
            return 0, 0

        # Acquire content sites
        sites = self.acquire_content(url_collector, soup_validator, config["site"])

        if not sites:
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

        # Basic completion log
        self.logger.always(f"{processed_count}/{total_attempted} articles successfully processed for {config['site']}")

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

        # Process all sites

        # Process sites sequentially for now (simpler)
        for config in enabled_sites:
            processed, attempted = self.process_site(config)
            total_processed += processed
            total_attempted += attempted

        success_rate = (
            (total_processed / total_attempted * 100) if total_attempted > 0 else 0
        )

        # Summary
        self.logger.always(f"Total: {total_processed}/{total_attempted} articles processed ({success_rate:.1f}% success)")
        self.logger.summary_box("Database Processing Complete", total_processed, total_attempted, success_rate)

        return total_processed, total_attempted
