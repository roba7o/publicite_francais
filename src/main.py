import time

from config.settings import DEBUG, OFFLINE, DATABASE_ENABLED
from database import initialize_database
from core.database_processor import DatabaseProcessor
from utils.logging_config_enhanced import configure_debug_mode, setup_logging
from utils.structured_logger import get_structured_logger


def create_database_configs():
    """Create database-focused source configurations."""
    return [
        {
            "name": "Slate.fr",
            "enabled": True,
            "scraper_class": "scrapers.slate_fr_scraper.SlateFrURLScraper",
            "scraper_kwargs": {"debug": DEBUG}
        },
        {
            "name": "FranceInfo.fr", 
            "enabled": True,
            "scraper_class": "scrapers.france_info_scraper.FranceInfoURLScraper",
            "scraper_kwargs": {"debug": DEBUG}
        },
        {
            "name": "TF1 Info",
            "enabled": True,
            "scraper_class": "scrapers.tf1_info_scraper.TF1InfoURLScraper",
            "scraper_kwargs": {"debug": DEBUG}
        },
        {
            "name": "Depeche.fr",
            "enabled": True,
            "scraper_class": "scrapers.ladepeche_fr_scraper.LadepecheFrURLScraper",
            "scraper_kwargs": {"debug": DEBUG}
        },
    ]


def main():
    """Main entry point - Database pipeline orchestration"""
    # Setup logging
    setup_logging()
    if DEBUG:
        configure_debug_mode(enabled=True)

    logger = get_structured_logger(__name__)
    mode = "OFFLINE" if OFFLINE else "LIVE"
    
    logger.info(f"\033[35m▲ Starting DATABASE French news collection ({mode} mode)\033[0m")

    if not DATABASE_ENABLED:
        logger.error("Database not enabled - cannot proceed")
        return

    # Initialize database
    initialize_database()
    logger.info("Starting database collection")

    # Create source configurations and process all sources
    source_configs = create_database_configs()
    start_time = time.time()
    processor = DatabaseProcessor()
    processor.process_all_sources(source_configs)
    elapsed_time = time.time() - start_time

    logger.info(f"\033[32m✓ Database collection completed\033[0m")

    # ASCII art completion
    print(f"""
\033[32m┌─────────────────────────────────────────────┐
│              COLLECTION COMPLETE            │
└─────────────────────────────────────────────┘\033[0m""")

    print(f"\033[32m✓ Database Collection Results:\033[0m")
    print(f"   \033[36m⧗ Time taken: {elapsed_time:.1f}s\033[0m")
    print()
    print(f"\033[36m▶ Check database:\033[0m")
    print(f"   docker compose exec postgres psql -U news_user -d french_news -c")
    print(f'   "SELECT title, LENGTH(full_text), scraped_at FROM news_data.articles ORDER BY scraped_at DESC LIMIT 3;"')
    print()
    print(f"\033[35m◆ Next: Run dbt transformations with 'make dbt-run'!\033[0m")


if __name__ == "__main__":
    main()
