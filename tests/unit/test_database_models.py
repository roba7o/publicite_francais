"""
Simple unit tests for database models.

Tests basic model functionality.
"""

from database.models import RawArticle


def test_raw_article_creation():
    """Test basic RawArticle creation."""
    article = RawArticle(
        url="https://example.com/test",
        raw_html="<html><body>Test content with some French words.</body></html>",
        site="example.com"
    )

    assert article.url == "https://example.com/test"
    assert article.site == "example.com"
    assert article.id is not None
    assert article.scraped_at is not None


def test_word_events_generation():
    """Test that word events are generated from article text."""
    article = RawArticle(
        url="https://example.com/test",
        raw_html="<html><body>Bonjour le monde français.</body></html>",
        site="example.com"
    )

    # Should have extracted text and word events
    assert article.extracted_text is not None
    assert article.word_events is not None
    assert len(article.word_events) > 0

    # Check word event structure
    word_event = article.word_events[0]
    assert "word" in word_event
    assert "article_id" in word_event
    assert "position_in_article" in word_event
    assert "scraped_at" in word_event
