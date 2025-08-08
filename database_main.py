#!/usr/bin/env python3
"""
Database-focused main script for raw data collection.

This script:
- Uses your existing scrapers (unchanged)
- Uses Database parsers (extend DatabaseBaseParser)
- Stores raw data in database only via to_database() 
- NO CSV output, NO word frequencies

Run this alongside your existing system to compare approaches.
The goal is to eventually replace main.py with this approach.
"""

import sys
import time
from pathlib import Path

# Add src directory to Python path  
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from config.settings import DEBUG, OFFLINE, DATABASE_ENABLED
from database import initialize_database
from core.database_processor import DatabaseProcessor
from utils.logging_config_enhanced import configure_debug_mode, setup_logging
from utils.structured_logger import get_structured_logger


def create_database_configs():
    """
    Create database-focused source configurations.
    
    Uses your existing scraper classes but Database parsers.
    """
    return [
        {
            "name": "Slate.fr",
            "enabled": True,
            "scraper_class": "scrapers.slate_fr_scraper.SlateFrURLScraper",  # Your existing scraper
            "scraper_kwargs": {"debug": DEBUG}
        },
        # Add other sources as you create database parsers for them
        # {
        #     "name": "FranceInfo.fr", 
        #     "enabled": False,
        #     "scraper_class": "scrapers.france_info_scraper.FranceInfoURLScraper",
        #     "scraper_kwargs": {"debug": DEBUG}
        # },
    ]


def main():
    """Main entry point for database-focused data collection."""
    # Setup logging (same as your existing system)
    setup_logging()
    if DEBUG:
        configure_debug_mode(enabled=True)

    logger = get_structured_logger(__name__)
    mode = "OFFLINE" if OFFLINE else "LIVE"
    
    logger.info(f"🚀 Starting DATABASE French news collection ({mode} mode)")

    # Check database is enabled and connected
    if not DATABASE_ENABLED:
        logger.error("❌ Database not enabled - set DATABASE_ENABLED=true")
        print("❌ Database not enabled. Set DATABASE_ENABLED=true in config.")
        return 1

    if not initialize_database():
        logger.error("❌ Database initialization failed")
        print("❌ Database connection failed. Check PostgreSQL is running.")
        return 1

    # Create source configurations
    source_configs = create_database_configs()
    enabled_sources = [config for config in source_configs if config.get("enabled", True)]

    logger.info(
        "Starting database collection",
        extra_data={
            "enabled_sources": len(enabled_sources),
            "mode": mode,
            "database_enabled": DATABASE_ENABLED
        }
    )

    # Process all sources
    start_time = time.time()
    total_stored, total_attempted = DatabaseProcessor.process_all_sources(source_configs)
    elapsed_time = time.time() - start_time

    # Summary
    success_rate = (total_stored / total_attempted * 100) if total_attempted > 0 else 0
    
    logger.info(
        "🎉 Database collection completed",
        extra_data={
            "articles_stored": total_stored,
            "articles_attempted": total_attempted,
            "success_rate_percent": round(success_rate, 1),
            "elapsed_time_seconds": round(elapsed_time, 2)
        }
    )

    print(f"\n✅ Database Collection Results:")
    print(f"   📰 Raw articles stored: {total_stored}")
    print(f"   🎯 Success rate: {success_rate:.1f}%") 
    print(f"   ⏱️  Time taken: {elapsed_time:.1f}s")
    print(f"\n🔍 Check database:")
    print(f"   docker compose exec postgres psql -U news_user -d french_news -c")
    print(f"   \"SELECT title, LENGTH(full_text), scraped_at FROM news_data.articles ORDER BY scraped_at DESC LIMIT 3;\"")
    print(f"\n💡 Next: Gradually migrate other parsers to Database* versions!")

    return 0 if total_stored > 0 else 1


if __name__ == "__main__":
    sys.exit(main())