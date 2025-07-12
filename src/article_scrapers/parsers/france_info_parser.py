# article_scrapers/parsers/france_info_parser.py

"""
Parser for FranceInfo.fr articles.

This module provides the FranceInfoArticleParser class, which extends BaseParser
to specifically extract and process content from FranceInfo.fr articles,
including text, title, date, author, tags, and image captions.
"""

from datetime import datetime
import re
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup

from article_scrapers.parsers.base_parser import BaseParser


class FranceInfoArticleParser(BaseParser):
    """
    Parses article content from franceinfo.fr.
    Inherits common fetching and text processing functionalities from BaseParser.
    """

    def __init__(self) -> None:
        """
        Initializes the FranceInfoArticleParser with its specific domain.
        The base parser handles loading and applying the site's configuration.
        """
        super().__init__(site_domain='franceinfo.fr')
        self.logger.info("FranceInfoArticleParser initialized.")

    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Parses the BeautifulSoup object to extract main article content and metadata.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the article page.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing extracted article data,
                                      or None if the main content cannot be found.
        """
        try:
            content_div = soup.find('div', class_='c-body')
            if not content_div:
                self.logger.warning("Main content div ('c-body') not found for FranceInfo article.")
                return None

            paragraphs = self._extract_paragraphs(content_div)
            full_text = '\n\n'.join(paragraphs) if paragraphs else ""

            if not full_text:
                self.logger.warning("No significant text extracted from FranceInfo article.")
                return None

            # Get text statistics for debugging
            if self.debug:
                stats = self.get_text_statistics(full_text)
                self.logger.info(f"FranceInfo text stats: unique_words={stats['total_unique_words']}, "
                               f"total_words={stats['total_word_count']}")
                self.logger.debug(f"FranceInfo top words: {stats['top_10_words']}")

            return {
                'full_text': full_text,
                'num_paragraphs': len(paragraphs),
                'title': self._extract_title(soup),
                'article_date': self._extract_date(soup),
                'date_scraped': datetime.now().strftime("%Y-%m-%d"),
                'author': self._extract_author(soup),
                'tags': self._extract_tags(soup),
                'image_caption': self._extract_image_caption(soup),
            }

        except Exception as e:
            self.logger.error(f"Error parsing FranceInfo article: {e}", exc_info=True)
            return None

    def _extract_paragraphs(self, content_div: BeautifulSoup) -> List[str]:
        """
        Extracts text paragraphs and subheaders from the main content div.

        Args:
            content_div (BeautifulSoup): The BeautifulSoup object of the main content area.

        Returns:
            List[str]: A list of extracted and cleaned paragraph strings.
        """
        paragraphs: List[str] = []
        for element in content_div.find_all(['p', 'h2', 'li']): # Added 'li' for list items often found in content
            if element.name == 'h2':
                text = element.get_text(strip=True)
                if text:
                    paragraphs.append(f"\n\n## {text} ##\n")
            elif element.name == 'p' or element.name == 'li':
                text = element.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip() # Normalize and strip whitespace
                if text and len(text.split()) > 3:  # Skip very short paragraphs or empty strings
                    paragraphs.append(text)
        return paragraphs

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extracts the article title from the HTML.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            str: The extracted title, or "Unknown title" if not found.
        """
        title_tag = soup.find('h1')
        if title_tag:
            return title_tag.get_text(strip=True)
        self.logger.debug("Article title (h1) not found.")
        return "Unknown title"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """
        Extracts the publication date from the HTML.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            str: The extracted date in "YYYY-MM-DD" format, or the current date if not found.
        """
        time_tag = soup.find('time')
        if time_tag and time_tag.has_attr('datetime'):
            date_str = time_tag['datetime']
            try:
                # Attempt to parse date to ensure it's valid, then reformat if needed
                # FranceInfo datetime can be "2023-10-26T10:00:00+02:00"
                dt_obj = datetime.fromisoformat(date_str)
                return dt_obj.strftime("%Y-%m-%d")
            except ValueError:
                self.logger.warning(f"Could not parse datetime attribute: {date_str}")
                return date_str # Return original if cannot parse, as a fallback

        self.logger.debug("Article date (time tag with datetime attribute) not found.")
        return datetime.now().strftime("%Y-%m-%d")

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """
        Extracts the author information from the HTML.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            str: The extracted author, or "Unknown author" if not found.
        """
        author_tag = soup.find('span', class_='c-signature__author')
        if author_tag:
            return author_tag.get_text(strip=True)
        self.logger.debug("Author tag ('c-signature__author') not found.")
        return "Unknown author"

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """
        Extracts article tags from the HTML.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            List[str]: A list of extracted tags.
        """
        tags: List[str] = []
        tags_section = soup.find('section', class_='related-tags')
        if tags_section:
            for tag in tags_section.find_all('a', class_='fi-tag'):
                tag_text = tag.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
        else:
            self.logger.debug("Related tags section not found.")
        return tags

    def _extract_image_caption(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extracts the caption of the main image from the HTML.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            Optional[str]: The extracted image caption, or None if not found.
        """
        figcaption = soup.find('figcaption')
        if figcaption:
            # Remove the photographer credit (content in span)
            for span in figcaption.find_all('span'):
                span.decompose()
            caption = figcaption.get_text(strip=True)
            return caption if caption else None
        self.logger.debug("Image figcaption not found.")
        return None