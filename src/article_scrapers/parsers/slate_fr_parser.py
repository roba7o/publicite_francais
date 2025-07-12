# article_scrapers/parsers/slate_fr_parser.py

"""
Parser for Slate.fr articles.

This module provides the SlateFrArticleParser class, which extends BaseParser
to specifically extract and process content from Slate.fr articles.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup

from article_scrapers.parsers.base_parser import BaseParser


class SlateFrArticleParser(BaseParser):
    """
    Parses article content from slate.fr.
    Inherits common fetching and text processing functionalities from BaseParser.
    """

    def __init__(self) -> None:
        """
        Initializes the SlateFrArticleParser with its specific domain.
        The base parser handles loading and applying the site's configuration
        (including stopwords and word length limits defined in text_processing_config.py).
        """
        super().__init__(site_domain='slate.fr')
        self.logger.info("SlateFrArticleParser initialized.")

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
            article_tag = soup.find('article')
            if not article_tag:
                self.logger.warning("No <article> tag found for Slate.fr article.")
                return None

            paragraphs = self._extract_paragraphs(article_tag)
            full_text = '\n\n'.join(paragraphs) if paragraphs else ""

            if not full_text:
                self.logger.warning("No significant text extracted from Slate.fr article.")
                return None

            # Get text statistics for debugging
            if self.debug:
                stats = self.get_text_statistics(full_text)
                self.logger.info(f"Slate.fr text stats: unique_words={stats['total_unique_words']}, "
                               f"total_words={stats['total_word_count']}")
                self.logger.debug(f"Slate.fr top words: {stats['top_10_words']}")

            return {
                'full_text': full_text,
                'num_paragraphs': len(paragraphs),
                'title': self._extract_title(soup),
                'article_date': self._extract_date(soup),
                'date_scraped': datetime.now().strftime("%Y-%m-%d"),
                'author': self._extract_author(soup), # Placeholder for future implementation
                'tags': self._extract_tags(soup), # Placeholder for future implementation
                'image_caption': self._extract_image_caption(soup), # Placeholder for future implementation
            }

        except Exception as e:
            self.logger.error(f"Error parsing Slate.fr article: {e}", exc_info=True)
            return None

    def _extract_paragraphs(self, article_tag: BeautifulSoup) -> List[str]:
        """
        Extracts text from paragraphs within the main article tag, filtering out non-content.

        Args:
            article_tag (BeautifulSoup): The BeautifulSoup object of the main article area.

        Returns:
            List[str]: A list of extracted and cleaned paragraph strings.
        """
        paragraphs: List[str] = []
        # Find all direct <p> children of article_tag that do not have a 'class' attribute.
        # This is a common pattern to filter out captions, footnotes, or other non-main text paragraphs.
        for p in article_tag.find_all('p'):
            if not p.get('class'): # Only include paragraphs without a class attribute
                text = p.get_text(separator=' ', strip=True)
                # Further cleaning for whitespace and minimum length
                text = ' '.join(text.split())
                if text and len(text.split()) > 5: # Require at least 5 words to be considered content
                    paragraphs.append(text)
        return paragraphs

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extracts the article's title.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            str: The extracted title, or "Unknown title" if not found.
        """
        title_tag = soup.find('h1')
        if title_tag:
            return title_tag.get_text(strip=True)
        self.logger.debug("Article title (h1) not found for Slate.fr.")
        return "Unknown title"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """
        Extracts the article's publication date.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
            str: The extracted date in "YYYY-MM-DD" format, or "Unknown date" if not found.
        """
        date_tag = soup.find('time')
        if date_tag and date_tag.has_attr('datetime'):
            date_str = date_tag['datetime']
            try:
                # Attempt to parse as ISO format (e.g., "2023-10-26T10:00:00+02:00")
                dt_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt_obj.strftime("%Y-%m-%d")
            except ValueError:
                self.logger.warning(f"Could not parse datetime attribute for Slate.fr: {date_str}")
                return date_str # Return original if cannot parse, as a fallback
        elif date_tag:
            # Fallback to text content if no datetime attribute
            text_date = date_tag.get_text(strip=True)
            if text_date:
                # Attempt to parse common text date formats if necessary
                # For example, "26 octobre 2023" -> add more parsing logic if needed
                return text_date
        self.logger.debug("Article date (time tag or datetime attribute) not found for Slate.fr.")
        return "Unknown date"

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """
        Extracts author information for Slate.fr. (Implement specific logic)
        """
        # Example for Slate.fr: Authors often appear in a specific span or link
        author_tag = soup.find('a', class_='author_name') or soup.find('span', class_='byline-author')
        if author_tag:
            return author_tag.get_text(strip=True)
        self.logger.debug("Author information not found for Slate.fr.")
        return "Unknown author"

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """
        Extracts article tags for Slate.fr. (Implement specific logic)
        """
        tags: List[str] = []
        # Example for Slate.fr: tags might be in a ul/li structure with specific classes
        tags_container = soup.find('ul', class_='tags')
        if tags_container:
            for li_tag in tags_container.find_all('li'):
                tag_text = li_tag.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
        self.logger.debug("Tags not found for Slate.fr.")
        return tags

    def _extract_image_caption(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extracts the main image caption for Slate.fr. (Implement specific logic)
        """
        # Example for Slate.fr: captions often in a figcaption tag
        figcaption = soup.find('figure', class_='article-img').find('figcaption') if soup.find('figure', class_='article-img') else None
        if figcaption:
            caption_text = figcaption.get_text(strip=True)
            return caption_text if caption_text else None
        self.logger.debug("Image caption not found for Slate.fr.")
        return None