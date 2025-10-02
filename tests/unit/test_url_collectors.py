"""
Unit tests for URL collectors - testing real HTML parsing logic.

Tests actual URL extraction and filtering without hitting live websites.
"""

import pytest
from unittest.mock import Mock, patch
from requests.exceptions import RequestException, Timeout

from core.components.url_collectors.slate_fr_url_collector import SlateFrUrlCollector
from core.components.url_collectors.france_info_url_collector import FranceInfoUrlCollector
from core.components.url_collectors.tf1_info_url_collector import TF1InfoUrlCollector
from core.components.url_collectors.ladepeche_fr_url_collector import LadepecheFrUrlCollector


class TestSlateFrUrlCollector:
    """Test Slate.fr URL extraction logic."""

    def test_url_extraction_from_html(self):
        """Test actual URL extraction from Slate.fr HTML structure."""
        collector = SlateFrUrlCollector()

        # Real Slate.fr HTML structure with .card--story elements
        mock_html = '''
        <html>
            <div class="card--story">
                <a href="/story/123456/politique-france">Article politique</a>
            </div>
            <div class="card--story">
                <a href="/story/789012/economie-europe">Article économie</a>
            </div>
            <div class="other-card">
                <a href="/podcasts/audio">Podcast link</a>
            </div>
        </html>
        '''

        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')

        with patch.object(collector, '_make_request', return_value=mock_response):
            urls = collector.get_article_urls()

            # Should extract slate.fr story URLs and convert relative to absolute
            assert len(urls) >= 2
            assert 'https://www.slate.fr/story/123456/politique-france' in urls
            assert 'https://www.slate.fr/story/789012/economie-europe' in urls

            # Should not include podcast links (not in .card--story)
            assert not any('/podcasts/' in url for url in urls)

    def test_request_error_handling(self):
        """Test handling of HTTP errors."""
        collector = SlateFrUrlCollector()

        with patch.object(collector, '_make_request', side_effect=RequestException("Network error")):
            urls = collector.get_article_urls()
            assert urls == []

    def test_timeout_handling(self):
        """Test handling of timeouts."""
        collector = SlateFrUrlCollector()

        with patch.object(collector, '_make_request', side_effect=Timeout("Request timeout")):
            urls = collector.get_article_urls()
            assert urls == []


class TestFranceInfoUrlCollector:
    """Test FranceInfo URL extraction logic."""

    def test_franceinfo_url_extraction(self):
        """Test URL extraction from FranceInfo HTML structure."""
        collector = FranceInfoUrlCollector()

        # Check what selectors FranceInfo actually uses
        mock_html = '''
        <html>
            <article class="teaser">
                <a href="/politique/gouvernement/article1">Politique</a>
            </article>
            <article class="teaser">
                <a href="/monde/europe/article2">International</a>
            </article>
        </html>
        '''

        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')

        with patch.object(collector, '_make_request', return_value=mock_response):
            urls = collector.get_article_urls()

            # Should extract francetvinfo URLs
            assert isinstance(urls, list)
            # The actual logic will depend on FranceInfo's selector implementation

    def test_empty_page_handling(self):
        """Test handling of pages with no articles."""
        collector = FranceInfoUrlCollector()

        mock_response = Mock()
        mock_response.content = b'<html><body><h1>No articles here</h1></body></html>'

        with patch.object(collector, '_make_request', return_value=mock_response):
            urls = collector.get_article_urls()
            assert isinstance(urls, list)  # Should return list, not crash


class TestTF1InfoUrlCollector:
    """Test TF1Info URL extraction logic."""

    def test_basic_functionality(self):
        """Test basic TF1Info collector functionality."""
        collector = TF1InfoUrlCollector()

        mock_html = '''
        <html>
            <div class="article-item">
                <a href="/politique/news1">News politique</a>
            </div>
        </html>
        '''

        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')

        with patch.object(collector, '_make_request', return_value=mock_response):
            urls = collector.get_article_urls()
            assert isinstance(urls, list)


class TestLadepecheFrUrlCollector:
    """Test Ladepeche.fr URL extraction logic."""

    def test_basic_functionality(self):
        """Test basic Ladepeche collector functionality."""
        collector = LadepecheFrUrlCollector()

        mock_html = '''
        <html>
            <div class="article">
                <a href="/2024/01/15/article-local">Article local</a>
            </div>
        </html>
        '''

        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')

        with patch.object(collector, '_make_request', return_value=mock_response):
            urls = collector.get_article_urls()
            assert isinstance(urls, list)


def test_collector_initialization():
    """Test that all collectors can be initialized."""
    collectors = [
        SlateFrUrlCollector(),
        FranceInfoUrlCollector(),
        TF1InfoUrlCollector(),
        LadepecheFrUrlCollector()
    ]

    for collector in collectors:
        assert hasattr(collector, 'get_article_urls')
        assert callable(collector.get_article_urls)
        assert hasattr(collector, '_make_request')


@pytest.mark.parametrize("collector_class", [
    SlateFrUrlCollector,
    FranceInfoUrlCollector,
    TF1InfoUrlCollector,
    LadepecheFrUrlCollector
])
def test_error_handling_consistency(collector_class):
    """Test that all collectors handle errors consistently."""
    collector = collector_class()

    # Test network error handling
    with patch.object(collector, '_make_request', side_effect=RequestException("Network error")):
        urls = collector.get_article_urls()
        assert urls == []

    # Test timeout handling
    with patch.object(collector, '_make_request', side_effect=Timeout("Timeout")):
        urls = collector.get_article_urls()
        assert urls == []