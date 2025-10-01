from concurrent.futures import ThreadPoolExecutor, as_completed

from config.environment import CONCURRENT_FETCHERS, DEBUG, FETCH_TIMEOUT, TEST_MODE
from core.component_factory import ComponentFactory
from utils.structured_logger import get_logger, visual_summary


class ArticleOrchestrator:
    """Simple orchestrator using components for all soup manipulation."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.component_factory = ComponentFactory()

    def process_site(self, config: dict) -> tuple[int, int]:
        """Process a single site using components."""
        if not config.get("enabled", True):
            return 0, 0

        try:
            url_collector = self.component_factory.create_collector(config)
            soup_validator = self.component_factory.create_validator(config)
        except Exception as e:
            self.logger.error(f"Component initialization failed: {str(e)}")
            return 0, 0

        # Get content based on mode
        if TEST_MODE:
            sites = soup_validator.get_test_sources_from_directory(config["site"])
        else:
            urls = url_collector.get_article_urls()
            if not urls:
                return 0, 0

            self.logger.info(f"{len(urls[:5])} URLs found for {config['site']}")
            target_urls = urls
            sites = []

            # Concurrent URL fetching
            max_workers = CONCURRENT_FETCHERS
            fetch_timeout = FETCH_TIMEOUT

            # Submitting all jobs
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_url = {
                    executor.submit(soup_validator.get_soup_from_url, url): url
                    for url in target_urls
                }

                # Collecting results as they complete
                for future in as_completed(future_to_url, timeout=fetch_timeout):
                    url = future_to_url[future]
                    try:
                        soup = future.result()
                        if soup:
                            sites.append((soup, url))
                    except Exception:
                        continue

            self.logger.info(
                f"{len(sites)}/{len(target_urls)} URLs successfully fetched for {config['site']}"
            )

        if not sites:
            return 0, 0

        # Collect articles for batch processing
        articles_batch = []  # list of RawArticle objects
        total_attempted = len(sites)

        for soup, site_identifier in sites:
            if soup:
                raw_article = soup_validator.validate_and_extract(soup, site_identifier)
                if raw_article:
                    articles_batch.append(raw_article)

        # Store articles in batch for better performance
        if articles_batch:
            from database import store_articles_batch, store_word_events

            processed_count, failed_count = store_articles_batch(articles_batch)

            if DEBUG:
                self.logger.info(
                    f"Batch processing results: {processed_count} successful, {failed_count} failed"
                )

            # Store word events for successfully processed articles
            if processed_count > 0:
                all_word_events = []
                for article in articles_batch:
                    if article.word_events:
                        all_word_events.extend(article.word_events)

                if all_word_events:
                    word_events_stored = store_word_events(all_word_events)
                    if DEBUG:
                        self.logger.info(
                            f"Word events: {len(all_word_events) if word_events_stored else 0} stored successfully"
                        )
        else:
            processed_count = 0

        self.logger.info(
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

        self.logger.info(
            f"Total: {total_processed}/{total_attempted} articles processed ({success_rate:.1f}% success)"
        )
        visual_summary(
            "Database Processing Complete",
            total_processed,
            total_attempted,
            success_rate,
        )

        return total_processed, total_attempted
