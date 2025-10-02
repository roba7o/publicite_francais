"""
Simple environment configuration management.

Direct access to environment variables with type safety and defaults.
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# type helpers for reading env vars -> os.getenv returns Optional[str]
def get_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


# Core settings
DEBUG = get_bool("DEBUG", True)
TEST_MODE = get_bool("TEST_MODE", False)

# Database configuration - switches between dev and test databases
if TEST_MODE:
    DATABASE_CONFIG = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": get_int("POSTGRES_PORT_TEST", 5433),
        "database": os.getenv("POSTGRES_DB_TEST", "french_news_test_db"),
        "user": os.getenv("POSTGRES_USER", "news_user"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    }
else:
    DATABASE_CONFIG = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": get_int("POSTGRES_PORT", 5432),
        "database": os.getenv("POSTGRES_DB", "french_news_db"),
        "user": os.getenv("POSTGRES_USER", "news_user"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    }

# Processing settings
CONCURRENT_FETCHERS = get_int("CONCURRENT_FETCHERS", 3)
FETCH_TIMEOUT = get_int("FETCH_TIMEOUT", 30)
