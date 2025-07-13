import importlib
from typing import Tuple, Optional, List, Any

from ..config.website_parser_scrapers_config import ScraperConfig
from ..config.settings import OFFLINE
from article_scrapers.utils.logger import get_logger
from article_scrapers.utils.validators import DataValidator
from article_scrapers.utils.error_recovery import health_monitor, graceful_degradation, retry_handler, CircuitBreaker
from bs4 import BeautifulSoup
import time

logger = get_logger(__name__)


class ArticleProcessor:
    """Main processor class that coordinates scraping and parsing operations."""
    
    # Circuit breakers for each source
    circuit_breakers = {}

    @staticmethod
    def import_class(class_path: str) -> type:
        """Dynamically import a class from a string path."""
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    
    @classmethod
    def get_circuit_breaker(cls, source_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a source"""
        if source_name not in cls.circuit_breakers:
            cls.circuit_breakers[source_name] = CircuitBreaker()
        return cls.circuit_breakers[source_name]

    @classmethod
    def process_source(cls, config: ScraperConfig) -> Tuple[int, int]:
        if not config.enabled:
            logger.info(f"Skipping disabled source: {config.name}")
            return 0, 0

        # Check if source should be skipped due to poor health
        if graceful_degradation.should_skip_source(config.name):
            health_monitor.record_attempt(config.name, False)
            return 0, 0

        logger.info(f"Processing source: {config.name}")
        start_time = time.time()

        try:
            circuit_breaker = cls.get_circuit_breaker(config.name)
            
            def initialize_components():
                ScraperClass = cls.import_class(config.scraper_class)
                ParserClass = cls.import_class(config.parser_class)
                scraper = ScraperClass(**(config.scraper_kwargs or {}))
                parser = ParserClass(**(config.parser_kwargs or {}))
                return scraper, parser
            
            scraper, parser = circuit_breaker.call(initialize_components)
            
        except Exception as e:
            logger.error(f"Failed to initialize components for {config.name}: {e}")
            health_monitor.record_attempt(config.name, False, time.time() - start_time)
            return 0, 0

        sources = (cls._get_test_sources(parser, config.name) if OFFLINE 
                  else cls._get_live_sources_with_recovery(scraper, parser, config.name))

        if not sources:
            logger.warning(f"No content sources found for {config.name}")
            health_monitor.record_attempt(config.name, False, time.time() - start_time)
            return 0, 0

        processed_count = 0
        total_attempted = len(sources)

        for soup, source_identifier in sources:
            if soup and cls._process_article_with_recovery(parser, soup, source_identifier, config.name):
                processed_count += 1

        # Record overall success for this source
        success_rate = processed_count / total_attempted if total_attempted > 0 else 0
        health_monitor.record_attempt(config.name, success_rate > 0.3, time.time() - start_time)

        logger.info(f"Finished {config.name}: {processed_count}/{total_attempted} articles processed")
        
        # Log health summary periodically
        if health_monitor.source_stats.get(config.name, {}).get("total_attempts", 0) % 10 == 0:
            health_summary = health_monitor.get_health_summary()
            logger.info(f"Health summary: {health_summary}")

        return processed_count, total_attempted

    @staticmethod
    def _get_live_sources_with_recovery(
        scraper: Any, parser: Any, source_name: str
    ) -> List[Tuple[Optional[BeautifulSoup], str]]:
        
        def get_urls():
            return scraper.get_article_urls()
        
        urls = retry_handler.execute_with_retry(get_urls)
        if not urls:
            logger.warning(f"No URLs found by {scraper.__class__.__name__}")
            return []

        # Apply graceful degradation to reduce load on struggling sources
        original_count = len(urls)
        urls = urls[:graceful_degradation.get_reduced_url_count(source_name, original_count)]
        
        soup_sources = []
        failed_count = 0
        adaptive_delay = graceful_degradation.get_adaptive_delay(source_name, parser.delay if hasattr(parser, 'delay') else 1.0)
        
        for i, url in enumerate(urls):
            try:
                validated_url = DataValidator.validate_url(url)
                if not validated_url:
                    logger.warning(f"Invalid URL skipped: {url}")
                    failed_count += 1
                    continue
                
                # Use adaptive delay between requests
                if i > 0:
                    time.sleep(adaptive_delay)
                
                def fetch_url():
                    return parser.get_soup_from_url(validated_url)
                
                soup = retry_handler.execute_with_retry(fetch_url)
                soup_sources.append((soup, validated_url))
                if soup is None:
                    failed_count += 1
                    
            except Exception as e:
                logger.warning(f"Error processing URL {url}: {e}")
                soup_sources.append((None, url))
                failed_count += 1
                
                # If too many consecutive failures, break early
                if failed_count >= 3 and (failed_count / (i + 1)) > 0.7:
                    logger.warning(f"Breaking early due to high failure rate for {source_name}")
                    break
        
        if failed_count > 0:
            logger.warning(f"Failed to fetch {failed_count}/{len(urls)} URLs for {source_name}")
        
        return soup_sources
    
    @staticmethod
    def _get_live_sources(
        scraper: Any, parser: Any
    ) -> List[Tuple[Optional[BeautifulSoup], str]]:
        # Legacy method for backward compatibility
        return ArticleProcessor._get_live_sources_with_recovery(scraper, parser, "unknown")

    @staticmethod
    def _get_test_sources(
        parser: Any, source_name: str
    ) -> List[Tuple[Optional[BeautifulSoup], str]]:
        """Load test files from the test_data directory."""
        return parser.get_test_sources_from_directory(source_name)

    @staticmethod
    def _process_article_with_recovery(
        parser: Any, soup: BeautifulSoup, source_identifier: str, source_name: str
    ) -> bool:
        
        def process_article():
            parsed_content = parser.parse_article(soup)
            if not parsed_content:
                raise ValueError(f"No content extracted from {source_identifier}")
            
            validated_content = DataValidator.validate_article_data(parsed_content)
            if not validated_content:
                raise ValueError(f"Article validation failed for {source_identifier}")
            
            parser.to_csv(validated_content, source_identifier)
            return True
        
        try:
            return retry_handler.execute_with_retry(process_article) is not None
            
        except Exception as e:
            logger.error(f"Failed to process article {source_identifier} for {source_name}: {e}")
            return False
    
    @staticmethod
    def _process_article(
        parser: Any, soup: BeautifulSoup, source_identifier: str
    ) -> bool:
        # Legacy method for backward compatibility
        return ArticleProcessor._process_article_with_recovery(parser, soup, source_identifier, "unknown")
