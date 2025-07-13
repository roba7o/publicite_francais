import re
import unicodedata
from collections import Counter
from typing import Dict, List, Set, Optional


class FrenchTextProcessor:
    def __init__(self):
        self.french_stopwords = {
            "le", "la", "les", "un", "une", "des", "du", "de", "au", "aux",
            "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "ce", "cette", "ces",
            "à", "dans", "sur", "avec", "sans", "pour", "par", "vers", "chez", "entre",
            "et", "ou", "mais", "donc", "car", "ni", "or",
            "est", "sont", "était", "étaient", "être", "avoir", "a", "ont", "avait",
            "comme", "aussi", "bien", "très", "plus", "moins", "tout", "tous", "toute",
            "toutes", "peu", "beaucoup", "encore", "déjà", "maintenant", "alors",
            "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix",
            "aujourd'hui", "hier", "demain", "semaine", "mois", "année", "jour",
            "ici", "là", "où", "quand", "comment", "pourquoi", "si", "non", "oui",
        }
        self.min_word_length = 3
        self.max_word_length = 50

    def validate_text(self, text: str) -> Optional[str]:
        if not text or not isinstance(text, str):
            return None
        
        text = text.strip()
        if len(text) < 10:
            return None
        
        if len(text) > 1000000:  # 1MB limit
            return None
        
        word_count = len(text.split())
        if word_count < 5:
            return None
        
        # Check for excessive repetition (spam detection)
        words = text.lower().split()
        if len(set(words)) / len(words) < 0.3:  # Less than 30% unique words
            return None
        
        # Check for excessive non-alphabetic content
        alpha_chars = sum(1 for c in text if c.isalpha())
        if alpha_chars / len(text) < 0.5:  # Less than 50% alphabetic
            return None
        
        return text

    def clean_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.lower()
        text = unicodedata.normalize('NFD', text)
        
        text = re.sub(r'[àâä]', 'a', text)
        text = re.sub(r'[éèêë]', 'e', text)
        text = re.sub(r'[îï]', 'i', text)
        text = re.sub(r'[ôö]', 'o', text)
        text = re.sub(r'[ûüù]', 'u', text)
        text = re.sub(r'[ÿ]', 'y', text)
        
        text = re.sub(r'[^a-z0-9\s\'-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def tokenize_french_text(self, text: str) -> List[str]:
        if not text:
            return []

        words = []
        for word in text.split():
            if (word.strip() and 
                self.min_word_length <= len(word) <= self.max_word_length and 
                word not in self.french_stopwords):
                words.append(word)
        
        return words

    def count_word_frequency(self, text: str) -> Dict[str, int]:
        validated_text = self.validate_text(text)
        if not validated_text:
            return {}

        cleaned_text = self.clean_text(validated_text)
        words = self.tokenize_french_text(cleaned_text)
        
        if not words:
            return {}
        
        word_counts = dict(Counter(words))
        
        # Remove words that appear suspiciously often (likely parsing errors)
        total_words = sum(word_counts.values())
        max_frequency = max(total_words * 0.1, 10)  # Max 10% of total or 10 occurrences
        
        return {word: count for word, count in word_counts.items() 
                if count <= max_frequency}

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
