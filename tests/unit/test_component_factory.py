import pytest
from tests.fixtures.helpers import DummyClass

from core.component_factory import ComponentFactory


def test_import_class_happy():
    class_path = "tests.fixtures.helpers.DummyClass"
    imported_class = ComponentFactory.import_class(class_path)
    assert imported_class is DummyClass


def test_import_class_not_full_path():
    incorrect_path = "notFullClassPath"
    with pytest.raises(ImportError, match="Invalid class path"):
        ComponentFactory.import_class(incorrect_path)


def test_create_component_happy(mock_import_class):
    dummy_class_path = "tests.fixtures.helpers.DummyClass"
    result = ComponentFactory.create_component(dummy_class_path)
    assert isinstance(result, DummyClass)


def test_create_component_invalid_class_path():
    invalid_path = "not really a path"
    with pytest.raises(ImportError, match="Invalid class path"):
        ComponentFactory.create_component(invalid_path)


def test_create_collector_happy(factory, collector_config, mock_import_class):
    result = factory.create_collector(collector_config)
    assert isinstance(result, DummyClass)


def test_create_collector_invalid_config(factory, mock_import_class):
    with pytest.raises(ValueError, match="No url_collector_class specified"):
        factory.create_collector({"site": None})


def test_create_validator_happy(factory, collector_config, mock_import_class):
    result = factory.create_validator(collector_config)
    assert isinstance(result, DummyClass)


def test_create_validator_invalid_config(factory, mock_import_class):
    with pytest.raises(ValueError, match="No soup_validator_class specified"):
        factory.create_validator({"site": None})
