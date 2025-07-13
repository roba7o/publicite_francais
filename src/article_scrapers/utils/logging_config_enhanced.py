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
    level: Union[str, int] = None,
    use_structured: bool = True,
    enable_file_logging: bool = True,
    console_format: str = "human",
    log_directory: str = None
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
        
        if OFFLINE:
            log_directory = os.path.join(project_root, "src", "article_scrapers", "test_data", "logs")
        else:
            log_directory = os.path.join(project_root, "logs")
    
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
    component_levels = {
        # Core processing - more verbose in debug mode
        "article_scrapers.core.processor": logging.DEBUG if DEBUG else logging.INFO,
        
        # Text processing - moderate verbosity
        "article_scrapers.utils.french_text_processor": logging.INFO,
        
        # CSV writing - less verbose unless debugging
        "article_scrapers.utils.csv_writer": logging.WARNING if not DEBUG else logging.INFO,
        
        # Error recovery - always informative
        "article_scrapers.utils.error_recovery": logging.INFO,
        
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
        debug_components = {
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
        debug_components = {
            "article_scrapers": logging.INFO,
            "urllib3": logging.WARNING,
            "requests": logging.WARNING,
        }
    
    configure_component_logging(debug_components)


def configure_production_logging() -> None:
    """
    Configure logging for production environment.
    
    Features:
        - INFO level for application logs
        - WARNING level for external libraries
        - Structured JSON logging for log aggregation
        - File rotation and retention
        - Error-only console output in production
    """
    setup_logging(
        level=logging.INFO,
        use_structured=True,
        enable_file_logging=True,
        console_format="structured",  # JSON for log aggregation
        log_directory="/var/log/scraper" if os.path.exists("/var/log") else "logs"
    )
    
    # Production-appropriate component levels
    production_levels = {
        "article_scrapers": logging.INFO,
        "article_scrapers.core": logging.INFO,
        "article_scrapers.utils.csv_writer": logging.WARNING,  # Less verbose
        "urllib3": logging.ERROR,  # Only errors
        "requests": logging.ERROR,
    }
    
    configure_component_logging(production_levels)


def configure_development_logging() -> None:
    """
    Configure logging for development environment.
    
    Features:
        - DEBUG level for detailed troubleshooting
        - Human-readable console output
        - Local file logging with rotation
        - Detailed HTTP request logging
    """
    setup_logging(
        level=logging.DEBUG,
        use_structured=True,
        enable_file_logging=True,
        console_format="human",  # Human-readable for development
        log_directory="logs"
    )
    
    # Enable debug mode
    configure_debug_mode(enabled=True)


def get_logging_summary() -> Dict[str, str]:
    """
    Get summary of current logging configuration.
    
    Returns:
        Dictionary with logging configuration details
        
    Useful for debugging logging issues and configuration verification.
    """
    root_logger = logging.getLogger()
    
    summary = {
        "root_level": logging.getLevelName(root_logger.level),
        "handlers": [],
        "formatters": [],
        "component_levels": {}
    }
    
    # Analyze handlers
    for handler in root_logger.handlers:
        handler_info = {
            "type": type(handler).__name__,
            "level": logging.getLevelName(handler.level),
            "formatter": type(handler.formatter).__name__ if handler.formatter else "None"
        }
        
        if hasattr(handler, 'baseFilename'):
            handler_info["filename"] = handler.baseFilename
            
        summary["handlers"].append(handler_info)
    
    # Get component levels for main application loggers
    app_loggers = [
        "article_scrapers",
        "article_scrapers.core",
        "article_scrapers.parsers", 
        "article_scrapers.scrapers",
        "article_scrapers.utils"
    ]
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        if logger.level != logging.NOTSET:
            summary["component_levels"][logger_name] = logging.getLevelName(logger.level)
    
    return summary


# Backward compatibility - maintain the original function name
def setup_enhanced_logging(*args, **kwargs):
    """Alias for setup_logging for backward compatibility."""
    return setup_logging(*args, **kwargs)