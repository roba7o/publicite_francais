"""
Integration tests for database operations using application's database layer.

These tests use the application's own database functions and connection
management for proper integration testing.
"""

from sqlalchemy import text

from database.database import store_articles_batch, store_article, get_session
from database.models import RawArticle


def test_store_single_article(clean_test_db):
    """Test storing a single article (metadata only, no HTML)."""
    article = RawArticle(
        url="https://slate.fr/test-article",
        raw_html="<html><h1>Breaking News</h1><p>Important story</p></html>",
        site="slate.fr",
    )

    # Store using application's database function
    result = store_article(article)
    assert result

    # Verify metadata stored in dim_articles (no raw_html)
    with get_session() as session:
        row = session.execute(
            text("""
            SELECT url, site
            FROM dim_articles
            WHERE id = :id
        """),
            {"id": article.id},
        ).fetchone()

        assert row is not None
        assert row[0] == article.url
        assert row[1] == article.site
        # raw_html is NOT stored in dim_articles


def test_store_batch_articles(clean_test_db):
    """Test storing multiple articles in batch (metadata only)."""
    articles = [
        RawArticle(
            url=f"https://franceinfo.fr/article-{i}",
            raw_html=f"<html><h1>News {i}</h1><p>Content {i}</p></html>",
            site="franceinfo.fr",
        )
        for i in range(3)
    ]

    # Store using application's database function
    successful, failed = store_articles_batch(articles)
    assert successful == 3
    assert failed == 0

    # Verify all in database
    with get_session() as session:
        count = session.execute(text("SELECT COUNT(*) FROM dim_articles")).fetchone()[0]
        assert count == 3

        # Check each article metadata
        for article in articles:
            row = session.execute(
                text("""
                SELECT url, site
                FROM dim_articles
                WHERE id = :id
            """),
                {"id": article.id},
            ).fetchone()

            assert row is not None
            assert row[0] == article.url
            assert row[1] == article.site
            # raw_html is NOT stored


def test_duplicate_urls_rejected(clean_test_db):
    """Test that duplicate URLs are rejected by UNIQUE constraint."""
    article1 = RawArticle(
        url="https://lemonde.fr/same-story",
        raw_html="<html><h1>First Version</h1></html>",
        site="lemonde.fr",
    )
    article2 = RawArticle(
        url="https://lemonde.fr/same-story",  # Same URL
        raw_html="<html><h1>Updated Version</h1></html>",
        site="lemonde.fr",
    )

    # Store first article - should succeed
    assert store_article(article1)

    # Store second article with same URL - should fail due to UNIQUE constraint
    assert not store_article(article2)

    # Verify only one article stored
    with get_session() as session:
        rows = session.execute(
            text("""
            SELECT id, url
            FROM dim_articles
            WHERE url = :url
        """),
            {"url": "https://lemonde.fr/same-story"},
        ).fetchall()

        assert len(rows) == 1
        assert rows[0][1] == "https://lemonde.fr/same-story"
