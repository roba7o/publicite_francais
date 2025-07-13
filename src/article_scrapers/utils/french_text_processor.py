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
        
        # Optimized accent replacement
        text = re.sub(r'[àâä]', 'a', text)
        text = re.sub(r'[éèêë]', 'e', text)
        text = re.sub(r'[îï]', 'i', text)
        text = re.sub(r'[ôö]', 'o', text)
        text = re.sub(r'[ûüù]', 'u', text)
        text = re.sub(r'[ÿ]', 'y', text)
        
        # Single regex for character filtering
        text = re.sub(r'[^a-z0-9\s\'-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def tokenize_french_text(self, text: str) -> List[str]:
        if not text:
            return []

        # Enhanced junk word patterns
        junk_patterns = {
            # Truncated words (common in French)
            'tre', 'ses', 'comple', 'apre', 'franc', 'cision', 'sente', 'core', 'bre',
            'tait', 'ment', 'leurs', 'dont', 'quipe', 'dote', 'serait', 'avance',
            'toiles', 'tecter', 'ramiro', 'caisse', 'saide', 'rentes', 'messages',
            'involontaires', 'monde', 'ducatif', 'suspecte', 'd\'avoir', 'mis',
            'examen', 'meurtre', 'personne', 'charge', 'd\'une', 'mission', 'public',
            'place', 'tention', 'provisoire', 'soupc', 'onne', 'lors', 'd\'un',
            'empreinte', 'repe', 'peut-e', 'contro', 'sacs', 'devant', 'franc',
            'oise-dolto', 'nucle', 'aires', 'bombe', 'europe', 'd\'un', 'ricain',
            'fense', 'l\'otan', 'certains', 'dissuasion', 'aire', 'continent',
            'l\'europe', 'l\'arsenal', 'face', 'enne', 'pourrait', 'pays',
            'l\'uranium', 'missiles', 'londres', 'l\'allemagne', 'politique',
            'france', 'royaume-uni', 'dote', 'ration', 'leur', 'renforcement',
            'reste', 'votre', 'argent', 'commenc', 'ait', 'travailler', 'premier',
            'certains', 'placements', 'offrent', 'potentiellement', 'jusqu',
            'rendement', 'cashback', 'imme', 'diat', 'investissement', 'payer',
            'cher', 'investir', 'suivez',
            
            # Common French words (too frequent for flashcards)
            'selon', 'qui', 'que', 'pas', 'monde', 'fait', 'peuvent', 'leur',
            'prix', 'offre', 'mode', 'impose', 'euros', 'dont', 'couverture',
            'simple', 'peut', 'ses', 'sente', 'ment', 'leurs', 'comple',
            
            # Short words (likely incomplete)
            'tre', 'ses', 'pre', 'qui', 'que', 'pas', 'fait', 'dont', 'peut',
            
            # Common verb forms
            'tait', 'serait', 'peuvent', 'offrent', 'commenc', 'ait', 'dote',
            
            # Common adjectives/adverbs
            'simple', 'comple', 'certains', 'potentiellement', 'imme', 'diat',
            
            # Common nouns (too generic)
            'monde', 'prix', 'offre', 'mode', 'euros', 'couverture', 'placements',
            'rendement', 'investissement', 'argent', 'votre', 'leur', 'leurs',
        }

        words = []
        for word in text.split():
            word_clean = word.strip().lower()
            
            # Skip if word is too short (less than 4 characters)
            if len(word_clean) < 4:
                continue
                
            # Skip if word is only numbers
            if word_clean.isdigit():
                continue
                
            # Skip if word is mostly numbers
            if sum(c.isdigit() for c in word_clean) / max(1, len(word_clean)) > 0.6:
                continue
                
            # Skip junk words
            if word_clean in junk_patterns:
                continue
                
            # Skip if word contains only punctuation
            if not any(c.isalpha() for c in word_clean):
                continue
                
            # Clean the word
            word_clean = re.sub(r'[^\w\s]', '', word_clean)
            word_clean = unicodedata.normalize('NFD', word_clean)
            word_clean = ''.join(c for c in word_clean if not unicodedata.combining(c))
            
            # Skip stopwords
            if word_clean in self.french_stopwords:
                continue
                
            # Skip if word is too short after cleaning
            if len(word_clean) < 4:
                continue
                
            if word_clean:
                words.append(word_clean)
                
        return words

    def extract_sentences_with_words(self, original_text: str, words: List[str]) -> Dict[str, str]:
        """
        Extract sentences containing specific words from the original text.
        Ensures each context is a single sentence, with no newlines or extra whitespace.
        Removes hashtags, triple quotes, and strips punctuation/whitespace from context.
        Args:
            original_text: The original text (before cleaning)
            words: List of words to find sentences for
        Returns:
            Dictionary mapping words to their containing sentences
        """
        import string
        if not original_text or not words:
            return {}

        # Split text into sentences (French sentence endings)
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, original_text)

        word_contexts = {}
        for sentence in sentences:
            # Remove newlines and extra spaces
            clean_sentence = ' '.join(sentence.split())
            # Remove hashtags and triple quotes
            clean_sentence = clean_sentence.replace('##', '').replace('"""', '')
            # Remove leading/trailing punctuation and whitespace
            clean_sentence = clean_sentence.strip(string.punctuation + ' "\'\n\t')
            if len(clean_sentence) < 10:
                continue
            cleaned_for_match = self.clean_text(clean_sentence)
            sentence_words = cleaned_for_match.split()
            for word in words:
                # Exclude words that are only numbers or mostly numbers
                if word.isdigit() or sum(c.isdigit() for c in word) / max(1, len(word)) > 0.6:
                    continue
                if word in sentence_words and word not in word_contexts:
                    word_contexts[word] = clean_sentence[:200]  # Limit context length
        return word_contexts

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
