"""
Simple integration tests for database operations.

Basic tests for article storage and word events.
"""

from sqlalchemy import text

from database.database import store_raw_article, get_session, store_word_events
from database.models import RawArticle


def test_store_single_article(clean_test_db):
    """Test storing a single article with word events."""
    article = RawArticle(
        url="https://slate.fr/test-article",
        raw_html="<html><h1>Breaking News</h1><p>This is a test article with French words.</p></html>",
        site="slate.fr",
    )

    # Store using application's database function
    result = store_raw_article(article)
    assert result is True

    # Store word events separately
    if article.word_events:
        word_result = store_word_events(article.word_events)
        assert word_result is True

    # Verify article in database
    with get_session() as session:
        article_count = session.execute(text("SELECT COUNT(*) FROM raw_articles")).scalar()
        assert article_count == 1

        # Verify word events were stored (if generated)
        word_count = session.execute(text("SELECT COUNT(*) FROM word_events")).scalar()
        if article.word_events:
            assert word_count > 0, "Word events should be stored when generated"


