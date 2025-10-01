"""
Integration tests for database operations using application's database layer.

These tests use the application's own database functions and connection
management for proper integration testing.
"""

import pytest
from sqlalchemy import text

from database.database import store_articles_batch, store_raw_article, get_session
from database.models import RawArticle
from config.environment import get_news_data_schema


def test_store_single_article(clean_test_db):
    """Test storing a single article."""
    article = RawArticle(
        url="https://slate.fr/test-article",
        raw_html="<html><h1>Breaking News</h1><p>Important story</p></html>",
        site="slate.fr",
    )

    # Store using application's database function
    result = store_raw_article(article)
    assert result is True

    # Verify in database using application's database layer
    schema = get_news_data_schema()

    with get_session() as session:
        row = session.execute(
            text(f"""
            SELECT url, site, extracted_text, title, extraction_status
            FROM {schema}.raw_articles
            WHERE id = :id
        """),
            {"id": article.id},
        ).fetchone()

        assert row is not None
        assert row[0] == article.url
        assert row[1] == article.site
        assert row[2] == article.extracted_text  # Trafilatura extraction
        assert row[3] == article.title
        assert row[4] == article.extraction_status


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

    # Verify all in database using application's database layer
    schema = get_news_data_schema()

    with get_session() as session:
        count = session.execute(
            text(f"SELECT COUNT(*) FROM {schema}.raw_articles")
        ).fetchone()[0]
        assert count == 3

        # Check each article
        for article in articles:
            row = session.execute(
                text(f"""
                SELECT url, site, raw_html
                FROM {schema}.raw_articles
                WHERE id = :id
            """),
                {"id": article.id},
            ).fetchone()

            assert row is not None
            assert row[0] == article.url
            assert row[1] == article.site
            assert row[2] == article.raw_html


def test_duplicate_urls_allowed(clean_test_db):
    """Test that duplicate URLs are stored with different UUIDs."""
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

    # Store both using application's database function
    assert store_raw_article(article1) is True
    assert store_raw_article(article2) is True

    # Verify both stored with different UUIDs using application's database layer
    schema = get_news_data_schema()

    with get_session() as session:
        rows = session.execute(
            text(f"""
            SELECT id, url, raw_html
            FROM {schema}.raw_articles
            WHERE url = :url
            ORDER BY scraped_at
        """),
            {"url": "https://lemonde.fr/same-story"},
        ).fetchall()

        assert len(rows) == 2
        assert rows[0][0] != rows[1][0]  # Different UUIDs
        assert rows[0][1] == rows[1][1]  # Same URL
        assert "First Version" in rows[0][2]
        assert "Updated Version" in rows[1][2]