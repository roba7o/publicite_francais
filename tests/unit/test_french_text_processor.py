"""
Unit tests for the French text processor.

Tests the core text processing functionality including validation,
cleaning, tokenization, and word frequency analysis.
"""

import pytest
from unittest.mock import patch, Mock
from article_scrapers.utils.french_text_processor import FrenchTextProcessor


class TestFrenchTextProcessor:
    """Test suite for FrenchTextProcessor class."""
    
    def test_initialization(self):
        """Test processor initializes correctly."""
        processor = FrenchTextProcessor()
        assert hasattr(processor, 'french_stopwords')
        assert hasattr(processor, 'junk_patterns')
        assert hasattr(processor, 'logger')
        assert len(processor.french_stopwords) > 0
        assert len(processor.junk_patterns) > 0
    
    def test_validate_text_valid_input(self, french_text_processor):
        """Test text validation with valid input."""
        valid_text = "Ceci est un texte français valide avec suffisamment de contenu pour l'analyse."
        result = french_text_processor.validate_text(valid_text)
        assert result is not None
        assert isinstance(result, str)
        assert len(result.strip()) > 0
    
    def test_validate_text_empty_input(self, french_text_processor):
        """Test text validation with empty input."""
        assert french_text_processor.validate_text("") is None
        assert french_text_processor.validate_text(None) is None
        assert french_text_processor.validate_text("   ") is None
    
    def test_validate_text_too_short(self, french_text_processor):
        """Test text validation with insufficient content."""
        short_text = "Court"
        result = french_text_processor.validate_text(short_text)
        assert result is None
    
    def test_validate_text_spam_detection(self, french_text_processor):
        """Test spam detection in text validation."""
        # Text with excessive repetition (spam)
        spam_text = "test " * 100
        result = french_text_processor.validate_text(spam_text)
        assert result is None
    
    def test_validate_text_low_alphabetic_content(self, french_text_processor):
        """Test validation rejects text with too few alphabetic characters."""
        numeric_text = "123 456 789 @#$ %^& 123 456 789 @#$ %^&"
        result = french_text_processor.validate_text(numeric_text)
        assert result is None
    
    def test_clean_text_basic(self, french_text_processor):
        """Test basic text cleaning functionality."""
        dirty_text = "  VOICI un TEXTE avec Accents: àéèîôù  "
        cleaned = french_text_processor.clean_text(dirty_text)
        
        assert cleaned.islower()
        assert cleaned.strip() == cleaned  # No leading/trailing whitespace
        assert "à" not in cleaned  # Accents removed
        assert "é" not in cleaned
        assert "è" not in cleaned
    
    def test_clean_text_accent_replacement(self, french_text_processor):
        """Test specific accent replacements."""
        accented = "àâäéèêëîïôöûüùÿ"
        cleaned = french_text_processor.clean_text(accented)
        expected = "aaaeeeeiioouuuy"
        assert cleaned == expected
    
    def test_clean_text_special_characters(self, french_text_processor):
        """Test removal of special characters."""
        special_text = "Texte avec @#$%^& caractères spéciaux!!!"
        cleaned = french_text_processor.clean_text(special_text)
        
        # Should only contain letters, numbers, spaces, and allowed punctuation
        for char in cleaned:
            assert char.isalnum() or char in " '-"
    
    def test_tokenize_french_text_basic(self, french_text_processor):
        """Test basic French text tokenization."""
        text = "Voici un texte français simple pour tester"
        tokens = french_text_processor.tokenize_french_text(text)
        
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(token, str) for token in tokens)
        assert all(len(token) >= 4 for token in tokens)  # Min length filter
    
    def test_tokenize_french_text_stopword_removal(self, french_text_processor):
        """Test stopword removal in tokenization."""
        text = "le chat mange la souris dans le jardin"
        tokens = french_text_processor.tokenize_french_text(text)
        
        # Common French stopwords should be removed
        assert "le" not in tokens
        assert "la" not in tokens  
        assert "dans" not in tokens
        
        # Content words should remain
        assert "chat" in tokens
        assert "mange" in tokens
        assert "souris" in tokens
        assert "jardin" in tokens
    
    def test_tokenize_french_text_junk_filtering(self, french_text_processor):
        """Test junk word filtering in tokenization."""
        text = "article monde prix tres franc comple selon"
        tokens = french_text_processor.tokenize_french_text(text)
        
        # Junk words should be filtered out
        junk_found = any(word in french_text_processor.junk_patterns for word in tokens)
        assert not junk_found
    
    def test_tokenize_french_text_numeric_filtering(self, french_text_processor):
        """Test filtering of numeric and mostly-numeric words."""
        text = "texte avec 123 et abc123def et 50pourcent"
        tokens = french_text_processor.tokenize_french_text(text)
        
        # Pure numbers and mostly-numeric words should be filtered
        assert "123" not in tokens
        
        # Words with some letters should be evaluated based on ratio
        mostly_numeric = [token for token in tokens if any(c.isdigit() for c in token)]
        for token in mostly_numeric:
            digit_ratio = sum(c.isdigit() for c in token) / len(token)
            assert digit_ratio <= 0.6  # Should not exceed 60% numeric
    
    def test_count_word_frequency_basic(self, french_text_processor):
        """Test basic word frequency counting."""
        text = "chat chat souris chat jardin souris"
        frequencies = french_text_processor.count_word_frequency(text)
        
        assert isinstance(frequencies, dict)
        assert frequencies.get("chat", 0) > frequencies.get("souris", 0)
        assert frequencies.get("jardin", 0) > 0
    
    def test_count_word_frequency_empty_input(self, french_text_processor):
        """Test word frequency with empty input."""
        assert french_text_processor.count_word_frequency("") == {}
        assert french_text_processor.count_word_frequency(None) == {}
    
    def test_count_word_frequency_outlier_filtering(self, french_text_processor):
        """Test filtering of suspiciously high-frequency words."""
        # Create text with one word appearing very frequently (likely error)
        normal_text = "texte normal avec vocabulaire français varié"
        spam_word = "erreur " * 50
        text = normal_text + " " + spam_word
        
        frequencies = french_text_processor.count_word_frequency(text)
        
        # Outlier words should be filtered out
        max_frequency = max(frequencies.values()) if frequencies else 0
        total_words = sum(frequencies.values())
        assert max_frequency <= max(total_words * 0.1, 10)
    
    def test_extract_sentences_with_words(self, french_text_processor):
        """Test sentence context extraction."""
        text = "Le chat mange. Le chien dort. Les oiseaux chantent."
        words = ["chat", "chien", "oiseaux"]
        
        contexts = french_text_processor.extract_sentences_with_words(text, words)
        
        assert isinstance(contexts, dict)
        assert "chat" in contexts
        assert "chien" in contexts  
        assert "oiseaux" in contexts
        
        # Contexts should be sentences containing the words
        assert "mange" in contexts["chat"]
        assert "dort" in contexts["chien"]
        assert "chantent" in contexts["oiseaux"]
    
    def test_extract_sentences_empty_input(self, french_text_processor):
        """Test sentence extraction with empty input."""
        assert french_text_processor.extract_sentences_with_words("", ["word"]) == {}
        assert french_text_processor.extract_sentences_with_words("text", []) == {}
    
    def test_extract_sentences_context_cleaning(self, french_text_processor):
        """Test that extracted contexts are properly cleaned."""
        text = "### Le chat mange!!! \"\"\" Le chien dort. ### \n\n"
        words = ["chat", "chien"]
        
        contexts = french_text_processor.extract_sentences_with_words(text, words)
        
        for context in contexts.values():
            # Should not contain hashtags, triple quotes, or excessive whitespace
            assert "###" not in context
            assert '"""' not in context
            assert context == context.strip()
    
    def test_get_top_words(self, french_text_processor):
        """Test getting top N most frequent words."""
        text = "chat chat chat souris souris jardin"
        top_words = french_text_processor.get_top_words(text, n=3)
        
        assert isinstance(top_words, list)
        assert len(top_words) <= 3
        assert all(isinstance(item, tuple) for item in top_words)
        assert all(len(item) == 2 for item in top_words)  # (word, frequency)
        
        # Should be sorted by frequency (descending)
        if len(top_words) > 1:
            assert top_words[0][1] >= top_words[1][1]
    
    def test_filter_by_frequency(self, french_text_processor):
        """Test frequency-based filtering."""
        word_freq = {"frequent": 5, "moderate": 2, "rare": 1}
        
        filtered = french_text_processor.filter_by_frequency(word_freq, min_freq=2)
        
        assert "frequent" in filtered
        assert "moderate" in filtered
        assert "rare" not in filtered
    
    def test_expand_stopwords(self, french_text_processor):
        """Test adding custom stopwords."""
        original_count = len(french_text_processor.french_stopwords)
        custom_stopwords = {"custom1", "custom2"}
        
        french_text_processor.expand_stopwords(custom_stopwords)
        
        assert len(french_text_processor.french_stopwords) == original_count + 2
        assert "custom1" in french_text_processor.french_stopwords
        assert "custom2" in french_text_processor.french_stopwords
    
    def test_set_word_length_limits(self, french_text_processor):
        """Test setting word length limits."""
        french_text_processor.set_word_length_limits(min_length=5, max_length=15)
        
        assert french_text_processor.min_word_length == 5
        assert french_text_processor.max_word_length == 15
    
    @pytest.mark.parametrize("invalid_input", [
        "",
        None,
        123,
        [],
        {"not": "text"}
    ])
    def test_validate_text_invalid_types(self, french_text_processor, invalid_input):
        """Test text validation with invalid input types."""
        result = french_text_processor.validate_text(invalid_input)
        assert result is None
    
    @pytest.mark.parametrize("text_with_accents,expected_clean", [
        ("café", "cafe"),
        ("hôtel", "hotel"), 
        ("élève", "eleve"),
        ("naïf", "naif"),
        ("coût", "cout"),
    ])
    def test_specific_accent_replacements(self, french_text_processor, text_with_accents, expected_clean):
        """Test specific accent replacement cases."""
        result = french_text_processor.clean_text(text_with_accents)
        assert expected_clean in result
    
    def test_performance_with_large_text(self, french_text_processor):
        """Test processor performance with large text input."""
        import time
        
        # Create moderately large text
        large_text = " ".join([
            "Voici un texte français pour tester les performances du processeur.",
            "Ce texte contient suffisamment de mots pour évaluer la vitesse.",
            "Le système doit traiter ce contenu de manière efficace et rapide."
        ] * 100)
        
        start_time = time.time()
        result = french_text_processor.count_word_frequency(large_text)
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should complete within 1 second
        assert isinstance(result, dict)
        assert len(result) > 0