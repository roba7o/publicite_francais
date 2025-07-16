# article_scrapers/parsers/slate_fr_parser.py

"""
Parser for Slate.fr articles.

This module provides the SlateFrArticleParser class, which extends BaseParser
to specifically extract and process content from Slate.fr articles.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup, Tag

from parsers.base_parser import BaseParser


class SlateFrArticleParser(BaseParser):
    def __init__(self) -> None:
        super().__init__(site_domain="slate.fr")

    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        try:
            article_tag = soup.find("article")
            if not article_tag or not isinstance(article_tag, Tag):
                return None

            paragraphs = self._extract_paragraphs(article_tag)
            full_text = "\n\n".join(paragraphs) if paragraphs else ""

            if not full_text:
                return None

            return {
                "full_text": full_text,
                "num_paragraphs": len(paragraphs),
                "title": self._extract_title(soup),
                "article_date": self._extract_date(soup),
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as e:
            self.logger.error(f"Error parsing Slate.fr article: {e}")
            return None

    def _extract_paragraphs(self, article_tag: Tag) -> List[str]:
        paragraphs: List[str] = []
        for p in article_tag.find_all("p"):
            if isinstance(p, Tag) and not p.get("class"):
                text = p.get_text(separator=" ", strip=True)
                text = " ".join(text.split())
                if text and len(text.split()) > 5:
                    paragraphs.append(text)
        return paragraphs

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_tag = soup.find("h1")
        if title_tag and isinstance(title_tag, Tag):
            return title_tag.get_text(strip=True)
        return "Unknown title"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        date_tag = soup.find("time")
        if (date_tag and isinstance(date_tag, Tag) and
                date_tag.has_attr("datetime")):
            date_str = str(date_tag["datetime"])
            try:
                dt_obj = datetime.fromisoformat(
                    date_str.replace("Z", "+00:00")
                )
                return dt_obj.strftime("%Y-%m-%d")
            except ValueError:
                return date_str
        elif date_tag and isinstance(date_tag, Tag):
            text_date = date_tag.get_text(strip=True)
            if text_date:
                return text_date
        return "Unknown date"
