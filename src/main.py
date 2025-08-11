import sys
import time
import traceback
from typing import Optional

from config.settings import DATABASE_ENABLED, OFFLINE
from config.website_parser_scrapers_config import get_scraper_configs
from core.database_processor import DatabaseProcessor
from database import initialize_database
from utils.cli_output import CLIOutput
from utils.logging_config_enhanced import configure_debug_mode, setup_logging
from utils.structured_logger import get_structured_logger


def main() -> Optional[int]:
    """
    Main entry point - Database pipeline orchestration

    Returns:
        Optional[int]: Exit code (0 for success, 1 for failure, None for normal exit)
    """
    # Setup CLI output based on environment
    cli = CLIOutput()  # Auto-detects production/development mode
    logger = None

    try:
        # Setup logging with dynamic DEBUG
        from config.settings import DEBUG

        setup_logging()
        if DEBUG:
            configure_debug_mode(enabled=True)

        logger = get_structured_logger(__name__)
        mode = "OFFLINE" if OFFLINE else "LIVE"

        cli.section_header(
            "French News Collection", f"Database pipeline in {mode} mode"
        )

        if not DATABASE_ENABLED:
            cli.error("Database not enabled - cannot proceed")
            logger.error("Pipeline aborted: DATABASE_ENABLED=False")
            return 1

        # Initialize database
        cli.info("Initializing database connection...")
        logger.info("Starting database initialization")

        if not initialize_database():
            cli.error("Database initialization failed")
            logger.error("Database initialization failed - pipeline aborted")
            return 1

        cli.success("Database initialized successfully")
        logger.info("Database initialization successful")

        # Get consolidated source configurations and convert to dict format
        scraper_configs = get_scraper_configs()
        source_configs = [config.to_dict() for config in scraper_configs]

        cli.info(f"Found {len(source_configs)} enabled news sources")
        logger.info(
            f"Starting pipeline with {len(source_configs)} sources",
            extra_data={"source_count": len(source_configs), "mode": mode},
        )

        # Process articles with error handling
        start_time = time.time()
        cli.info(f"Processing {len(source_configs)} news sources...")

        processor = DatabaseProcessor()
        processed, attempted = processor.process_all_sources(source_configs)

        elapsed_time = time.time() - start_time
        success_rate = (processed / attempted * 100) if attempted > 0 else 0

        # Log final results
        logger.info(
            "Pipeline completed successfully",
            extra_data={
                "articles_processed": processed,
                "articles_attempted": attempted,
                "success_rate_percent": round(success_rate, 1),
                "elapsed_time_seconds": round(elapsed_time, 1),
                "mode": mode,
            },
        )

        cli.success("Database collection completed")

        # Display completion summary
        cli.completion_summary(
            "Collection Results",
            {
                "Articles Processed": f"{processed}/{attempted}",
                "Success Rate": f"{success_rate:.1f}%",
                "Processing Time": f"{elapsed_time:.1f}s",
                "Mode": mode.upper(),
            },
        )

        # Check if pipeline was successful
        if success_rate < 50.0:
            cli.warning(
                f"Low success rate ({success_rate:.1f}%) - check logs for issues"
            )
            logger.warning(
                "Pipeline completed with low success rate",
                extra_data={"success_rate": success_rate},
            )

        cli.info("Check database:")
        cli.info(
            'docker compose exec postgres psql -U news_user -d french_news -c "SELECT title, LENGTH(full_text), scraped_at FROM news_data_test.articles ORDER BY scraped_at DESC LIMIT 3;"'
        )
        cli.info("Next: Run dbt transformations with 'make dbt-run'!")

        return 0

    except KeyboardInterrupt:
        cli.warning("Pipeline interrupted by user (Ctrl+C)")
        if logger:
            logger.warning("Pipeline interrupted by user")
        return 1

    except Exception as e:
        cli.error(f"Pipeline failed with error: {str(e)}")
        if logger:
            logger.error(
                "Pipeline failed with unexpected error",
                extra_data={"error": str(e), "traceback": traceback.format_exc()},
            )
        else:
            # If logger isn't available, print to stderr
            print(f"CRITICAL ERROR: {str(e)}", file=sys.stderr)
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    if exit_code is not None:
        sys.exit(exit_code)
