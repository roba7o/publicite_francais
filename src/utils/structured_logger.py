"""
Clean logging with Rich output when needed.
"""

import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

# Global Rich console for visual output
console = Console()


class RichFormatter(logging.Formatter):
    """
    Custom formatter for Rich handler.
    It inherits the standard logging.Formatter class
    and overrides the format method to customize log message formatting.

    """

    def format(self, record):
        return f"[{record.name}] {record.getMessage()}"


def setup_logging():
    """Setup logging once for entire application."""
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return  # Already configured

    # Rich handler for beautiful output
    rich_handler = RichHandler(
        console=console,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )
    rich_handler.setFormatter(RichFormatter())

    root_logger.addHandler(rich_handler)
    root_logger.setLevel(logging.INFO)


def get_logger(name: str):
    """Get logger for module with Rich formatting."""
    setup_logging()  # sets up only once if handlers already exist
    return logging.getLogger(name)


# ---- console related visual functions -------


def visual_header(title: str, subtitle: str | None = None) -> None:
    """Display section header using Rich panel."""
    content = title
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"

    panel = Panel(content, style="bold blue", border_style="blue", padding=(1, 2))
    console.print(panel)


def visual_summary(
    title: str, total_stored: int, total_attempted: int, success_rate: float
) -> None:
    """Display processing summary using Rich table."""
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
    console.print(panel)


def visual_source_summary(
    source_stats: list,
    total_attempted: int,
    total_stored: int,
    total_deduplicated: int,
    total_words: int,
    all_word_counts: list[int],
    success_rate: float,
) -> None:
    """Display detailed per-source summary table with statistics."""
    # Acronymize source names for compact display
    def acronymize(name: str) -> str:
        """Convert source names to short acronyms."""
        mapping = {
            "tf1info.fr": "TF1Info",
            "franceinfo.fr": "FranceI",
            "slate.fr": "Slate",
            "ladepeche.fr": "LaDepech",
        }
        return mapping.get(name, name[:8])

    # Create summary table
    table = Table(
        title="Pipeline Summary by Source",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        show_lines=False,
        padding=(0, 1),
    )

    # Define columns
    table.add_column("Source", style="cyan", justify="left")
    table.add_column("Attempt", justify="right")
    table.add_column("Stored", justify="right", style="green")
    table.add_column("Dedup", justify="right", style="yellow")
    table.add_column("Rate", justify="right")
    table.add_column("Words", justify="right", style="magenta")
    table.add_column("Avg", justify="right")
    table.add_column("Min", justify="right", style="dim")
    table.add_column("Max", justify="right", style="dim")

    # Add rows for each source
    for stats in source_stats:
        table.add_row(
            acronymize(stats.site_name),
            str(stats.attempted),
            str(stats.stored),
            str(stats.deduplicated),
            f"{stats.success_rate:.1f}%",
            f"{stats.total_words:,}",
            str(stats.avg_words),
            str(stats.min_words),
            str(stats.max_words),
        )

    # Add separator and total row
    table.add_section()
    avg_all = int(sum(all_word_counts) / len(all_word_counts)) if all_word_counts else 0
    min_all = min(all_word_counts) if all_word_counts else 0
    max_all = max(all_word_counts) if all_word_counts else 0

    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{total_attempted}[/bold]",
        f"[bold green]{total_stored}[/bold green]",
        f"[bold yellow]{total_deduplicated}[/bold yellow]",
        f"[bold]{success_rate:.1f}%[/bold]",
        f"[bold magenta]{total_words:,}[/bold magenta]",
        f"[bold]{avg_all}[/bold]",
        f"[bold dim]{min_all}[/bold dim]",
        f"[bold dim]{max_all}[/bold dim]",
    )

    console.print()
    console.print(table)
    console.print()


def visual_status(message: str, status_type: str = "info") -> None:
    """Display status message with appropriate styling."""
    status_styles = {
        "found": "[cyan]🔍 {msg}[/cyan]",
        "fetched": "[green]📥 {msg}[/green]",
        "processed": "[green]✅ {msg}[/green]",
        "total": "[bold blue]📊 {msg}[/bold blue]",
        "info": "{msg}",
    }

    style = status_styles.get(status_type, status_styles["info"])
    console.print(style.format(msg=message))
