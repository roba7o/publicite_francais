"""
Basic Database Connectivity Tests.

Simple connectivity tests without the full database connection test suite.
These are unit-level tests for basic database functionality.
"""


class TestBasicDatabaseConnectivity:
    """Basic database connectivity tests."""

    def test_database_connectivity_check(self):
        """Test database connectivity without actual database operations."""
        # Database is always enabled (no CSV fallback)
        # This test verifies database configuration can be imported

        from config.environment import DATABASE_CONFIG

        assert isinstance(DATABASE_CONFIG, dict)
        assert "database" in DATABASE_CONFIG

    def test_database_models_import(self):
        """Test that database models can be imported."""
        from database.models import RawArticle

        assert RawArticle is not None

    def test_database_initialization_import(self):
        """Test that database initialization functions can be imported."""
        from database.database import get_session, initialize_database

        assert initialize_database is not None
        assert get_session is not None
