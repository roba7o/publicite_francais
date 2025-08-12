"""
Database-focused FranceInfo.fr parser that stores raw data to PostgreSQL.

This is the database equivalent of FranceInfoArticleParser that:
- Uses DatabaseBaseParser instead of BaseParser
- Keeps the exact same HTML parsing logic
- Stores to database via to_database() method
"""

import re
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup, Tag

from models import ArticleData
from parsers.database_base_parser import DatabaseBaseParser


class DatabaseFranceInfoParser(DatabaseBaseParser):
    """
    Database-focused FranceInfo.fr parser that stores raw data only.

    This mirrors FranceInfoArticleParser exactly but extends DatabaseBaseParser
    instead of BaseParser, so it stores to PostgreSQL.

    The HTML parsing logic is identical to your existing parser.
    """

    def __init__(self, source_id: str) -> None:
        """Initialize with source ID for database storage."""
        super().__init__(site_domain="franceinfo.fr", source_id=source_id)

    def parse_article(self, soup: BeautifulSoup) -> Optional[ArticleData]:
        """
        Parse FranceInfo article from BeautifulSoup object.

        This method is identical to FranceInfoArticleParser.parse_article()
        to ensure consistent parsing behavior.
        """
        try:
            content_div = soup.find("div", class_="c-body")
            if not content_div or not isinstance(content_div, Tag):
                return None

            paragraphs = self._extract_paragraphs(content_div)
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
            self.logger.error(f"Error parsing FranceInfo article: {e}")
            return None

    def _extract_paragraphs(self, content_div: Tag) -> List[str]:
        """Extract paragraphs from article content div."""
        paragraphs: List[str] = []
        for element in content_div.find_all(["p", "h2", "li"]):
            if isinstance(element, Tag):
                if element.name == "h2":
                    text = element.get_text(strip=True)
                    if text:
                        paragraphs.append(f"\n\n## {text} ##\n")
                elif element.name == "p" or element.name == "li":
                    text = element.get_text(separator=" ", strip=True)
                    text = re.sub(r"\s+", " ", text).strip()
                    if text and len(text.split()) > 3:
                        paragraphs.append(text)
        return paragraphs

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        title_tag = soup.find("h1", class_="c-title-editorial__title")
        if title_tag and isinstance(title_tag, Tag):
            return title_tag.get_text(strip=True)
        return "No title found"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract article publication date."""
        date_tag = soup.find("time")
        if date_tag and isinstance(date_tag, Tag):
            datetime_str = date_tag.get("datetime")
            if datetime_str:
                try:
                    # Parse ISO format datetime
                    dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
                    return dt.strftime("%Y-%m-%d")
                except (ValueError, AttributeError):
                    pass

            # Fallback to text content
            date_text = date_tag.get_text(strip=True)
            if date_text:
                return date_text

        return "No date found"
