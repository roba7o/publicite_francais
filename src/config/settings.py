"""
Global settings for the French article scraping system.

This module contains configuration flags that control the behavior
of the entire scraping system, including database connectivity.
"""

import os

# Enable debug logging for detailed output
DEBUG = True

# Switch between live scraping and offline test mode
# True: Use local test files from test_data/ directory
# False: Scrape live websites
OFFLINE = True

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Database connection settings
# These can be overridden by environment variables for different environments
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "french_news"),
    "user": os.getenv("DB_USER", "news_user"),
    "password": os.getenv("DB_PASSWORD", "dev_password_123"),
    "min_connections": int(os.getenv("DB_MIN_CONNECTIONS", 1)),
    "max_connections": int(os.getenv("DB_MAX_CONNECTIONS", 20)),
    "connection_timeout": int(os.getenv("DB_TIMEOUT", 30)),
}

# Enable database functionality
# True: Use PostgreSQL database for future features
# False: Continue using CSV files only (current behavior)
DATABASE_ENABLED = os.getenv("DATABASE_ENABLED", "true").lower() == "true"

# Environment-based schema selection
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')  # dev, test, prod
SCHEMA_MAPPING = {
    'dev': 'news_data_dev',
    'test': 'news_data_test', 
    'prod': 'news_data_prod'
}
DATABASE_SCHEMA = SCHEMA_MAPPING.get(ENVIRONMENT, 'news_data_dev')
