"""
Enhanced logging configuration for the French article scraper.

This module provides backward-compatible enhanced logging that integrates
with the new structured logging system while maintaining compatibility
with existing code.

Usage:
    # Simple setup (backward compatible)
    >>> from article_scrapers.utils.logging_config_enhanced import setup_logging
    >>> setup_logging()
    
    # Advanced setup with structured logging
    >>> setup_logging(level="DEBUG", use_structured=True, enable_file_logging=True)
    
    # Component-specific log levels
    >>> from article_scrapers.utils.logging_config_enhanced import configure_component_levels
    >>> configure_component_levels({
    ...     "article_scrapers.core": "DEBUG",
    ...     "article_scrapers.parsers": "INFO"
    ... })
"""

import logging
import os
from typing import Union, Dict, Optional

from article_scrapers.config.settings import DEBUG, OFFLINE
from article_scrapers.utils.structured_logger import LogConfig, configure_component_logging


def setup_logging(
    level: Union[str, int] = logging.INFO,
    use_structured: bool = True,
    enable_file_logging: bool = True,
    console_format: str = "human",
    log_directory: Optional[str] = None
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
        
    Features:
        - Structured JSON logging for machine parsing
        - Human-readable console output for development
        - Rotating log files with size limits
        - Performance tracking capabilities
        - Context-aware logging
        - Component-specific log levels
    """
    # Determine default log level based on configuration
    if level is None:
        level = logging.DEBUG if DEBUG else logging.INFO
    elif isinstance(level, str):
        level = getattr(logging, level.upper())
    
    # Determine default log directory (relative to project root)
    if log_directory is None:
        import os
        # Get the project root directory (3 levels up from this file: utils -> article_scrapers -> src -> project_root)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        
        # Always use the logs directory inside src/article_scrapers
        log_directory = os.path.join(project_root, "src", "article_scrapers", "logs")
    
    # Use the structured logging system
    LogConfig.setup_logging(
        log_level=level,
        enable_file_logging=enable_file_logging,
        log_directory=log_directory,
        enable_structured_logging=use_structured,
        console_format=console_format
    )
    
    # Setup component-specific log levels for better debugging
    _setup_component_log_levels()


def _setup_component_log_levels() -> None:
    """Setup appropriate log levels for different components."""
    component_levels: Dict[str, Union[str, int]] = {
        # Core processing - more verbose in debug mode
        "article_scrapers.core.processor": logging.DEBUG if DEBUG else logging.INFO,
        
        # Text processing - moderate verbosity
        "article_scrapers.utils.french_text_processor": logging.INFO,
        
        # CSV writing - less verbose unless debugging
        "article_scrapers.utils.csv_writer": logging.WARNING if not DEBUG else logging.INFO,
        
        # Parsers - moderate verbosity
        "article_scrapers.parsers": logging.INFO,
        
        # Scrapers - moderate verbosity  
        "article_scrapers.scrapers": logging.INFO,
        
        # External libraries - quiet unless errors
        "urllib3": logging.WARNING,
        "requests": logging.WARNING,
        "urllib3.connectionpool": logging.WARNING,
    }
    
    configure_component_logging(component_levels)


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
        debug_components.update({
            "urllib3": logging.DEBUG,
            "requests": logging.DEBUG,
            "urllib3.connectionpool": logging.DEBUG,
        })
    else:
        # Normal operation levels
        normal_components: Dict[str, Union[str, int]] = {
            "article_scrapers": logging.INFO,
            "urllib3": logging.WARNING,
            "requests": logging.WARNING,
        }
        debug_components = normal_components
    
    configure_component_logging(debug_components)


# Backward compatibility - maintain the original function name
def setup_enhanced_logging(*args, **kwargs):
    """Alias for setup_logging for backward compatibility."""
    return setup_logging(*args, **kwargs)