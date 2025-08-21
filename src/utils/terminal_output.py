"""
Consolidated output system that combines structured logging with CLI display.

This module unifies the CLI output and structured logging into a single system
that provides both user-friendly terminal output and structured log data.

Provides a shared instance for the entire application to eliminate duplicate creation patterns.
"""

from typing import Any

from config.environment import is_production
from utils.structured_logger import GeneralLogger


class ConsolidatedOutput:
    """
    Unified output system combining CLI display and structured logging.

    Provides user-friendly terminal output while simultaneously generating
    structured log data for monitoring and debugging.
    """

    def __init__(self, component_name: str, ascii_art: bool | None = None):
        """
        Initialize consolidated output system.

        Args:
            component_name: Name of the component for logging context
            ascii_art: Whether to use ASCII art. If None, auto-detects from PRODUCTION env var.
        """
        self.component_name = component_name
        self.logger = GeneralLogger(component_name)

        if ascii_art is None:
            # Auto-detect: ASCII art in development, clean in production
            self.ascii_art = not is_production()
        else:
            self.ascii_art = ascii_art

    def success(self, message: str, extra_data: dict | None = None) -> None:
        """Display success message and log structured data."""
        print(f"✓ {message}")
        self.logger.info(f"Success: {message}", extra_data=extra_data or {})

    def error(self, message: str, extra_data: dict | None = None) -> None:
        """Display error message and log structured data."""
        print(f"✗ {message}")
        self.logger.error(f"Error: {message}", extra_data=extra_data or {})

    def info(self, message: str, extra_data: dict | None = None) -> None:
        """Display info message and log structured data."""
        print(f"• {message}")
        self.logger.info(message, extra_data=extra_data or {})

    def warning(self, message: str, extra_data: dict | None = None) -> None:
        """Display warning message and log structured data."""
        print(f"⚠ {message}")
        self.logger.warning(f"Warning: {message}", extra_data=extra_data or {})

    def section_header(
        self,
        title: str,
        subtitle: str | None = None,
        extra_data: dict | None = None,
    ) -> None:
        """Display section header with optional ASCII art and log section start."""
        if self.ascii_art:
            self._ascii_header(title, subtitle)
        else:
            print(f"\n=== {title} ===")
            if subtitle:
                print(subtitle)

        # Log section start with structured data
        log_data = {"section": title}
        if subtitle:
            log_data["subtitle"] = subtitle
        if extra_data:
            log_data.update(extra_data)

        self.logger.info(f"Section started: {title}", extra_data=log_data)

    def _ascii_header(self, title: str, subtitle: str | None = None) -> None:
        """Display ASCII art header for development mode."""
        width = max(len(title) + 4, len(subtitle) + 4 if subtitle else 0, 50)

        # Top border
        print(f"╔{'═' * (width - 2)}╗")

        # Title
        padding = (width - 2 - len(title)) // 2
        print(f"║{' ' * padding}{title}{' ' * (width - 2 - len(title) - padding)}║")

        # Subtitle if provided
        if subtitle:
            sub_padding = (width - 2 - len(subtitle)) // 2
            print(
                f"║{' ' * sub_padding}{subtitle}{' ' * (width - 2 - len(subtitle) - sub_padding)}║"
            )

        # Bottom border
        print(f"╚{'═' * (width - 2)}╝")

    def completion_summary(
        self, title: str, stats: dict[str, Any], extra_data: dict | None = None
    ) -> None:
        """Display completion summary with ASCII art and log structured completion data."""
        if self.ascii_art:
            self._ascii_completion(title, stats)
        else:
            print(f"\n{title}:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

        # Log completion with full structured data
        log_data = {"completion_title": title, "completion_stats": stats}
        if extra_data:
            log_data.update(extra_data)

        self.logger.info(f"Process completed: {title}", extra_data=log_data)

    def _ascii_completion(self, title: str, stats: dict[str, Any]) -> None:
        """Display ASCII completion summary."""
        # Calculate width based on content
        max_key_len = max(len(str(key)) for key in stats.keys()) if stats else 0
        max_val_len = max(len(str(value)) for value in stats.values()) if stats else 0
        content_width = max_key_len + max_val_len + 10  # padding
        width = max(len(title) + 4, content_width, 60)

        print(f"""
╔{"═" * (width - 2)}╗
║{title.center(width - 2)}║
║{" " * (width - 2)}║""")

        for key, value in stats.items():
            key_part = f"{key}"
            value_part = f"{value}"
            total_content = len(key_part) + len(value_part)
            spacing = width - 4 - total_content
            print(f"║  {key_part}{' ' * spacing}{value_part}  ║")

        print(f"╚{'═' * (width - 2)}╝")

    def process_start(self, process_name: str, extra_data: dict | None = None) -> None:
        """Log process start with structured data (logging only, no CLI output)."""
        log_data = {"process": process_name, "status": "started"}
        if extra_data:
            log_data.update(extra_data)
        self.logger.info(f"Process started: {process_name}", extra_data=log_data)

    def process_complete(
        self, process_name: str, extra_data: dict | None = None
    ) -> None:
        """Log process completion with structured data (logging only, no CLI output)."""
        log_data = {"process": process_name, "status": "completed"}
        if extra_data:
            log_data.update(extra_data)
        self.logger.info(f"Process completed: {process_name}", extra_data=log_data)


# Shared instance for the entire application
output = ConsolidatedOutput("database_pipeline")
