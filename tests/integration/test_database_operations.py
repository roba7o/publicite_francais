"""
Simple integration tests using test PostgreSQL container.
"""

import pytest
import time
from unittest.mock import patch
from sqlalchemy import create_engine, text

from database.models import RawArticle
from database.database import store_raw_article, store_articles_batch


# Test database configuration
TEST_DB_CONFIG = {
    'user': 'news_user',
    'password': 'test_password', 
    'host': 'localhost',
    'port': '5433',
    'database': 'french_news_test'
}


@pytest.fixture(scope="session")
def test_db():
    """Set up test database with migrations."""
    # Wait for test database to be ready
    engine = create_engine(f"postgresql://{TEST_DB_CONFIG['user']}:{TEST_DB_CONFIG['password']}@{TEST_DB_CONFIG['host']}:{TEST_DB_CONFIG['port']}/{TEST_DB_CONFIG['database']}")
    
    # Wait for database to be ready
    for _ in range(30):  # 30 second timeout
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception:
            time.sleep(1)
    else:
        raise RuntimeError("Test database not ready after 30 seconds")
    
    # Point database functions to test database
    with patch('database.database.DATABASE_CONFIG', TEST_DB_CONFIG):
        # Run migrations on test database
        import sys
        from pathlib import Path
        
        db_path = Path(__file__).parent.parent.parent / "database"
        sys.path.insert(0, str(db_path))
        
        from migrations.run_migrations import run_all_migrations
        
        try:
            run_all_migrations()
        except SystemExit:
            pass  # Migration runner exits on completion
        
        yield engine


@pytest.fixture
def clean_db(test_db):
    """Clean database before each test."""
    with test_db.connect() as conn:
        # Clean all tables
        conn.execute(text("TRUNCATE TABLE news_data_dev.raw_articles CASCADE"))
        conn.execute(text("DELETE FROM migration_history"))
        conn.commit()
    
    # Re-run migrations for clean state
    import sys
    from pathlib import Path
    
    db_path = Path(__file__).parent.parent.parent / "database"
    sys.path.insert(0, str(db_path))
    
    from migrations.run_migrations import run_all_migrations
    
    try:
        run_all_migrations()
    except SystemExit:
        pass
    
    return test_db  # Return the engine for use in tests


def test_store_single_article(clean_db):
    """Test storing a single article."""
    article = RawArticle(
        url="https://slate.fr/test-article",
        raw_html="<html><h1>Breaking News</h1><p>Important story</p></html>",
        site="slate.fr"
    )
    
    # Store using actual function
    result = store_raw_article(article)
    assert result is True
    
    # Verify in database
    with clean_db.connect() as conn:
        row = conn.execute(text("""
            SELECT url, site, extracted_text, title, extraction_status
            FROM news_data_dev.raw_articles 
            WHERE id = :id
        """), {"id": article.id}).fetchone()
        
        assert row is not None
        assert row[0] == article.url
        assert row[1] == article.site
        assert row[2] == article.extracted_text  # Trafilatura extraction
        assert row[3] == article.title
        assert row[4] == article.extraction_status


def test_store_batch_articles(clean_db):
    """Test storing multiple articles in batch."""
    articles = [
        RawArticle(
            url=f"https://franceinfo.fr/article-{i}",
            raw_html=f"<html><h1>News {i}</h1><p>Content {i}</p></html>",
            site="franceinfo.fr"
        )
        for i in range(3)
    ]
    
    # Store using actual function
    successful, failed = store_articles_batch(articles)
    assert successful == 3
    assert failed == 0
    
    # Verify all in database
    with clean_db.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM news_data_dev.raw_articles")).fetchone()[0]
        assert count == 3
        
        # Check each article
        for article in articles:
            row = conn.execute(text("""
                SELECT url, site, raw_html
                FROM news_data_dev.raw_articles 
                WHERE id = :id
            """), {"id": article.id}).fetchone()
            
            assert row is not None
            assert row[0] == article.url
            assert row[1] == article.site
            assert row[2] == article.raw_html


def test_duplicate_urls_allowed(clean_db):
    """Test that duplicate URLs are stored with different UUIDs."""
    article1 = RawArticle(
        url="https://lemonde.fr/same-story",
        raw_html="<html><h1>First Version</h1></html>",
        site="lemonde.fr"
    )
    article2 = RawArticle(
        url="https://lemonde.fr/same-story",  # Same URL
        raw_html="<html><h1>Updated Version</h1></html>",
        site="lemonde.fr"
    )
    
    # Store both
    assert store_raw_article(article1) is True
    assert store_raw_article(article2) is True
    
    # Verify both stored with different UUIDs
    with clean_db.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, url, raw_html 
            FROM news_data_dev.raw_articles
            WHERE url = :url
            ORDER BY scraped_at
        """), {"url": "https://lemonde.fr/same-story"}).fetchall()
        
        assert len(rows) == 2
        assert rows[0][0] != rows[1][0]  # Different UUIDs
        assert rows[0][1] == rows[1][1]  # Same URL
        assert "First Version" in rows[0][2]
        assert "Updated Version" in rows[1][2]