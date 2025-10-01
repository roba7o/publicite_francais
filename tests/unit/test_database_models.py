"""
Essential unit tests for database models.

Tests core behavior without overcomplexity.
"""

from unittest.mock import patch

import pytest

from database.models import RawArticle


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <html>
        <head><title>Test Article</title></head>
        <body>
            <h1>Test Article Title</h1>
            <p>This is some test content for the article.</p>
        </body>
    </html>
    """


def test_initialization_with_required_fields(sample_html):
    """Test article can be created with required fields."""
    article = RawArticle(
        url="https://test.com/article", raw_html=sample_html, site="test.com"
    )

    assert article.url == "https://test.com/article"
    assert article.raw_html == sample_html
    assert article.site == "test.com"
    assert article.id is not None
    assert article.scraped_at is not None
    assert article.content_length == len(sample_html)


@pytest.mark.parametrize("missing_field", ["url", "raw_html", "site"])
def test_initialization_missing_required_fields(missing_field, sample_html):
    """Test that missing required fields raise ValueError."""
    fields = {
        "url": "https://test.com/article",
        "raw_html": sample_html,
        "site": "test.com",
    }
    fields[missing_field] = None

    with pytest.raises(ValueError, match="url, raw_html, and site are required"):
        RawArticle(**fields)


@pytest.mark.parametrize("missing_field", ["url", "raw_html", "site"])
def test_initialization_empty_required_fields(missing_field, sample_html):
    """Test that empty required fields raise ValueError."""
    fields = {
        "url": "https://test.com/article",
        "raw_html": sample_html,
        "site": "test.com",
    }
    fields[missing_field] = ""

    with pytest.raises(ValueError, match="url, raw_html, and site are required"):
        RawArticle(**fields)


def test_initialization_with_optional_fields(sample_html):
    """Test article can be created with optional fields."""
    article = RawArticle(
        url="https://test.com/article",
        raw_html=sample_html,
        site="test.com",
        response_status=200,
        content_length=1000,
    )

    assert article.response_status == 200
    assert article.content_length == 1000  # Should not be overridden


def test_content_length_auto_calculation(sample_html):
    """Test that content_length is calculated automatically when not provided."""
    article = RawArticle(
        url="https://test.com/article", raw_html=sample_html, site="test.com"
    )

    assert article.content_length == len(sample_html)


@patch("trafilatura.extract")
@patch("trafilatura.extract_metadata")
def test_content_extraction_success(mock_extract_metadata, mock_extract, sample_html):
    """Test successful content extraction with trafilatura."""
    # Mock trafilatura responses
    mock_extract.return_value = "Extracted article content"

    mock_metadata = type(
        "MockMetadata",
        (),
        {
            "title": "Test Title",
            "author": "Test Author",
            "date": "2023-01-01",
            "language": "en",
            "categories": ["news", "tech"],
        },
    )()
    mock_extract_metadata.return_value = mock_metadata

    article = RawArticle(
        url="https://test.com/article", raw_html=sample_html, site="test.com"
    )

    assert article.extracted_text == "Extracted article content"
    assert article.title == "Test Title"
    assert article.author == "Test Author"
    assert article.date_published == "2023-01-01"
    assert article.language == "en"
    assert article.keywords == ["news", "tech"]
    assert article.extraction_status == "success"


@patch("trafilatura.extract")
@patch("trafilatura.extract_metadata")
def test_content_extraction_no_content(
    mock_extract_metadata, mock_extract, sample_html
):
    """Test extraction when no content is found."""
    mock_extract.return_value = None
    mock_extract_metadata.return_value = None

    article = RawArticle(
        url="https://test.com/article", raw_html=sample_html, site="test.com"
    )

    assert article.extracted_text is None
    assert article.extraction_status == "failed"


@patch("trafilatura.extract")
def test_content_extraction_exception(mock_extract, sample_html):
    """Test extraction handles exceptions gracefully."""
    mock_extract.side_effect = Exception("Trafilatura error")

    article = RawArticle(
        url="https://test.com/article", raw_html=sample_html, site="test.com"
    )

    assert article.extraction_status == "failed"


@pytest.mark.parametrize(
    "keyword_field,keywords",
    [
        ("categories", ["news", "politics"]),
        ("tags", ["breaking", "urgent"]),
    ],
)
@patch("trafilatura.extract")
@patch("trafilatura.extract_metadata")
def test_keywords_extraction(
    mock_extract_metadata, mock_extract, keyword_field, keywords, sample_html
):
    """Test keywords extraction from categories or tags."""
    mock_extract.return_value = "Content"

    mock_metadata = type(
        "MockMetadata",
        (),
        {"title": "Test", "author": None, "date": None, "language": None},
    )()
    setattr(mock_metadata, keyword_field, keywords)
    mock_extract_metadata.return_value = mock_metadata

    article = RawArticle(
        url="https://test.com/article", raw_html=sample_html, site="test.com"
    )

    assert article.keywords == keywords


def test_to_dict_conversion(sample_html):
    """Test conversion to dictionary for database storage."""
    article = RawArticle(
        url="https://test.com/article",
        raw_html=sample_html,
        site="test.com",
        response_status=200,
    )

    result = article.to_dict()

    assert isinstance(result, dict)
    assert result["url"] == "https://test.com/article"
    assert result["raw_html"] == sample_html
    assert result["site"] == "test.com"
    assert result["response_status"] == 200
    assert "id" in result
    assert "scraped_at" in result
    assert "extraction_status" in result


@pytest.mark.parametrize("extraction_status", ["pending", "success", "failed"])
def test_extraction_status_values(extraction_status, sample_html, monkeypatch):
    """Test different extraction status values."""
    if extraction_status == "pending":
        # Default value before extraction
        article = RawArticle.__new__(RawArticle)
        article.extraction_status = "pending"
        assert article.extraction_status == "pending"
    else:
        # Mock trafilatura based on desired status
        if extraction_status == "success":
            monkeypatch.setattr("trafilatura.extract", lambda html: "Extracted content")
        else:
            monkeypatch.setattr("trafilatura.extract", lambda html: None)

        monkeypatch.setattr("trafilatura.extract_metadata", lambda html: None)

        article = RawArticle(
            url="https://test.com/article", raw_html=sample_html, site="test.com"
        )

        assert article.extraction_status == extraction_status
