"""
Word Processing Tests.

Simple tests for French word extraction and processing functionality.
"""


class TestWordProcessing:
    """Word processing functionality tests."""

    def test_raw_article_word_extraction_import(self):
        """Test that word extraction functionality can be imported."""
        from database.models import RawArticle

        assert RawArticle is not None

    def test_word_events_basic_extraction(self):
        """Test basic word extraction from sample French text."""
        from database.models import RawArticle

        sample_html = """
        <html><body>
        <p>La politique française évolue rapidement avec des réformes importantes.</p>
        </body></html>
        """

        article = RawArticle(
            url="https://test.example.com/test",
            raw_html=sample_html,
            site="test.fr"
        )

        # Should extract words and filter stop words
        assert article.word_events is not None
        assert isinstance(article.word_events, list)
        assert len(article.word_events) > 0

        # Check word event structure
        word_event = article.word_events[0]
        assert 'word' in word_event
        assert 'position_in_article' in word_event
        assert 'article_id' in word_event
        assert 'scraped_at' in word_event

    def test_all_words_extracted(self):
        """Test that all words including stop words are extracted."""
        from database.models import RawArticle

        sample_html = """
        <html><body>
        <p>Le gouvernement français avec des réformes et de la politique.</p>
        </body></html>
        """

        article = RawArticle(
            url="https://test.example.com/test",
            raw_html=sample_html,
            site="test.fr"
        )

        # Extract just the words
        extracted_words = [event['word'] for event in article.word_events]

        # Should contain content words
        assert 'gouvernement' in extracted_words
        assert 'réformes' in extracted_words
        assert 'politique' in extracted_words

        # Should also contain stop words (dbt will filter these)
        assert 'le' in extracted_words
        assert 'avec' in extracted_words
        assert 'des' in extracted_words
        assert 'et' in extracted_words
        assert 'de' in extracted_words
        assert 'la' in extracted_words

    def test_word_storage_function_import(self):
        """Test that word storage function can be imported."""
        from database import store_word_events

        assert store_word_events is not None

    def test_empty_content_handling(self):
        """Test handling of articles with no extractable content."""
        from database.models import RawArticle

        empty_html = "<html><body></body></html>"

        article = RawArticle(
            url="https://test.example.com/empty",
            raw_html=empty_html,
            site="test.fr"
        )

        # Should handle empty content gracefully
        assert article.word_events is not None
        assert isinstance(article.word_events, list)
        assert len(article.word_events) == 0
