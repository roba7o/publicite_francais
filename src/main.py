from config.website_parser_scrapers_config import SCRAPER_CONFIGS
from config.settings import OFFLINE, DEBUG
from core.processor import ArticleProcessor
from utils.logging_config_enhanced import setup_logging, configure_debug_mode
from utils.structured_logger import get_structured_logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

setup_logging()
logger = get_structured_logger(__name__)

# Configure debug mode based on settings

if DEBUG:
    configure_debug_mode(enabled=True)


def process_source_wrapper(config):
    """Wrapper function for concurrent processing"""
    try:
        processed, attempted = ArticleProcessor.process_source(config)
        return config.name, processed, attempted, None
    except Exception as e:
        logger.error(
            "Critical source processing failure",
            extra_data={"source": config.name, "error": str(e)},
            exc_info=True,
        )
        return config.name, 0, 0, str(e)


def main():
    mode = "OFFLINE" if OFFLINE else "LIVE"
    start_time = time.time()

    total_processed = 0
    total_attempted = 0
    failed_sources = []

    # Use ThreadPoolExecutor for concurrent processing
    max_workers = min(len(SCRAPER_CONFIGS), 4)  # Limit to 4 concurrent sources

    logger.info(
        "Article scraping system starting",
        extra_data={
            "mode": mode,
            "offline": OFFLINE,
            "debug": DEBUG,
            "sources_count": len(SCRAPER_CONFIGS),
            "max_workers": max_workers,
        },
    )
    enabled_sources = [config.name for config in SCRAPER_CONFIGS if config.enabled]
    logger.info(
        "Processing configuration",
        extra_data={
            "total_sources": len(SCRAPER_CONFIGS),
            "enabled_sources": enabled_sources,
            "disabled_sources": [
                config.name for config in SCRAPER_CONFIGS if not config.enabled
            ],
            "max_workers": max_workers,
            "concurrent_processing": True,
        },
    )

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
                    success_rate = (processed / attempted * 100) if attempted > 0 else 0
                    logger.warning(
                        "Low success rate detected",
                        extra_data={
                            "source": source_name,
                            "processed": processed,
                            "attempted": attempted,
                            "success_rate_percent": round(success_rate, 1),
                            "threshold_percent": 30,
                        },
                    )
                else:
                    success_rate = (processed / attempted * 100) if attempted > 0 else 0
                    logger.info(
                        "Source processing completed successfully",
                        extra_data={
                            "source": source_name,
                            "processed": processed,
                            "attempted": attempted,
                            "success_rate_percent": round(success_rate, 1),
                        },
                    )

            except Exception as e:
                logger.error(
                    "Unexpected source processing error",
                    extra_data={"source": config.name, "error": str(e)},
                    exc_info=True,
                )
                failed_sources.append(config.name)

    elapsed_time = time.time() - start_time
    success_rate = (
        (total_processed / total_attempted * 100) if total_attempted > 0 else 0
    )

    # Summary log for total articles processed
    if not OFFLINE:
        logger.info(
            f"LIVE RUN SUMMARY: {total_processed}/{total_attempted} articles "
            f"parsed successfully ({round(success_rate, 1)}%)",
            extra_data={
                "total_articles_successfully_parsed": total_processed,
                "total_articles_attempted": total_attempted,
                "success_rate_percent": round(success_rate, 1),
                "sources_processed": len(enabled_sources),
                "sources_failed": len(failed_sources),
                "mode": "LIVE",
            },
        )

    logger.info(
        "Processing session completed",
        extra_data={
            "elapsed_time_seconds": round(elapsed_time, 2),
            "total_processed": total_processed,
            "total_attempted": total_attempted,
            "overall_success_rate_percent": round(success_rate, 1),
            "articles_per_second": round(
                total_processed / elapsed_time if elapsed_time > 0 else 0, 2
            ),
            "failed_sources_count": len(failed_sources),
        },
    )

    if failed_sources:
        logger.warning(
            "Sources encountered issues",
            extra_data={
                "failed_sources": failed_sources,
                "failed_count": len(failed_sources),
                "total_sources": len(SCRAPER_CONFIGS),
            },
        )

    logger.info(
        "Results saved",
        extra_data={"output_directory": "src/output", "mode": mode, "offline": OFFLINE},
    )


if __name__ == "__main__":
    main()
