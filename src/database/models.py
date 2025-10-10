"""
Data models for the French news scraper with clean architecture.

Separate concerns:
- RawArticle: Store raw HTML content only
- WordFact: Individual words for vocabulary learning (denormalized)
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4

__all__ = ["RawArticle", "WordFact"]


@dataclass
class RawArticle:
    """
    Raw scraped article data - no processing, just storage.

    Clean separation: only handles raw HTML storage.
    Word processing happens separately via WordExtractor service.
    """

    # Required fields
    url: str
    raw_html: str  # Complete HTML content as text
    site: str  # News site identifier

    # Auto-generated fields
    id: str = field(default_factory=lambda: str(uuid4()))
    scraped_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Optional metadata
    response_status: int | None = None
    content_length: int | None = None

    def __post_init__(self) -> None:
        """Validate required fields and set content length."""
        if not self.url or not self.raw_html or not self.site:
            raise ValueError("url, raw_html, and site are required")

        # Set content_length if not provided
        if self.content_length is None:
            self.content_length = len(self.raw_html)

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "url": self.url,
            "raw_html": self.raw_html,
            "site": self.site,
            "scraped_at": self.scraped_at,
            "response_status": self.response_status,
            "content_length": self.content_length,
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
