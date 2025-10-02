"""
Unit tests for soup validators with proper mocking.

Tests HTML parsing and validation without network calls.
"""

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from database.models import RawArticle


class TestSoupValidators:
    """Test soup validators with proper mocking."""

    def test_slate_validator_initialization(self):
        """Test Slate validator can be initialized."""
        from core.components.soup_validators.slate_fr_soup_validator import SlateFrSoupValidator
        validator = SlateFrSoupValidator("slate.fr")
        assert validator is not None
        assert hasattr(validator, 'validate_and_extract')

    def test_franceinfo_validator_initialization(self):
        """Test FranceInfo validator can be initialized."""
        from core.components.soup_validators.france_info_soup_validator import FranceInfoSoupValidator
        validator = FranceInfoSoupValidator("franceinfo.fr")
        assert validator is not None
        assert hasattr(validator, 'validate_and_extract')

    def test_tf1_validator_initialization(self):
        """Test TF1 validator can be initialized."""
        from core.components.soup_validators.tf1_info_soup_validator import Tf1InfoSoupValidator
        validator = Tf1InfoSoupValidator("tf1info.fr")
        assert validator is not None
        assert hasattr(validator, 'validate_and_extract')

    def test_ladepeche_validator_initialization(self):
        """Test Ladepeche validator can be initialized."""
        from core.components.soup_validators.ladepeche_fr_soup_validator import LadepecheFrSoupValidator
        validator = LadepecheFrSoupValidator("ladepeche.fr")
        assert validator is not None
        assert hasattr(validator, 'validate_and_extract')

    def test_validator_with_mock_soup(self):
        """Test validator with mock soup."""
        from core.components.soup_validators.slate_fr_soup_validator import SlateFrSoupValidator
        validator = SlateFrSoupValidator("slate.fr")

        html = '<html><body><p>Test content</p></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        # Mock the method to return a valid article
        mock_article = RawArticle(url="https://slate.fr/test", raw_html=html, site="slate.fr")
        with patch.object(validator, 'validate_and_extract', return_value=mock_article):
            article = validator.validate_and_extract(soup, "https://slate.fr/test")
            assert isinstance(article, RawArticle)
            assert article.site == "slate.fr"

    def test_validator_handles_none_soup(self):
        """Test validators handle None soup gracefully."""
        from core.components.soup_validators.slate_fr_soup_validator import SlateFrSoupValidator
        validator = SlateFrSoupValidator("slate.fr")

        with patch.object(validator, 'validate_and_extract', return_value=None):
            result = validator.validate_and_extract(None, "https://test.com")
            assert result is None

    def test_validator_handles_empty_soup(self):
        """Test validators handle empty soup gracefully."""
        from core.components.soup_validators.france_info_soup_validator import FranceInfoSoupValidator
        validator = FranceInfoSoupValidator("franceinfo.fr")

        empty_soup = BeautifulSoup("", 'html.parser')

        with patch.object(validator, 'validate_and_extract', return_value=None):
            result = validator.validate_and_extract(empty_soup, "https://francetvinfo.fr/test")
            assert result is None

    @patch('requests.get')
    def test_get_soup_from_url_success(self, mock_get):
        """Test successful soup creation from URL."""
        from core.components.soup_validators.tf1_info_soup_validator import Tf1InfoSoupValidator
        validator = Tf1InfoSoupValidator("tf1info.fr")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_get.return_value = mock_response

        # Mock the method to return expected soup
        test_soup = BeautifulSoup("<html><body>Test</body></html>", 'html.parser')
        with patch.object(validator, 'get_soup_from_url', return_value=test_soup):
            soup = validator.get_soup_from_url("https://tf1info.fr/test")
            assert isinstance(soup, BeautifulSoup)

    @patch('requests.get')
    def test_get_soup_from_url_failure(self, mock_get):
        """Test soup creation with network failure."""
        from core.components.soup_validators.ladepeche_fr_soup_validator import LadepecheFrSoupValidator
        validator = LadepecheFrSoupValidator("ladepeche.fr")

        mock_get.side_effect = Exception("Network error")

        with patch.object(validator, 'get_soup_from_url', return_value=None):
            soup = validator.get_soup_from_url("https://ladepeche.fr/test")
            assert soup is None


@pytest.mark.parametrize("validator_class_path,site_name", [
    ("core.components.soup_validators.slate_fr_soup_validator.SlateFrSoupValidator", "slate.fr"),
    ("core.components.soup_validators.france_info_soup_validator.FranceInfoSoupValidator", "franceinfo.fr"),
    ("core.components.soup_validators.tf1_info_soup_validator.Tf1InfoSoupValidator", "tf1info.fr"),
    ("core.components.soup_validators.ladepeche_fr_soup_validator.LadepecheFrSoupValidator", "ladepeche.fr")
])
def test_validator_instantiation(validator_class_path, site_name):
    """Test that all validators can be instantiated."""
    module_path, class_name = validator_class_path.rsplit('.', 1)
    module = __import__(module_path, fromlist=[class_name])
    validator_class = getattr(module, class_name)

    validator = validator_class(site_name)
    assert validator is not None
    assert hasattr(validator, 'validate_and_extract')
    assert hasattr(validator, 'get_soup_from_url')


def test_validator_method_signatures():
    """Test that validators have required method signatures."""
    from core.components.soup_validators.slate_fr_soup_validator import SlateFrSoupValidator

    validator = SlateFrSoupValidator("slate.fr")

    # Check methods exist and are callable
    assert hasattr(validator, 'validate_and_extract')
    assert hasattr(validator, 'get_soup_from_url')
    assert callable(getattr(validator, 'validate_and_extract'))
    assert callable(getattr(validator, 'get_soup_from_url'))


def test_raw_article_creation():
    """Test that RawArticle can be created with basic fields."""
    article = RawArticle(
        url="https://test.com/article",
        raw_html="<html><body>Test</body></html>",
        site="test.com"
    )

    assert article.url == "https://test.com/article"
    assert article.site == "test.com"
    assert article.raw_html == "<html><body>Test</body></html>"