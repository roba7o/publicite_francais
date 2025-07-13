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

    for config in SCRAPER_CONFIGS:
        processed, attempted = ArticleProcessor.process_source(config)
        total_processed += processed
        total_attempted += attempted

    logger.info(f"Completed processing. Success: {total_processed}/{total_attempted}")
    output_dir = "test_data/test_output/" if OFFLINE else "output/"
    logger.info(f"Results saved to {output_dir} directory")


if __name__ == "__main__":
    main()
