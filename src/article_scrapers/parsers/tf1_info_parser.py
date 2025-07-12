"""
TF1 Info Parser - Extracts content from TF1 Info articles
"""

from bs4 import BeautifulSoup
from article_scrapers.parsers.base_parser import BaseParser
from datetime import datetime
import re

class TF1InfoArticleParser(BaseParser):
    def __init__(self):
        super().__init__(site_domain='tf1info.fr')
        
        # TF1 Info specific configurations
        self.add_custom_stopwords({
            'tf1', 'info', 'lci', 'vidéo', 'reportage', 'commenter', 'partager'
        })
        self.set_word_length_limits(min_length=3, max_length=30)

    def parse_article_content(self, soup):
        """
        Parse TF1 Info article content
        Args:
            soup: BeautifulSoup object of the article page
        Returns:
            dict: Parsed article content and metadata
        """
        try:
            # Extract main content
            content_div = soup.find('div', class_=re.compile(r'article-body|content-body|main-content'))
            if not content_div:
                # Try <article> as fallback
                content_div = soup.find('article')
            if not content_div:
                self.logger.warning("No main content div or article tag found")
                return None

            # Extract paragraphs and clean text
            paragraphs = self._extract_paragraphs(content_div)
            full_text = '\n\n'.join(paragraphs) if paragraphs else "No content"

            # Extract metadata
            metadata = {
                'full_text': full_text,
                'num_paragraphs': len(paragraphs),
                'title': self._extract_title(soup),
                'article_date': self._extract_date(soup),
                'date_scraped': datetime.now().strftime("%Y-%m-%d"),
                'author': self._extract_author(soup),
                'image_caption': self._extract_image_caption(soup),
                'tags': self._extract_tags(soup),
            }

            if self.debug:
                stats = self.get_text_statistics(full_text)
                self.logger.info(f"TF1 Info article stats: {stats['total_word_count']} words")
                
            return metadata

        except Exception as e:
            self.logger.error(f"Error parsing TF1 Info article: {e}")
            return None

    def _extract_paragraphs(self, content_div):
        """Extract and clean paragraphs from content div"""
        paragraphs = []
        for element in content_div.find_all(['p', 'h2', 'h3']):
            if element.name == 'p':
                text = element.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                if text and len(text.split()) > 3:  # Skip short paragraphs
                    paragraphs.append(text)
            elif element.name in ['h2', 'h3']:
                # Add subheaders as markdown-style headers
                header_text = element.get_text(strip=True)
                if header_text:
                    paragraphs.append(f"\n\n## {header_text} ##\n")
        return paragraphs

    def _extract_title(self, soup):
        """Extract article title"""
        title_tag = soup.find('h1') or soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else "Unknown Title"

    def _extract_date(self, soup):
        """Extract article date"""
        # Try multiple possible date locations
        date_selectors = [
            'time[datetime]',  # Standard time tag with datetime attribute
            'span.date',        # Common date class
            'div.timestamp',    # Another common date container
            'meta[property="article:published_time"]'  # OG meta tag
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if element.has_attr('datetime'):
                    return element['datetime']
                if element.has_attr('content'):
                    return element['content']
                return element.get_text(strip=True)
        
        return datetime.now().strftime("%Y-%m-%d")

    def _extract_author(self, soup):
        """Extract article author"""
        author_selectors = [
            'span.author-name',
            'div.author a',
            'meta[name="author"]',
            'a[rel="author"]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.has_attr('content'):
                    return element['content']
                return element.get_text(strip=True)
                
        return "Unknown Author"

    def _extract_image_caption(self, soup):
        """Extract main image caption"""
        figcaption = soup.find('figcaption')
        if figcaption:
            # Remove any nested spans that might contain credits
            for span in figcaption.find_all('span'):
                span.decompose()
            return figcaption.get_text(strip=True)
        return None

    def _extract_tags(self, soup):
        """Extract article tags/categories"""
        tags = []
        tag_containers = [
            'div.tags', 
            'ul.tag-list',
            'div.categories',
            'meta[property="article:tag"]'
        ]
        
        for container in tag_containers:
            elements = soup.select(container)
            for element in elements:
                if element.name == 'meta':
                    if element.has_attr('content'):
                        tags.append(element['content'])
                else:
                    for a in element.find_all('a'):
                        if tag_text := a.get_text(strip=True):
                            tags.append(tag_text)
        
        return list(set(tags))[:5]  # Return up to 5 unique tags