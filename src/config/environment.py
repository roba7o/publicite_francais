"""
Centralized environment configuration management.

This module provides a single source of truth for environment variable handling
and configuration across the application. It replaces direct os.environ calls
with a structured config system.
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class EnvironmentConfig:
    """
    Centralized configuration manager for environment variables.

    Provides type-safe access to environment variables with sensible defaults
    and eliminates the need for direct os.environ calls throughout the codebase.
    """

    def __init__(self):
        """Initialize the configuration manager."""
        self._config_cache = {}
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load all configuration values from environment variables."""
        # Core application settings
        self._config_cache.update(
            {
                # Debug and development settings
                "DEBUG": self._get_bool_env("DEBUG", True),
                "TEST_MODE": self._get_bool_env("TEST_MODE", False),
                "PRODUCTION": self._get_bool_env("PRODUCTION", False),
                # Database connection settings
                "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "localhost"),
                "POSTGRES_PORT": self._get_int_env("POSTGRES_PORT", 5432),
                "POSTGRES_DB": os.getenv("POSTGRES_DB", "french_news"),
                "POSTGRES_USER": os.getenv("POSTGRES_USER", "news_user"),
                "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
                # Schema configuration
                "DATABASE_ENV": self._determine_database_env(),
                "NEWS_DATA_TEST_SCHEMA": os.getenv(
                    "NEWS_DATA_TEST_SCHEMA", "news_data_test"
                ),
                "NEWS_DATA_DEV_SCHEMA": os.getenv(
                    "NEWS_DATA_DEV_SCHEMA", "news_data_dev"
                ),
                "NEWS_DATA_PROD_SCHEMA": os.getenv(
                    "NEWS_DATA_PROD_SCHEMA", "news_data_prod"
                ),
                # Concurrent processing settings
                "CONCURRENT_FETCHERS": self._get_int_env("CONCURRENT_FETCHERS", 3),
                "FETCH_TIMEOUT": self._get_int_env("FETCH_TIMEOUT", 30),
            }
        )

    def _get_bool_env(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable with type safety."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable with type safety."""
        try:
            return int(os.getenv(key, str(default)))
        except (ValueError, TypeError):
            return default

    def _determine_database_env(self) -> str:
        """Determine the database environment based on mode and explicit setting."""
        explicit_env = os.getenv("DATABASE_ENV")
        if explicit_env:
            return explicit_env

        # Auto-detect based on TEST_MODE
        test_mode = self._get_bool_env("TEST_MODE", False)
        return "test" if test_mode else "dev"

    def get(self, key: str, default=None):
        """
        Get configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config_cache.get(key, default)

    def is_test_mode(self) -> bool:
        """Check if application is running in test mode."""
        return self.get("TEST_MODE", False)

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get("DEBUG", True)

    def is_production(self) -> bool:
        """Check if application is running in production mode."""
        return self.get("PRODUCTION", False)

    def get_database_config(self) -> dict[str, str | int]:
        """Get database connection configuration."""
        return {
            "host": self.get("POSTGRES_HOST"),
            "port": self.get("POSTGRES_PORT"),
            "database": self.get("POSTGRES_DB"),
            "user": self.get("POSTGRES_USER"),
            "password": self.get("POSTGRES_PASSWORD"),
        }

    def get_database_env(self) -> str:
        """Get the current database environment (test/dev/prod)."""
        return self.get("DATABASE_ENV", "dev")

    def get_news_data_schema(self) -> str:
        """Get the news data schema name for current environment."""
        env = self.get_database_env()
        schema_map = {
            "test": self.get("NEWS_DATA_TEST_SCHEMA"),
            "dev": self.get("NEWS_DATA_DEV_SCHEMA"),
            "prod": self.get("NEWS_DATA_PROD_SCHEMA"),
        }
        return schema_map.get(env, schema_map["dev"])

    def get_concurrent_fetchers(self) -> int:
        """Get number of concurrent URL fetchers."""
        return self.get("CONCURRENT_FETCHERS", 3)

    def get_fetch_timeout(self) -> int:
        """Get timeout for URL fetching in seconds."""
        return self.get("FETCH_TIMEOUT", 30)

    def refresh(self) -> None:
        """Refresh configuration from environment variables."""
        self._config_cache.clear()
        self._load_configuration()


# Global configuration instance
env_config = EnvironmentConfig()


# Convenience functions for common operations
def is_test_mode() -> bool:
    """Check if application is running in test mode."""
    return env_config.is_test_mode()


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return env_config.is_debug_mode()


def is_production() -> bool:
    """Check if application is running in production mode."""
    return env_config.is_production()


def get_database_config() -> dict[str, str | int]:
    """Get database connection configuration."""
    return env_config.get_database_config()


def get_database_env() -> str:
    """Get the current database environment."""
    return env_config.get_database_env()


def get_news_data_schema() -> str:
    """Get the news data schema name for current environment."""
    return env_config.get_news_data_schema()
