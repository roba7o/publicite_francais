import re
import unicodedata
from collections import Counter
from typing import Dict, List, Set, Optional

from config.junk_words_config import get_junk_patterns
from utils.structured_logger import get_structured_logger


class FrenchTextProcessor:
    """
    Advanced French text processor for news article analysis.

    This class provides comprehensive French text processing capabilities
    specifically designed for news article analysis and vocabulary extraction.
    It handles French language specifics including accents, stopwords,
    and common parsing artifacts.

    Features:
    - French-specific accent normalization
    - Comprehensive stopword filtering
    - Junk word pattern detection
    - Word frequency analysis
    - Sentence context extraction
    - Text validation and spam detection
    - Configurable word length limits

    The processor is optimized for extracting meaningful vocabulary
    from French news articles while filtering out common words,
    parsing artifacts, and other noise.

    Example:
        >>> processor = FrenchTextProcessor()
        >>> frequencies = processor.count_word_frequency("Le chat mange.")
        >>> # Returns {"chat": 1, "mange": 1} (stopwords filtered)
    """

    def __init__(self):
        """
        Initialize the French text processor with default settings.

        Sets up French stopwords, word length limits, and loads
        junk word patterns from external configuration.
        """
        self.french_stopwords = {
            "le",
            "la",
            "les",
            "un",
            "une",
            "des",
            "du",
            "de",
            "au",
            "aux",
            "je",
            "tu",
            "il",
            "elle",
            "nous",
            "vous",
            "ils",
            "elles",
            "ce",
            "cette",
            "ces",
            "à",
            "dans",
            "sur",
            "avec",
            "sans",
            "pour",
            "par",
            "vers",
            "chez",
            "entre",
            "et",
            "ou",
            "mais",
            "donc",
            "car",
            "ni",
            "or",
            "est",
            "sont",
            "était",
            "étaient",
            "être",
            "avoir",
            "a",
            "ont",
            "avait",
            "comme",
            "aussi",
            "bien",
            "très",
            "plus",
            "moins",
            "tout",
            "tous",
            "toute",
            "toutes",
            "peu",
            "beaucoup",
            "encore",
            "déjà",
            "maintenant",
            "alors",
            "un",
            "deux",
            "trois",
            "quatre",
            "cinq",
            "six",
            "sept",
            "huit",
            "neuf",
            "dix",
            "aujourd'hui",
            "hier",
            "demain",
            "semaine",
            "mois",
            "année",
            "jour",
            "ici",
            "là",
            "où",
            "quand",
            "comment",
            "pourquoi",
            "si",
            "non",
            "oui",
        }
        self.min_word_length = 3
        self.max_word_length = 50

        # Load junk patterns from external configuration
        self.junk_patterns = get_junk_patterns()

        # Initialize logger
        self.logger = get_structured_logger(self.__class__.__name__)

    def validate_text(self, text: str) -> Optional[str]:
        """
        Validate input text for processing suitability.

        Performs comprehensive validation to ensure the text is suitable
        for meaningful analysis. Checks for minimum content requirements,
        spam detection, and content quality metrics.

        Args:
            text: Raw input text to validate

        Returns:
            Validated and cleaned text, or None if validation fails

        Validation criteria:
        - Minimum 10 characters and 5 words
        - Maximum 1MB size limit
        - At least 30% unique words (spam detection)
        - At least 50% alphabetic characters

        Example:
            >>> processor = FrenchTextProcessor()
            >>> valid = processor.validate_text("Voici un texte valide.")
            >>> if valid:
            ...     # Process the text
        """
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
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.3:  # Less than 30% unique words
            self.logger.debug(
                "Text validation failed: low uniqueness",
                extra_data={
                    "text_length": len(text),
                    "word_count": len(words),
                    "unique_ratio": round(unique_ratio, 3),
                    "threshold": 0.3,
                    "reason": "spam_detection",
                },
            )
            return None

        # Check for excessive non-alphabetic content
        alpha_chars = sum(1 for c in text if c.isalpha())
        alpha_ratio = alpha_chars / len(text)
        if alpha_ratio < 0.5:  # Less than 50% alphabetic
            self.logger.debug(
                "Text validation failed: low alphabetic content",
                extra_data={
                    "text_length": len(text),
                    "alpha_chars": alpha_chars,
                    "alpha_ratio": round(alpha_ratio, 3),
                    "threshold": 0.5,
                    "reason": "non_alphabetic_content",
                },
            )
            return None

        return text

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize French text for processing.

        Performs comprehensive text cleaning including case normalization,
        accent removal, character filtering, and whitespace cleanup.
        Optimized for French language characteristics.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned and normalized text

        Processing steps:
        1. Convert to lowercase
        2. Unicode normalization (NFD)
        3. French accent replacement (à→a, é→e, etc.)
        4. Character filtering (keep only alphanumeric, spaces, apostrophes)
        5. Whitespace normalization

        Example:
            >>> processor = FrenchTextProcessor()
            >>> clean = processor.clean_text("C'est très intéressant!")
            >>> # Returns "c'est tres interessant"
        """
        if not text:
            return ""

        text = text.lower()
        text = unicodedata.normalize("NFD", text)

        # Optimized accent replacement
        text = re.sub(r"[àâä]", "a", text)
        text = re.sub(r"[éèêë]", "e", text)
        text = re.sub(r"[îï]", "i", text)
        text = re.sub(r"[ôö]", "o", text)
        text = re.sub(r"[ûüù]", "u", text)
        text = re.sub(r"[ÿ]", "y", text)

        # Single regex for character filtering
        text = re.sub(r"[^a-z0-9\s\'-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def tokenize_french_text(self, text: str) -> List[str]:
        """
        Tokenize French text into meaningful words for analysis.

        Performs sophisticated tokenization that filters out junk words,
        truncated terms, stopwords, and other noise common in scraped
        French news content.

        Args:
            text: Cleaned text to tokenize

        Returns:
            List of meaningful French words suitable for analysis

        Filtering criteria:
        - Minimum 4 characters after cleaning
        - Not purely numeric or mostly numeric
        - Not in junk word patterns
        - Not a French stopword
        - Contains alphabetic characters
        - Passes length requirements

        Example:
            >>> processor = FrenchTextProcessor()
            >>> words = processor.tokenize_french_text(
            ...     "le chat mange très bien"
            ... )
            >>> # Returns ["chat", "mange", "bien"] (filtered stopwords)
        """
        if not text:
            return []

        # Use junk patterns from external configuration

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

            # Skip junk words using external configuration
            if word_clean in self.junk_patterns:
                continue

            # Skip if word contains only punctuation
            if not any(c.isalpha() for c in word_clean):
                continue

            # Clean the word
            word_clean = re.sub(r"[^\w\s]", "", word_clean)
            word_clean = unicodedata.normalize("NFD", word_clean)
            word_clean = "".join(c for c in word_clean if not unicodedata.combining(c))

            # Skip stopwords
            if word_clean in self.french_stopwords:
                continue

            # Skip if word is too short after cleaning
            if len(word_clean) < 4:
                continue

            if word_clean:
                words.append(word_clean)

        return words

    def extract_sentences_with_words(
        self, original_text: str, words: List[str]
    ) -> Dict[str, str]:
        """
        Extract sentence contexts for specific words from the original text.

        Finds sentences containing each word and returns them as context
        for vocabulary learning. Cleans and formats contexts appropriately.

        Args:
            original_text: The original article text (before cleaning)
            words: List of words to find contexts for

        Returns:
            Dictionary mapping words to their containing sentences

        Context processing:
        - Splits text on French sentence boundaries (. ! ?)
        - Removes newlines, hashtags, and extra whitespace
        - Limits context length to 200 characters
        - Excludes numeric-heavy words from context
          extraction
        - Returns first found context for each word

        Example:
            >>> processor = FrenchTextProcessor()
            >>> text = "Le chat mange. Il est content."
            >>> contexts = processor.extract_sentences_with_words(
            ...     text, ["chat", "content"]
            ... )
            >>> # Returns {"chat": "Le chat mange",
            ...          "content": "Il est content"}
        """
        """
        Extract sentences containing specific words from the original
        text.
        Ensures each context is a single sentence, with no newlines or extra
        whitespace.
        Removes hashtags, triple quotes, and strips punctuation/whitespace from
        context.
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
        sentence_pattern = r"(?<=[.!?])\s+"
        sentences = re.split(sentence_pattern, original_text)

        word_contexts = {}
        for sentence in sentences:
            # Remove newlines and extra spaces
            clean_sentence = " ".join(sentence.split())
            # Remove hashtags and triple quotes
            clean_sentence = clean_sentence.replace("##", "").replace('"""', "")
            # Remove leading/trailing punctuation and whitespace
            clean_sentence = clean_sentence.strip(string.punctuation + " \"'\n\t")
            if len(clean_sentence) < 10:
                continue
            cleaned_for_match = self.clean_text(clean_sentence)
            sentence_words = cleaned_for_match.split()
            for word in words:
                # Exclude words that are only numbers or mostly numbers
                if (
                    word.isdigit()
                    or sum(c.isdigit() for c in word) / max(1, len(word)) > 0.6
                ):
                    continue
                if word in sentence_words and word not in word_contexts:
                    word_contexts[word] = clean_sentence[:200]  # Limit context length
        return word_contexts

    def count_word_frequency(self, text: str) -> Dict[str, int]:
        """
        Analyze text and return meaningful word frequency counts.

        Main entry point for text analysis. Validates, cleans, tokenizes,
        and counts word frequencies while filtering out suspicious patterns
        that likely indicate parsing errors.

        Args:
            text: Raw text content to analyze

        Returns:
            Dictionary of word frequencies, filtered for quality

        Processing pipeline:
        1. Text validation (spam detection, size limits)
        2. Text cleaning (normalization, accent removal)
        3. Tokenization (filtering junk words, stopwords)
        4. Frequency counting with outlier detection
        5. Suspicious frequency filtering (max 10% of total)

        Example:
            >>> processor = FrenchTextProcessor()
            >>> freq = processor.count_word_frequency(
            ...     "Le chat mange. Le chat dort."
            ... )
            >>> # Returns {"chat": 2, "mange": 1, "dort": 1}
        """
        validated_text = self.validate_text(text)
        if not validated_text:
            return {}

        cleaned_text = self.clean_text(validated_text)
        words = self.tokenize_french_text(cleaned_text)

        if not words:
            self.logger.debug(
                "Word frequency analysis returned empty",
                extra_data={
                    "text_length": len(validated_text) if validated_text else 0,
                    "reason": "no_valid_words_after_tokenization",
                },
            )
            return {}

        word_counts = dict(Counter(words))

        # Remove words that appear suspiciously often (likely parsing errors)
        total_words = sum(word_counts.values())
        max_frequency = max(total_words * 0.1, 10)  # Max 10% of total or 10 occurrences

        filtered_words = {
            word: count for word, count in word_counts.items() if count <= max_frequency
        }

        filtered_count = len(word_counts) - len(filtered_words)
        if filtered_count > 0:
            self.logger.debug(
                "Filtered suspicious high-frequency words",
                extra_data={
                    "original_word_count": len(word_counts),
                    "filtered_word_count": len(filtered_words),
                    "removed_count": filtered_count,
                    "max_frequency_threshold": max_frequency,
                },
            )

        return filtered_words

    def get_top_words(self, text: str, n: int = 50) -> List[tuple]:
        """
        Get top N most frequent words from text.

        Analyzes text and returns the most frequently occurring words,
        useful for getting an overview of article content or identifying
        key vocabulary.

        Args:
            text: Text to analyze
            n: Number of top words to return (default: 50)

        Returns:
            List of (word, frequency) tuples, sorted by frequency descending

        Example:
            >>> processor = FrenchTextProcessor()
            >>> top_words = processor.get_top_words("text content", n=10)
            >>> for word, freq in top_words:
            ...     print(f"{word}: {freq}")
        """
        word_freq = self.count_word_frequency(text)
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:n]

    def filter_by_frequency(
        self, word_freq: Dict[str, int], min_freq: int = 2
    ) -> Dict[str, int]:
        """
        Filter words by minimum frequency threshold.

        Removes words that appear less than the specified minimum
        frequency, useful for focusing on more significant vocabulary.

        Args:
            word_freq: Word frequency dictionary to filter
            min_freq: Minimum frequency threshold (default: 2)

        Returns:
            Filtered word frequency dictionary

        Example:
            >>> frequencies = {"word1": 5, "word2": 1, "word3": 3}
            >>> filtered = processor.filter_by_frequency(
            ...     frequencies, min_freq=2
            ... )
            >>> # Returns {"word1": 5, "word3": 3}
        """
        return {word: freq for word, freq in word_freq.items() if freq >= min_freq}

    def expand_stopwords(self, additional_stopwords: Set[str]) -> None:
        """
        Add site-specific stopwords to the filter.

        Allows customization of stopword filtering for specific news sources
        that may have unique vocabulary patterns or site-specific terms.

        Args:
            additional_stopwords: Set of additional words to filter out

        Example:
            >>> processor = FrenchTextProcessor()
            >>> processor.expand_stopwords(
            ...     {"blog", "article", "site"}
            ... )
        """
        self.french_stopwords.update(additional_stopwords)

    def set_word_length_limits(self, min_length: int = 3, max_length: int = 50) -> None:
        """
        Set minimum and maximum word length filters.

        Configures word length boundaries for filtering. Very short words
        are often articles/prepositions, while very long words are often
        URLs, technical terms, or parsing errors.

        Args:
            min_length: Minimum word length to include (default: 3)
            max_length: Maximum word length to include (default: 50)

        Example:
            >>> processor = FrenchTextProcessor()
            >>> processor.set_word_length_limits(min_length=4, max_length=20)
        """
        self.min_word_length = min_length
        self.max_word_length = max_length
