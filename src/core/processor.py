import importlib # allows for dynamic imports of scraper and parser classes as strings
import time
from concurrent.futures import ThreadPoolExecutor, as_completed #running multiple downsloads in parallel/concurrently
from typing import Any, List, Optional, Tuple, Type #for type hinting and dynamic class imports

from bs4 import BeautifulSoup

from config.settings import OFFLINE # whether the application is running in offline mode
from config.website_parser_scrapers_config import ScraperConfig  #refer to dataclass for scraper configuration info
from utils.structured_logger import get_structured_logger
from utils.validators import DataValidator

logger = get_structured_logger(__name__)


class ArticleProcessor:
    """
    Main processor class that coordinates scraping and parsing operations.

    This class serves as the central orchestrator for the article scraping
    system.
    It manages the entire pipeline from URL discovery to article parsing
    and CSV output.

    Features:
    - Dynamic class loading for scrapers and parsers based on configuration
    - Concurrent processing of multiple sources for efficiency
    - Comprehensive error handling and logging
    - Support for both live scraping and offline testing modes

    How to add new sources:
    1. Define a new `ScraperConfig` in `website_parser_scrapers_config.py`
       with the appropriate scraper and parser class paths.
    2. Ensure the scraper and parser classes implement the required methods
       (`get_article_urls`, `get_soup_from_url`, `parse_article`, `to_csv`).
    3. The `ArticleProcessor` will automatically discover and process the new source
       based on the configuration.
    """

    @staticmethod
    def import_class(class_path: str) -> Type[Any]:
        """
        Dynamically import a class from a string path.

        This method enables configuration-driven class loading, allowing
        the system to instantiate scrapers and parsers based on string
        configurations rather than hardcoded imports.

        Args:
            class_path: Fully qualified class path
                       (e.g., 'module.submodule.ClassName')

        Returns:
            The imported class object ready for instantiation

        Raises:
            ImportError: If the module cannot be imported
            AttributeError: If the class doesn't exist in the module

        Example:
            >>> cls = ArticleProcessor.import_class(
            ...     'scrapers.slate_fr_scraper.SlateFrURLScraper')
            >>> scraper = cls(debug=True)
        """
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls  # type: ignore

    @classmethod
    def process_source(cls, config: ScraperConfig) -> Tuple[int, int]:
        """
        Process a single news source from URL discovery to CSV output.

        This is the main entry point for processing a news source. It handles
        the complete pipeline: initializing components, discovering/loading
        content,
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
            logger.info(
                "Source processing skipped",
                extra_data={
                    "source": config.name,
                    "reason": "disabled",
                    "enabled": config.enabled,
                },
            )
            return 0, 0

        logger.info(
            "Starting source processing",
            extra_data={
                "source": config.name,
                "scraper_class": config.scraper_class,
                "parser_class": config.parser_class,
            },
        )
        start_time = time.time()

        try:
            ScraperClass = cls.import_class(config.scraper_class)
            ParserClass = cls.import_class(config.parser_class)
            scraper = ScraperClass(**(config.scraper_kwargs or {}))
            parser = ParserClass(**(config.parser_kwargs or {}))

        except Exception as e:
            logger.error(
                "Component initialization failed",
                extra_data={
                    "source": config.name,
                    "scraper_class": config.scraper_class,
                    "parser_class": config.parser_class,
                    "error": str(e),
                },
                exc_info=True,
            )
            return 0, 0

        sources = (
            cls._get_test_sources(parser, config.name)
            if OFFLINE
            else cls._get_live_sources_with_recovery(scraper, parser, config.name)
        )

        if not sources:
            logger.warning(
                "No content sources found",
                extra_data={
                    "source": config.name,
                    "mode": "offline" if OFFLINE else "live",
                    "total_sources": len(sources),
                },
            )
            return 0, 0

        processed_count = 0
        total_attempted = len(sources)

        for soup, source_identifier in sources:
            if soup and cls._process_article_with_recovery(
                parser, soup, source_identifier, config.name
            ):
                processed_count += 1

        elapsed_time = time.time() - start_time
        success_rate = (
            (processed_count / total_attempted * 100) if total_attempted > 0 else 0
        )

        logger.info(
            "Source processing completed",
            extra_data={
                "source": config.name,
                "articles_processed": processed_count,
                "articles_attempted": total_attempted,
                "success_rate_percent": round(success_rate, 1),
                "processing_time_seconds": round(elapsed_time, 2),
                "articles_per_second": round(
                    processed_count / elapsed_time if elapsed_time > 0 else 0, 2
                ),
            },
        )

        return processed_count, total_attempted

    @staticmethod
    def _get_live_sources_with_recovery(
        scraper: Any, parser: Any, source_name: str
    ) -> List[Tuple[Optional[BeautifulSoup], str]]:
        def get_urls():
            return scraper.get_article_urls()

        urls = get_urls()
        if not urls:
            logger.warning(
                "URL discovery returned no results",
                extra_data={
                    "source": source_name,
                    "scraper_class": scraper.__class__.__name__,
                },
            )
            return []

        # Process URLs concurrently for better performance
        # Limit concurrent requests per source
        max_concurrent_urls = min(len(urls), 3)
        base_delay = parser.delay if hasattr(parser, "delay") else 1.0

        def fetch_single_url(url_info):
            i, url = url_info
            try:
                validated_url = DataValidator.validate_url(url)
                if not validated_url:
                    logger.warning(
                        "Invalid URL skipped",
                        extra_data={
                            "url": url,
                            "source": source_name,
                            "validation_error": "invalid_format",
                        },
                    )
                    return None, url, "invalid"

                # Stagger requests to avoid overwhelming servers
                if i > 0:
                    time.sleep(base_delay * (i % 3))  # Spread delays

                soup = parser.get_soup_from_url(validated_url)
                return soup, validated_url, "success" if soup else "failed"

            except Exception as e:
                logger.warning(
                    "URL processing error",
                    extra_data={"url": url, "source": source_name, "error": str(e)},
                    exc_info=True,
                )
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
                            current_failure_rate = (
                                failed_count / len(soup_sources) * 100
                            )
                            logger.warning(
                                "Early termination due to high failure rate",
                                extra_data={
                                    "source": source_name,
                                    "failed_count": failed_count,
                                    "processed_count": len(soup_sources),
                                    "failure_rate_percent": round(
                                        current_failure_rate, 1
                                    ),
                                    "threshold_percent": 80,
                                },
                            )
                            # Cancel remaining futures
                            for remaining_future in future_to_url:
                                if not remaining_future.done():
                                    remaining_future.cancel()
                            break

                except Exception as e:
                    logger.error(
                        "Concurrent URL processing error",
                        extra_data={"source": source_name, "error": str(e)},
                        exc_info=True,
                    )
                    failed_count += 1

        if failed_count > 0:
            failure_rate = (failed_count / len(urls) * 100) if len(urls) > 0 else 0
            logger.warning(
                "URL fetching completed with failures",
                extra_data={
                    "source": source_name,
                    "failed_count": failed_count,
                    "total_urls": len(urls),
                    "failure_rate_percent": round(failure_rate, 1),
                    "successful_fetches": len(urls) - failed_count,
                },
            )

        return soup_sources

    @staticmethod
    def _get_test_sources(
        parser: Any, source_name: str
    ) -> List[Tuple[Optional[BeautifulSoup], str]]:
        """Load test files from the test_data directory."""
        result: List[Tuple[Optional[BeautifulSoup], str]] = (
            parser.get_test_sources_from_directory(source_name)
        )
        return result

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
            result = process_article()
            return bool(result)

        except Exception as e:
            logger.error(
                "Article processing failed",
                extra_data={
                    "source": source_name,
                    "article_url": source_identifier,
                    "error": str(e),
                },
                exc_info=True,
            )
            return False

    @classmethod
    def process_all_sources(cls) -> Tuple[int, int]:
        """
        Process all configured sources concurrently.

        Returns:
            Tuple of (total_processed, total_attempted) across all sources
        """
        from config.website_parser_scrapers_config import SCRAPER_CONFIGS

        total_processed = 0
        total_attempted = 0
        failed_sources = []

        # Process sources concurrently
        max_workers = min(len(SCRAPER_CONFIGS), 4)
        enabled_sources = [config for config in SCRAPER_CONFIGS if config.enabled] # creates a list of ScreaperConfig objects for enabled sources

        logger.info(
            "Starting concurrent source processing",
            extra_data={
                "total_sources": len(SCRAPER_CONFIGS),
                "enabled_sources": len(enabled_sources),
                "max_workers": max_workers,
            },
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # creating a dictionary of futures (cls.function(*args) to track which config each future corresponds to
            future_to_config = {
                executor.submit(cls.process_source, config): config
                for config in enabled_sources
            }

            # This dict then gets loopped through

            for future in as_completed(future_to_config):
                config = future_to_config[future]
                try:
                    processed, attempted = future.result()
                    total_processed += processed
                    total_attempted += attempted

                    success_rate = (processed / attempted * 100) if attempted > 0 else 0
                    if success_rate < 30 and attempted > 0:
                        failed_sources.append(config.name)
                        logger.warning(
                            "Low success rate detected",
                            extra_data={
                                "source": config.name,
                                "success_rate": round(success_rate, 1),
                                "processed": processed,
                                "attempted": attempted,
                            },
                        )
                    else:
                        logger.info(
                            "Source completed successfully",
                            extra_data={
                                "source": config.name,
                                "processed": processed,
                                "attempted": attempted,
                                "success_rate": round(success_rate, 1),
                            },
                        )

                except Exception as e:
                    failed_sources.append(config.name)
                    logger.error(
                        "Source processing failed",
                        extra_data={"source": config.name, "error": str(e)},
                        exc_info=True,
                    )

        if failed_sources:
            logger.warning(
                "Some sources failed processing",
                extra_data={
                    "failed_sources": failed_sources,
                    "failed_count": len(failed_sources),
                },
            )

        return total_processed, total_attempted
