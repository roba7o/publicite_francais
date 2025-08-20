import sys
import time
import traceback

from config.settings import (
    DEBUG,
    MIN_SUCCESS_RATE_THRESHOLD,
    NEWS_DATA_SCHEMA,
    TEST_MODE,
)
from config.site_configs import get_site_configs
from core.orchestrator import ArticleOrchestrator
from database.database import initialize_database
from utils.logging_config_enhanced import configure_debug_mode, setup_logging
from utils.terminal_output import output


def main() -> int | None:
    """
    Main entry point - Database pipeline orchestration

    Returns:
        Optional[int]: Exit code (0 for success, 1 for failure, None for normal exit)
    """
    try:
        # Setup logging
        setup_logging()
        if DEBUG:
            configure_debug_mode(enabled=True)

        mode = "TEST" if TEST_MODE else "LIVE"

        output.section_header(
            "French News Collection",
            f"Database pipeline in {mode} mode",
            extra_data={
                "mode": mode,
                "test_mode": TEST_MODE,
                "database_required": True,
            },
        )

        # Database is always required (no CSV fallback)

        # Initialize database
        if not initialize_database():
            output.error(
                "Database initialization failed",
                extra_data={"step": "database_initialization", "status": "failed"},
            )
            return 1

        output.success(
            "Database initialized successfully",
            extra_data={"step": "database_initialization", "status": "success"},
        )

        # Get site configurations and start processing
        site_configs = get_site_configs()
        start_time = time.time()

        output.process_start(
            "article_processing",
            extra_data={
                "site_count": len(site_configs),
                "mode": mode,
                "step": "processing_start",
            },
        )

        # Execute pipeline
        processor = ArticleOrchestrator()
        processed, attempted = processor.process_all_sites(site_configs)

        # Calculate results
        elapsed_time = time.time() - start_time
        success_rate = (processed / attempted * 100) if attempted > 0 else 0

        # Single consolidated completion report
        completion_data = {
            "articles_processed": processed,
            "articles_attempted": attempted,
            "success_rate_percent": round(success_rate, 1),
            "elapsed_time_seconds": round(elapsed_time, 1),
            "mode": mode,
            "pipeline_completion": True,
        }

        output.completion_summary(
            "Collection Results",
            {
                "Articles Processed": f"{processed}/{attempted}",
                "Success Rate": f"{success_rate:.1f}%",
                "Processing Time": f"{elapsed_time:.1f}s",
                "Mode": mode.upper(),
            },
            extra_data=completion_data,
        )

        # Quality check
        if success_rate < MIN_SUCCESS_RATE_THRESHOLD:
            output.warning(
                f"Low success rate ({success_rate:.1f}%) - check logs for issues",
                extra_data={
                    "success_rate": success_rate,
                    "threshold": MIN_SUCCESS_RATE_THRESHOLD,
                    "status": "low_success_rate",
                },
            )

        _show_next_steps()

        return 0

    except KeyboardInterrupt:
        output.warning(
            "Pipeline interrupted by user (Ctrl+C)",
            extra_data={"interruption_type": "keyboard_interrupt"},
        )
        return 1

    except Exception as e:
        output.error(
            f"Pipeline failed with error: {str(e)}",
            extra_data={"error": str(e), "traceback": traceback.format_exc()},
        )
        return 1


def _show_next_steps() -> None:
    """Display next steps for user after pipeline completion."""
    db_check_cmd = (
        f"docker compose exec postgres psql -U news_user -d french_news "
        f'-c "SELECT title, LENGTH(full_text), scraped_at FROM {NEWS_DATA_SCHEMA}.articles '
        f'ORDER BY scraped_at DESC LIMIT 3;"'
    )

    output.info(
        "Next steps:",
        extra_data={
            "database_check_command": db_check_cmd,
            "dbt_command": "make dbt-run",
            "next_steps": ["database_verification", "dbt_transformations"],
        },
    )
    output.info(f"Check database: {db_check_cmd}")
    output.info("Run dbt transformations: make dbt-run")


if __name__ == "__main__":
    exit_code = main()
    if exit_code is not None:
        sys.exit(exit_code)
