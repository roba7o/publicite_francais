"""
Database-focused Slate.fr parser that stores raw data to PostgreSQL.

This is the database equivalent of SlateFrArticleParser that:
- Uses DatabaseBaseParser instead of BaseParser
- Keeps the exact same HTML parsing logic
- Stores to database instead of CSV via to_database() method
"""

from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup, Tag

from models import ArticleData
from parsers.database_base_parser import DatabaseBaseParser


class DatabaseSlateFrParser(DatabaseBaseParser):
    """
    Database-focused Slate.fr parser that stores raw data only.

    This mirrors SlateFrArticleParser exactly but extends DatabaseBaseParser
    instead of BaseParser, so it stores to PostgreSQL instead of CSV.

    The HTML parsing logic is identical to your existing parser.
    """

    def __init__(self, source_id: str) -> None:
        """
        Initialize with source ID from database.

        Args:
            source_id: UUID of Slate.fr source from news_sources table
        """
        super().__init__(site_domain="slate.fr", source_id=source_id)

    def parse_article(self, soup: BeautifulSoup) -> Optional[ArticleData]:
        """
        Parse Slate.fr article - identical logic to SlateFrArticleParser.

        The only difference: uses DatabaseBaseParser instead of BaseParser.
        """
        try:
            article_tag = soup.find("article")
            if not article_tag or not isinstance(article_tag, Tag):
                return None

            paragraphs = self._extract_paragraphs(article_tag)
            full_text = "\n\n".join(paragraphs) if paragraphs else ""

            if not full_text:
                return None

            return ArticleData(
                full_text=full_text,
                num_paragraphs=len(paragraphs),
                title=self._extract_title(soup),
                article_date=self._extract_date(soup),
                date_scraped=datetime.now().strftime("%Y-%m-%d"),
            )

        except Exception as e:
            self.logger.error(f"Error parsing Slate.fr article: {e}")
            return None

    def _extract_paragraphs(self, article_tag: Tag) -> List[str]:
        """Extract paragraphs - identical logic to SlateFrArticleParser."""
        paragraphs: List[str] = []
        for p in article_tag.find_all("p"):
            if isinstance(p, Tag) and not p.get("class"):
                text = p.get_text(separator=" ", strip=True)
                text = " ".join(text.split())  # Basic cleanup only
                if text and len(text.split()) > 5:
                    paragraphs.append(text)
        return paragraphs

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title - identical logic to SlateFrArticleParser."""
        title_tag = soup.find("h1")
        if title_tag and isinstance(title_tag, Tag):
            return title_tag.get_text(strip=True)
        return "Unknown title"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract date - identical logic to SlateFrArticleParser."""
        date_tag = soup.find("time")
        if date_tag and isinstance(date_tag, Tag) and date_tag.has_attr("datetime"):
            date_str = str(date_tag["datetime"])
            try:
                dt_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt_obj.strftime("%Y-%m-%d")
            except ValueError:
                return date_str
        elif date_tag and isinstance(date_tag, Tag):
            text_date = date_tag.get_text(strip=True)
            if text_date:
                return text_date
        return "Unknown date"
