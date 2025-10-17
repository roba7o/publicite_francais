from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed

from config.environment import CONCURRENT_FETCHERS, DEBUG, FETCH_TIMEOUT, ENVIRONMENT
from config.settings import MIN_SUCCESS_RATE_THRESHOLD
from core.component_factory import ComponentFactory
from database.models import SourceStats
from services.word_extractor import WordExtractor
from utils.structured_logger import get_logger, visual_source_summary


class ArticleOrchestrator:
    """Simple orchestrator using components for all soup manipulation."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.component_factory = ComponentFactory()
        self.word_extractor = WordExtractor()

    def process_site(self, config: dict) -> SourceStats | None:
        """Process a single site using components and return detailed statistics."""
        site_name = config.get("site", "unknown")

        if not config.get("enabled", True):
            return None

        try:
            url_collector = self.component_factory.create_collector(config)
            soup_validator = self.component_factory.create_validator(config)
        except Exception as e:
            self.logger.error(f"Component initialization failed: {str(e)}")
            return None

        # Get content based on mode
        if ENVIRONMENT == "test":
            sites = soup_validator.get_test_sources_from_directory(config["site"])
        else:
            urls = url_collector.get_article_urls()
            if not urls:
                return None

            self.logger.info(f"{len(urls)} URLs found for {config['site']}")
            target_urls = urls
            sites = []

            # Concurrent URL fetching
            max_workers = CONCURRENT_FETCHERS
            per_request_timeout = FETCH_TIMEOUT  # Timeout per individual request

            # Submitting all jobs
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_url = {
                    executor.submit(soup_validator.get_soup_from_url, url): url
                    for url in target_urls
                }

                # Collecting results as they complete (no global timeout)
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        # Apply timeout per-request, not globally
                        soup = future.result(timeout=per_request_timeout)
                        if soup:
                            sites.append((soup, url))
                    except TimeoutError:
                        if DEBUG:
                            self.logger.debug(
                                f"Timeout fetching {url} (>{per_request_timeout}s)"
                            )
                        continue
                    except Exception as e:
                        if DEBUG:
                            self.logger.debug(f"Error fetching {url}: {e}")
                        continue

            self.logger.info(
                f"{len(sites)}/{len(target_urls)} URLs successfully fetched for {config['site']}"
            )

        if not sites:
            return None

        # Collect articles for batch processing
        articles_batch = []  # list of RawArticle objects
        total_attempted = len(sites)

        for soup, site_identifier in sites:
            if soup:
                raw_article = soup_validator.validate_and_extract(soup, site_identifier)
                if raw_article:
                    articles_batch.append(raw_article)

        # Store articles and extract words
        word_counts = []  # Track word count per article
        if articles_batch:
            from database import store_articles_batch, store_word_facts_batch

            # Step 1: Store articles in batch
            processed_count, failed_count = store_articles_batch(articles_batch)

            if DEBUG:
                self.logger.info(
                    f"Articles stored: {processed_count} successful, {failed_count} failed"
                )

            # Step 2: Extract words from successfully stored articles and store them
            if processed_count > 0:
                all_word_facts = []

                for article in articles_batch:
                    word_facts = self.word_extractor.extract_words_from_article(article)
                    if word_facts:
                        word_counts.append(len(word_facts))
                        all_word_facts.extend(word_facts)

                # Store word facts in batch
                if all_word_facts:
                    words_stored, words_failed = store_word_facts_batch(all_word_facts)

                    if DEBUG:
                        self.logger.info(
                            f"Words extracted and stored: {words_stored} successful, {words_failed} failed"
                        )
                else:
                    self.logger.warning("No words extracted from any articles")
        else:
            processed_count = 0

        # Calculate statistics
        deduplicated = failed_count if articles_batch else 0
        total_words = sum(word_counts)

        self.logger.info(
            f"{processed_count}/{total_attempted} articles successfully processed for {site_name}"
        )

        return SourceStats(
            site_name=site_name,
            attempted=total_attempted,
            stored=processed_count,
            deduplicated=deduplicated,
            total_words=total_words,
            word_counts=word_counts,
        )

    def process_all_sites(self, site_configs: list[dict]) -> None:
        """Orchestrate processing of all enabled sites and display summary."""
        enabled_sites = [
            config for config in site_configs if config.get("enabled", True)
        ]

        # Collect statistics from each source
        source_stats: list[SourceStats] = []
        for config in enabled_sites:
            stats = self.process_site(config)
            if stats:
                source_stats.append(stats)

        # Calculate totals
        total_attempted = sum(s.attempted for s in source_stats)
        total_stored = sum(s.stored for s in source_stats)
        total_deduplicated = sum(s.deduplicated for s in source_stats)
        total_words = sum(s.total_words for s in source_stats)
        all_word_counts = [wc for s in source_stats for wc in s.word_counts]

        success_rate = (total_stored / total_attempted * 100) if total_attempted > 0 else 0

        # Display per-source summary table
        visual_source_summary(source_stats, total_attempted, total_stored, total_deduplicated, total_words, all_word_counts, success_rate)

        # Quality check
        if success_rate < MIN_SUCCESS_RATE_THRESHOLD:
            self.logger.warning(
                f"Low success rate ({success_rate:.1f}%) - check logs for issues (soup components may be dated)"
            )
