import sys

from config.environment import ENVIRONMENT
from config.site_configs import get_site_configs
from core.orchestrator import ArticleOrchestrator
from database.database import initialize_database
from utils.structured_logger import get_logger, visual_header


def main() -> int | None:
    """
    Main entry point - Database pipeline orchestration

    Returns:
        Optional[int]: Exit code (0 for success, 1 for failure, None for normal exit)
    """
    logger = get_logger(__name__)

    try:
        visual_header(
            "French News Collection", f"Database pipeline in {ENVIRONMENT.upper()} mode"
        )

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
        processor.process_all_sites(site_configs)

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
