"""
Integration tests for database operations using application's database layer.

These tests use the application's own database functions and connection
management for proper integration testing.
"""

from sqlalchemy import text

from database.database import store_articles_batch, store_article, get_session
from database.models import RawArticle


def test_store_single_article(clean_test_db):
    """Test storing a single article."""
    article = RawArticle(
        url="https://slate.fr/test-article",
        raw_html="<html><h1>Breaking News</h1><p>Important story</p></html>",
        site="slate.fr",
    )

    # Store using application's database function
    result = store_article(article)
    assert result

    # Verify in database - single schema, no conditionals
    with get_session() as session:
        row = session.execute(
            text("""
            SELECT url, site, raw_html
            FROM raw_articles
            WHERE id = :id
        """),
            {"id": article.id},
        ).fetchone()

        assert row is not None
        assert row[0] == article.url
        assert row[1] == article.site
        assert row[2] == article.raw_html


def test_store_batch_articles(clean_test_db):
    """Test storing multiple articles in batch."""
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

    # Verify all in database - single schema
    with get_session() as session:
        count = session.execute(text("SELECT COUNT(*) FROM raw_articles")).fetchone()[0]
        assert count == 3

        # Check each article
        for article in articles:
            row = session.execute(
                text("""
                SELECT url, site, raw_html
                FROM raw_articles
                WHERE id = :id
            """),
                {"id": article.id},
            ).fetchone()

            assert row is not None
            assert row[0] == article.url
            assert row[1] == article.site
            assert row[2] == article.raw_html


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
            SELECT id, url, raw_html
            FROM raw_articles
            WHERE url = :url
        """),
            {"url": "https://lemonde.fr/same-story"},
        ).fetchall()

        assert len(rows) == 1
        assert "First Version" in rows[0][2]
