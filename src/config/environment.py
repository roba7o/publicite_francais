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


# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
VALID_ENVIRONMENTS = {"development", "test", "production"}
IS_TEST = ENVIRONMENT == "test"
DEBUG = ENVIRONMENT == "development"

# Validate environment
if ENVIRONMENT not in VALID_ENVIRONMENTS:
    raise ValueError(
        f"Invalid ENVIRONMENT: {ENVIRONMENT}. Must be one of: {VALID_ENVIRONMENTS}"
    )

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


# Single schema approach - no environment-based schema switching
# All environments use the public schema with separate databases
