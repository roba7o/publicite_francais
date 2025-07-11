import importlib
from typing import Tuple
from ..config.scrapers_config import ScraperConfig
from article_scrapers.utils.logger import get_logger

logger = get_logger(__name__)

class ArticleProcessor:
    @staticmethod
    def import_class(class_path: str):
        """Dynamically import a class from module path"""
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    @classmethod
    def process_source(cls, config: ScraperConfig) -> Tuple[int, int]:
        """Process articles from a single source"""
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
            logger.error(f"Failed to initialize {config.name} components: {e}")
            return 0, 0

        # Get content sources (URLs or files)
        if config.live_mode:
            logger.info(f"Fetching live articles from {config.name}...")
            sources = cls._get_live_sources(scraper, parser)
        else:
            logger.info(f"Using test files for {config.name}")
            sources = cls._get_test_sources(parser, config.test_files)

        if not sources:
            return 0, 0

        # Process articles
        processed_count = 0
        for soup, source in sources:
            if not soup:
                logger.error(f"Failed to fetch article: {source}")
                continue

            if cls._process_article(parser, soup, source):
                processed_count += 1

        total_count = len(sources)
        logger.info(f"Processed {processed_count}/{total_count} articles from {config.name}")
        return processed_count, total_count

    @staticmethod
    def _get_live_sources(scraper, parser):
        """Get live URLs and prepare for processing"""
        urls = scraper.get_article_urls()
        if not urls:
            logger.warning("No URLs were fetched")
            return []
        return [(parser.get_soup_from_url(url), url) for url in urls]

    @staticmethod
    def _get_test_sources(parser, test_files):
        """Get test files and prepare for processing"""
        if not test_files:
            logger.warning("No test files configured")
            return []
        return [(parser.get_soup_from_localfile(file), file) for file in test_files]

    @staticmethod
    def _process_article(parser, soup, source) -> bool:
        """Process a single article"""
        logger.info(f"Processing article: {source}")
        parsed_content = parser.parse_article_content(soup)
        if parsed_content:
            parser.to_csv(parsed_content, source)
            logger.debug(f"Article processed: {source}")
            return True
        logger.error(f"Failed to parse article: {source}")
        return False