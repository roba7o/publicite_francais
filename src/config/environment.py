"""
Simple environment configuration management.

Direct access to environment variables with type safety and defaults.
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable with type safety."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_int(key: str, default: int) -> int:
    """Get integer environment variable with type safety."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


# Core settings
DEBUG = get_bool("DEBUG", True)
TEST_MODE = get_bool("TEST_MODE", False)
PRODUCTION = get_bool("PRODUCTION", False)

# Database configuration
DATABASE_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": get_int("POSTGRES_PORT", 5432),
    "database": os.getenv("POSTGRES_DB", "french_news"),
    "user": os.getenv("POSTGRES_USER", "news_user"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}

# Processing settings
CONCURRENT_FETCHERS = get_int("CONCURRENT_FETCHERS", 3)
FETCH_TIMEOUT = get_int("FETCH_TIMEOUT", 30)


def get_database_env() -> str:
    """Get the current database environment (test/dev/prod)."""
    explicit_env = os.getenv("DATABASE_ENV")
    if explicit_env:
        return explicit_env
    return "test" if TEST_MODE else "dev"


def get_news_data_schema() -> str:
    """Get the news data schema name for current environment."""
    env = get_database_env()
    schema_map = {
        "test": os.getenv("NEWS_DATA_TEST_SCHEMA", "news_data_test"),
        "dev": os.getenv("NEWS_DATA_DEV_SCHEMA", "news_data_dev"),
        "prod": os.getenv("NEWS_DATA_PROD_SCHEMA", "news_data_prod"),
    }
    return schema_map.get(env, schema_map["dev"])
