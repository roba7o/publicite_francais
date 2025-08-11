"""
Global settings for the French article scraping system.

This module contains configuration flags that control the behavior
of the entire scraping system, including database connectivity.
"""

import os

# Enable debug logging for detailed output
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Switch between live scraping and offline test mode
# True: Use local test files from test_data/ directory
# False: Scrape live websites
OFFLINE = os.getenv("OFFLINE", "true").lower() == "true"

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Database connection settings
# These can be overridden by environment variables for different environments
DATABASE_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "french_news"),
    "user": os.getenv("POSTGRES_USER", "news_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "dev_password_123"),
    "min_connections": int(os.getenv("DB_MIN_CONNECTIONS", 1)),
    "max_connections": int(os.getenv("DB_MAX_CONNECTIONS", 20)),
    "connection_timeout": int(os.getenv("DB_TIMEOUT", 30)),
}

# Enable database functionality
# True: Use PostgreSQL database (current behavior)
# False: Disable database storage
DATABASE_ENABLED = os.getenv("DATABASE_ENABLED", "true").lower() == "true"

# Database schema environment
# This determines which schema to use for articles and sources:
# - "test": Uses news_data_test schema (for integration testing with HTML files)
# - "dev": Uses news_data_dev schema (for development with real/live data)
# - "prod": Uses news_data_prod schema (for production)
DATABASE_ENV = os.getenv("DATABASE_ENV", "test" if OFFLINE else "dev")
