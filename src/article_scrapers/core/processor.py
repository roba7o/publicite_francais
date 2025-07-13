import importlib
from typing import Tuple, Optional, List, Any

from ..config.website_parser_scrapers_config import ScraperConfig
from ..config.settings import OFFLINE
from article_scrapers.utils.structured_logger import get_structured_logger
from article_scrapers.utils.validators import DataValidator
from article_scrapers.utils.error_recovery import (
    health_monitor,
    graceful_degradation,
    retry_handler,
    CircuitBreaker,
)
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = get_structured_logger(__name__)


class ArticleProcessor:
    """
    Main processor class that coordinates scraping and parsing operations.
    
    This class serves as the central orchestrator for the article scraping system.
    It manages the entire pipeline from URL discovery to article parsing and CSV output,
    with built-in resilience patterns including circuit breakers, health monitoring,
    and graceful degradation.
    
    Features:
    - Concurrent processing of multiple news sources
    - Circuit breaker pattern for failing sources
    - Health monitoring and adaptive degradation
    - Retry mechanisms with exponential backoff
    - Duplicate detection and prevention
    - Both live and offline testing modes
    
    Attributes:
        circuit_breakers (Dict[str, CircuitBreaker]): Per-source circuit breakers
        
    Example:
        >>> config = ScraperConfig(name="test", enabled=True, ...)
        >>> processed, attempted = ArticleProcessor.process_source(config)
        >>> print(f"Processed {processed}/{attempted} articles")
    """

    # Circuit breakers for each source
    circuit_breakers = {}

    @staticmethod
    def import_class(class_path: str) -> type:
        """
        Dynamically import a class from a string path.
        
        This method enables configuration-driven class loading, allowing
        the system to instantiate scrapers and parsers based on string
        configurations rather than hardcoded imports.
        
        Args:
            class_path: Fully qualified class path (e.g., 'module.submodule.ClassName')
            
        Returns:
            The imported class object ready for instantiation
            
        Raises:
            ImportError: If the module cannot be imported
            AttributeError: If the class doesn't exist in the module
            
        Example:
            >>> cls = ArticleProcessor.import_class('scrapers.slate_fr_scraper.SlateFrURLScraper')
            >>> scraper = cls(debug=True)
        """
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    @classmethod
    def get_circuit_breaker(cls, source_name: str) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a specific news source.
        
        Circuit breakers prevent cascading failures by temporarily stopping
        requests to sources that are experiencing repeated failures. This
        implements the Circuit Breaker pattern for improved system resilience.
        
        Args:
            source_name: Name of the news source (e.g., 'Slate.fr')
            
        Returns:
            CircuitBreaker instance for the specified source
            
        Note:
            Circuit breakers are shared across all processing operations
            for the same source to maintain consistent state.
        """
        if source_name not in cls.circuit_breakers:
            cls.circuit_breakers[source_name] = CircuitBreaker()
        return cls.circuit_breakers[source_name]

    @classmethod
    def process_source(cls, config: ScraperConfig) -> Tuple[int, int]:
        """
        Process a single news source from URL discovery to CSV output.
        
        This is the main entry point for processing a news source. It handles
        the complete pipeline: initializing components, discovering/loading content,
        parsing articles, and writing results to CSV.
        
        The method includes comprehensive error handling, health monitoring,
        and performance tracking. It supports both live web scraping and
        offline testing modes.
        
        Args:
            config: ScraperConfig object containing source configuration
                   including scraper/parser classes and parameters
        
        Returns:
            Tuple of (processed_count, total_attempted) where:
            - processed_count: Number of articles successfully processed
            - total_attempted: Total number of articles attempted
            
        Note:
            - Updates global health monitoring statistics
            - Respects circuit breaker states for resilience
            - Supports graceful degradation under load
            - Logs comprehensive processing statistics
            
        Example:
            >>> config = ScraperConfig(name="Slate.fr", enabled=True, ...)
            >>> processed, attempted = ArticleProcessor.process_source(config)
            >>> success_rate = processed / attempted if attempted > 0 else 0
        """
        if not config.enabled:
            logger.info("Source processing skipped", extra_data={
            "source": config.name,
            "reason": "disabled",
            "enabled": config.enabled
        })
            return 0, 0

        # Check if source should be skipped due to poor health
        if graceful_degradation.should_skip_source(config.name):
            health_monitor.record_attempt(config.name, False)
            return 0, 0

        logger.info("Starting source processing", extra_data={
            "source": config.name,
            "scraper_class": config.scraper_class,
            "parser_class": config.parser_class
        })
        start_time = time.time()

        try:
            circuit_breaker = cls.get_circuit_breaker(config.name)

            def initialize_components():
                with logger.performance.timer("component_initialization", 
                                            {"source": config.name, "scraper": config.scraper_class, "parser": config.parser_class}):
                    ScraperClass = cls.import_class(config.scraper_class)
                    ParserClass = cls.import_class(config.parser_class)
                    scraper = ScraperClass(**(config.scraper_kwargs or {}))
                    parser = ParserClass(**(config.parser_kwargs or {}))
                    return scraper, parser

            scraper, parser = circuit_breaker.call(initialize_components)

        except Exception as e:
            logger.error("Component initialization failed", extra_data={
            "source": config.name,
            "scraper_class": config.scraper_class,
            "parser_class": config.parser_class,
            "error": str(e)
        }, exc_info=True)
            health_monitor.record_attempt(config.name, False, time.time() - start_time)
            return 0, 0

        sources = (
            cls._get_test_sources(parser, config.name)
            if OFFLINE
            else cls._get_live_sources_with_recovery(scraper, parser, config.name)
        )

        if not sources:
            logger.warning("No content sources found", extra_data={
            "source": config.name,
            "mode": "offline" if OFFLINE else "live",
            "total_sources": len(sources)
        })
            health_monitor.record_attempt(config.name, False, time.time() - start_time)
            return 0, 0

        processed_count = 0
        total_attempted = len(sources)

        if sources:
            logger.performance.start_timer("article_processing_batch")
        
        for soup, source_identifier in sources:
            with logger.performance.timer("single_article_processing", 
                                        {"source": config.name, "url": source_identifier}):
                if soup and cls._process_article_with_recovery(
                    parser, soup, source_identifier, config.name
                ):
                    processed_count += 1
                    
        if sources and processed_count > 0:
            batch_duration = logger.performance.end_timer("article_processing_batch", 
                                                         {"source": config.name, "processed": processed_count, "attempted": total_attempted})

        # Record overall success for this source
        success_rate = processed_count / total_attempted if total_attempted > 0 else 0
        health_monitor.record_attempt(
            config.name, success_rate > 0.3, time.time() - start_time
        )

        elapsed_time = time.time() - start_time
        success_rate = (processed_count / total_attempted * 100) if total_attempted > 0 else 0
        
        logger.info("Source processing completed", extra_data={
            "source": config.name,
            "articles_processed": processed_count,
            "articles_attempted": total_attempted,
            "success_rate_percent": round(success_rate, 1),
            "processing_time_seconds": round(elapsed_time, 2),
            "articles_per_second": round(processed_count / elapsed_time if elapsed_time > 0 else 0, 2)
        })

        # Log health summary periodically
        if (
            health_monitor.source_stats.get(config.name, {}).get("total_attempts", 0)
            % 10
            == 0
        ):
            health_summary = health_monitor.get_health_summary()
            logger.info("Health monitoring summary", extra_data={
                "source": config.name,
                "health_summary": health_summary
            })

        return processed_count, total_attempted

    @staticmethod
    def _get_live_sources_with_recovery(
        scraper: Any, parser: Any, source_name: str
    ) -> List[Tuple[Optional[BeautifulSoup], str]]:

        def get_urls():
            return scraper.get_article_urls()

        with logger.performance.timer("url_discovery", {"source": source_name}):
            urls = retry_handler.execute_with_retry(get_urls)
        if not urls:
            logger.warning("URL discovery returned no results", extra_data={
                "source": source_name,
                "scraper_class": scraper.__class__.__name__
            })
            return []

        # Apply graceful degradation to reduce load on struggling sources
        original_count = len(urls)
        reduced_count = graceful_degradation.get_reduced_url_count(source_name, original_count)
        urls = urls[:reduced_count]
        
        if reduced_count < original_count:
            logger.info("URL count reduced due to source health", extra_data={
                "source": source_name,
                "original_count": original_count,
                "reduced_count": reduced_count,
                "reduction_percent": round((1 - reduced_count/original_count) * 100, 1)
            })

        # Process URLs concurrently for better performance
        max_concurrent_urls = min(len(urls), 3)  # Limit concurrent requests per source
        adaptive_delay = graceful_degradation.get_adaptive_delay(
            source_name, parser.delay if hasattr(parser, "delay") else 1.0
        )

        def fetch_single_url(url_info):
            i, url = url_info
            try:
                validated_url = DataValidator.validate_url(url)
                if not validated_url:
                    logger.warning("Invalid URL skipped", extra_data={
                    "url": url,
                    "source": source_name,
                    "validation_error": "invalid_format"
                })
                    return None, url, "invalid"

                # Stagger requests to avoid overwhelming servers
                if i > 0:
                    time.sleep(adaptive_delay * (i % 3))  # Spread delays

                def fetch_url():
                    return parser.get_soup_from_url(validated_url)

                soup = retry_handler.execute_with_retry(fetch_url)
                return soup, validated_url, "success" if soup else "failed"

            except Exception as e:
                logger.warning("URL processing error", extra_data={
                    "url": url,
                    "source": source_name,
                    "error": str(e)
                }, exc_info=True)
                return None, url, str(e)

        soup_sources = []
        failed_count = 0

        # Use ThreadPoolExecutor for concurrent URL fetching
        with ThreadPoolExecutor(max_workers=max_concurrent_urls) as executor:
            future_to_url = {
                executor.submit(fetch_single_url, (i, url)): url
                for i, url in enumerate(urls)
            }

            for future in as_completed(future_to_url):
                try:
                    soup, processed_url, status = future.result()
                    soup_sources.append((soup, processed_url))

                    if status != "success":
                        failed_count += 1

                        # Early termination if too many failures
                        if failed_count >= 5 and failed_count / len(soup_sources) > 0.8:
                            current_failure_rate = (failed_count / len(soup_sources) * 100)
                            logger.warning("Early termination due to high failure rate", extra_data={
                                "source": source_name,
                                "failed_count": failed_count,
                                "processed_count": len(soup_sources),
                                "failure_rate_percent": round(current_failure_rate, 1),
                                "threshold_percent": 80
                            })
                            # Cancel remaining futures
                            for remaining_future in future_to_url:
                                if not remaining_future.done():
                                    remaining_future.cancel()
                            break

                except Exception as e:
                    logger.error("Concurrent URL processing error", extra_data={
                    "source": source_name,
                    "error": str(e)
                }, exc_info=True)
                    failed_count += 1

        if failed_count > 0:
            failure_rate = (failed_count / len(urls) * 100) if len(urls) > 0 else 0
            logger.warning("URL fetching completed with failures", extra_data={
                "source": source_name,
                "failed_count": failed_count,
                "total_urls": len(urls),
                "failure_rate_percent": round(failure_rate, 1),
                "successful_fetches": len(urls) - failed_count
            })

        return soup_sources

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
            logger.error("Article processing failed", extra_data={
                "source": source_name,
                "article_url": source_identifier,
                "error": str(e)
            }, exc_info=True)
            return False

    @staticmethod
    def _process_article(
        parser: Any, soup: BeautifulSoup, source_identifier: str
    ) -> bool:
        """Parse a single article and save results to CSV."""
        try:
            parsed_content = parser.parse_article(soup)
            if parsed_content:
                # source_identifier is now the mapped URL (from base_parser)
                parser.to_csv(parsed_content, source_identifier)
                return True
            return False
        except Exception as e:
            logger.error("Legacy article processing error", extra_data={
                "article_url": source_identifier,
                "error": str(e)
            }, exc_info=True)
            return False
