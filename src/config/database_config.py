"""
Clean database configuration management.

Provides environment-specific database configurations without hardcoded if/else logic.
"""

import os
from typing import Dict, Any


class DatabaseConfig:
    """Clean database configuration with environment separation."""

    CONFIGS = {
        "dev": {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "french_news_db"),
            "user": os.getenv("POSTGRES_USER", "news_user"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        },
        "test": {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT_TEST", "5433")),
            "database": os.getenv("POSTGRES_DB_TEST", "french_news_test_db"),
            "user": os.getenv("POSTGRES_USER", "news_user"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        }
    }

    @classmethod
    def get_config(cls, test_mode: bool = False) -> Dict[str, Any]:
        """Get database configuration for the specified environment."""
        env = "test" if test_mode else "dev"
        return cls.CONFIGS[env].copy()