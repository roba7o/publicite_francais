"""
Essential unit tests for BaseSoupValidator.

Tests core behavior without overcomplexity.
"""

from unittest.mock import Mock

import pytest
from bs4 import BeautifulSoup

from core.components.soup_validators.base_soup_validator import BaseSoupValidator


class MockSoupValidator(BaseSoupValidator):
    """Concrete implementation for testing abstract base class."""

    def validate_and_extract(self, soup, url):
        return None


@pytest.fixture
def validator():
    """Create a validator instance for testing."""
    return MockSoupValidator("test.com", "Test Site", 1.0)


@pytest.fixture
def soup_with_h1():
    """BeautifulSoup object with h1 tag."""
    html = "<html><body><h1>Test Title</h1><p>Content</p></body></html>"
    return BeautifulSoup(html, "html.parser")


@pytest.fixture
def soup_without_h1():
    """BeautifulSoup object without h1 tag."""
    html = "<html><body><p>Content only</p></body></html>"
    return BeautifulSoup(html, "html.parser")


def test_initialization(validator):
    """Test validator can be created with basic parameters."""
    assert validator.site_domain == "test.com"
    assert validator.site_name == "Test Site"
    assert validator.delay == 1.0


def test_domain_validation_passes(validator, monkeypatch):
    """Test domain validation passes for matching domain."""
    monkeypatch.setattr(validator, "validate_url_domain", lambda url, domain: True)

    result = validator._validate_domain_and_log("https://test.com/article", "test.com")

    assert result is True


def test_domain_validation_fails(validator, monkeypatch):
    """Test domain validation fails for non-matching domain."""
    monkeypatch.setattr(validator, "validate_url_domain", lambda url, domain: False)
    warning_calls = []
    monkeypatch.setattr(
        validator.logger, "warning", lambda *args, **kwargs: warning_calls.append(1)
    )

    result = validator._validate_domain_and_log("https://wrong.com/article", "test.com")

    assert result is False
    assert len(warning_calls) == 1


def test_title_validation_with_h1(validator, soup_with_h1):
    """Test title validation passes when h1 tag is present."""
    result = validator._validate_title_structure(
        soup_with_h1, "https://test.com/article"
    )

    assert result is True


def test_title_validation_without_h1(validator, soup_without_h1, monkeypatch):
    """Test title validation fails when h1 tag is missing."""
    warning_calls = []
    monkeypatch.setattr(
        validator.logger, "warning", lambda *args, **kwargs: warning_calls.append(1)
    )

    result = validator._validate_title_structure(
        soup_without_h1, "https://test.com/article"
    )

    assert result is False
    assert len(warning_calls) == 1


def test_url_fetch_in_test_mode(validator, monkeypatch):
    """Test that URL fetching returns None when in TEST_MODE."""
    monkeypatch.setattr(
        "core.components.soup_validators.base_soup_validator.TEST_MODE", True
    )
    warning_calls = []
    monkeypatch.setattr(
        validator.logger, "warning", lambda *args, **kwargs: warning_calls.append(1)
    )

    result = validator.get_soup_from_url("https://test.com/article")

    assert result is None
    assert len(warning_calls) == 1


def test_url_fetch_successful(validator, monkeypatch):
    """Test successful URL fetching and parsing."""
    monkeypatch.setattr(
        "core.components.soup_validators.base_soup_validator.TEST_MODE", False
    )

    html = "<html><body><h1>Test</h1></body></html>" + "x" * 100  # Long enough content
    mock_response = Mock()
    mock_response.content = html.encode("utf-8")
    mock_response.raise_for_status.return_value = None

    monkeypatch.setattr(validator, "make_request", lambda url, timeout: mock_response)
    monkeypatch.setattr(
        validator, "parse_html_fast", lambda content: BeautifulSoup(html, "html.parser")
    )

    result = validator.get_soup_from_url("https://test.com/article")

    assert result is not None
    assert isinstance(result, BeautifulSoup)


def test_directory_loading_nonexistent(validator, monkeypatch):
    """Test handling of non-existent test directory."""
    warning_calls = []
    monkeypatch.setattr(
        validator.logger, "warning", lambda *args, **kwargs: warning_calls.append(1)
    )

    result = validator.get_test_sources_from_directory("nonexistent.site")

    assert result == []
    assert len(warning_calls) == 1


def test_directory_loading_valid_files(validator, monkeypatch):
    """Test loading test sources from existing directory."""
    mock_file = Mock()
    mock_file.suffix = ".html"
    mock_file.name = "test.html"

    html = "<html><body><h1>Test</h1></body></html>"

    # Mock path operations
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    monkeypatch.setattr("pathlib.Path.iterdir", lambda self: [mock_file])
    monkeypatch.setattr(
        "utils.url_mapping.URL_MAPPING", {"test.html": "https://test.com/article"}
    )

    # Mock file reading
    def mock_open(*args, **kwargs):
        class MockFile:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                return html

        return MockFile()

    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(
        validator, "parse_html_fast", lambda content: BeautifulSoup(html, "html.parser")
    )

    result = validator.get_test_sources_from_directory("slate.fr")

    assert len(result) == 1
    soup, url = result[0]
    assert isinstance(soup, BeautifulSoup)
    assert url == "https://test.com/article"


def test_abstract_class_cannot_be_instantiated():
    """Test that abstract base class cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseSoupValidator("test.com", "Test", 1.0)  # type: ignore
