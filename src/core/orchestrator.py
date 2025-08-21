from concurrent.futures import ThreadPoolExecutor, as_completed

from core.component_factory import ComponentFactory
from config.environment import env_config, is_test_mode
from utils.structured_logger import Logger


class ArticleOrchestrator:
    """Simple orchestrator using components for all soup manipulation."""

    def __init__(self):
        self.logger = Logger(__name__)
        self.component_factory = ComponentFactory()

    def process_site(self, config: dict) -> tuple[int, int]:
        """Process a single site using components."""
        if not config.get("enabled", True):
            return 0, 0

        try:
            url_collector = self.component_factory.create_scraper(config)
            soup_validator = self.component_factory.create_parser(config)
        except Exception as e:
            self.logger.error(f"Component initialization failed: {str(e)}")
            return 0, 0

        # Get content based on mode
        if is_test_mode():
            sites = soup_validator.get_test_sources_from_directory(config["site"])
        else:
            urls = url_collector.get_article_urls()
            if not urls:
                return 0, 0

            self.logger.always(f"{len(urls[:5])} URLs found for {config['site']}")
            target_urls = urls[:5]
            sites = []

            # Concurrent URL fetching
            max_workers = env_config.get_concurrent_fetchers()
            fetch_timeout = env_config.get_fetch_timeout()

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_url = {
                    executor.submit(soup_validator.get_soup_from_url, url): url
                    for url in target_urls
                }

                for future in as_completed(future_to_url, timeout=fetch_timeout):
                    url = future_to_url[future]
                    try:
                        soup = future.result()
                        if soup:
                            sites.append((soup, url))
                    except Exception:
                        continue

            self.logger.always(
                f"{len(sites)}/{len(target_urls)} URLs successfully fetched for {config['site']}"
            )

        if not sites:
            return 0, 0

        processed_count = 0
        total_attempted = len(sites)

        for soup, site_identifier in sites:
            if soup:
                raw_article = soup_validator.validate_and_extract(soup, site_identifier)
                if raw_article and soup_validator.store_to_database(raw_article):
                    processed_count += 1

        self.logger.always(
            f"{processed_count}/{total_attempted} articles successfully processed for {config['site']}"
        )
        return processed_count, total_attempted

    def process_all_sites(self, site_configs: list[dict]) -> tuple[int, int]:
        """Orchestrate processing of all enabled sites."""
        total_processed = 0
        total_attempted = 0

        enabled_sites = [
            config for config in site_configs if config.get("enabled", True)
        ]

        for config in enabled_sites:
            processed, attempted = self.process_site(config)
            total_processed += processed
            total_attempted += attempted

        success_rate = (
            (total_processed / total_attempted * 100) if total_attempted > 0 else 0
        )

        self.logger.always(
            f"Total: {total_processed}/{total_attempted} articles processed ({success_rate:.1f}% success)"
        )
        self.logger.summary_box(
            "Database Processing Complete",
            total_processed,
            total_attempted,
            success_rate,
        )

        return total_processed, total_attempted
