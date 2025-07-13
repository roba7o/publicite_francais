from article_scrapers.config.website_parser_scrapers_config import SCRAPER_CONFIGS
from article_scrapers.config.settings import OFFLINE
from article_scrapers.core.processor import ArticleProcessor
from article_scrapers.utils.logging_config import setup_logging
from article_scrapers.utils.logger import get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    mode = "OFFLINE" if OFFLINE else "LIVE"
    logger.info(f"Starting article scraping system in {mode} mode")

    total_processed = 0
    total_attempted = 0
    failed_sources = []

    for config in SCRAPER_CONFIGS:
        try:
            processed, attempted = ArticleProcessor.process_source(config)
            total_processed += processed
            total_attempted += attempted
            
            if attempted > 0 and processed / attempted < 0.3:
                failed_sources.append(config.name)
                logger.warning(f"Low success rate for {config.name}: {processed}/{attempted}")
                
        except Exception as e:
            logger.error(f"Critical failure processing {config.name}: {e}")
            failed_sources.append(config.name)

    success_rate = (total_processed / total_attempted * 100) if total_attempted > 0 else 0
    logger.info(f"Completed processing. Success: {total_processed}/{total_attempted} ({success_rate:.1f}%)")
    
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
