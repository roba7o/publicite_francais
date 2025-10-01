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


# Original fixtures below
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
