"""
Essential unit tests for BaseUrlCollector.

Tests core behavior without overcomplexity.
"""

from unittest.mock import Mock

import pytest
import requests

from core.components.url_collectors.base_url_collector import BaseUrlCollector


class MockUrlCollector(BaseUrlCollector):
    """Concrete implementation for testing abstract base class."""

    def get_article_urls(self):
        return ["https://test.com/article1", "https://test.com/article2"]


@pytest.fixture
def collector():
    """Create a URL collector instance for testing."""
    return MockUrlCollector()


def test_initialization(collector):
    """Test collector can be created with basic parameters."""
    assert collector.base_url == ""
    assert hasattr(collector, "logger")
    assert hasattr(collector, "debug")


@pytest.mark.parametrize("debug_value", [True, False])
def test_initialization_with_debug(debug_value):
    """Test collector can be created with debug parameter."""
    collector = MockUrlCollector(debug=debug_value)
    assert collector.debug is debug_value


def test_make_request_successful(collector, monkeypatch):
    """Test successful HTTP request."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None

    monkeypatch.setattr(collector, "make_request", lambda url, timeout: mock_response)

    result = collector._make_request("https://test.com")

    assert result is mock_response


def test_make_request_handles_exception(collector, monkeypatch):
    """Test HTTP request handles exceptions."""
    error_calls = []

    def mock_make_request(*args, **kwargs):
        raise requests.exceptions.RequestException("Network error")

    def mock_error(*args, **kwargs):
        error_calls.append(1)

    monkeypatch.setattr(collector, "make_request", mock_make_request)
    monkeypatch.setattr(collector.logger, "error", mock_error)

    with pytest.raises(requests.exceptions.RequestException):
        collector._make_request("https://test.com")

    assert len(error_calls) == 1


def test_log_results_in_debug_mode(collector, monkeypatch):
    """Test that results are logged when debug is enabled."""
    collector.debug = True
    info_calls = []
    debug_calls = []

    monkeypatch.setattr(
        collector.logger, "info", lambda *args: info_calls.append(args[0])
    )
    monkeypatch.setattr(
        collector.logger, "debug", lambda *args: debug_calls.append(args[0])
    )

    urls = ["https://test.com/1", "https://test.com/2"]
    collector._log_results(urls)

    assert len(info_calls) == 1
    assert "Found 2 article URLs" in info_calls[0]
    assert len(debug_calls) == 2


def test_log_results_not_in_debug_mode(collector, monkeypatch):
    """Test that results are not logged when debug is disabled."""
    collector.debug = False
    info_calls = []

    monkeypatch.setattr(collector.logger, "info", lambda *args: info_calls.append(1))

    urls = ["https://test.com/1", "https://test.com/2"]
    collector._log_results(urls)

    assert len(info_calls) == 0


@pytest.mark.parametrize(
    "urls,expected",
    [
        # Test deduplication
        (
            [
                "https://test.com/1",
                "https://test.com/2",
                "https://test.com/1",
                "https://test.com/3",
                "https://test.com/2",
            ],
            ["https://test.com/1", "https://test.com/2", "https://test.com/3"],
        ),
        # Test order preservation
        (
            ["https://b.com", "https://a.com", "https://c.com", "https://a.com"],
            ["https://b.com", "https://a.com", "https://c.com"],
        ),
        # Test empty list
        ([], []),
        # Test no duplicates
        (["https://a.com", "https://b.com"], ["https://a.com", "https://b.com"]),
    ],
)
def test_deduplicate_urls(collector, urls, expected):
    """Test URL deduplication removes duplicates while preserving order."""
    result = collector._deduplicate_urls(urls)
    assert result == expected


def test_abstract_class_cannot_be_instantiated():
    """Test that abstract base class cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseUrlCollector()  # type: ignore
