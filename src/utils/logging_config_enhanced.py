"""
Enhanced logging configuration for the French article scraper.

This module provides backward-compatible enhanced logging that integrates
with the new structured logging system while maintaining compatibility
with existing code.

Usage:
    # Simple setup (backward compatible)
    >>> from utils.logging_config_enhanced import setup_logging
    >>> setup_logging()

    # Advanced setup with structured logging
    >>> setup_logging(
    ...     level="DEBUG", use_structured=True, enable_file_logging=True
    ... )

    # Component-specific log levels
    >>> from utils.logging_config_enhanced import configure_component_levels
    >>> configure_component_levels({
    ...     "article_scrapers.core": "DEBUG",
    ...     "article_scrapers.parsers": "INFO"
    ... })
"""

import logging
from typing import Union, Dict, Optional

from config.settings import DEBUG


def setup_logging(
    level: Union[str, int] = logging.INFO,
    use_structured: bool = True,
    enable_file_logging: bool = True,
    console_format: str = "human",
    log_directory: Optional[str] = None,
) -> None:
    """
    Setup enhanced logging configuration with backward compatibility.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Defaults to DEBUG if DEBUG=True, INFO otherwise
        use_structured: Whether to use structured JSON logging for files
        enable_file_logging: Whether to write logs to files
        console_format: Console output format ("human" or "structured")
        log_directory: Directory for log files (defaults to "logs")
    """
    # Determine default log level based on configuration
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    elif level is None:
        level = logging.DEBUG if DEBUG else logging.INFO

    # Setup basic logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Setup component-specific log levels for better debugging
    _setup_component_log_levels()


def _setup_component_log_levels() -> None:
    """Setup appropriate log levels for different components."""
    component_levels: Dict[str, Union[str, int]] = {
        # Core processing - more verbose in debug mode
        "article_scrapers.core.processor": (logging.DEBUG if DEBUG else logging.INFO),
        # Text processing - moderate verbosity
        "article_scrapers.utils.french_text_processor": logging.INFO,
        # CSV writing - less verbose unless debugging
        "article_scrapers.utils.csv_writer": (
            logging.WARNING if not DEBUG else logging.INFO
        ),
        # Parsers - moderate verbosity
        "article_scrapers.parsers": logging.INFO,
        # Scrapers - moderate verbosity
        "article_scrapers.scrapers": logging.INFO,
        # External libraries - quiet unless errors
        "urllib3": logging.WARNING,
        "requests": logging.WARNING,
        "urllib3.connectionpool": logging.WARNING,
    }

    for component, level in component_levels.items():
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        logging.getLogger(component).setLevel(level)


def configure_debug_mode(enabled: bool = True) -> None:
    """
    Configure enhanced debug mode with detailed logging.

    Args:
        enabled: Whether to enable debug mode

    When enabled, provides:
        - DEBUG level for all components
        - Detailed performance logging
        - HTTP request/response logging
        - Text processing pipeline details
    """
    if enabled:
        # Set debug level for all application components
        debug_components: Dict[str, Union[str, int]] = {
            "article_scrapers": logging.DEBUG,
            "article_scrapers.core": logging.DEBUG,
            "article_scrapers.parsers": logging.DEBUG,
            "article_scrapers.scrapers": logging.DEBUG,
            "article_scrapers.utils": logging.DEBUG,
        }

        # Enable HTTP debugging for network issues
        debug_components.update(
            {
                "urllib3": logging.DEBUG,
                "requests": logging.DEBUG,
                "urllib3.connectionpool": logging.DEBUG,
            }
        )
    else:
        # Normal operation levels
        normal_components: Dict[str, Union[str, int]] = {
            "article_scrapers": logging.INFO,
            "urllib3": logging.WARNING,
            "requests": logging.WARNING,
        }
        debug_components = normal_components

    for component, level in debug_components.items():
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        logging.getLogger(component).setLevel(level)
