"""
Simple logging for the French article scraper.
"""

import logging


class Logger:
    """Simple logger with basic methods and box display."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)

        # Simple setup - basic logging
        if not logging.getLogger().handlers:
            logging.basicConfig(level=logging.INFO, format="%(message)s")

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)

    def always(self, message: str) -> None:
        """Always show message."""
        # Use logging instead of print for CI/CD compatibility
        logging.getLogger().warning(message)

    def summary_box(self, title: str, total_stored: int, total_attempted: int, success_rate: float) -> None:
        """Display final processing summary in a box."""
        # Content lines
        content_lines = [
            "",  # Empty line for spacing
            f"Articles Stored                                       {total_stored:>3}",
            f"Articles Attempted                                    {total_attempted:>3}",
            f"Success Rate                                      {success_rate:>5.1f}%",
            ""   # Empty line for spacing
        ]

        # Calculate box width
        max_content_width = max(len(line) for line in content_lines)
        title_width = len(title)
        box_width = max(60, max_content_width + 4, title_width + 6)

        # Use logging instead of print for CI/CD
        logger = logging.getLogger()

        # Top border
        logger.warning(f"╔{'═' * (box_width - 2)}╗")

        # Title line
        title_padding = (box_width - 2 - len(title)) // 2
        logger.warning(f"║{' ' * title_padding}{title}{' ' * (box_width - 2 - len(title) - title_padding)}║")

        # Content lines
        for line in content_lines:
            padding = box_width - len(line) - 3
            logger.warning(f"║{line}{' ' * padding}║")

        # Bottom border
        logger.warning(f"╚{'═' * (box_width - 2)}╝")

    def header(self, title: str, subtitle: str = None) -> None:
        """Display section header."""
        width = max(len(title) + 4, len(subtitle) + 4 if subtitle else 0, 50)

        # Use logging instead of print for CI/CD
        logger = logging.getLogger()

        # Top border
        logger.warning(f"╔{'═' * (width - 2)}╗")

        # Title
        padding = (width - 2 - len(title)) // 2
        logger.warning(f"║{' ' * padding}{title}{' ' * (width - 2 - len(title) - padding)}║")

        # Subtitle if provided
        if subtitle:
            sub_padding = (width - 2 - len(subtitle)) // 2
            logger.warning(f"║{' ' * sub_padding}{subtitle}{' ' * (width - 2 - len(subtitle) - sub_padding)}║")

        # Bottom border
        logger.warning(f"╚{'═' * (width - 2)}╝")
