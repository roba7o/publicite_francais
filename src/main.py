import sys
import time
import traceback
from typing import Optional

from config.settings import DATABASE_ENABLED, OFFLINE, get_schema_name
from config.website_parser_scrapers_config import get_scraper_configs
from core.database_processor import DatabaseProcessor
from database import initialize_database
from utils.consolidated_output import ConsolidatedOutput
from utils.logging_config_enhanced import configure_debug_mode, setup_logging


def main() -> Optional[int]:
    """
    Main entry point - Database pipeline orchestration

    Returns:
        Optional[int]: Exit code (0 for success, 1 for failure, None for normal exit)
    """
    # Setup consolidated output system (combines CLI + structured logging)
    output = ConsolidatedOutput("main")  # Auto-detects production/development mode

    try:
        # Setup logging with dynamic DEBUG
        from config.settings import DEBUG

        setup_logging()
        if DEBUG:
            configure_debug_mode(enabled=True)

        mode = "OFFLINE" if OFFLINE else "LIVE"

        output.section_header(
            "French News Collection", 
            f"Database pipeline in {mode} mode",
            extra_data={"mode": mode, "database_enabled": DATABASE_ENABLED}
        )

        if not DATABASE_ENABLED:
            output.error("Database not enabled - cannot proceed", 
                        extra_data={"database_enabled": False})
            return 1

        # Initialize database
        output.info("Initializing database connection...", 
                   extra_data={"step": "database_initialization"})

        if not initialize_database():
            output.error("Database initialization failed",
                        extra_data={"step": "database_initialization", "status": "failed"})
            return 1

        output.success("Database initialized successfully",
                      extra_data={"step": "database_initialization", "status": "success"})

        # Get consolidated source configurations
        source_configs = get_scraper_configs()

        output.info(f"Found {len(source_configs)} enabled news sources",
                   extra_data={"source_count": len(source_configs), "step": "source_loading"})

        # Process articles with error handling
        start_time = time.time()
        output.process_start("article_processing", 
                            extra_data={"source_count": len(source_configs), "mode": mode})
        
        output.info(f"Processing {len(source_configs)} news sources...",
                   extra_data={"sources_to_process": len(source_configs)})

        processor = DatabaseProcessor()
        processed, attempted = processor.process_all_sources(source_configs)

        elapsed_time = time.time() - start_time
        success_rate = (processed / attempted * 100) if attempted > 0 else 0

        output.process_complete("article_processing", 
                               extra_data={
                                   "articles_processed": processed,
                                   "articles_attempted": attempted,
                                   "success_rate_percent": round(success_rate, 1),
                                   "elapsed_time_seconds": round(elapsed_time, 1),
                                   "mode": mode,
                               })

        output.success("Database collection completed",
                      extra_data={"final_status": "success"})

        # Display completion summary
        output.completion_summary(
            "Collection Results",
            {
                "Articles Processed": f"{processed}/{attempted}",
                "Success Rate": f"{success_rate:.1f}%",
                "Processing Time": f"{elapsed_time:.1f}s",
                "Mode": mode.upper(),
            },
            extra_data={
                "pipeline_completion": True,
                "total_processed": processed,
                "total_attempted": attempted,
                "success_rate": success_rate,
                "elapsed_seconds": elapsed_time
            }
        )

        # Check if pipeline was successful
        if success_rate < 50.0:
            output.warning(
                f"Low success rate ({success_rate:.1f}%) - check logs for issues",
                extra_data={"success_rate": success_rate, "threshold": 50.0, "status": "low_success_rate"}
            )

        output.info("Check database:",
                   extra_data={"next_step": "database_verification"})
        news_schema = get_schema_name("news_data")
        output.info(
            f'docker compose exec postgres psql -U news_user -d french_news -c "SELECT title, LENGTH(full_text), scraped_at FROM {news_schema}.articles ORDER BY scraped_at DESC LIMIT 3;"',
            extra_data={"command_type": "database_check", "schema_used": news_schema}
        )
        output.info("Next: Run dbt transformations with 'make dbt-run'!",
                   extra_data={"next_step": "dbt_transformations"})

        return 0

    except KeyboardInterrupt:
        output.warning("Pipeline interrupted by user (Ctrl+C)",
                      extra_data={"interruption_type": "keyboard_interrupt"})
        return 1

    except Exception as e:
        output.error(f"Pipeline failed with error: {str(e)}",
                    extra_data={"error": str(e), "traceback": traceback.format_exc()})
        return 1


if __name__ == "__main__":
    exit_code = main()
    if exit_code is not None:
        sys.exit(exit_code)
