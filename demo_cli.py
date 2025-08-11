#!/usr/bin/env python3
"""
Demo script showcasing the simplified CLI output package.

Run with:
    python demo_cli.py                    # Development mode (ASCII art)
    PRODUCTION=true python demo_cli.py    # Production mode (clean)
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, 'src')

from utils.consolidated_output import ConsolidatedOutput


def demo_basic_messages(cli):
    """Demo basic message types."""
    cli.section_header("Basic Messages Demo", "Testing different message types")
    
    cli.success("Database connection successful!")
    cli.info("Processing 4 news sources...")
    cli.warning("Rate limiting detected - slowing down requests")
    cli.error("Failed to connect to external API")
    print()


def demo_completion_summary(cli):
    """Demo completion summary."""
    cli.completion_summary("Processing Results", {
        "Articles Scraped": "47/50",
        "Success Rate": "94.0%",
        "Processing Time": "2.3s",
        "Sources Processed": "4/4",
        "Database Writes": "47",
        "Errors": "3"
    })


def main():
    """Run CLI demo."""
    # Determine mode
    is_production = os.getenv("PRODUCTION", "false").lower() == "true"
    mode_name = "PRODUCTION" if is_production else "DEVELOPMENT"
    
    cli = ConsolidatedOutput("demo")  # Auto-detects mode from environment
    
    print(f"\n🎨 CLI Output Package Demo - {mode_name} Mode")
    print("=" * 60)
    
    # Run demos
    demo_basic_messages(cli)
    demo_completion_summary(cli)
    
    cli.section_header("Demo Complete!", "Simple ASCII art modularity")
    cli.info("PRODUCTION=true python demo_cli.py  # Clean production output")
    cli.info("python demo_cli.py                  # Development with ASCII art")


if __name__ == "__main__":
    main()