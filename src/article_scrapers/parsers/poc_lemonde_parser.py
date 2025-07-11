# lemonde_parser.py
from article_scrapers.parsers.base_parser import BaseParser
from datetime import datetime

class LemondeArticleParser(BaseParser):
    def __init__(self):
        # Just pass the site domain - all config is handled by BaseParser
        super().__init__(site_domain='lemonde.fr')

    def parse_article_content(self, soup):
        """Parses Le Monde article content and extracts metadata."""
        try:
            # Le Monde might have different HTML structure
            article = soup.find('article') or soup.find('.article__content')
            if not article:
                self.logger.warning("No article content found")
                return None

            paragraphs = self.extract_paragraphs(article)
            if not paragraphs:
                self.logger.warning("No content extracted from paragraphs")
                return None

            full_text = '\n\n'.join(paragraphs) if paragraphs else "No content"
            
            return {
                'full_text': full_text,
                'num_paragraphs': len(paragraphs),
                'title': self.extract_title(soup) or "Unknown title",
                'article_date': self.extract_date(soup) or "Unknown date",
                'date_scraped': datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as e:
            self.logger.error(f"Error parsing article: {e}")
            return None

    def extract_paragraphs(self, article):
        """Extract text from paragraphs - Le Monde specific."""
        paragraphs = article.find_all('p')
        return [p.get_text(separator=' ', strip=True) for p in paragraphs]

    def extract_title(self, soup):
        """Extract title - Le Monde specific."""
        title_tag = soup.find('h1') or soup.find('.article__title')
        return title_tag.get_text(strip=True) if title_tag else "Unknown title"

    def extract_date(self, soup):
        """Extract date - Le Monde specific."""
        date_tag = soup.find('time') or soup.find('.article__date')
        return date_tag.get_text(strip=True) if date_tag else "Unknown date"

