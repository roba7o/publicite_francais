"""
Database-focused Slate.fr parser that stores raw data to PostgreSQL.

This is the database equivalent of SlateFrArticleParser that:
- Uses DatabaseBaseParser instead of BaseParser
- Keeps the exact same HTML parsing logic
- Stores to database via to_database() method
"""

from datetime import datetime

from bs4 import BeautifulSoup, Tag

from core.models import RawArticle
from parsers.database_base_parser import DatabaseBaseParser


class DatabaseSlateFrParser(DatabaseBaseParser):
    """
    Database-focused Slate.fr parser that stores raw data only.

    This mirrors SlateFrArticleParser exactly but extends DatabaseBaseParser
    instead of BaseParser, so it stores to PostgreSQL.

    The HTML parsing logic is identical to your existing parser.
    """

    def __init__(self, source_name: str, debug: bool = False) -> None:
        """
        Initialize Slate.fr parser.

        Args:
            source_name: Name of the source (should be "Slate.fr")
            debug: Enable debug logging (default: False)
        """
        super().__init__(site_domain="slate.fr", source_name=source_name)
        self.debug = debug

    def parse_article(self, soup: BeautifulSoup, url: str) -> RawArticle | None:
        """
        Create RawArticle for ELT processing.

        Returns raw HTML data - all processing done by dbt.
        """
        try:
            # Simple validation - ensure we have an article
            article_tag = soup.find("article")
            if not article_tag or not isinstance(article_tag, Tag):
                return None

            # Return raw HTML for dbt processing
            return RawArticle(
                url=url,
                raw_html=str(soup),
                source="slate.fr",
            )

        except Exception as e:
            self.logger.error(f"Error creating raw article data: {e}")
            return None

    def _extract_paragraphs(self, article_tag: Tag) -> list[str]:
        """Extract paragraphs - identical logic to SlateFrArticleParser."""
        paragraphs: list[str] = []
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
