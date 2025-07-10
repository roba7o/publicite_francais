from article_scrapers.parsers.base_parser import BaseParser
from datetime import datetime

class SlateFrArticleParser(BaseParser):
    def __init__(self):
        super().__init__()

    def parse_article_content(self, soup):
        """Parses article content and extracts metadata."""
        try:
            article = soup.find('article')
            if not article:
                self.logger.warning("No <article> tag found — this might not be an <article> page")
                return None

            paragraphs = self.extract_paragraphs(article)
            if not paragraphs:
                self.logger.warning("No content extracted from paragraphs")
                return None

            return {
                'full_text': '\n\n'.join(paragraphs) if paragraphs else "No content",
                'num_paragraphs': len(paragraphs) if paragraphs else 0,
                'title': self.extract_title(soup) or "Unknown title",
                'article_date': self.extract_date(soup) or "Unknown date",
                'date_scraped': datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as e:
            self.logger.error(f"Error parsing article: {e}")
            return None

    def extract_paragraphs(self, article):
        """Extract text from paragraphs in the article."""
        paragraphs = article.find_all('p')
        return [p.get_text(separator=' ', strip=True) for p in paragraphs if not p.get('class')]

    def extract_title(self, soup):
        """Extract the article's title."""
        title_tag = soup.find('h1')
        return title_tag.get_text(strip=True) if title_tag else "Unknown title"

    def extract_date(self, soup):
        """Extract the article's date."""
        date_tag = soup.find('time')
        return date_tag.get_text(strip=True) if date_tag else "Unknown date"
