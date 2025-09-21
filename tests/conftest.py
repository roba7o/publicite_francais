from unittest import mock

import pytest
from tests.fixtures.helpers import DummyClass

from core.component_factory import ComponentFactory


@pytest.fixture
def factory():
    return ComponentFactory()


@pytest.fixture
def mock_import_class():
    with mock.patch.object(ComponentFactory, "import_class") as mock_import:
        mock_import.return_value = DummyClass
        yield mock_import


@pytest.fixture
def collector_config():
    return {
        "site": "example",
        "url_collector_class": "tests.fixtures.helpers.DummyClass",
        "soup_validator_class": "tests.fixtures.helpers.DummyClass",
        "url_collector_kwargs": {"arg1": 1, "arg2": 2},
        "soup_validator_kwargs": {"arg1": 1, "arg2": 2},
    }
