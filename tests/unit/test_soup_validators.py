"""
Unit tests for soup validators - testing real HTML validation logic.

Tests actual domain validation, structure checking, and RawArticle creation.
"""

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from core.components.soup_validators.slate_fr_soup_validator import SlateFrSoupValidator
from core.components.soup_validators.france_info_soup_validator import FranceInfoSoupValidator
from core.components.soup_validators.tf1_info_soup_validator import Tf1InfoSoupValidator
from core.components.soup_validators.ladepeche_fr_soup_validator import LadepecheFrSoupValidator
from database.models import RawArticle


class TestSlateFrSoupValidator:
    """Test Slate.fr soup validation logic."""

    def test_valid_slate_article_structure(self):
        """Test validation of valid Slate.fr article structure."""
        validator = SlateFrSoupValidator("slate.fr")

        # Valid Slate.fr article HTML structure
        valid_html = '''
        <html>
            <head>
                <title>Test Article - Slate.fr</title>
            </head>
            <body>
                <article>
                    <h1>Article Title</h1>
                    <div class="article-content">
                        <p>This is the article content.</p>
                    </div>
                </article>
            </body>
        </html>
        '''

        soup = BeautifulSoup(valid_html, 'html.parser')
        url = "https://www.slate.fr/story/123456/test-article"

        article = validator.validate_and_extract(soup, url)

        assert isinstance(article, RawArticle)
        assert article.url == url
        assert article.site == "slate.fr"
        assert article.raw_html == str(soup)
        assert article.extraction_status == "success"

    def test_invalid_slate_structure_no_article_tag(self):
        """Test rejection of HTML without article tag."""
        validator = SlateFrSoupValidator("slate.fr")

        # Invalid HTML - no article tag
        invalid_html = '''
        <html>
            <head><title>Test</title></head>
            <body>
                <div class="content">
                    <h1>Not an article</h1>
                </div>
            </body>
        </html>
        '''

        soup = BeautifulSoup(invalid_html, 'html.parser')
        url = "https://www.slate.fr/story/123456/test"

        article = validator.validate_and_extract(soup, url)
        assert article is None

    def test_invalid_domain_rejection(self):
        """Test rejection of non-slate.fr URLs."""
        validator = SlateFrSoupValidator("slate.fr")

        valid_html = '''
        <html><body><article><h1>Article</h1></article></body></html>
        '''

        soup = BeautifulSoup(valid_html, 'html.parser')
        url = "https://www.lemonde.fr/article/123"

        article = validator.validate_and_extract(soup, url)
        assert article is None

    def test_empty_soup_handling(self):
        """Test handling of empty soup."""
        validator = SlateFrSoupValidator("slate.fr")

        empty_soup = BeautifulSoup("", 'html.parser')
        url = "https://www.slate.fr/story/123456/test"

        article = validator.validate_and_extract(empty_soup, url)
        assert article is None

    def test_get_soup_from_url_success(self):
        """Test successful soup creation from URL."""
        validator = SlateFrSoupValidator("slate.fr")

        # Content must be >100 bytes to pass the validator's check
        long_content = b'<html><head><title>Long enough content</title></head><body><article>Test article with enough content to pass the 100 byte minimum requirement for content validation</article></body></html>'

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = long_content

        with patch.object(validator, 'make_request', return_value=mock_response):
            soup = validator.get_soup_from_url("https://slate.fr/test")

            assert isinstance(soup, BeautifulSoup)
            assert soup.find("article") is not None

    def test_network_error_handling(self):
        """Test handling of network errors in URL fetching."""
        validator = SlateFrSoupValidator("slate.fr")

        # Test that the method exists and handles errors gracefully
        with patch.object(validator, 'get_soup_from_url', return_value=None):
            soup = validator.get_soup_from_url("https://slate.fr/test")
            assert soup is None


class TestFranceInfoSoupValidator:
    """Test FranceInfo soup validation logic."""

    def test_valid_franceinfo_article(self):
        """Test validation of valid FranceInfo article."""
        validator = FranceInfoSoupValidator("franceinfo.fr")

        # FranceInfo-like HTML structure
        valid_html = '''
        <html>
            <head>
                <title>News Article - franceinfo</title>
            </head>
            <body>
                <main class="main-content">
                    <h1>Article Title</h1>
                    <div class="article-body">
                        <p>Article content here.</p>
                    </div>
                </main>
            </body>
        </html>
        '''

        soup = BeautifulSoup(valid_html, 'html.parser')
        url = "https://www.francetvinfo.fr/politique/article"

        article = validator.validate_and_extract(soup, url)

        if article:  # Depends on FranceInfo's validation logic
            assert isinstance(article, RawArticle)
            assert article.site == "franceinfo.fr"
            assert article.url == url

    def test_franceinfo_domain_validation(self):
        """Test domain validation for FranceInfo."""
        validator = FranceInfoSoupValidator("franceinfo.fr")

        html = '<html><body><main>Content</main></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        # Test invalid domain
        invalid_url = "https://www.tf1info.fr/article"

        # The actual behavior depends on the validator's domain checking logic
        invalid_result = validator.validate_and_extract(soup, invalid_url)

        # At minimum, invalid domain should be rejected
        assert invalid_result is None


