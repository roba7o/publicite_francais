"""
Data models for the French news scraper with clean architecture.

Separate concerns:
- RawArticle: Transient container for scraped HTML (used in memory only)
- WordFact: Individual words for vocabulary learning (stored in DB)

Note: raw_html is NOT persisted to database - only metadata is stored in dim_articles.
HTML is processed in memory via trafilatura to extract words, then discarded.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4

__all__ = ["RawArticle", "WordFact", "SourceStats"]


@dataclass
class RawArticle:
    """
    Transient container for scraped article data.

    Used in-memory during processing:
    1. Scraper creates RawArticle with HTML
    2. WordExtractor processes raw_html via trafilatura
    3. Only metadata stored to dim_articles (HTML discarded)

    The raw_html field exists only for word extraction, never persisted.
    """

    # Required fields
    url: str
    raw_html: str  # Complete HTML content (transient, not stored)
    site: str  # News site identifier

    # Auto-generated fields
    id: str = field(default_factory=lambda: str(uuid4()))
    scraped_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Optional metadata
    response_status: int | None = None

    def __post_init__(self) -> None:
        """Validate required fields."""
        if not self.url or not self.raw_html or not self.site:
            raise ValueError("url, raw_html, and site are required")

    def to_dict(self) -> dict:
        """
        Convert to dictionary for database storage (metadata only).

        Note: raw_html is intentionally excluded - it's never persisted.
        """
        return {
            "id": self.id,
            "url": self.url,
            "site": self.site,
            "scraped_at": self.scraped_at,
            "response_status": self.response_status,
        }


@dataclass
class WordFact:
    """
    Individual word extracted from an article for vocabulary learning.

    Denormalized design: each word gets its own row for vocabulary analysis.
    Links back to source article for context.
    """

    # Required fields
    word: str  # The French word (normalized/cleaned)
    article_id: str  # Reference to RawArticle.id
    position_in_article: int  # Word position for context
    scraped_at: datetime  # When the word was extracted

    # Auto-generated fields
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        """Validate required fields."""
        if not self.word or not self.article_id:
            raise ValueError("word and article_id are required")

        if self.position_in_article < 0:
            raise ValueError("position_in_article must be >= 0")

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "word": self.word,
            "article_id": self.article_id,
            "position_in_article": self.position_in_article,
            "scraped_at": self.scraped_at,
        }


@dataclass
class SourceStats:
    """Statistics for a single news source."""

    site_name: str
    attempted: int
    stored: int
    deduplicated: int
    total_words: int
    word_counts: list[int]  # Individual article word counts

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        return (self.stored / self.attempted * 100) if self.attempted > 0 else 0.0

    @property
    def avg_words(self) -> int:
        """Calculate average words per article."""
        return int(sum(self.word_counts) / len(self.word_counts)) if self.word_counts else 0

    @property
    def min_words(self) -> int:
        """Get minimum word count."""
        return min(self.word_counts) if self.word_counts else 0

    @property
    def max_words(self) -> int:
        """Get maximum word count."""
        return max(self.word_counts) if self.word_counts else 0
