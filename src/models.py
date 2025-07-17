"""
Data models for the article scraper system.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

__all__ = ["ArticleData"]


@dataclass
class ArticleData:
    """
    Represents scraped article data with validation and normalization.

    This dataclass replaces the previous dictionary-based approach for
    representing article data, providing type safety and better structure.
    """

    # Required fields
    title: str
    full_text: str
    article_date: str  # Format: YYYY-MM-DD
    date_scraped: str  # Format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS

    # Optional fields
    num_paragraphs: Optional[int] = None
    author: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate and normalize data after initialization."""
        # Ensure date_scraped is set if not provided
        if not self.date_scraped:
            self.date_scraped = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ArticleData to dictionary for backward compatibility.

        Returns:
            dict: Dictionary representation of the article data
        """
        return {
            "title": self.title,
            "full_text": self.full_text,
            "article_date": self.article_date,
            "date_scraped": self.date_scraped,
            "num_paragraphs": self.num_paragraphs,
            "author": self.author,
            "category": self.category,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArticleData":
        """
        Create ArticleData from dictionary.

        Args:
            data: Dictionary containing article data

        Returns:
            ArticleData: New instance with data from dictionary
        """
        return cls(
            title=data.get("title", ""),
            full_text=data.get("full_text", ""),
            article_date=data.get("article_date", ""),
            date_scraped=data.get("date_scraped", ""),
            num_paragraphs=data.get("num_paragraphs"),
            author=data.get("author"),
            category=data.get("category"),
            summary=data.get("summary"),
        )