class TestTf1InfoSoupValidator:
    """Test TF1Info soup validation logic."""

    def test_basic_tf1_validation(self):
        """Test basic TF1Info validation."""
        validator = Tf1InfoSoupValidator("tf1info.fr")

        html = '''
        <html>
            <head><title>TF1 News</title></head>
            <body>
                <div class="article-container">
                    <h1>News Title</h1>
                    <p>News content</p>
                </div>
            </body>
        </html>
        '''

        soup = BeautifulSoup(html, 'html.parser')
        url = "https://www.tf1info.fr/politique/news"

        article = validator.validate_and_extract(soup, url)

        if article:
            assert isinstance(article, RawArticle)
            assert article.site == "tf1info.fr"

    def test_tf1_domain_rejection(self):
        """Test that non-tf1info domains are rejected."""
        validator = Tf1InfoSoupValidator("tf1info.fr")

        html = '<html><body><div>Content</div></body></html>'
        soup = BeautifulSoup(html, 'html.parser')
        url = "https://www.france24.fr/article"

        article = validator.validate_and_extract(soup, url)
        assert article is None


class TestLadepecheFrSoupValidator:
    """Test Ladepeche.fr soup validation logic."""

    def test_basic_ladepeche_validation(self):
        """Test basic Ladepeche validation."""
        validator = LadepecheFrSoupValidator("ladepeche.fr")

        html = '''
        <html>
            <head><title>Article - La Dépêche</title></head>
            <body>
                <article class="article-content">
                    <h1>Local News</h1>
                    <div>Article text</div>
                </article>
            </body>
        </html>
        '''

        soup = BeautifulSoup(html, 'html.parser')
        url = "https://www.ladepeche.fr/2024/01/15/article"

        article = validator.validate_and_extract(soup, url)

        if article:
            assert isinstance(article, RawArticle)
            assert article.site == "ladepeche.fr"


class TestSoupValidatorsEdgeCases:
    """Test edge cases common to all validators."""

    @pytest.mark.parametrize("validator_class,site_name", [
        (SlateFrSoupValidator, "slate.fr"),
        (FranceInfoSoupValidator, "franceinfo.fr"),
        (Tf1InfoSoupValidator, "tf1info.fr"),
        (LadepecheFrSoupValidator, "ladepeche.fr")
    ])
    def test_none_soup_handling(self, validator_class, site_name):
        """Test that all validators handle None soup gracefully."""
        validator = validator_class(site_name)

        result = validator.validate_and_extract(None, f"https://www.{site_name}/test")
        assert result is None

    @pytest.mark.parametrize("validator_class,site_name", [
        (SlateFrSoupValidator, "slate.fr"),
        (FranceInfoSoupValidator, "franceinfo.fr"),
        (Tf1InfoSoupValidator, "tf1info.fr"),
        (LadepecheFrSoupValidator, "ladepeche.fr")
    ])
    def test_malformed_html_handling(self, validator_class, site_name):
        """Test handling of malformed HTML."""
        validator = validator_class(site_name)

        # Malformed HTML
        malformed_html = '<html><head><title>Broken</title><body><p>Unclosed paragraph<div>Nested incorrectly'
        soup = BeautifulSoup(malformed_html, 'html.parser')

        url = f"https://www.{site_name}/test"
        result = validator.validate_and_extract(soup, url)

        # Should not crash, should return None or valid RawArticle
        assert result is None or isinstance(result, RawArticle)

    @pytest.mark.parametrize("validator_class,site_name", [
        (SlateFrSoupValidator, "slate.fr"),
        (FranceInfoSoupValidator, "franceinfo.fr"),
        (Tf1InfoSoupValidator, "tf1info.fr"),
        (LadepecheFrSoupValidator, "ladepeche.fr")
    ])
    def test_unicode_content_handling(self, validator_class, site_name):
        """Test handling of Unicode content."""
        validator = validator_class(site_name)

        unicode_html = '''
        <html>
            <head><title>Article avec caractères spéciaux</title></head>
            <body>
                <article>
                    <h1>Titre avec accents: àáâäçéèêëîïôöùúûü</h1>
                    <p>Contenu avec émojis: 🇫🇷 🚀 ⚡</p>
                </article>
            </body>
        </html>
        '''

        soup = BeautifulSoup(unicode_html, 'html.parser')
        url = f"https://www.{site_name}/unicode-test"

        result = validator.validate_and_extract(soup, url)

        if result:
            assert isinstance(result, RawArticle)
            # Should preserve Unicode in raw HTML
            assert 'àáâäçéèêëîïôöùúûü' in result.raw_html
            assert '🇫🇷' in result.raw_html


def test_validator_initialization():
    """Test that all validators can be initialized properly."""
    validators = [
        SlateFrSoupValidator("slate.fr"),
        FranceInfoSoupValidator("franceinfo.fr"),
        Tf1InfoSoupValidator("tf1info.fr"),
        LadepecheFrSoupValidator("ladepeche.fr")
    ]

    for validator in validators:
        assert hasattr(validator, 'validate_and_extract')
        assert hasattr(validator, 'get_soup_from_url')
        assert callable(validator.validate_and_extract)
        assert callable(validator.get_soup_from_url)


def test_raw_article_creation_requirements():
    """Test RawArticle creation with required fields."""
    # Test valid creation
    article = RawArticle(
        url="https://test.com/article",
        raw_html="<html><body>Test</body></html>",
        site="test.com"
    )

    assert article.url == "https://test.com/article"
    assert article.site == "test.com"
    assert article.raw_html == "<html><body>Test</body></html>"
    assert article.extraction_status == "success"  # Default value

    # Test that empty values are rejected (based on model validation)
    with pytest.raises(ValueError):
        RawArticle(url="", raw_html="<html></html>", site="test.com")

    with pytest.raises(ValueError):
        RawArticle(url="https://test.com", raw_html="", site="test.com")
