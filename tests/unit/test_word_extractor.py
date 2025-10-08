"""
Unit tests for WordExtractor service.

Tests the French word extraction logic and WordFact creation.
"""

from unittest.mock import patch
import pytest

from database.models import RawArticle, WordFact
from services.word_extractor import WordExtractor


@pytest.fixture
def extractor():
    """WordExtractor instance for testing."""
    return WordExtractor()


@pytest.fixture
def sample_article():
    """Sample article for testing."""
    return RawArticle(
        url="https://test.fr/article",
        raw_html="<html><body><p>Test content</p></body></html>",
        site="test.fr",
    )


def test_extractor_initialization(extractor):
    """Test WordExtractor initializes with correct pattern."""
    assert extractor.french_word_pattern is not None


@patch("trafilatura.extract")
def test_extract_words_success(mock_extract, extractor, sample_article):
    """Test successful word extraction from article."""
    # Mock trafilatura to return French text
    mock_extract.return_value = (
        "L'économie française traverse une période difficile avec inflation."
    )

    word_facts = extractor.extract_words_from_article(sample_article)

    # Should extract all French words (no filtering)
    assert len(word_facts) > 0
    assert all(isinstance(wf, WordFact) for wf in word_facts)

    # Check word content - all words should be present
    words = [wf.word for wf in word_facts]
    assert "l'économie" in words  # French contractions kept as single words
    assert "française" in words
    assert "traverse" in words
    assert "une" in words  # Common words NOT filtered
    assert "période" in words
    assert "difficile" in words
    assert "avec" in words  # Common words NOT filtered
    assert "inflation" in words

    # Check metadata
    for i, wf in enumerate(word_facts):
        assert wf.article_id == sample_article.id
        assert wf.position_in_article == i
        assert wf.scraped_at is not None


@patch("trafilatura.extract")
def test_extract_words_no_content(mock_extract, extractor, sample_article):
    """Test extraction when trafilatura returns no content."""
    mock_extract.return_value = None

    word_facts = extractor.extract_words_from_article(sample_article)

    assert word_facts == []


@patch("trafilatura.extract")
def test_extract_words_exception(mock_extract, extractor, sample_article):
    """Test extraction handles trafilatura exceptions gracefully."""
    mock_extract.side_effect = Exception("Trafilatura error")

    word_facts = extractor.extract_words_from_article(sample_article)

    assert word_facts == []


def test_french_word_pattern(extractor):
    """Test French word pattern recognition."""
    text = "Voici des mots français: économie, café, naïf, être, coûter"
    words = extractor._extract_french_words(text)

    # Should capture French words with accents
    assert "économie" in words
    assert "café" in words
    assert "naïf" in words
    assert "être" in words
    assert "coûter" in words


def test_word_filtering(extractor):
    """Test that NO filtering is applied - all words are captured."""
    text = "Le chat mange une pomme dans la cuisine avec de l'eau"
    words = extractor._extract_french_words(text)

    # Should capture ALL words (no filtering)
    assert "chat" in words
    assert "mange" in words
    assert "pomme" in words
    assert "cuisine" in words

    # Should also include common words (NOT filtered)
    assert "le" in words
    assert "une" in words
    assert "dans" in words
    assert "la" in words
    assert "avec" in words
    assert "de" in words

    # Short words also captured (no length filtering)
    assert "l'" not in words


def test_word_normalization(extractor):
    """Test word normalization (lowercase)."""
    text = "ÉCONOMIE Française POLITIQUE"
    words = extractor._extract_french_words(text)

    # Should normalize to lowercase
    assert "économie" in words
    assert "française" in words
    assert "politique" in words

    # Should not contain uppercase
    assert "ÉCONOMIE" not in words
    assert "Française" not in words


def test_position_tracking(extractor):
    """Test that word positions are tracked correctly."""
    with patch("trafilatura.extract") as mock_extract:
        mock_extract.return_value = "premier second troisième quatrième"

        article = RawArticle(url="test.fr/pos", raw_html="<p>test</p>", site="test.fr")

        word_facts = extractor.extract_words_from_article(article)

        # Should maintain position order
        assert len(word_facts) == 4
        assert word_facts[0].word == "premier"
        assert word_facts[0].position_in_article == 0
        assert word_facts[1].word == "second"
        assert word_facts[1].position_in_article == 1
        assert word_facts[2].word == "troisième"
        assert word_facts[2].position_in_article == 2
        assert word_facts[3].word == "quatrième"
        assert word_facts[3].position_in_article == 3


def test_empty_text_handling(extractor):
    """Test handling of empty or whitespace-only text."""
    with patch("trafilatura.extract") as mock_extract:
        mock_extract.return_value = "   \n\t   "

        article = RawArticle(url="test.fr/empty", raw_html="<p></p>", site="test.fr")

        word_facts = extractor.extract_words_from_article(article)

        assert word_facts == []


@pytest.mark.parametrize(
    "french_text,expected_words",
    [
        ("C'est formidable", ["c'est", "formidable"]),
        ("Jean-Pierre mange", ["jean-pierre", "mange"]),
        ("L'hôtel français", ["l'hôtel", "français"]),
        ("Rendez-vous demain", ["rendez-vous", "demain"]),
    ],
)
def test_complex_french_patterns(extractor, french_text, expected_words):
    """Test extraction of complex French word patterns."""
    words = extractor._extract_french_words(french_text)

    for expected in expected_words:
        assert expected in words
