"""
Essential unit tests for database models.

Tests core behavior for clean architecture:
- RawArticle: Simple storage model (no processing)
- WordFact: Individual vocabulary facts
"""

import pytest

from database.models import RawArticle, WordFact


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
    assert "content_length" in result
    # Clean model - no extraction fields
    assert "extracted_text" not in result
    assert "extraction_status" not in result


# === WordFact Model Tests ===


def test_word_fact_creation():
    """Test WordFact can be created with required fields."""
    word_fact = WordFact(
        word="économie",
        article_id="test-article-id",
        position_in_article=5,
        scraped_at="2025-01-01T10:00:00",
    )

    assert word_fact.word == "économie"
    assert word_fact.article_id == "test-article-id"
    assert word_fact.position_in_article == 5
    assert word_fact.scraped_at == "2025-01-01T10:00:00"
    assert word_fact.id is not None


def test_word_fact_validation():
    """Test WordFact validation rules."""
    # Missing word should fail
    with pytest.raises(ValueError, match="word and article_id are required"):
        WordFact(
            word="",
            article_id="test-id",
            position_in_article=0,
            scraped_at="2025-01-01T10:00:00",
        )

    # Missing article_id should fail
    with pytest.raises(ValueError, match="word and article_id are required"):
        WordFact(
            word="test",
            article_id="",
            position_in_article=0,
            scraped_at="2025-01-01T10:00:00",
        )

    # Negative position should fail
    with pytest.raises(ValueError, match="position_in_article must be >= 0"):
        WordFact(
            word="test",
            article_id="test-id",
            position_in_article=-1,
            scraped_at="2025-01-01T10:00:00",
        )


def test_word_fact_to_dict():
    """Test WordFact conversion to dictionary."""
    word_fact = WordFact(
        word="français",
        article_id="article-123",
        position_in_article=10,
        scraped_at="2025-01-01T10:00:00",
    )

    result = word_fact.to_dict()

    assert isinstance(result, dict)
    assert result["word"] == "français"
    assert result["article_id"] == "article-123"
    assert result["position_in_article"] == 10
    assert result["scraped_at"] == "2025-01-01T10:00:00"
    assert "id" in result
