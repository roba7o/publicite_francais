"""
Test configuration and fixtures for pytest.

Includes both original test fixtures and automatic ENVIRONMENT=test setup.
"""

import os
import sys
from unittest import mock

import pytest
from tests.fixtures.helpers import DummyClass

from core.component_factory import ComponentFactory

# Set ENVIRONMENT=test immediately when conftest.py is imported
os.environ["ENVIRONMENT"] = "test"

# Clear any cached environment modules
modules_to_clear = [mod for mod in sys.modules.keys() if mod.startswith("config")]
for mod in modules_to_clear:
    del sys.modules[mod]


@pytest.fixture(autouse=True, scope="session")
def setup_test_environment():
    """
    Ensure ENVIRONMENT=test for all tests.

    This is set at import time above, but this fixture ensures
    it stays set throughout the test session.
    """
    # Verify ENVIRONMENT is set to test
    assert os.environ.get("ENVIRONMENT") == "test", (
        "ENVIRONMENT should be set to 'test'"
    )


@pytest.fixture(scope="session")
def test_database():
    """
    Set up test database for all tests using application's database layer.

    Uses the application's own database initialization and connection management.
    """
    from database.database import initialize_database

    # Initialize database using application's own function
    success = initialize_database()
    assert success, "Failed to initialize test database"

    # Tests will use get_session() from the application
    yield "initialized"


@pytest.fixture
def clean_test_db(test_database):
    """
    Clean test database using application's database layer.

    This ensures test isolation by clearing all data using the same
    database functions that the application uses.
    """
    from database.database import clear_test_database

    # Clear database using application's own function
    success = clear_test_database()
    assert success, "Failed to clear test database"

    # Tests can now use get_session() and other database functions normally
    yield


# Component testing fixtures
@pytest.fixture
def factory():
    """ComponentFactory instance for testing."""
    return ComponentFactory()


@pytest.fixture
def mock_import_class():
    """Mock ComponentFactory.import_class to return DummyClass."""
    with mock.patch.object(ComponentFactory, "import_class") as mock_import:
        mock_import.return_value = DummyClass
        yield mock_import


@pytest.fixture
def collector_config():
    """Standard collector configuration for testing."""
    return {
        "site": "example",
        "url_collector_class": "tests.fixtures.helpers.DummyClass",
        "soup_validator_class": "tests.fixtures.helpers.DummyClass",
        "url_collector_kwargs": {"arg1": 1, "arg2": 2},
        "soup_validator_kwargs": {"arg1": 1, "arg2": 2},
    }
