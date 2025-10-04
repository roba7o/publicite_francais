"""
Word extraction service for French vocabulary learning.

Extracts individual French words from article HTML and creates
denormalized WordFact objects for database storage.
"""

import re
from datetime import datetime

import trafilatura

from database.models import RawArticle, WordFact
from utils.structured_logger import get_logger

logger = get_logger(__name__)


class WordExtractor:
    """Service for extracting French words from articles."""

    def __init__(self):
        """Initialize the word extractor."""
        # Basic French word pattern (letters with accents, apostrophes, hyphens)
        self.french_word_pattern = re.compile(
            r"\b[a-zA-ZàâäéèêëïîôöùûüÿñæœÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÑÆŒ''-]+\b"
        )

        # Words to skip (too common/not useful for vocabulary)
        self.skip_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
            'est', 'sont', 'a', 'ont', 'dans', 'sur', 'avec', 'pour', 'par',
            'ce', 'cette', 'ces', 'il', 'elle', 'ils', 'elles', 'qui', 'que',
            'se', 'sa', 'son', 'ses', 'nous', 'vous', 'leur', 'leurs'
        }

    def extract_words_from_article(self, article: RawArticle) -> list[WordFact]:
        """
        Extract French words from article and return as WordFact objects.

        Args:
            article: RawArticle with HTML content

        Returns:
            List of WordFact objects (empty if extraction fails)
        """
        try:
            # Extract text content using trafilatura
            extracted_text = trafilatura.extract(article.raw_html)

            if not extracted_text:
                logger.warning(f"No text extracted from article {article.id}")
                return []

            # Extract French words
            words = self._extract_french_words(extracted_text)

            # Create WordFact objects
            word_facts = []
            extraction_time = datetime.now().isoformat()

            for position, word in enumerate(words):
                word_fact = WordFact(
                    word=word,
                    article_id=article.id,
                    position_in_article=position,
                    scraped_at=extraction_time
                )
                word_facts.append(word_fact)

            logger.info(f"Extracted {len(word_facts)} words from article {article.id}")
            return word_facts

        except Exception as e:
            logger.warning(f"Failed to extract words from article {article.id}: {e}")
            return []  # Fail gracefully

    def _extract_french_words(self, text: str) -> list[str]:
        """
        Extract and normalize French words from text.

        Args:
            text: Extracted article text

        Returns:
            List of normalized French words
        """
        # Find all words matching French pattern
        words = self.french_word_pattern.findall(text.lower())

        # Filter out common words and short words
        filtered_words = [
            word for word in words
            if len(word) >= 3 and word not in self.skip_words
        ]

        return filtered_words