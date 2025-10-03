"""
Simple environment configuration management.

Direct access to environment variables with type safety and defaults.
"""

import os

from dotenv import load_dotenv

from config.database_config import DatabaseConfig

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
TEST_MODE = get_bool("TEST_MODE", False)  # Backwards compatibility
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev").lower()

# Database configuration - clean separation by environment
DATABASE_CONFIG = DatabaseConfig.get_config(test_mode=(ENVIRONMENT == "test" or TEST_MODE))

# Processing settings
CONCURRENT_FETCHERS = get_int("CONCURRENT_FETCHERS", 3)
FETCH_TIMEOUT = get_int("FETCH_TIMEOUT", 30)
