# Example of how to use the enhanced parser in your slate_fr_parser.py

from article_scrapers.parsers.base_parser import BaseParser
from datetime import datetime

class SlateFrArticleParser(BaseParser):
    def __init__(self):
        # Initializing with custom settings
        super().__init__(
            min_word_frequency=2,  # Only keep words that appear at least twice
            debug=True
        )
        
        # Add site-specific stopwords if needed
        slate_stopwords = {
            'slate', 'article', 'lire', 'aussi', 'voir', 'copyright', 'droits', 'réservés'
        }
        self.add_custom_stopwords(slate_stopwords)
        
        # Set word length limits (optional)
        self.set_word_length_limits(min_length=4, max_length=30)

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

            full_text = '\n\n'.join(paragraphs) if paragraphs else "No content"
            
            # Get text statistics for debugging
            if self.debug:
                stats = self.get_text_statistics(full_text)
                self.logger.info(f"Text stats: {stats['total_unique_words']} unique words, "
                               f"{stats['total_word_count']} total words")
                self.logger.debug(f"Top words: {stats['top_10_words']}")

            return {
                'full_text': full_text,
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


# Optional: Create a configuration file for different sites
# config/text_processing_config.py

SITE_CONFIGS = {
    'slate.fr': {
        'additional_stopwords': {'slate', 'article', 'lire', 'aussi', 'voir', 'copyright'},
        'min_word_frequency': 2,
        'min_word_length': 4,
        'max_word_length': 30
    },
    'lemonde.fr': {
        'additional_stopwords': {'monde', 'article', 'abonnés', 'premium'},
        'min_word_frequency': 1,
        'min_word_length': 3,
        'max_word_length': 25
    },
    'default': {
        'additional_stopwords': set(),
        'min_word_frequency': 2,
        'min_word_length': 3,
        'max_word_length': 50
    }
}