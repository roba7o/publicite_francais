"""
French text processing utilities for article analysis.

This module provides text cleaning, normalization, and word frequency analysis
specifically optimized for French news articles.
"""

import re
import unicodedata
from collections import Counter
from typing import Dict, List, Set


class FrenchTextProcessor:
    """Enhanced text processor for French articles with optimized stopword filtering."""

    def __init__(self):
        # Essential French stopwords - reduced from massive list for better performance
        self.french_stopwords = {
            # Articles
            "le", "la", "les", "un", "une", "des", "du", "de", "au", "aux",
            # Pronouns
            "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "ce", "cette", "ces",
            # Prepositions
            "à", "dans", "sur", "avec", "sans", "pour", "par", "vers", "chez", "entre",
            # Conjunctions
            "et", "ou", "mais", "donc", "car", "ni", "or",
            # Common verbs (conjugated forms)
            "est", "sont", "était", "étaient", "être", "avoir", "a", "ont", "avait",
            # Common words
            "comme", "aussi", "bien", "très", "plus", "moins", "tout", "tous", "toute",
            "toutes", "peu", "beaucoup", "encore", "déjà", "maintenant", "alors",
            # Numbers
            "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix",
            # Time words
            "aujourd'hui", "hier", "demain", "semaine", "mois", "année", "jour",
            # Common adverbs
            "ici", "là", "où", "quand", "comment", "pourquoi", "si", "non", "oui",
            # Site-specific words (will be expanded by config)
        }
        
        self.min_word_length = 3
        self.max_word_length = 50

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize French text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text ready for analysis
        """
        if not text:
            return ""

        # Convert to lowercase and normalize unicode
        text = text.lower()
        text = unicodedata.normalize('NFD', text)
        
        # Remove accents from vowels (keep cedilla)
        text = re.sub(r'[àâä]', 'a', text)
        text = re.sub(r'[éèêë]', 'e', text)
        text = re.sub(r'[îï]', 'i', text)
        text = re.sub(r'[ôö]', 'o', text)
        text = re.sub(r'[ûüù]', 'u', text)
        text = re.sub(r'[ÿ]', 'y', text)
        
        # Remove special characters but keep apostrophes and hyphens
        text = re.sub(r'[^a-z0-9\s\'-]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def tokenize_french_text(self, text: str) -> List[str]:
        """
        Tokenize French text into words, handling contractions.
        
        Args:
            text: Cleaned text to tokenize
            
        Returns:
            List of individual words
        """
        if not text:
            return []

        # Split on whitespace
        words = text.split()
        
        # Handle French contractions (l'eau -> l'eau, d'accord -> d'accord)
        # Keep contractions as single tokens for better analysis
        processed_words = []
        
        for word in words:
            # Skip empty words
            if not word.strip():
                continue
                
            # Apply length filters
            if len(word) < self.min_word_length or len(word) > self.max_word_length:
                continue
                
            # Skip stopwords
            if word in self.french_stopwords:
                continue
                
            processed_words.append(word)
        
        return processed_words

    def count_word_frequency(self, text: str) -> Dict[str, int]:
        """
        Count word frequencies in French text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of word frequencies
        """
        if not text:
            return {}

        # Clean and tokenize text
        cleaned_text = self.clean_text(text)
        words = self.tokenize_french_text(cleaned_text)
        
        # Count frequencies
        return dict(Counter(words))

    def get_top_words(self, text: str, n: int = 50) -> List[tuple]:
        """
        Get top N most frequent words from text.
        
        Args:
            text: Text to analyze
            n: Number of top words to return
            
        Returns:
            List of (word, frequency) tuples, sorted by frequency
        """
        word_freq = self.count_word_frequency(text)
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:n]

    def filter_by_frequency(
        self, word_freq: Dict[str, int], min_freq: int = 2
    ) -> Dict[str, int]:
        """
        Filter words by minimum frequency.
        
        Args:
            word_freq: Word frequency dictionary
            min_freq: Minimum frequency threshold
            
        Returns:
            Filtered word frequency dictionary
        """
        return {word: freq for word, freq in word_freq.items() if freq >= min_freq}

    def expand_stopwords(self, additional_stopwords: Set[str]) -> None:
        """
        Add site-specific stopwords to the filter.
        
        Args:
            additional_stopwords: Set of additional words to filter out
        """
        self.french_stopwords.update(additional_stopwords)

    def set_word_length_limits(self, min_length: int = 3, max_length: int = 50) -> None:
        """
        Set minimum and maximum word length filters.
        
        Args:
            min_length: Minimum word length to include
            max_length: Maximum word length to include
        """
        self.min_word_length = min_length
        self.max_word_length = max_length
