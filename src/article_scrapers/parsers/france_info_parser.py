from article_scrapers.parsers.base_parser import BaseParser
from datetime import datetime
import re

class FranceInfoArticleParser(BaseParser):
    def __init__(self):
        super().__init__(site_domain='franceinfo.fr')
        

    def parse_article_content(self, soup):
        """Parses FranceInfo article content and extracts metadata."""
        try:
            # Main content extraction
            content_div = soup.find('div', class_='c-body')
            if not content_div:
                self.logger.warning("No main content div found")
                return None

            paragraphs = self.extract_paragraphs(content_div)
            full_text = '\n\n'.join(paragraphs) if paragraphs else "No content"
            
            # Get text statistics
            if self.debug:
                stats = self.get_text_statistics(full_text)
                self.logger.info(f"Text stats: {stats['total_unique_words']} unique words, "
                               f"{stats['total_word_count']} total words")
                self.logger.debug(f"Top words: {stats['top_10_words']}")

            return {
                'full_text': full_text,
                'num_paragraphs': len(paragraphs),
                'title': self.extract_title(soup),
                'article_date': self.extract_date(soup),
                'date_scraped': datetime.now().strftime("%Y-%m-%d"),
                'author': self.extract_author(soup),
                'tags': self.extract_tags(soup),
                'image_caption': self.extract_image_caption(soup),
            }

        except Exception as e:
            self.logger.error(f"Error parsing article: {e}")
            return None

    def extract_paragraphs(self, content_div):
        """Extract text paragraphs from main content."""
        paragraphs = []
        for element in content_div.find_all(['p', 'h2']):
            if element.name == 'h2':
                # Add subheaders as separate paragraphs
                paragraphs.append(f"\n\n## {element.get_text(strip=True)} ##\n")
            else:
                # Clean paragraph text
                text = element.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                if text and len(text.split()) > 3:  # Skip very short paragraphs
                    paragraphs.append(text)
        return paragraphs

    def extract_title(self, soup):
        """Extract article title from h1 tag."""
        title_tag = soup.find('h1')
        return title_tag.get_text(strip=True) if title_tag else "Unknown title"

    def extract_date(self, soup):
        """Extract publication date from time tag."""
        time_tag = soup.find('time')
        if time_tag and time_tag.has_attr('datetime'):
            return time_tag['datetime']
        return datetime.now().strftime("%Y-%m-%d")

    def extract_author(self, soup):
        """Extract author information if available."""
        author_tag = soup.find('span', class_='c-signature__author')
        return author_tag.get_text(strip=True) if author_tag else "Unknown author"

    def extract_tags(self, soup):
        """Extract article tags."""
        tags_section = soup.find('section', class_='related-tags')
        if not tags_section:
            return []
        
        tags = []
        for tag in tags_section.find_all('a', class_='fi-tag'):
            tag_text = tag.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)
        return tags

    def extract_image_caption(self, soup):
        """Extract caption from article's main image."""
        figcaption = soup.find('figcaption')
        if figcaption:
            # Remove the photographer credit (content in span)
            for span in figcaption.find_all('span'):
                span.decompose()
            return figcaption.get_text(strip=True)
        return None