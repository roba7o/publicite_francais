"""
Data models for the article scraper system using ELT approach.

ELT = Extract, Load, Transform
- Extract: Scrape raw HTML
- Load: Store raw data in database
- Transform: Process with dbt
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

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

    # Auto-generated fields
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Optional metadata
    response_status: int | None = None
    content_length: int | None = None

    def __post_init__(self) -> None:
        """Validate raw data after initialization."""
        if not self.url or not self.raw_html or not self.site:
            raise ValueError("url, raw_html, and site are required")

        # Set content_length if not provided
        if self.content_length is None:
            self.content_length = len(self.raw_html)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "url": self.url,
            "raw_html": self.raw_html,
            "site": self.site,
            "scraped_at": self.scraped_at,
            "response_status": self.response_status,
            "content_length": self.content_length,
        }