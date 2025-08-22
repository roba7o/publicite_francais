"""
Database Integration Tests.

Tests database connectivity, schema operations, and data persistence
as part of the integration test suite.
"""

import pytest
from sqlalchemy import text

from config.environment import env_config
from database.database import get_session, initialize_database, store_raw_article, store_articles_batch
from database.models import RawArticle


class TestDatabaseConnectivity:
    """Test basic database connectivity and infrastructure."""

    def test_database_initialization(self):
        """Test that database can be initialized successfully."""
        result = initialize_database()
        assert result is True, "Database initialization should succeed"

    def test_basic_connection(self):
        """Test basic database connection works."""
        with get_session() as session:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1, "Basic database query should work"

    def test_database_info_query(self):
        """Test that we can query database information."""
        with get_session() as session:
            result = session.execute(
                text("SELECT current_database(), current_user, version()")
            ).fetchone()
            
            assert result is not None, "Database info query should return results"
            assert len(result) == 3, "Should get database name, user, and version"
            assert result[0] is not None, "Database name should not be None"
            assert result[1] is not None, "Database user should not be None"
            assert result[2] is not None, "Database version should not be None"

    def test_environment_schema_access(self):
        """Test that environment-specific schema is accessible."""
        schema = env_config.get_news_data_schema()
        assert schema is not None, "Schema name should be available"
        assert isinstance(schema, str), "Schema name should be a string"
        
        # Test that we can query the schema
        with get_session() as session:
            result = session.execute(
                text(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{schema.split('.')[0]}'
                ORDER BY table_name
                """)
            ).fetchall()
            
            # Should have at least the raw_articles table
            table_names = [row[0] for row in result]
            assert "raw_articles" in table_names, "raw_articles table should exist"


class TestDatabaseOperations:
    """Test database operations with models."""

    def test_raw_article_creation(self, clean_test_database):
        """Test creating and storing RawArticle objects."""
        # Create a test article
        article = RawArticle(
            url="https://test.example.com/article-1",
            raw_html="<html><body><h1>Test Article</h1><p>Test content</p></body></html>",
            site="test.example.com"
        )
        
        # Store to database using the database function
        success = store_raw_article(article)
        assert success, "Article should be stored successfully"
        
        # Verify it was stored by querying the database
        schema = env_config.get_news_data_schema()
        with get_session() as session:
            result = session.execute(
                text(f"SELECT url, site, raw_html, content_length FROM {schema}.raw_articles WHERE url = :url"),
                {"url": "https://test.example.com/article-1"}
            ).fetchone()
            
            assert result is not None, "Article should be stored in database"
            assert result[0] == "https://test.example.com/article-1"
            assert result[1] == "test.example.com"
            assert "Test Article" in result[2]
            assert result[3] > 0

    def test_raw_article_duplicate_handling(self, clean_test_database):
        """Test how the database handles duplicate URLs (ELT approach allows them)."""
        # Create first article
        article1 = RawArticle(
            url="https://test.example.com/duplicate-test",
            raw_html="<html><body><h1>First Version</h1></body></html>",
            site="test.example.com"
        )
        
        # Create second article with same URL but different content
        article2 = RawArticle(
            url="https://test.example.com/duplicate-test", 
            raw_html="<html><body><h1>Updated Version</h1></body></html>",
            site="test.example.com"
        )
        
        # Store both articles
        success1 = store_raw_article(article1)
        assert success1, "First article should be stored successfully"
        
        success2 = store_raw_article(article2)
        assert success2, "Second article should also be stored successfully"
        
        # In ELT approach, duplicates are allowed (for historical tracking)
        schema = env_config.get_news_data_schema()
        with get_session() as session:
            count = session.execute(
                text(f"SELECT COUNT(*) FROM {schema}.raw_articles WHERE url = :url"),
                {"url": "https://test.example.com/duplicate-test"}
            ).scalar()
            
            # ELT approach allows multiple versions of the same URL
            assert count == 2, "ELT approach should allow duplicate URLs for historical tracking"

    def test_bulk_operations(self, clean_test_database):
        """Test bulk database operations for performance."""
        # Create multiple test articles
        articles = []
        for i in range(5):
            article = RawArticle(
                url=f"https://test.example.com/bulk-test-{i}",
                raw_html=f"<html><body><h1>Bulk Article {i}</h1></body></html>",
                site="test.example.com"
            )
            articles.append(article)
        
        # Bulk insert using the database function
        successful, attempted = store_articles_batch(articles)
        assert successful == 5, "All 5 articles should be inserted successfully"
        # Note: attempted count may vary based on implementation (batch vs fallback)
        
        # Verify all were inserted by counting
        schema = env_config.get_news_data_schema()
        with get_session() as session:
            count = session.execute(
                text(f"SELECT COUNT(*) FROM {schema}.raw_articles WHERE url LIKE :pattern"),
                {"pattern": "https://test.example.com/bulk-test-%"}
            ).scalar()
            
            assert count == 5, "Should be able to query all 5 bulk articles"


class TestSchemaOperations:
    """Test schema-level database operations."""

    def test_table_exists(self):
        """Test that required tables exist in the schema."""
        schema = env_config.get_news_data_schema()
        
        with get_session() as session:
            # Check if raw_articles table exists
            result = session.execute(
                text(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = '{schema.split('.')[0]}' 
                AND table_name = 'raw_articles'
                """)
            ).scalar()
            
            assert result == 1, "raw_articles table should exist"

    def test_table_structure(self):
        """Test that raw_articles table has expected columns."""
        schema = env_config.get_news_data_schema()
        
        with get_session() as session:
            # Get table columns
            result = session.execute(
                text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = '{schema.split('.')[0]}' 
                AND table_name = 'raw_articles'
                ORDER BY column_name
                """)
            ).fetchall()
            
            columns = {row[0]: {"type": row[1], "nullable": row[2]} for row in result}
            
            # Check required columns exist (based on actual RawArticle model)
            required_columns = ["id", "url", "raw_html", "site", "scraped_at", "content_length"]
            for col in required_columns:
                assert col in columns, f"Column '{col}' should exist in raw_articles table"
            
            # Check specific constraints
            assert columns["id"]["nullable"] == "NO", "id column should be NOT NULL"
            assert columns["url"]["nullable"] == "NO", "url column should be NOT NULL"

    def test_database_permissions(self, clean_test_database):
        """Test that we have necessary database permissions."""
        schema = env_config.get_news_data_schema()
        
        with get_session() as session:
            # Test SELECT permission
            session.execute(text(f"SELECT 1 FROM {schema}.raw_articles LIMIT 1"))
            
        # Test INSERT permission using the database function
        test_article = RawArticle(
            url="https://permission.test.com/test",
            raw_html="<html><body>Permission test</body></html>",
            site="permission.test.com"
        )
        success = store_raw_article(test_article)
        assert success, "Should have INSERT permission"
        
        # Test UPDATE and DELETE permissions using raw SQL
        with get_session() as session:
            # Test UPDATE permission
            session.execute(
                text(f"UPDATE {schema}.raw_articles SET site = :new_site WHERE url = :url"),
                {"new_site": "permission-updated.test.com", "url": "https://permission.test.com/test"}
            )
            session.commit()
            
            # Test DELETE permission
            session.execute(
                text(f"DELETE FROM {schema}.raw_articles WHERE url = :url"),
                {"url": "https://permission.test.com/test"}
            )
            session.commit()