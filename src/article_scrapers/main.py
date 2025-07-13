"""
Main entry point for the French article scraping system.

This module orchestrates the scraping of French news articles from multiple sources,
extracts word frequencies, and saves results to CSV files.
"""

from article_scrapers.config.website_parser_scrapers_config import SCRAPER_CONFIGS
from article_scrapers.config.settings import OFFLINE
from article_scrapers.core.processor import ArticleProcessor
from article_scrapers.utils.logging_config import setup_logging
from article_scrapers.utils.logger import get_logger

# Initialize logging system
setup_logging()
logger = get_logger(__name__)


def main():
    """Main function that processes all configured news sources."""
    mode = "OFFLINE" if OFFLINE else "LIVE"
    logger.info(f"Starting article scraping system in {mode} mode")

    total_processed = 0
    total_attempted = 0

    # Process each configured news source
    for config in SCRAPER_CONFIGS:
        processed, attempted = ArticleProcessor.process_source(config)
        total_processed += processed
        total_attempted += attempted

    logger.info(f"Completed processing. Success: {total_processed}/{total_attempted}")

    if OFFLINE:
        logger.info("Results saved to test_data/test_output/ directory")
    else:
        logger.info("Results saved to output/ directory")


if __name__ == "__main__":
    main()
