"""
Environment configuration management.

Single source of truth for environment-based settings.

Configuration priority:
1. Environment variables (set externally or in .env)
2. Defaults defined here

Quick config (when not using env vars):
- Set DEFAULT_ENVIRONMENT to switch between 'development' and 'test'
- Set DEFAULT_DEBUG to control logging verbosity
"""

import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# Generate unique RUN_ID for this execution
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")


def _get_int(key: str, default: int) -> int:
    """Parse integer from environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _get_bool(key: str, default: bool) -> bool:
    """Parse boolean from environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


# ============================================================================
# QUICK CONFIG - Edit these defaults when not using environment variables
# ============================================================================
# Examples:
#   Run dev with debug:    DEFAULT_ENVIRONMENT = "development", DEFAULT_DEBUG = True
#   Run dev without debug: DEFAULT_ENVIRONMENT = "development", DEFAULT_DEBUG = False
#   Run tests with debug:  DEFAULT_ENVIRONMENT = "test", DEFAULT_DEBUG = True
#   Run tests quietly:     DEFAULT_ENVIRONMENT = "test", DEFAULT_DEBUG = False
# ============================================================================
DEFAULT_ENVIRONMENT = "development"  # Options: "development" or "test"
DEFAULT_DEBUG = False  # Set True to enable verbose logging


# ============================================================================
# Environment setup (uses env vars if set, otherwise uses defaults above)
# ============================================================================
ENVIRONMENT = os.getenv("ENVIRONMENT", DEFAULT_ENVIRONMENT).lower()

if ENVIRONMENT not in {"development", "test"}:
    raise ValueError(
        f"Invalid ENVIRONMENT: {ENVIRONMENT}. Must be 'development' or 'test'"
    )

DEBUG = _get_bool("DEBUG", DEFAULT_DEBUG)


# Database configuration
if ENVIRONMENT == "test":
    DATABASE_CONFIG = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": _get_int("POSTGRES_PORT_TEST", 5433),
        "database": os.getenv("POSTGRES_DB_TEST", "french_news_test"),
        "user": os.getenv("POSTGRES_USER", "news_user"),
        "password": os.getenv("POSTGRES_PASSWORD_TEST", "test_password"),
    }
else:  # development
    DATABASE_CONFIG = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": _get_int("POSTGRES_PORT", 5432),
        "database": os.getenv("POSTGRES_DB", "french_news"),
        "user": os.getenv("POSTGRES_USER", "news_user"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    }


# Application settings
CONCURRENT_FETCHERS = _get_int("CONCURRENT_FETCHERS", 3)
FETCH_TIMEOUT = _get_int("FETCH_TIMEOUT", 30)

# Scraping limits - Set to None for unlimited articles
# Override with MAX_ARTICLES env var (e.g., MAX_ARTICLES=50)
_max_articles_env = os.getenv("MAX_ARTICLES")
MAX_ARTICLES = int(_max_articles_env) if _max_articles_env else None

# Logging configuration
LOG_TO_FILE = _get_bool("LOG_TO_FILE", True)  # Default to file logging

# Create logs directory if it doesn't exist
_logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(_logs_dir, exist_ok=True)

# Generate timestamped log file path
LOG_FILE_PATH = os.path.join(_logs_dir, f"{RUN_ID}.log")
LOG_LATEST_PATH = os.path.join(_logs_dir, "latest.log")
