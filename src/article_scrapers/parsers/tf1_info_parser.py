# article_scrapers/parsers/tf1_info_parser.py

"""
Parser for TF1Info.fr articles.

This module provides the TF1InfoArticleParser class, which extends BaseParser
to specifically extract and process content from TF1Info.fr articles.
"""

from datetime import datetime
import re
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup, Tag

from article_scrapers.parsers.base_parser import BaseParser


class TF1InfoArticleParser(BaseParser):
    def __init__(self) -> None:
        super().__init__(site_domain="tf1info.fr")

    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        try:
            content_div = soup.find(
                "div", class_=re.compile(r"article-body|content-body|main-content")
            )
            if not content_div:
                content_div = soup.find("article")
            if not content_div or not isinstance(content_div, Tag):
                self.logger.warning(
                    "No main content div or article tag found for TF1 Info article."
                )
                return None

            paragraphs = self._extract_paragraphs(content_div)
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
            self.logger.error(f"Error parsing TF1 Info article: {e}")
            return None

    def _extract_paragraphs(self, content_div: Tag) -> List[str]:
        paragraphs = []
        text_elements = content_div.find_all(["p", "h2", "h3", "li"])

        for element in text_elements:
            if isinstance(element, Tag):
                if element.name in ["h2", "h3"]:
                    header_text = element.get_text(strip=True)
                    if header_text:
                        paragraphs.append(f"\n\n## {header_text} ##\n")
                elif element.name in ["p", "li"]:
                    text = element.get_text(separator=" ", strip=True)
                    text = re.sub(r"\s+", " ", text).strip()
                    if text and len(text.split()) > 3:
                        paragraphs.append(text)
        return paragraphs

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_selectors = [
            "h1.article-title",
            "h1",
            'meta[property="og:title"]',
            "title",
        ]

        for selector in title_selectors:
            if selector.startswith("meta"):
                tag = soup.find(
                    lambda t: t.name == "meta" and t.get("property") == "og:title"
                )
                if tag and isinstance(tag, Tag) and tag.has_attr("content"):
                    return str(tag["content"]).strip()
            else:
                tag = soup.select_one(selector)
                if tag and isinstance(tag, Tag):
                    return tag.get_text(strip=True)

        return "Unknown Title"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        date_selectors = [
            "time[datetime]",
            "span.date",
            "div.timestamp",
            'meta[property="article:published_time"]',
            'meta[itemprop="datePublished"]',
        ]

        for selector in date_selectors:
            element = soup.select_one(selector)
            if element and isinstance(element, Tag):
                date_str = None
                if element.has_attr("datetime"):
                    date_str = str(element["datetime"])
                elif element.has_attr("content"):
                    date_str = str(element["content"])
                else:
                    date_str = element.get_text(strip=True)

                if date_str:
                    try:
                        dt_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        return dt_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        continue

        return datetime.now().strftime("%Y-%m-%d")
