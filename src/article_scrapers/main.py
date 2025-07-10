"""
Main script for scraping and parsing articles.

- Uses custom scrapers and parsers for Slate.fr articles
- Outputs a CSV file with word frequencies and metadata (source, date, etc.)
- Simple local CSV saving to start, future integration with PostgreSQL
"""

from article_scrapers.parsers.slate_fr_parser import SlateFrArticleParser
from article_scrapers.scrapers.slate_fr_scraper import SlateFrURLScraper

from article_scrapers.utils.logging_config import setup_logging
from article_scrapers.utils.logger import get_logger

# Initialize global logging config
setup_logging()
logger = get_logger(__name__)


def main():
    logger.info("Starting the scraping and parsing process")

    slate_scraper = SlateFrURLScraper()
    slate_parser = SlateFrArticleParser()

    live_parser = True  # Switch to False for local HTML file parsing

    if live_parser:
        logger.info("Fetching article URLs from Slate.fr...")
        slate_urls = slate_scraper.get_article_urls()

        if not slate_urls:
            logger.warning("No URLs were fetched.")
            return

        logger.info(f"Found {len(slate_urls)} URLs. Beginning parsing...")
        soups_url_pairs = [
            (slate_parser.get_soup_from_url(url), url) for url in slate_urls
        ]
    else:
        logger.info("Using local test HTML files for parsing.")
        test_local_files = [
            "canada-quelque-chose-mysterieux-tue-grands-requins-blancs-cerveau-inflammation-maladie-autopsie-deces-mort-scientifiques.html",
            "regle-baillon-mondial-trump-entraver-acces-avortement-mexico-city-policy-anti-ivg-dangers-mort-femmes-deces-grossesse.html"
        ]
        soups_url_pairs = [
            (slate_parser.get_soup_from_localfile(file), file) for file in test_local_files
        ]

    if not soups_url_pairs:
        logger.warning("No soup/url pairs were generated. Exiting.")
        return

    processed_count = 0
    for soup, url in soups_url_pairs:
        if not soup:
            logger.error(f"Failed to fetch article: {url}")
            continue

        logger.info(f"Processing article: {url}")
        parsed_content = slate_parser.parse_article_content(soup)

        if parsed_content:
            slate_parser.to_csv(parsed_content, url)
            processed_count += 1
            logger.debug(f"Article processed and saved: {url}")
        else:
            logger.error(f"Failed to parse article content: {url}")

    if processed_count == 0:
        logger.warning("No articles were processed successfully. Skipping DB upload.")
        return

    logger.info(f"Processed {processed_count} articles successfully. TODO: Upload to DB.")


if __name__ == "__main__":
    main()
