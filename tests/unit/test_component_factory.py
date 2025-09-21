import pytest
from tests.fixtures.helpers import DummyClass

from core.component_factory import ComponentFactory


def test_import_class_not_full_path():
    incorrect_path = "notFullClassPath"
    with pytest.raises(ImportError, match="Invalid class path"):
        ComponentFactory.import_class(incorrect_path)


def test_import_class_happy():
    class_path = "tests.fixtures.helpers.DummyClass"
    imported_class = ComponentFactory.import_class(class_path)
    assert imported_class is DummyClass
