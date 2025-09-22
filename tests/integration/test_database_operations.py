"""
Integration tests for database operations.

Starting simple with working SQLite in-memory fixture.
"""

import pytest
from sqlalchemy import create_engine, text

from database.models import RawArticle


@pytest.fixture
def sqlite_db():
    """Create in-memory SQLite database with raw_articles table."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create the table
    with engine.connect() as conn:
        conn.execute(
            text("""
            CREATE TABLE raw_articles (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                raw_html TEXT NOT NULL,
                site TEXT NOT NULL,
                scraped_at TEXT,
                response_status INTEGER,
                content_length INTEGER,
                extracted_text TEXT,
                title TEXT,
                author TEXT,
                date_published TEXT,
                language TEXT,
                summary TEXT,
                keywords TEXT,
                extraction_status TEXT
            )
        """)
        )
        conn.commit()

    yield engine
    engine.dispose()


@pytest.fixture
def sample_article():
    """Create a sample RawArticle for testing."""
    return RawArticle(
        url="https://test.com/article",
        raw_html="<html><body><h1>Test</h1></body></html>",
        site="test.com",
    )


def test_sqlite_fixture_works(sqlite_db):
    """Test that the SQLite fixture creates a working database."""
    with sqlite_db.connect() as conn:
        result = conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='raw_articles'"
            )
        )
        tables = result.fetchall()

        assert len(tables) == 1
        assert tables[0][0] == "raw_articles"


def test_can_insert_article(sqlite_db, sample_article):
    """Test that we can insert an article into the database."""
    article_dict = sample_article.to_dict()

    with sqlite_db.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO raw_articles (
                id, url, raw_html, site, scraped_at, response_status, 
                content_length, extracted_text, title, author, 
                date_published, language, summary, keywords, extraction_status
            ) VALUES (
                :id, :url, :raw_html, :site, :scraped_at, :response_status,
                :content_length, :extracted_text, :title, :author,
                :date_published, :language, :summary, :keywords, :extraction_status
            )
        """),
            article_dict,
        )
        conn.commit()

        # Verify it was inserted
        result = conn.execute(text("SELECT COUNT(*) FROM raw_articles"))
        count = result.fetchone()[0]

        assert count == 1


def test_can_query_article(sqlite_db, sample_article):
    """Test that we can query an inserted article."""
    article_dict = sample_article.to_dict()

    with sqlite_db.connect() as conn:
        # Insert article
        conn.execute(
            text("""
            INSERT INTO raw_articles (
                id, url, raw_html, site, scraped_at, response_status, 
                content_length, extracted_text, title, author, 
                date_published, language, summary, keywords, extraction_status
            ) VALUES (
                :id, :url, :raw_html, :site, :scraped_at, :response_status,
                :content_length, :extracted_text, :title, :author,
                :date_published, :language, :summary, :keywords, :extraction_status
            )
        """),
            article_dict,
        )
        conn.commit()

        # Query it back
        result = conn.execute(
            text("SELECT url, site FROM raw_articles WHERE id = :id"),
            {"id": sample_article.id},
        )
        row = result.fetchone()

        assert row[0] == sample_article.url
        assert row[1] == sample_article.site
