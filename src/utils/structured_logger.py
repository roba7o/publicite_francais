"""
Simple structured logging system for the French article scraper.

Just import the logger class you need with Logger(__name__). That's it.
All logging configuration stays in this file.
"""

import logging
import sys

from config.environment import env_config

# Global logging setup - done once, applies everywhere
_logging_initialized = False

def _initialize_logging():
    """Initialize logging once for the entire application."""
    global _logging_initialized
    if _logging_initialized:
        return

    log_level = logging.DEBUG if env_config.is_debug_mode() else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Silence noisy third-party libraries globally
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    logging.getLogger('trafilatura').setLevel(logging.WARNING)
    logging.getLogger('trafilatura.main_extractor').setLevel(logging.WARNING)
    logging.getLogger('trafilatura.readability_lxml').setLevel(logging.WARNING)
    logging.getLogger('trafilatura.external').setLevel(logging.WARNING)
    logging.getLogger('trafilatura.core').setLevel(logging.WARNING)
    logging.getLogger('filelock').setLevel(logging.WARNING)

    # Silence SQLAlchemy completely for migrations and database operations
    logging.getLogger('sqlalchemy').setLevel(logging.CRITICAL)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)
    logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.CRITICAL)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.CRITICAL)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.CRITICAL)

    _logging_initialized = True


class BaseLogger:
    """Simple logger class. Just pass __name__ and you're done."""

    def __init__(self, name: str):
        _initialize_logging()  # Ensure logging is set up
        self.name = name
        self.logger = logging.getLogger(name)

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


# Simple aliases for backwards compatibility
MigrationLogger = BaseLogger
DatabaseLogger = BaseLogger
WebScraperLogger = BaseLogger
GeneralLogger = BaseLogger

# Usage: logger = MigrationLogger(__name__)
#        logger = DatabaseLogger(__name__)
#        logger = WebScraperLogger(__name__)
#        logger = GeneralLogger(__name__)
