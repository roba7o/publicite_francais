from article_scrapers.config.website_parser_scrapers_config import SCRAPER_CONFIGS
from article_scrapers.config.settings import OFFLINE
from article_scrapers.core.processor import ArticleProcessor
from article_scrapers.utils.logging_config import setup_logging
from article_scrapers.utils.logger import get_logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

setup_logging()
logger = get_logger(__name__)


def process_source_wrapper(config):
    """Wrapper function for concurrent processing"""
    try:
        processed, attempted = ArticleProcessor.process_source(config)
        return config.name, processed, attempted, None
    except Exception as e:
        logger.error(f"Critical failure processing {config.name}: {e}")
        return config.name, 0, 0, str(e)


def main():
    mode = "OFFLINE" if OFFLINE else "LIVE"
    logger.info(f"Starting article scraping system in {mode} mode")
    start_time = time.time()

    total_processed = 0
    total_attempted = 0
    failed_sources = []

    # Use ThreadPoolExecutor for concurrent processing
    max_workers = min(len(SCRAPER_CONFIGS), 4)  # Limit to 4 concurrent sources
    logger.info(f"Processing {len(SCRAPER_CONFIGS)} sources with {max_workers} workers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all source processing tasks
        future_to_config = {
            executor.submit(process_source_wrapper, config): config
            for config in SCRAPER_CONFIGS
        }

        # Process completed tasks as they finish
        for future in as_completed(future_to_config):
            config = future_to_config[future]
            try:
                source_name, processed, attempted, error = future.result()

                total_processed += processed
                total_attempted += attempted

                if error:
                    failed_sources.append(source_name)
                elif attempted > 0 and processed / attempted < 0.3:
                    failed_sources.append(source_name)
                    logger.warning(
                        f"Low success rate for {source_name}: {processed}/{attempted}"
                    )
                else:
                    logger.info(
                        f"Completed {source_name}: {processed}/{attempted} articles"
                    )

            except Exception as e:
                logger.error(f"Unexpected error processing {config.name}: {e}")
                failed_sources.append(config.name)

    elapsed_time = time.time() - start_time
    success_rate = (
        (total_processed / total_attempted * 100) if total_attempted > 0 else 0
    )

    logger.info(f"Completed processing in {elapsed_time:.1f}s")
    logger.info(f"Success: {total_processed}/{total_attempted} ({success_rate:.1f}%)")

    if failed_sources:
        logger.warning(f"Sources with issues: {', '.join(failed_sources)}")

    output_dir = "test_data/test_output/" if OFFLINE else "output/"
    logger.info(f"Results saved to {output_dir} directory")

    # Print final health summary
    from article_scrapers.utils.error_recovery import health_monitor

    health_summary = health_monitor.get_health_summary()
    if health_summary:
        logger.info(f"Final health summary: {health_summary}")


if __name__ == "__main__":
    main()
