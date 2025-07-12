"""
Main entry point for article scraping system
"""

from article_scrapers.config.website_parser_scrapers_config import SCRAPER_CONFIGS
from article_scrapers.core.processor import ArticleProcessor
from article_scrapers.utils.logging_config import setup_logging
from article_scrapers.utils.logger import get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    logger.info("Starting article scraping system")

    total_processed = 0
    total_attempted = 0

    for config in SCRAPER_CONFIGS:
        processed, attempted = ArticleProcessor.process_source(config)
        total_processed += processed
        total_attempted += attempted

    logger.info(f"Completed processing. Success: {total_processed}/{total_attempted}")


if __name__ == "__main__":
    main()
