from config.website_parser_scrapers_config import SCRAPER_CONFIGS
from config.settings import OFFLINE, DEBUG
from core.processor import ArticleProcessor
from utils.logging_config_enhanced import setup_logging, configure_debug_mode
from utils.structured_logger import get_structured_logger
import time


def main():
    """Main entry point - simple orchestration"""
    # Setup logging
    setup_logging()
    if DEBUG:
        configure_debug_mode(enabled=True)
    
    logger = get_structured_logger(__name__)
    mode = "OFFLINE" if OFFLINE else "LIVE"
    enabled_sources = [config.name for config in SCRAPER_CONFIGS if config.enabled]
    
    logger.info(f"Starting {mode} mode with {len(enabled_sources)} sources")
    
    # Process all sources
    start_time = time.time()
    total_processed, total_attempted = ArticleProcessor.process_all_sources()
    elapsed_time = time.time() - start_time
    
    # Simple summary
    success_rate = (total_processed / total_attempted * 100) if total_attempted > 0 else 0
    logger.info(
        f"Completed: {total_processed}/{total_attempted} articles "
        f"({success_rate:.1f}% success rate) in {elapsed_time:.1f}s"
    )


if __name__ == "__main__":
    main()