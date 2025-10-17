"""
Word extraction service for French vocabulary learning.

Extracts individual French words from article HTML and creates
denormalized WordFact objects for database storage.
"""

import re

import trafilatura

from database.models import RawArticle, WordFact
from utils.structured_logger import get_logger

logger = get_logger(__name__)


class WordExtractor:
    """Service for extracting French words from articles."""

    def __init__(self):
        """Initialize the word extractor."""
        # Complete French word pattern (all French letters, accents, apostrophes, hyphens)
        self.french_word_pattern = re.compile(
            r"\b[a-zA-ZàâäçéèêëïîôöùûüÿñæœÀÂÄÇÉÈÊËÏÎÔÖÙÛÜŸÑÆŒ''-]+\b"
        )

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

            # Extract French words (find all words matching pattern, normalize to lowercase)
            words = self.french_word_pattern.findall(extracted_text.lower())

            # Create WordFact objects
            # Use article's scraped_at timestamp for consistency
            # (extraction happens immediately after scraping in the same pipeline)
            word_facts = []

            for position, word in enumerate(words):
                word_fact = WordFact(
                    word=word,
                    article_id=article.id,
                    position_in_article=position,
                    scraped_at=article.scraped_at,
                )
                word_facts.append(word_fact)

            logger.debug(f"Extracted {len(word_facts)} words from article {article.id}")
            return word_facts

        except Exception as e:
            logger.debug(f"Failed to extract words from article {article.id}: {e}")
            return []  # Fail gracefully
