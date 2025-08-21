"""
Flexible structured logging system for the French article scraper.

Provides specialized loggers for different modules with customizable configurations.
"""

import logging
import sys
from abc import ABC, abstractmethod

from config.environment import env_config


class BaseLogger(ABC):
    """Base logger class with common functionality."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self._configure()

    @abstractmethod
    def _configure(self) -> None:
        """Configure logger-specific settings. Override in subclasses."""
        pass

    def _ensure_root_logger(self) -> None:
        """Ensure root logger is configured if not already done."""
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            log_level = logging.DEBUG if env_config.is_debug_mode() else logging.INFO
            logging.basicConfig(
                level=log_level,
                format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                handlers=[logging.StreamHandler(sys.stdout)],
            )

    def debug(self, message: str, extra_data: dict | None = None, **kwargs) -> None:
        """Log debug message with optional structured data."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, extra_data: dict | None = None, **kwargs) -> None:
        """Log info message with optional structured data."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, extra_data: dict | None = None, **kwargs) -> None:
        """Log warning message with optional structured data."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, extra_data: dict | None = None, **kwargs) -> None:
        """Log error message with optional structured data."""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, extra_data: dict | None = None, **kwargs) -> None:
        """Log critical message with optional structured data."""
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, extra_data: dict | None = None, **kwargs) -> None:
        """Log exception message with traceback."""
        self.logger.exception(message, **kwargs)


class SQLAlchemyFilter(logging.Filter):
    """Filter to exclude SQLAlchemy logs from output."""
    
    def filter(self, record):
        return not record.name.startswith('sqlalchemy')


class GeneralLogger(BaseLogger):
    """General-purpose logger with standard configuration."""
    
    def _configure(self) -> None:
        """Configure standard logging."""
        self._ensure_root_logger()


class MigrationLogger(BaseLogger):
    """Specialized logger for database migrations that suppresses SQLAlchemy noise."""
    
    def _configure(self) -> None:
        """Configure migration-specific logging with SQLAlchemy filtering."""
        self._ensure_root_logger()
        
        # Apply SQLAlchemy filtering to all root handlers  
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if not any(isinstance(f, SQLAlchemyFilter) for f in handler.filters):
                handler.addFilter(SQLAlchemyFilter())
        
        # Set SQLAlchemy loggers to ERROR level - this needs to be CRITICAL to override engine echo
        for logger_name in ['sqlalchemy', 'sqlalchemy.engine', 'sqlalchemy.pool', 'sqlalchemy.dialects']:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
        
        # Also set the engine logger specifically
        logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.CRITICAL)


class DatabaseLogger(BaseLogger):
    """Logger for database operations with SQLAlchemy logs formatted nicely."""
    
    def _configure(self) -> None:
        """Configure database-specific logging."""
        self._ensure_root_logger()
        # Keep SQLAlchemy logs but maybe format them differently in future


class WebScraperLogger(BaseLogger):
    """Logger for web scraping operations."""
    
    def _configure(self) -> None:
        """Configure web scraping-specific logging."""
        self._ensure_root_logger()
        # Future: Could filter HTTP connection logs, add request tracking, etc.


# Direct imports - no factory functions needed
# Usage: logger = MigrationLogger(__name__)
#        logger = DatabaseLogger(__name__)
#        logger = WebScraperLogger(__name__)
#        logger = GeneralLogger(__name__)
