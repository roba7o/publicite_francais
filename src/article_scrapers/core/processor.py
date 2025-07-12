# article_scrapers/core/processor.py

"""
ArticleProcessor module for dynamically importing and processing web articles.

This module orchestrates the scraping and parsing of articles from various
sources based on a provided configuration. It handles dynamic loading of
scraper and parser classes, fetching content (live or from test files),
and delegating the parsing and data storage to the respective parser instances.
"""

import importlib
from typing import Tuple, Optional, List, Any, Dict

# Assuming these imports are correct relative to your project structure
from ..config.website_parser_scrapers_config import ScraperConfig
from article_scrapers.utils.logger import get_logger
# Assuming BaseParser and BeautifulSoup are not directly used here but are for parser classes
# from article_scrapers.parsers.base_parser import BaseParser
from bs4 import BeautifulSoup


logger = get_logger(__name__)

class ArticleProcessor:
    """
    Manages the end-to-end process of scraping and parsing articles.
    It dynamically loads scraper and parser classes based on configuration
    and handles the flow of fetching content and processing it.
    """

    @staticmethod
    def import_class(class_path: str) -> type:
        """
        Dynamically imports a class from a given module path.

        Args:
            class_path (str): The full dotted path to the class (e.g., "module.submodule.ClassName").

        Returns:
            type: The imported class object.

        Raises:
            ImportError: If the module or class cannot be found.
        """
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    @classmethod
    def process_source(cls, config: ScraperConfig) -> Tuple[int, int]:
        """
        Processes articles from a single configured source (website).

        Args:
            config (ScraperConfig): The configuration object for the source.

        Returns:
            Tuple[int, int]: A tuple containing (number of processed articles, total attempted articles).
        """
        if not config.enabled:
            logger.info(f"Skipping disabled source: {config.name}")
            return 0, 0

        logger.info(f"Initiating processing for source: {config.name}")

        try:
            # Dynamically load scraper and parser classes
            ScraperClass = cls.import_class(config.scraper_class)
            ParserClass = cls.import_class(config.parser_class) # This is where the BaseParser subclasses are loaded

            # Instantiate scraper and parser with their respective kwargs
            # Ensure parser is correctly instantiated as a BaseParser subclass
            scraper = ScraperClass(**(config.scraper_kwargs or {}))
            parser = ParserClass(**(config.parser_kwargs or {})) # This will call BaseParser's __init__
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to initialize components for {config.name}: {e}", exc_info=True)
            return 0, 0
        except Exception as e:
            logger.error(f"An unexpected error occurred during component initialization for {config.name}: {e}", exc_info=True)
            return 0, 0

        # Determine content sources (live URLs or local test files)
        sources: List[Tuple[Optional[BeautifulSoup], str]] = []
        if config.live_mode:
            logger.info(f"Attempting to fetch live article URLs from {config.name}...")
            sources = cls._get_live_sources(scraper, parser)
        else:
            logger.info(f"Using configured test files for {config.name}")
            sources = cls._get_test_sources(parser, config.test_files)

        if not sources:
            logger.warning(f"No content sources (URLs or test files) found for {config.name}. Nothing to process.")
            return 0, 0

        # Process each article
        processed_count = 0
        total_attempted = len(sources)

        for soup, source_identifier in sources:
            if not soup:
                logger.error(f"Failed to obtain BeautifulSoup object for source: {source_identifier}. Skipping.")
                continue

            if cls._process_article(parser, soup, source_identifier):
                processed_count += 1
            else:
                logger.warning(f"Article processing failed for: {source_identifier}")

        logger.info(f"Finished processing {config.name}: {processed_count}/{total_attempted} articles successfully processed.")
        return processed_count, total_attempted

    @staticmethod
    def _get_live_sources(scraper: Any, parser: Any) -> List[Tuple[Optional[BeautifulSoup], str]]:
        """
        Retrieves live article URLs using the scraper and fetches their BeautifulSoup objects.

        Args:
            scraper (Any): The scraper instance with a 'get_article_urls' method.
            parser (Any): The parser instance with a 'get_soup_from_url' method.

        Returns:
            List[Tuple[Optional[BeautifulSoup], str]]: A list of tuples, each containing
                                                        (BeautifulSoup object, URL).
        """
        urls: List[str] = []
        try:
            urls = scraper.get_article_urls()
            if not urls:
                logger.warning(f"No URLs were fetched by the scraper: {scraper.__class__.__name__}")
                return []
        except Exception as e:
            logger.error(f"Error getting live article URLs from scraper {scraper.__class__.__name__}: {e}", exc_info=True)
            return []

        # Fetch soup for each URL
        soup_sources: List[Tuple[Optional[BeautifulSoup], str]] = []
        for url in urls:
            soup = parser.get_soup_from_url(url)
            soup_sources.append((soup, url))
        return soup_sources

    @staticmethod
    def _get_test_sources(parser: Any, test_files: Optional[List[str]]) -> List[Tuple[Optional[BeautifulSoup], str]]:
        """
        Loads content from local test files and returns their BeautifulSoup objects.

        Args:
            parser (Any): The parser instance with a 'get_soup_from_localfile' method.
            test_files (Optional[List[str]]): A list of local file names.

        Returns:
            List[Tuple[Optional[BeautifulSoup], str]]: A list of tuples, each containing
                                                        (BeautifulSoup object, file name).
        """
        if not test_files:
            logger.warning("No test files configured.")
            return []

        soup_sources: List[Tuple[Optional[BeautifulSoup], str]] = []
        for file_name in test_files:
            soup = parser.get_soup_from_localfile(file_name)
            soup_sources.append((soup, file_name))
        return soup_sources

    @staticmethod
    def _process_article(parser: Any, soup: BeautifulSoup, source_identifier: str) -> bool:
        """
        Processes a single article by parsing its content and saving it to CSV.

        Args:
            parser (Any): The parser instance (a subclass of BaseParser).
            soup (BeautifulSoup): The BeautifulSoup object of the article page.
            source_identifier (str): The URL or file path of the article.

        Returns:
            bool: True if the article was successfully parsed and saved, False otherwise.
        """
        logger.info(f"Attempting to parse article from: {source_identifier}")
        try:
            # THIS IS THE CRUCIAL CHANGE: Call parse_article instead of parse_article_content
            parsed_content: Optional[Dict[str, Any]] = parser.parse_article(soup)

            if parsed_content:
                parser.to_csv(parsed_content, source_identifier)
                logger.debug(f"Article successfully parsed and saved: {source_identifier}")
                return True
            else:
                logger.error(f"Parser returned None for article content from: {source_identifier}")
                return False
        except Exception as e:
            logger.error(f"An error occurred during parsing or CSV writing for {source_identifier}: {e}", exc_info=True)
            return False