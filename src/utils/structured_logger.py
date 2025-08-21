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
        self.logger.debug(message)
        
    def info(self, message: str, extra_data: dict = None) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str, extra_data: dict = None) -> None:
        """Log warning message."""
        self.console.print(f"[yellow]WARNING: {message}[/yellow]")

    def error(self, message: str, extra_data: dict = None) -> None:
        """Log error message."""
        self.console.print(f"[red]ERROR: {message}[/red]")

    def always(self, message: str, extra_data: dict = None) -> None:
        """Always show message with colors and icons."""
        if "URLs found" in message:
            self.console.print(f"[cyan]🔍 {message}[/cyan]")
        elif "successfully fetched" in message:
            self.console.print(f"[green]📥 {message}[/green]")
        elif "successfully processed" in message:
            self.console.print(f"[green]✅ {message}[/green]")
        elif "Total:" in message:
            self.console.print(f"[bold blue]📊 {message}[/bold blue]")
        else:
            self.console.print(message)

    def summary_box(self, title: str, total_stored: int, total_attempted: int, success_rate: float) -> None:
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
            padding=(1, 2)
        )
        self.console.print(panel)

    def header(self, title: str, subtitle: str = None) -> None:
        """Display section header using Rich panel."""
        content = title
        if subtitle:
            content += f"\n[dim]{subtitle}[/dim]"
        
        panel = Panel(
            content,
            style="bold blue",
            border_style="blue", 
            padding=(1, 2)
        )
        self.console.print(panel)