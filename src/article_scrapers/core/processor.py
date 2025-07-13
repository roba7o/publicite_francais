import importlib
from typing import Tuple, Optional, List, Any

from ..config.website_parser_scrapers_config import ScraperConfig
from ..config.settings import OFFLINE
from article_scrapers.utils.logger import get_logger
from bs4 import BeautifulSoup

logger = get_logger(__name__)


class ArticleProcessor:
    """Main processor class that coordinates scraping and parsing operations."""

    @staticmethod
    def import_class(class_path: str) -> type:
        """Dynamically import a class from a string path."""
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    @classmethod
    def process_source(cls, config: ScraperConfig) -> Tuple[int, int]:
        if not config.enabled:
            logger.info(f"Skipping disabled source: {config.name}")
            return 0, 0

        logger.info(f"Processing source: {config.name}")

        try:
            ScraperClass = cls.import_class(config.scraper_class)
            ParserClass = cls.import_class(config.parser_class)
            scraper = ScraperClass(**(config.scraper_kwargs or {}))
            parser = ParserClass(**(config.parser_kwargs or {}))
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to initialize components for {config.name}: {e}")
            return 0, 0

        sources = (cls._get_test_sources(parser, config.name) if OFFLINE 
                  else cls._get_live_sources(scraper, parser))

        if not sources:
            logger.warning(f"No content sources found for {config.name}")
            return 0, 0

        processed_count = 0
        total_attempted = len(sources)

        for soup, source_identifier in sources:
            if soup and cls._process_article(parser, soup, source_identifier):
                processed_count += 1

        logger.info(f"Finished {config.name}: {processed_count}/{total_attempted} articles processed")
        return processed_count, total_attempted

    @staticmethod
    def _get_live_sources(
        scraper: Any, parser: Any
    ) -> List[Tuple[Optional[BeautifulSoup], str]]:
        try:
            urls = scraper.get_article_urls()
            if not urls:
                logger.warning(f"No URLs found by {scraper.__class__.__name__}")
                return []
        except Exception as e:
            logger.error(f"Failed to get URLs from {scraper.__class__.__name__}: {e}")
            return []

        soup_sources = []
        failed_count = 0
        
        for url in urls:
            try:
                soup = parser.get_soup_from_url(url)
                soup_sources.append((soup, url))
                if soup is None:
                    failed_count += 1
            except Exception as e:
                logger.warning(f"Error processing URL {url}: {e}")
                soup_sources.append((None, url))
                failed_count += 1
        
        if failed_count > 0:
            logger.warning(f"Failed to fetch {failed_count}/{len(urls)} URLs")
        
        return soup_sources

    @staticmethod
    def _get_test_sources(
        parser: Any, source_name: str
    ) -> List[Tuple[Optional[BeautifulSoup], str]]:
        """Load test files from the test_data directory."""
        return parser.get_test_sources_from_directory(source_name)

    @staticmethod
    def _process_article(
        parser: Any, soup: BeautifulSoup, source_identifier: str
    ) -> bool:
        try:
            parsed_content = parser.parse_article(soup)
            if not parsed_content:
                logger.warning(f"No content extracted from {source_identifier}")
                return False
            
            required_fields = ['title', 'full_text']
            missing_fields = [field for field in required_fields if not parsed_content.get(field)]
            if missing_fields:
                logger.warning(f"Missing fields {missing_fields} in {source_identifier}")
                return False
            
            parser.to_csv(parsed_content, source_identifier)
            return True
            
        except AttributeError as e:
            logger.error(f"Parser method error for {source_identifier}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing {source_identifier}: {e}")
            return False
