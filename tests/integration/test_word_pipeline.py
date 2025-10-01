"""
Word Processing Pipeline Integration Tests.

Tests for the complete word processing pipeline from extraction to storage.
"""

import pytest


class TestWordPipeline:
    """Word processing pipeline integration tests."""

    def test_word_pipeline_imports(self):
        """Test that all word processing components can be imported."""
        from database import store_word_events, initialize_database
        from database.models import RawArticle

        assert RawArticle is not None
        assert store_word_events is not None
        assert initialize_database is not None

    @pytest.mark.integration
    def test_word_events_database_storage(self):
        """Test storing word events in the database."""
        from database import initialize_database, store_word_events, store_raw_article
        from database.models import RawArticle

        # Initialize database
        assert initialize_database()

        # Create test article
        sample_html = """
        <html><body>
        <h1>Article Test</h1>
        <p>La politique française moderne nécessite des réformes importantes.</p>
        </body></html>
        """

        article = RawArticle(
            url="https://test.example.com/pipeline-test",
            raw_html=sample_html,
            site="test.fr"
        )

        # Store article first (required for foreign key)
        assert store_raw_article(article)

        # Store word events
        if article.word_events:
            assert store_word_events(article.word_events)

    @pytest.mark.integration
    def test_stop_words_table_exists(self):
        """Test that stop words table exists and is populated."""
        from database import initialize_database, get_session
        from sqlalchemy import text

        # Initialize database
        assert initialize_database()

        with get_session() as session:
            # Check stop words table exists and has data
            result = session.execute(text("""
                SELECT COUNT(*) FROM news_data_test.stop_words
                WHERE language = 'fr'
            """))
            count = result.scalar()
            assert count > 0

            # Test specific stop word lookup
            result = session.execute(text("""
                SELECT EXISTS(
                    SELECT 1 FROM news_data_test.stop_words
                    WHERE word = 'le' AND language = 'fr'
                )
            """))
            exists = result.scalar()
            assert exists is True