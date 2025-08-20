"""
Schema utilities for database operations.

Simple utilities for getting the correct database schema based on environment.
"""

import os


def get_current_schema() -> str:
    """Get current schema name dynamically based on environment."""
    # Replicate settings.py logic but evaluate dynamically
    database_env = os.getenv("DATABASE_ENV") or (
        "test" if os.getenv("TEST_MODE", "false").lower() == "true" else "dev"
    )

    schema_config = {
        "test": os.getenv("NEWS_DATA_TEST_SCHEMA", "news_data_test"),
        "dev": os.getenv("NEWS_DATA_DEV_SCHEMA", "news_data_dev"),
        "prod": os.getenv("NEWS_DATA_PROD_SCHEMA", "news_data_prod"),
    }

    return schema_config[database_env]