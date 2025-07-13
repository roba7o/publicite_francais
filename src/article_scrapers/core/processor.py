import importlib
from typing import Tuple, Optional, List, Any, Dict

from ..config.website_parser_scrapers_config import ScraperConfig
from ..config.settings import OFFLINE
from article_scrapers.utils.logger import get_logger
from bs4 import BeautifulSoup


logger = get_logger(__name__)


class ArticleProcessor:
    @staticmethod
    def import_class(class_path: str) -> type:
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

        if OFFLINE:
            sources = cls._get_test_sources(parser, config.name)
        else:
            sources = cls._get_live_sources(scraper, parser)

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
    def _get_live_sources(scraper: Any, parser: Any) -> List[Tuple[Optional[BeautifulSoup], str]]:
        try:
            urls = scraper.get_article_urls()
            if not urls:
                return []
        except Exception as e:
            logger.error(f"Error getting URLs from {scraper.__class__.__name__}: {e}")
            return []

        soup_sources = []
        for url in urls:
            soup = parser.get_soup_from_url(url)
            soup_sources.append((soup, url))
        return soup_sources

    @staticmethod
    def _get_test_sources(parser: Any, source_name: str) -> List[Tuple[Optional[BeautifulSoup], str]]:
        # Auto-discover test files based on source name
        return parser.get_test_sources_from_directory(source_name)

    @staticmethod
    def _process_article(parser: Any, soup: BeautifulSoup, source_identifier: str) -> bool:
        try:
            parsed_content = parser.parse_article(soup)
            if parsed_content:
                parser.to_csv(parsed_content, source_identifier)
                return True
            return False
        except Exception as e:
            logger.error(f"Error processing {source_identifier}: {e}")
            return False
