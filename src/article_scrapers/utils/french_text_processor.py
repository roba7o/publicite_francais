import re
import unicodedata
from collections import Counter
from typing import Dict, List, Set

class FrenchTextProcessor:
    """
    Enhanced text processor for French articles with proper cleaning,
    normalization, and stopword filtering.
    """
    
    def __init__(self):
        # Common French stopwords - you might want to expand this list
        self.french_stopwords = {
            'le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour',
            'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus',
            'par', 'grand', 'il', 'me', 'même', 'faire', 'elle', 'si', 'lors', 'mon',
            'man', 'qui', 'lui', 'va', 'où', 'up', 'du', 'la', 'au', 'sur', 'je', 'ma',
            'ta', 'sa', 'notre', 'votre', 'leur', 'mes', 'tes', 'ses', 'nos', 'vos',
            'leurs', 'ce', 'cet', 'cette', 'ces', 'mon', 'ton', 'son', 'ma', 'ta', 'sa',
            'mes', 'tes', 'ses', 'notre', 'votre', 'leur', 'nos', 'vos', 'leurs', 'le',
            'la', 'les', 'un', 'une', 'des', 'du', 'de', 'des', 'à', 'au', 'aux', 'dans',
            'sur', 'sous', 'avec', 'sans', 'pour', 'par', 'vers', 'chez', 'contre',
            'depuis', 'pendant', 'avant', 'après', 'devant', 'derrière', 'entre', 'parmi',
            'selon', 'malgré', 'grâce', 'dès', 'jusque', 'jusqu', 'car', 'donc', 'mais',
            'ou', 'et', 'ni', 'or', 'si', 'que', 'quand', 'comme', 'lorsque', 'puisque',
            'bien', 'quoique', 'afin', 'pour', 'de', 'peur', 'crainte', 'condition',
            'pourvu', 'moins', 'suppose', 'cas', 'soit', 'alors', 'ainsi', 'aussi',
            'cependant', 'néanmoins', 'toutefois', 'pourtant', 'en', 'effet', 'par',
            'ailleurs', 'addition', 'autre', 'part', 'contraire', 'revanche', 'fait',
            'réalité', 'vérité', 'dire', 'autres', 'termes', 'exemple', 'bref', 'somme',
            'toute', 'façon', 'cas', 'lieu', 'enfin', 'finalement', 'conclusion'
        }
        
        # Minimum word length to consider
        self.min_word_length = 3
        
        # Maximum word length (to filter out very long strings that might be URLs, etc.)
        self.max_word_length = 50

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize French text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Remove HTML entities and normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Remove URLs
        text = re.sub(r'https?://[^\s]+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove numbers (optional - you might want to keep them)
        # text = re.sub(r'\d+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def tokenize_french_text(self, text: str) -> List[str]:
        """
        Tokenize French text into words with proper handling of French punctuation.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        if not text:
            return []
            
        # Clean the text first
        text = self.clean_text(text)
        
        # Split on whitespace and punctuation, but preserve contractions
        # This regex keeps apostrophes in contractions like "l'humanité"
        tokens = re.findall(r"\b[a-zA-Zàâäéèêëïîôöùûüÿç]+(?:'[a-zA-Zàâäéèêëïîôöùûüÿç]+)?\b", text.lower())
        
        # Filter tokens
        filtered_tokens = []
        for token in tokens:
            # Skip if too short or too long
            if len(token) < self.min_word_length or len(token) > self.max_word_length:
                continue
                
            # Skip stopwords
            if token in self.french_stopwords:
                continue
                
            # Skip tokens that are mostly punctuation
            if re.match(r'^[^\w\s]+$', token):
                continue
                
            filtered_tokens.append(token)
            
        return filtered_tokens

    def count_word_frequency(self, text: str) -> Dict[str, int]:
        """
        Count word frequencies in French text with proper cleaning.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of word frequencies
        """
        tokens = self.tokenize_french_text(text)
        return dict(Counter(tokens))

    def get_top_words(self, text: str, n: int = 50) -> List[tuple]:
        """
        Get the top N most frequent words.
        
        Args:
            text: Text to analyze
            n: Number of top words to return
            
        Returns:
            List of (word, frequency) tuples
        """
        word_freq = self.count_word_frequency(text)
        return Counter(word_freq).most_common(n)

    def filter_by_frequency(self, word_freq: Dict[str, int], min_freq: int = 2) -> Dict[str, int]:
        """
        Filter words by minimum frequency.
        
        Args:
            word_freq: Dictionary of word frequencies
            min_freq: Minimum frequency threshold
            
        Returns:
            Filtered dictionary
        """
        return {word: freq for word, freq in word_freq.items() if freq >= min_freq}

    def expand_stopwords(self, additional_stopwords: Set[str]) -> None:
        """
        Add additional stopwords to the filter list.
        
        Args:
            additional_stopwords: Set of additional stopwords to add
        """
        self.french_stopwords.update(additional_stopwords)

    def set_word_length_limits(self, min_length: int = 3, max_length: int = 50) -> None:
        """
        Set minimum and maximum word length limits.
        
        Args:
            min_length: Minimum word length
            max_length: Maximum word length
        """
        self.min_word_length = min_length
        self.max_word_length = max_length