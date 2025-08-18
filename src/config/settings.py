"""
Global settings for the French article scraping system.

This module contains configuration flags that control the behavior
of the entire scraping system, including database connectivity.
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable debug logging for detailed output
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Mode detection: TEST_MODE determines scraping behavior and schema
# True: Use local test files from test_data/ directory (test schema)
# False: Scrape live websites (dev schema) - DEFAULT
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

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
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    # Connection pool settings removed - not used by current SQLAlchemy setup
}

# Database functionality is always enabled (no CSV fallback implemented)
# DATABASE_ENABLED removed - database is required for this pipeline

# Database schema environment - auto-detected based on mode
# - TEST_MODE=true → "test" schema (for testing with HTML files)
# - TEST_MODE=false → "dev" schema (for live scraping)
# - Production: Set DATABASE_ENV=prod manually
DATABASE_ENV = os.getenv("DATABASE_ENV") or ("test" if TEST_MODE else "dev")

# Schema configuration mapping
SCHEMA_CONFIG = {
    "test": os.getenv("NEWS_DATA_TEST_SCHEMA", "news_data_test"),
    "dev": os.getenv("NEWS_DATA_DEV_SCHEMA", "news_data_dev"),
    "prod": os.getenv("NEWS_DATA_PROD_SCHEMA", "news_data_prod"),
}

# Pre-computed schema name for current environment
NEWS_DATA_SCHEMA = SCHEMA_CONFIG[DATABASE_ENV]

# Pipeline quality thresholds
MIN_SUCCESS_RATE_THRESHOLD = 50.0
