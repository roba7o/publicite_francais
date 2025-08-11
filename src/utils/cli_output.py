"""
Simple CLI output package with modular ASCII art support.

This package provides clean output with optional ASCII art that can be easily
toggled on/off for different environments (development vs production).

Usage:
    from utils.cli_output import CLIOutput
    
    cli = CLIOutput(ascii_art=True)   # Development mode with ASCII art
    cli = CLIOutput(ascii_art=False)  # Production mode, clean output
    
    cli.success("Database connected!")
    cli.info("Processing articles...")
    cli.section_header("Database Processing", "Storing articles to PostgreSQL")
"""

import os
from typing import Dict, Any


class CLIOutput:
    """
    Simple CLI output manager with optional ASCII art.
    
    Provides clean, professional output that can optionally include
    ASCII art headers and completion boxes for development environments.
    """
    
    def __init__(self, ascii_art: bool = None):
        """
        Initialize CLI output manager.
        
        Args:
            ascii_art: Whether to use ASCII art. If None, auto-detects from PRODUCTION env var.
        """
        if ascii_art is None:
            # Auto-detect: ASCII art in development, clean in production
            is_production = os.getenv("PRODUCTION", "false").lower() == "true"
            self.ascii_art = not is_production
        else:
            self.ascii_art = ascii_art
    
    def success(self, message: str) -> None:
        """Display success message."""
        print(f"✓ {message}")
    
    def error(self, message: str) -> None:
        """Display error message."""
        print(f"✗ {message}")
    
    def info(self, message: str) -> None:
        """Display info message."""
        print(f"• {message}")
    
    def warning(self, message: str) -> None:
        """Display warning message."""
        print(f"⚠ {message}")
    
    def section_header(self, title: str, subtitle: str = None) -> None:
        """Display section header with optional ASCII art."""
        if self.ascii_art:
            self._ascii_header(title, subtitle)
        else:
            print(f"\n=== {title} ===")
            if subtitle:
                print(subtitle)
    
    def _ascii_header(self, title: str, subtitle: str = None) -> None:
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
            print(f"║{' ' * sub_padding}{subtitle}{' ' * (width - 2 - len(subtitle) - sub_padding)}║")
        
        # Bottom border
        print(f"╚{'═' * (width - 2)}╝")
    
    def completion_summary(self, title: str, stats: Dict[str, Any]) -> None:
        """Display completion summary with optional ASCII art."""
        if self.ascii_art:
            self._ascii_completion(title, stats)
        else:
            print(f"\n{title}:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
    
    def _ascii_completion(self, title: str, stats: Dict[str, Any]) -> None:
        """Display ASCII completion summary."""
        # Calculate width based on content
        max_key_len = max(len(str(key)) for key in stats.keys()) if stats else 0
        max_val_len = max(len(str(value)) for value in stats.values()) if stats else 0
        content_width = max_key_len + max_val_len + 10  # padding
        width = max(len(title) + 4, content_width, 60)
        
        print(f"""
╔{'═' * (width - 2)}╗
║{title.center(width - 2)}║
║{' ' * (width - 2)}║""")
        
        for key, value in stats.items():
            key_part = f"{key}"
            value_part = f"{value}"
            total_content = len(key_part) + len(value_part)
            spacing = width - 4 - total_content
            print(f"║  {key_part}{' ' * spacing}{value_part}  ║")
        
        print(f"╚{'═' * (width - 2)}╝")


# Global CLI instance for easy access
cli = CLIOutput()


# Convenience functions for quick access
def success(message: str) -> None:
    """Global success message."""
    cli.success(message)


def error(message: str) -> None:
    """Global error message."""
    cli.error(message)


def info(message: str) -> None:
    """Global info message."""
    cli.info(message)


def warning(message: str) -> None:
    """Global warning message."""
    cli.warning(message)


def section_header(title: str, subtitle: str = None) -> None:
    """Global section header."""
    cli.section_header(title, subtitle)


def completion_summary(title: str, stats: Dict[str, Any]) -> None:
    """Global completion summary."""
    cli.completion_summary(title, stats)