from datetime import datetime
import re
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup, Tag

from parsers.base_parser import BaseParser


class FranceInfoArticleParser(BaseParser):
    def __init__(self) -> None:
        super().__init__(site_domain="franceinfo.fr")

    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        try:
            content_div = soup.find("div", class_="c-body")
            if not content_div or not isinstance(content_div, Tag):
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
            self.logger.error(f"Error parsing FranceInfo article: {e}")
            return None

    def _extract_paragraphs(self, content_div: Tag) -> List[str]:
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
        title_tag = soup.find("h1")
        if title_tag and isinstance(title_tag, Tag):
            return title_tag.get_text(strip=True)
        return "Unknown title"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        time_tag = soup.find("time")
        if (time_tag and isinstance(time_tag, Tag) and
                time_tag.has_attr("datetime")):
            date_str = str(time_tag["datetime"])
            try:
                dt_obj = datetime.fromisoformat(date_str)
                return dt_obj.strftime("%Y-%m-%d")
            except ValueError:
                return date_str

        return datetime.now().strftime("%Y-%m-%d")
