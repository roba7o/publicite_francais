# article_scrapers/parsers/tf1_info_parser.py

"""
Parser for TF1Info.fr articles.

This module provides the TF1InfoArticleParser class, which extends BaseParser
to specifically extract and process content from TF1Info.fr articles.
"""

from datetime import datetime
import re
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup

from article_scrapers.parsers.base_parser import BaseParser


class TF1InfoArticleParser(BaseParser):
    """
    Parses article content from tf1info.fr.
    Inherits common fetching and text processing functionalities from BaseParser.
    """

    def __init__(self) -> None:
        """
        Initializes the TF1InfoArticleParser with its specific domain.
        The base parser handles loading and applying the site's configuration
        (including stopwords and word length limits defined in text_processing_config.py).
        """
        super().__init__(site_domain='tf1info.fr')
        self.logger.info("TF1InfoArticleParser initialized.")

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
            # Extract main content - try multiple common TF1 Info selectors
            content_div = soup.find('div', class_=re.compile(r'article-body|content-body|main-content'))
            if not content_div:
                # Try <article> as fallback
                content_div = soup.find('article')
            if not content_div:
                self.logger.warning("No main content div or article tag found for TF1 Info article.")
                return None

            paragraphs = self._extract_paragraphs(content_div)
            full_text = '\n\n'.join(paragraphs) if paragraphs else ""

            if not full_text:
                self.logger.warning("No significant text extracted from TF1 Info article.")
                return None

            # Get text statistics for debugging
            if self.debug:
                stats = self.get_text_statistics(full_text)
                self.logger.info(f"TF1 Info article text stats: unique_words={stats['total_unique_words']}, "
                               f"total_words={stats['total_word_count']}")
                self.logger.debug(f"TF1 Info top words: {stats['top_10_words']}")

            return {
                'full_text': full_text,
                'num_paragraphs': len(paragraphs),
                'title': self._extract_title(soup),
                'article_date': self._extract_date(soup),
                'date_scraped': datetime.now().strftime("%Y-%m-%d"),
                'author': self._extract_author(soup),
                'image_caption': self._extract_image_caption(soup),
                'tags': self._extract_tags(soup),
            }

        except Exception as e:
            self.logger.error(f"Error parsing TF1 Info article: {e}", exc_info=True)
            return None

    def _extract_paragraphs(self, content_div: BeautifulSoup) -> List[str]:
        """
        Extracts and cleans paragraphs and subheaders from the content div.

        Args:
            content_div (BeautifulSoup): The BeautifulSoup object of the main content area.

        Returns:
            List[str]: A list of extracted and cleaned paragraph strings.
        """
        paragraphs: List[str] = []
        # Elements that typically contain main article text and subheaders
        text_elements = content_div.find_all(['p', 'h2', 'h3', 'li'])

        for element in text_elements:
            if element.name in ['h2', 'h3']:
                header_text = element.get_text(strip=True)
                if header_text:
                    paragraphs.append(f"\n\n## {header_text} ##\n")
            elif element.name in ['p', 'li']:
                text = element.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip()  # Normalize and strip whitespace
                if text and len(text.split()) > 3:  # Skip very short paragraphs/list items
                    paragraphs.append(text)
        return paragraphs

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extracts the article title. Tries multiple common selectors.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            str: The extracted title, or "Unknown Title" if not found.
        """
        title_selectors = [
            'h1.article-title', # Common for TF1 Info
            'h1',               # General h1 tag
            'meta[property="og:title"]', # Open Graph title
            'title'             # Fallback to HTML <title> tag
        ]

        for selector in title_selectors:
            if selector.startswith('meta'):
                tag = soup.find(lambda t: t.name == 'meta' and t.get('property') == 'og:title')
                if tag and tag.has_attr('content'):
                    return tag['content'].strip()
            else:
                tag = soup.select_one(selector)
                if tag:
                    return tag.get_text(strip=True)

        self.logger.debug("Article title not found for TF1 Info using common selectors.")
        return "Unknown Title"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """
        Extracts the article's publication date. Tries multiple selectors and formats.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            str: The extracted date in "YYYY-MM-DD" format, or the current date if not found.
        """
        date_selectors = [
            'time[datetime]',  # Standard time tag with datetime attribute
            'span.date',        # Common date class
            'div.timestamp',    # Another common date container
            'meta[property="article:published_time"]',  # OG meta tag
            'meta[itemprop="datePublished"]' # Schema.org
        ]

        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_str = None
                if element.has_attr('datetime'):
                    date_str = element['datetime']
                elif element.has_attr('content'): # For meta tags
                    date_str = element['content']
                else:
                    date_str = element.get_text(strip=True)

                if date_str:
                    try:
                        # Attempt to parse as ISO 8601 format (e.g., "2023-10-26T10:00:00+02:00")
                        dt_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        return dt_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        self.logger.warning(f"Could not parse date string '{date_str}' from selector '{selector}'.")
                        # Fallback for other simple date string formats if needed
                        # e.g., if date_str is "26/10/2023" -> datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                        pass # Continue to next selector or fallback to current date

        self.logger.debug("Article date not found for TF1 Info using common selectors.")
        return datetime.now().strftime("%Y-%m-%d")

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """
        Extracts the article author. Tries multiple common selectors.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            str: The extracted author, or "Unknown Author" if not found.
        """
        author_selectors = [
            'span.author-name',
            'div.author a',
            'meta[name="author"]',
            'a[rel="author"]',
            '.c-signature__author' # If TF1 uses a similar structure to FranceInfo
        ]

        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta' and element.has_attr('content'):
                    return element['content'].strip()
                else:
                    return element.get_text(strip=True)

        self.logger.debug("Author information not found for TF1 Info using common selectors.")
        return "Unknown Author"

    def _extract_image_caption(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extracts the main image caption.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            Optional[str]: The extracted image caption, or None if not found.
        """
        figcaption = soup.find('figcaption')
        if figcaption:
            # Remove any nested spans that might contain credits, common in news sites
            for span in figcaption.find_all('span'):
                span.decompose()
            caption = figcaption.get_text(strip=True)
            return caption if caption else None
        self.logger.debug("Image caption not found for TF1 Info.")
        return None

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """
        Extracts article tags/categories. Tries multiple common containers.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            List[str]: A list of unique tags (up to 5).
        """
        tags: List[str] = []
        tag_containers = [
            'div.tags',
            'ul.tag-list',
            'div.categories',
            'meta[property="article:tag"]', # Open Graph tags
            'meta[name="keywords"]' # General keywords meta tag
        ]

        for container_selector in tag_containers:
            elements = soup.select(container_selector)
            for element in elements:
                if element.name == 'meta':
                    if element.has_attr('content'):
                        # For meta keywords, split by comma if multiple tags are in one content string
                        meta_tags = [t.strip() for t in element['content'].split(',') if t.strip()]
                        tags.extend(meta_tags)
                else: # For div, ul, etc.
                    for a_tag in element.find_all('a'):
                        if tag_text := a_tag.get_text(strip=True):
                            tags.append(tag_text)

        unique_tags = list(set(tags)) # Get unique tags
        self.logger.debug(f"Extracted {len(unique_tags)} unique tags for TF1 Info.")
        return unique_tags[:5]  # Return up to 5 unique tags