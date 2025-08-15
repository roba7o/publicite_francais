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
    "password": os.getenv("POSTGRES_PASSWORD"),
    # Connection pool settings removed - not used by current SQLAlchemy setup
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

# Schema configuration mapping
SCHEMA_CONFIG = {
    "news_data": {
        "test": os.getenv("NEWS_DATA_TEST_SCHEMA", "news_data_test"),
        "dev": os.getenv("NEWS_DATA_DEV_SCHEMA", "news_data_dev"),
        "prod": os.getenv("NEWS_DATA_PROD_SCHEMA", "news_data_prod"),
    },
    "dbt": {
        "test": os.getenv("DBT_TEST_SCHEMA", "dbt_test"),
        "dev": os.getenv("DBT_DEV_SCHEMA", "dbt_dev"),
        "prod": os.getenv("DBT_PROD_SCHEMA", "dbt_prod"),
    },
}

# Pre-computed schema names for current environment
NEWS_DATA_SCHEMA = SCHEMA_CONFIG["news_data"][DATABASE_ENV]
# DBT_SCHEMA removed - not used anywhere in codebase


def get_schema_name(schema_type: str, env: str = None) -> str:
    """
    Get schema name for given type and environment.

    Args:
        schema_type: Type of schema ('news_data' or 'dbt')
        env: Environment ('test', 'dev', 'prod'). If None, uses DATABASE_ENV

    Returns:
        Schema name string

    Raises:
        KeyError: If schema_type or env not found in configuration
    """
    if env is None:
        env = DATABASE_ENV

    return SCHEMA_CONFIG[schema_type][env]
