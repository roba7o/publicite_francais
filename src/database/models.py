"""
Data models for the article scraper system using ELT approach.

ELT = Extract, Load, Transform
- Extract: Scrape raw HTML
- Load: Store raw data in database
- Transform: Process with dbt
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

import re

import trafilatura

# just ensuring public api seeing this only
__all__ = ["RawArticle"]


@dataclass
class RawArticle:
    """
    Raw scraped data - no processing, just collection.

    This follows the ELT pattern where Python only collects raw data
    and dbt handles all content processing and extraction.
    """

    # Required fields
    url: str
    raw_html: str  # Complete HTML content as text
    site: str  # News site: "slate.fr", "franceinfo.fr"

    # Auto-generated fields -> at instantiaion not model is loaded
    id: str = field(default_factory=lambda: str(uuid4()))
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Optional metadata
    response_status: int | None = None
    content_length: int | None = None

    # Extracted content fields (populated by trafilatura)
    extracted_text: str | None = None
    title: str | None = None
    author: str | None = None
    date_published: str | None = None
    language: str | None = None
    summary: str | None = None
    keywords: list[str] | None = None
    extraction_status: str = "pending"

    # Word extraction fields
    word_events: list[dict] | None = None

    # Post-initialization processing -> assign default values and extract content
    def __post_init__(self) -> None:
        """Validate raw data and extract content using trafilatura."""
        if not self.url or not self.raw_html or not self.site:
            raise ValueError("url, raw_html, and site are required")

        # Set content_length if not provided
        if self.content_length is None:
            self.content_length = len(self.raw_html)

        # Extract content using trafilatura
        self._extract_content()

        # Extract French words for event storage
        self._extract_french_words()

    def _extract_content(self) -> None:
        """Extract content from raw HTML using trafilatura."""
        try:
            # Extract main text content
            self.extracted_text = trafilatura.extract(self.raw_html)

            # Extract metadata
            metadata = trafilatura.extract_metadata(self.raw_html)

            if metadata:
                self.title = metadata.title
                self.author = metadata.author
                self.date_published = metadata.date
                self.language = metadata.language

                # Handle categories/tags as keywords
                if hasattr(metadata, "categories") and metadata.categories:
                    self.keywords = metadata.categories
                elif hasattr(metadata, "tags") and metadata.tags:
                    self.keywords = metadata.tags

            # Mark as successful if we got at least some content
            if self.extracted_text:
                self.extraction_status = "success"
            else:
                self.extraction_status = "failed"

        except Exception:
            # Don't break the pipeline on extraction failures
            self.extraction_status = "failed"

    def _extract_french_words(self) -> None:
        """Extract French words from extracted text and create word events."""
        if not self.extracted_text:
            self.word_events = []
            return

        try:
            # Clean and tokenize text
            text = self.extracted_text.lower()
            # Remove punctuation and split into words
            words = re.findall(r'\b[a-záàâäéèêëíìîïóòôöúùûüÿç]+\b', text)

            # Create word events for ALL words (no filtering - dbt will handle this)
            word_events = []
            for position, word in enumerate(words):
                # Only filter out very short words (< 2 characters)
                if len(word) >= 2:
                    word_events.append({
                        'word': word,
                        'position_in_article': position,
                        'article_id': self.id,
                        'scraped_at': self.scraped_at
                    })

            self.word_events = word_events

        except Exception:
            # Don't break the pipeline on word extraction failures
            self.word_events = []

    def to_dict(self):
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "url": self.url,
            "raw_html": self.raw_html,
            "site": self.site,
            "scraped_at": self.scraped_at,
            "response_status": self.response_status,
            "content_length": self.content_length,
            "extracted_text": self.extracted_text,
            "title": self.title,
            "author": self.author,
            "date_published": self.date_published,
            "language": self.language,
            "summary": self.summary,
            "keywords": self.keywords,
            "extraction_status": self.extraction_status,
            "word_events": self.word_events,
        }
