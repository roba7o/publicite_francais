"""
Database-focused Ladepeche.fr parser that stores raw data to PostgreSQL.

This is the database equivalent of LadepecheFrArticleParser that:
- Uses DatabaseBaseParser instead of BaseParser
- Keeps the exact same HTML parsing logic
- Stores to database via to_database() method
"""

import re
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from models import ArticleData
from parsers.database_base_parser import DatabaseBaseParser


class DatabaseLadepecheFrParser(DatabaseBaseParser):
    """
    Database-focused Ladepeche.fr parser that stores raw data only.

    This mirrors LadepecheFrArticleParser exactly but extends DatabaseBaseParser
    instead of BaseParser, so it stores to PostgreSQL.

    The HTML parsing logic is identical to your existing parser.
    """

    def __init__(self, source_id: str) -> None:
        """Initialize with source ID for database storage."""
        super().__init__(site_domain="ladepeche.fr", source_id=source_id)
        self.logger.info("DatabaseLadepecheFrParser initialized.")

    def parse_article(self, soup: BeautifulSoup) -> Optional[ArticleData]:
        """
        Parse Ladepeche.fr article from BeautifulSoup object.
        
        This method is identical to LadepecheFrArticleParser.parse_article()
        to ensure consistent parsing behavior.
        """
        try:
            # Look for the main article content area
            article_content_area = soup.find("article") or soup.find(
                "div", class_="article-content"
            )
            if not article_content_area:
                self.logger.warning(
                    "No main article content area found (article or .article-content)."
                )
                # Attempt a more general fallback if specific elements
                # aren't found
                article_content_area = soup.find("main")

            if not article_content_area:
                self.logger.warning(
                    "No article content found even with general fallback. "
                    "This might not be an article page."
                )
                return None

            paragraphs = self._extract_paragraphs(
                BeautifulSoup(str(article_content_area), "html.parser")
            )
            full_text = "\n\n".join(paragraphs) if paragraphs else ""

            if not full_text:
                self.logger.warning(
                    "No significant text extracted from Ladepeche.fr article."
                )
                return None

            # Log basic text info for debugging
            if self.debug:
                word_count = len(full_text.split())
                self.logger.info(f"Ladepeche.fr text stats: total_words={word_count}")

            return ArticleData(
                full_text=full_text,
                num_paragraphs=len(paragraphs),
                title=self._extract_title(soup),
                article_date=self._extract_date(soup),
                date_scraped=datetime.now().strftime("%Y-%m-%d"),
                author=self._extract_author(soup),
            )

        except Exception as e:
            self.logger.error(f"Error parsing Ladepeche.fr article: {e}", exc_info=True)
            return None

    def _extract_paragraphs(self, content_area: BeautifulSoup) -> List[str]:
        """
        Extract text from paragraphs within the main content area, filtering
        out non-content.
        """
        paragraphs: List[str] = []

        # Common classes for non-content elements to skip. Extend as needed.
        skip_classes = [
            "nav",
            "menu",
            "sidebar",
            "footer",
            "ad",
            "promo",
            "share",
            "social",
            "widget",
            "caption-credit",
        ]
        # Elements that typically contain main article text
        text_elements = content_area.find_all(["p", "h2", "li"])

        for element in text_elements:
            # Check for parent elements that might indicate non-content
            # sections. This can prevent including text from 'related articles'
            # or 'author boxes'
            if element.find_parent(
                class_=["related-articles", "author-box", "article-meta"]
            ):
                continue

            # Check the element's own classes
            if hasattr(element, "has_attr") and element.has_attr("class"):
                element_classes = (
                    element.get("class", []) if hasattr(element, "get") else []
                )
                if isinstance(element_classes, list):
                    class_string = " ".join(c.lower() for c in element_classes)
                    if any(skip_class in class_string for skip_class in skip_classes):
                        continue

            text = element.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()  # Normalize whitespace

            # Filter out very short or empty strings that might be artifacts
            if (
                text and len(text.split()) > 5
            ):  # Require at least 5 words to be considered a content paragraph
                paragraphs.append(text)

        return paragraphs

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract the article's title. Tries multiple common selectors.
        """
        title_selectors = [
            "h1.article-title",  # Specific for Ladepeche.fr if available
            "h1",  # General h1
            ".main-title",  # Another common pattern
            'meta[property="og:title"]',  # Open Graph title
            "title",  # Fallback to HTML <title> tag
        ]

        for selector in title_selectors:
            if selector.startswith("meta"):
                tag = soup.find(
                    lambda tag: tag.name == "meta" and tag.get("property") == "og:title"
                )
                if tag and hasattr(tag, "has_attr") and tag.has_attr("content"):
                    content = tag.get("content") if hasattr(tag, "get") else None
                    if isinstance(content, str):
                        return content.strip()
            else:
                tag = soup.select_one(selector)
                if tag:
                    title = tag.get_text(strip=True)
                    # Clean up common patterns like " - SiteName"
                    if " - LaDepeche.fr" in title:
                        title = title.replace(" - LaDepeche.fr", "").strip()
                    if " | " in title:
                        title = title.split(" | ")[0].strip()
                    return title

        self.logger.debug("Article title not found using common selectors.")
        return "Unknown title"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """
        Extract the article's date. Tries multiple selectors and formats.
        """
        date_selectors = [
            "time[datetime]",
            ".article-date time",
            ".date-publication",
            ".published-date",
            "[data-time]",  # Added for robustness, covers the
            # "20250712190208" case
            'meta[property="article:published_time"]',
            'meta[itemprop="datePublished"]',
        ]

        # Initialize date_str to None before the loop
        date_str: Optional[str] = None

        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if hasattr(element, "has_attr") and element.has_attr("datetime"):
                    datetime_attr = element.get("datetime")
                    if isinstance(datetime_attr, str):
                        date_str = datetime_attr.strip()
                elif hasattr(element, "has_attr") and element.has_attr("data-time"):
                    data_time_attr = element.get("data-time")
                    if isinstance(data_time_attr, str):
                        date_str = data_time_attr.strip()
                elif (
                    element.name == "meta"
                    and hasattr(element, "has_attr")
                    and element.has_attr("content")
                ):
                    content_attr = element.get("content")
                    if isinstance(content_attr, str):
                        date_str = content_attr.strip()
                else:
                    date_str = element.get_text(strip=True)

                # Now, if date_str has a value, attempt to parse it
                if date_str:
                    # Format: 20250712190208 -> 2025-07-12 19:02:08
                    if len(date_str) == 14 and date_str.isdigit():
                        try:
                            # Parse as datetime object first to ensure
                            # validity, then format
                            dt_obj = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                            return dt_obj.strftime("%Y-%m-%d")
                        except ValueError:
                            self.logger.debug(
                                f"Failed to parse '{date_str}' as YYYYMMDDHHMMSS."
                            )
                            # Continue to try other formats if this one fails

                    # ISO 8601 format (e.g., 2023-10-26T10:00:00+02:00)
                    try:
                        dt_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        return dt_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        self.logger.debug(f"Failed to parse '{date_str}' as ISO 8601.")
                        pass  # Try other parsing methods

                    # Simple date format (e.g., "12/07/2025" or
                    # "Octobre 26, 2023")
                    # Add more common French date formats as needed.
                    # For "DD/MM/YYYY"
                    try:
                        dt_obj = datetime.strptime(date_str, "%d/%m/%Y")
                        return dt_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        pass
                    # For "YYYY-MM-DD"
                    try:
                        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        return dt_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        pass

                    # If a string was found but couldn't be parsed into a
                    # standard date format,
                    # return it as is, logging a warning.
                    self.logger.warning(
                        f"Date string '{date_str}' found but could not be "
                        "parsed into a standard format. Returning raw string."
                    )
                    # Return raw string if no known format matches
                    return date_str

        self.logger.debug(
            "Article date not found or parsed using common selectors and "
            "formats. Falling back to 'Unknown date'."
        )
        return "Unknown date"

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """
        Extract author information. (Placeholder - implement specific logic
        for Ladepeche if needed)
        """
        # Example for Ladepeche: look for a specific class or rel="author"
        author_tag = soup.find("span", class_="author-name") or soup.find(
            "a", rel="author"
        )
        if author_tag:
            return author_tag.get_text(strip=True)
        self.logger.debug("Author information not found for Ladepeche.fr.")
        return "Unknown author"