"""
Enhanced structured logging system for the French article scraper.

This module provides a comprehensive logging framework with structured output,
multiple handlers, and detailed debugging capabilities.
Designed for production environments with configurable log levels and formats.

Features:
- Structured JSON logging for machine parsing
- Human-readable console output for development
- Context-aware logging with request IDs
- File rotation and retention
- Configurable log levels per component
- Error aggregation and reporting
- Debug mode with detailed tracing

Example:
    >>> from article_scrapers.utils.structured_logger import get_structured_logger
    >>> logger = get_structured_logger(__name__)
    >>> logger.info("Processing started", extra_data={"source": "slate.fr", "articles": 25})
"""

import logging
import logging.handlers
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
from contextlib import contextmanager
from pathlib import Path
import threading

from article_scrapers.config.settings import DEBUG


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs for machine parsing.
    
    Includes timestamp, level, module, message, and any additional context
    provided through the 'extra' parameter. Designed for log aggregation
    systems like ELK stack, Splunk, or CloudWatch.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string with structured log data
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add any extra context provided
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
            
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class HumanFormatter(logging.Formatter):
    """
    Human-readable formatter for console output during development.
    
    Provides colored output, clear formatting, and context information
    that's easy to read during debugging and development.
    """
    
    # ANSI color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record for human readability.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted string with colors and context
        """
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Base format with color
        formatted = f"{color}[{record.levelname}]{reset} "
        formatted += f"{timestamp} | "
        formatted += f"{record.name} | "
        formatted += f"{record.getMessage()}"
        
        # Add context if available
        if hasattr(record, 'extra_data') and record.extra_data:
            context_items = []
            for key, value in record.extra_data.items():
                if isinstance(value, (str, int, float, bool)):
                    context_items.append(f"{key}={value}")
            if context_items:
                formatted += f" | {' '.join(context_items)}"
            
        return formatted




class StructuredLogger:
    """
    Enhanced logger with structured output.
    
    Wraps the standard Python logger with additional functionality for
    structured logging and context management.
    """
    
    def __init__(self, name: str, logger: logging.Logger):
        self.name = name
        self.logger = logger
        self._context: Dict[str, Any] = {}
        
    def add_context(self, **kwargs) -> None:
        """Add persistent context to all log messages."""
        self._context.update(kwargs)
        
    def clear_context(self) -> None:
        """Clear all persistent context."""
        self._context.clear()
        
    def _log_with_context(self, level: int, message: str, 
                         extra_data: Optional[Dict] = None, **kwargs) -> None:
        """Internal method to log with context and extra data."""
        combined_extra = self._context.copy()
        if extra_data:
            combined_extra.update(extra_data)
            
        if combined_extra:
            kwargs['extra'] = {'extra_data': combined_extra}
            
        self.logger.log(level, message, **kwargs)
    
    def debug(self, message: str, extra_data: Optional[Dict] = None, **kwargs) -> None:
        """Log debug message with optional structured data."""
        self._log_with_context(logging.DEBUG, message, extra_data, **kwargs)
        
    def info(self, message: str, extra_data: Optional[Dict] = None, **kwargs) -> None:
        """Log info message with optional structured data."""
        self._log_with_context(logging.INFO, message, extra_data, **kwargs)
        
    def warning(self, message: str, extra_data: Optional[Dict] = None, **kwargs) -> None:
        """Log warning message with optional structured data."""
        self._log_with_context(logging.WARNING, message, extra_data, **kwargs)
        
    def error(self, message: str, extra_data: Optional[Dict] = None, **kwargs) -> None:
        """Log error message with optional structured data."""
        self._log_with_context(logging.ERROR, message, extra_data, **kwargs)
        
    def critical(self, message: str, extra_data: Optional[Dict] = None, **kwargs) -> None:
        """Log critical message with optional structured data."""
        self._log_with_context(logging.CRITICAL, message, extra_data, **kwargs)
        
    def exception(self, message: str, extra_data: Optional[Dict] = None, **kwargs) -> None:
        """Log exception message with traceback."""
        kwargs['exc_info'] = True
        self._log_with_context(logging.ERROR, message, extra_data, **kwargs)


class LogConfig:
    """
    Centralized logging configuration for the application.
    
    Manages setup of different handlers, formatters, and log levels
    based on environment and configuration settings.
    """
    
    @staticmethod
    def setup_logging(
        log_level: Union[str, int] = None,
        enable_file_logging: bool = True,
        log_directory: str = None,
        enable_structured_logging: bool = True,
        console_format: str = "human"  # "human" or "structured"
    ) -> None:
        """
        Setup comprehensive logging configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_file_logging: Whether to write logs to files
            log_directory: Directory for log files
            enable_structured_logging: Whether to use structured JSON format
            console_format: Console output format ("human" or "structured")
        """
        # Determine log level
        if log_level is None:
            log_level = logging.DEBUG if DEBUG else logging.INFO
        elif isinstance(log_level, str):
            log_level = getattr(logging, log_level.upper())
            
        # Clear any existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(log_level)
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        if console_format == "structured":
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(HumanFormatter())
            
        root_logger.addHandler(console_handler)
        
        # Setup file handlers if enabled
        if enable_file_logging:
            # Determine default log directory if not provided
            if log_directory is None:
                import os
                # Get the project root directory from this file's location
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
                log_directory = os.path.join(project_root, "src", "article_scrapers", "logs")
            
            LogConfig._setup_file_handlers(root_logger, log_directory, 
                                         enable_structured_logging, log_level)
            
        # Set specific log levels for noisy libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        
    @staticmethod
    def _setup_file_handlers(
        root_logger: logging.Logger,
        log_directory: str,
        enable_structured_logging: bool,
        log_level: int
    ) -> None:
        """Setup rotating file handlers for different log levels."""
        # Create log directory with parents
        log_path = Path(log_directory)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Main application log (all levels)
        main_handler = logging.handlers.RotatingFileHandler(
            log_path / "scraper.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        main_handler.setLevel(log_level)
        
        # Error log (ERROR and CRITICAL only)
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / "scraper_errors.log",
            maxBytes=5*1024*1024,   # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        
        # Performance log (structured data for analysis)
        perf_handler = logging.handlers.RotatingFileHandler(
            log_path / "scraper_performance.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3
        )
        perf_handler.setLevel(logging.INFO)
        
        # Use appropriate formatters
        if enable_structured_logging:
            main_handler.setFormatter(StructuredFormatter())
            error_handler.setFormatter(StructuredFormatter())
            perf_handler.setFormatter(StructuredFormatter())
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
            )
            main_handler.setFormatter(file_formatter)
            error_handler.setFormatter(file_formatter)
            perf_handler.setFormatter(file_formatter)
            
        root_logger.addHandler(main_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(perf_handler)


# Global cache for logger instances
_logger_cache: Dict[str, StructuredLogger] = {}
_cache_lock = threading.Lock()


def get_structured_logger(name: str) -> StructuredLogger:
    """
    Get or create a structured logger instance.
    
    Args:
        name: Logger name (usually __name__ from calling module)
        
    Returns:
        StructuredLogger instance with enhanced capabilities
        
    Note:
        Loggers are cached to avoid recreation and maintain context.
    """
    with _cache_lock:
        if name not in _logger_cache:
            standard_logger = logging.getLogger(name)
            _logger_cache[name] = StructuredLogger(name, standard_logger)
        return _logger_cache[name]


def configure_component_logging(component_levels: Dict[str, Union[str, int]]) -> None:
    """
    Configure specific log levels for different components.
    
    Args:
        component_levels: Dict mapping component names to log levels
        
    Example:
        >>> configure_component_logging({
        ...     "article_scrapers.core": "DEBUG",
        ...     "article_scrapers.parsers": "INFO",
        ...     "article_scrapers.utils.csv_writer": "WARNING"
        ... })
    """
    for component, level in component_levels.items():
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        logging.getLogger(component).setLevel(level)


# Initialize logging on module import
def _initialize_default_logging():
    """Initialize default logging configuration if not already setup."""
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        LogConfig.setup_logging()


# Auto-initialize when module is imported
_initialize_default_logging()