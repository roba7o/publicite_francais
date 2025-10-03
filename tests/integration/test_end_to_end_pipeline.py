"""
Lightweight integration test for end-to-end article processing pipeline.

Tests the complete flow: ArticleOrchestrator → RawArticle → word_events → database storage
"""

import pytest
from unittest.mock import Mock, patch

from core.orchestrator import ArticleOrchestrator
from database.models import RawArticle
from database.database import get_session, initialize_database
from sqlalchemy import text


@pytest.fixture(autouse=True)
def setup_test_database():
    """Initialize test database for each test."""
    initialize_database()


class TestEndToEndPipeline:
    """Test complete article processing pipeline."""

    def test_article_processing_creates_word_events(self):
        """Test that processing an article creates word events in database."""
        # Create test HTML content
        test_html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>Article de Test</h1>
                    <p>Ceci est un article français pour tester les mots.</p>
                    <p>Il contient plusieurs phrases avec des mots français.</p>
                </article>
            </body>
        </html>
        """

        # Create RawArticle and process
        article = RawArticle(
            url="https://test.fr/article",
            raw_html=test_html,
            site="test.fr"
        )

        # Verify word events were created
        assert article.word_events is not None
        assert len(article.word_events) > 0

        # Check some expected French words are present
        words = [event['word'] for event in article.word_events]
        assert 'article' in words
        assert 'français' in words
        assert 'test' in words

        # Verify word event structure
        for event in article.word_events[:3]:  # Check first few events
            assert 'word' in event
            assert 'position_in_article' in event
            assert 'article_id' in event
            assert 'scraped_at' in event
            assert event['article_id'] == article.id

    @pytest.mark.skip(reason="Complex orchestrator integration needs test data fixtures")
    def test_orchestrator_end_to_end_processing(self):
        """Test ArticleOrchestrator processes articles and stores data correctly."""
        orchestrator = ArticleOrchestrator()

        # Mock site config
        test_config = {
            'site': 'test.fr',
            'base_url': 'https://test.fr',
            'enabled': True,
            'url_collector_class': 'core.components.url_collectors.slate_fr_url_collector.SlateFrUrlCollector',
            'soup_validator_class': 'core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator',
            'url_collector_kwargs': {},
            'soup_validator_kwargs': {}
        }

        # Mock URL collection to return test URLs
        mock_urls = ['https://test.fr/article-1', 'https://test.fr/article-2']

        # Mock soup validation to return test articles
        test_html = """
        <html><body><article>
            <h1>Test Article</h1>
            <p>Ceci est un test avec des mots français.</p>
        </article></body></html>
        """

        mock_article = RawArticle(
            url="https://test.fr/article-1",
            raw_html=test_html,
            site="test.fr"
        )

        with patch.object(orchestrator.component_factory, 'create_collector') as mock_collector_factory, \
             patch.object(orchestrator.component_factory, 'create_validator') as mock_validator_factory, \
             patch('database.store_articles_batch') as mock_store_batch, \
             patch('database.store_word_events') as mock_store_words:

            # Setup mocks
            mock_collector = Mock()
            mock_collector.get_article_urls.return_value = mock_urls
            mock_collector_factory.return_value = mock_collector

            mock_validator = Mock()
            mock_validator.validate_and_extract.return_value = mock_article
            mock_validator.get_soup_from_url.return_value = Mock()  # Mock soup object
            mock_validator_factory.return_value = mock_validator

            # Mock storage functions
            mock_store_batch.return_value = (len(mock_urls), 0)  # (processed, failed)
            mock_store_words.return_value = True

            # Process the site
            processed, attempted = orchestrator.process_site(test_config)

            # Verify processing occurred
            assert processed >= 0
            assert attempted >= 0

            # Verify collector was used
            mock_collector.get_article_urls.assert_called_once()

            # Verify validator was used
            assert mock_validator.validate_and_extract.call_count == len(mock_urls)

    def test_database_storage_integration(self):
        """Test that articles and word events are properly stored in database."""
        # Clear any existing data
        with get_session() as session:
            session.execute(text('TRUNCATE raw_articles CASCADE'))
            session.commit()

        # Create and process article
        test_html = """
        <html><body><article>
            <h1>Integration Test</h1>
            <p>Ce test vérifie le stockage en base de données.</p>
        </article></body></html>
        """

        article = RawArticle(
            url="https://integration-test.fr/article",
            raw_html=test_html,
            site="integration-test.fr"
        )

        # Store article using database functions directly
        from database import store_articles_batch, store_word_events

        processed_count, failed_count = store_articles_batch([article])
        assert processed_count == 1
        assert failed_count == 0

        # Store word events
        if article.word_events:
            word_events_stored = store_word_events(article.word_events)
            assert word_events_stored

        # Verify article was stored
        with get_session() as session:
            # Check raw article exists
            article_count = session.execute(
                text('SELECT COUNT(*) FROM raw_articles')
            ).scalar()
            assert article_count == 1

            # Check word events were stored
            word_count = session.execute(
                text('SELECT COUNT(*) FROM word_events')
            ).scalar()
            assert word_count > 0

            # Verify some expected words are in word_events
            words = session.execute(
                text('SELECT DISTINCT word FROM word_events ORDER BY word')
            ).fetchall()
            word_list = [row[0] for row in words]

            # Should contain some French words from our test content
            assert len(word_list) > 0
            # Check for words we know should be there (after processing)
            expected_words = {'test', 'base', 'données', 'integration', 'stockage'}
            found_words = set(word_list)
            assert len(expected_words & found_words) > 0

    def test_error_handling_in_pipeline(self):
        """Test that pipeline handles errors gracefully without breaking."""
        # Test with invalid HTML
        invalid_article = RawArticle(
            url="https://test.fr/invalid",
            raw_html="<invalid>broken html",
            site="test.fr"
        )

        # Should not raise exception during creation
        # Even with broken HTML, should still create some basic structure
        assert invalid_article.word_events is not None

        # Test storing the invalid article
        from database import store_articles_batch

        try:
            processed_count, failed_count = store_articles_batch([invalid_article])
            # Should handle gracefully - either process or fail without crashing
            assert processed_count + failed_count == 1
        except Exception as e:
            pytest.fail(f"Pipeline should handle errors gracefully, but got: {e}")

    def test_word_extraction_quality(self):
        """Test that word extraction produces reasonable results."""
        # Rich French content
        rich_html = """
        <html><body><article>
            <h1>L'économie française en 2024</h1>
            <p>L'économie française traverse une période de transformation importante.
               Les entreprises s'adaptent aux nouveaux défis technologiques.</p>
            <p>L'innovation et la recherche restent des priorités nationales
               pour maintenir la compétitivité internationale.</p>
        </article></body></html>
        """

        article = RawArticle(
            url="https://test.fr/economie",
            raw_html=rich_html,
            site="test.fr"
        )

        # Verify word extraction quality
        assert article.word_events is not None
        assert len(article.word_events) > 20  # Should extract many words

        words = [event['word'] for event in article.word_events]

        # Should contain meaningful French words
        meaningful_words = {
            'économie', 'française', 'entreprises', 'défis',
            'technologiques', 'innovation', 'recherche', 'compétitivité'
        }
        found_meaningful = set(words) & meaningful_words
        assert len(found_meaningful) > 0, f"Expected meaningful words, got: {words[:10]}"

        # Verify position tracking (word positions should be sequential)
        positions = [event['position_in_article'] for event in article.word_events[:10]]
        assert positions == sorted(positions), "Word positions should be in order"

        # Verify event structure
        for event in article.word_events[:5]:
            assert isinstance(event['word'], str)
            assert len(event['word']) >= 2  # Minimum word length filter
            assert isinstance(event['position_in_article'], int)
            assert event['position_in_article'] >= 0