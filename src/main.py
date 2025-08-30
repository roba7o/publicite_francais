import sys

from config.environment import TEST_MODE
from config.settings import MIN_SUCCESS_RATE_THRESHOLD
from config.site_configs import get_site_configs
from core.orchestrator import ArticleOrchestrator
from database.database import initialize_database
from utils.structured_logger import Logger


def main() -> int | None:
    """
    Main entry point - Database pipeline orchestration

    Returns:
        Optional[int]: Exit code (0 for success, 1 for failure, None for normal exit)
    """
    logger = Logger(__name__)

    try:
        mode = "TEST" if TEST_MODE else "LIVE"

        logger.header("French News Collection", f"Database pipeline in {mode} mode")

        # Database is always required (no CSV fallback)

        # Initialize database
        if not initialize_database():
            logger.error("Database initialization failed")
            return 1

        logger.info("Database initialized successfully")

        # Get site configurations and start processing
        site_configs = get_site_configs()

        # Execute pipeline
        processor = ArticleOrchestrator()
        processed, attempted = processor.process_all_sites(site_configs)

        # Calculate results
        success_rate = (processed / attempted * 100) if attempted > 0 else 0

        # Quality check
        if success_rate < MIN_SUCCESS_RATE_THRESHOLD:
            logger.warning(
                f"Low success rate ({success_rate:.1f}%) - check logs for issues (soup componetnts may be dated)"
            )

        return 0

    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user using: Ctrl+C")
        return 1

    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    if exit_code is not None:
        sys.exit(exit_code)
