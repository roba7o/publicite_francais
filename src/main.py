import time
import os

from config.settings import OFFLINE, DATABASE_ENABLED
from config.website_parser_scrapers_config import get_scraper_configs
from database import initialize_database
from core.database_processor import DatabaseProcessor
from utils.logging_config_enhanced import configure_debug_mode, setup_logging
from utils.structured_logger import get_structured_logger
from utils.cli_output import CLIOutput


def main():
    """Main entry point - Database pipeline orchestration"""
    # Setup CLI output based on environment  
    cli = CLIOutput()  # Auto-detects production/development mode
    
    # Setup logging with dynamic DEBUG
    from config.settings import DEBUG
    setup_logging()
    if DEBUG:
        configure_debug_mode(enabled=True)

    logger = get_structured_logger(__name__)
    mode = "OFFLINE" if OFFLINE else "LIVE"
    
    cli.section_header(
        "French News Collection", 
        f"Database pipeline in {mode} mode"
    )

    if not DATABASE_ENABLED:
        cli.error("Database not enabled - cannot proceed")
        return

    # Initialize database
    cli.info("Initializing database connection...")
    if not initialize_database():
        cli.error("Database initialization failed")
        return
    cli.success("Database initialized successfully")

    # Get consolidated source configurations and convert to dict format
    scraper_configs = get_scraper_configs()
    source_configs = [config.to_dict() for config in scraper_configs]
    
    cli.info(f"Found {len(source_configs)} enabled news sources")
    
    start_time = time.time()
    cli.info(f"Processing {len(source_configs)} news sources...")
    processor = DatabaseProcessor()
    processed, attempted = processor.process_all_sources(source_configs)
    
    elapsed_time = time.time() - start_time
    success_rate = (processed / attempted * 100) if attempted > 0 else 0

    cli.success("Database collection completed")

    # Display completion summary
    cli.completion_summary("Collection Results", {
        "Articles Processed": f"{processed}/{attempted}",
        "Success Rate": f"{success_rate:.1f}%",
        "Processing Time": f"{elapsed_time:.1f}s",
        "Mode": mode.upper(),
    })

    cli.info("Check database:")
    cli.info('docker compose exec postgres psql -U news_user -d french_news -c "SELECT title, LENGTH(full_text), scraped_at FROM news_data.articles ORDER BY scraped_at DESC LIMIT 3;"')
    cli.info("Next: Run dbt transformations with 'make dbt-run'!")


if __name__ == "__main__":
    main()
