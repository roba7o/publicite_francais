"""
Simple logging for the French article scraper using Rich.
"""

import logging

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class Logger:
    """Simple logger with Rich formatting."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.console = Console()

        # Simple setup - basic logging
        if not logging.getLogger().handlers:
            logging.basicConfig(level=logging.INFO, format="%(message)s")

    def debug(self, message: str, extra_data: dict = None) -> None:
        """Log debug message."""
        if extra_data:
            self.logger.debug(f"{message} - Data: {extra_data}")
        else:
            self.logger.debug(message)

    def info(self, message: str, extra_data: dict = None) -> None:
        """Log info message."""
        if extra_data:
            self.logger.info(f"{message} - Data: {extra_data}")
        else:
            self.logger.info(message)

    def warning(self, message: str, extra_data: dict = None) -> None:
        """Log warning message."""
        warning_msg = f"[yellow]WARNING: {message}[/yellow]"
        if extra_data:
            warning_msg += f" - Data: {extra_data}"
        self.console.print(warning_msg)

    def error(self, message: str, extra_data: dict = None) -> None:
        """Log error message."""
        error_msg = f"[red]ERROR: {message}[/red]"
        if extra_data:
            error_msg += f" - Data: {extra_data}"
        self.console.print(error_msg)

    def always(self, message: str, extra_data: dict = None) -> None:
        """Always show message with colors and icons."""
        # Respect log level for controllability
        if self.logger.level > logging.INFO:
            return

        # Robust message type matching
        message_types = {
            "URLs found": "[cyan]🔍 {msg}[/cyan]",
            "successfully fetched": "[green]📥 {msg}[/green]",
            "successfully processed": "[green]✅ {msg}[/green]",
            "Total:": "[bold blue]📊 {msg}[/bold blue]",
        }

        formatted_message = message
        if extra_data:
            formatted_message += f" - Data: {extra_data}"

        for key, style in message_types.items():
            if key in message:
                self.console.print(style.format(msg=formatted_message))
                return

        self.console.print(formatted_message)

    def summary_box(
        self, title: str, total_stored: int, total_attempted: int, success_rate: float
    ) -> None:
        """Display final processing summary using Rich table."""
        table = Table.grid(padding=1)
        table.add_column("Metric", style="cyan", justify="left")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Articles Stored", str(total_stored))
        table.add_row("Articles Attempted", str(total_attempted))
        table.add_row("Success Rate", f"{success_rate:.1f}%")

        panel = Panel(
            table,
            title=f"[bold white]{title}[/bold white]",
            border_style="green",
            padding=(1, 2),
        )
        self.console.print(panel)

    def header(self, title: str, subtitle: str = None) -> None:
        """Display section header using Rich panel."""
        content = title
        if subtitle:
            content += f"\n[dim]{subtitle}[/dim]"

        panel = Panel(content, style="bold blue", border_style="blue", padding=(1, 2))
        self.console.print(panel)
