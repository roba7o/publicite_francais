"""
Simplified structured logging system for the French article scraper.
"""

import logging
import sys

from config.settings import DEBUG


class StructuredLogger:
    """Simplified logger with structured output support."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)

    def debug(self, message: str, extra_data: dict | None = None, **kwargs) -> None:
        """Log debug message with optional structured data."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, extra_data: dict | None = None, **kwargs) -> None:
        """Log info message with optional structured data."""
        self.logger.info(message, **kwargs)

    def warning(
        self, message: str, extra_data: dict | None = None, **kwargs
    ) -> None:
        """Log warning message with optional structured data."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, extra_data: dict | None = None, **kwargs) -> None:
        """Log error message with optional structured data."""
        self.logger.error(message, **kwargs)

    def critical(
        self, message: str, extra_data: dict | None = None, **kwargs
    ) -> None:
        """Log critical message with optional structured data."""
        self.logger.critical(message, **kwargs)

    def exception(
        self, message: str, extra_data: dict | None = None, **kwargs
    ) -> None:
        """Log exception message with traceback."""
        self.logger.exception(message, **kwargs)


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


# Initialize basic logging
def _initialize_logging() -> None:
    """Initialize basic logging configuration."""
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        log_level = logging.DEBUG if DEBUG else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )


_initialize_logging()
