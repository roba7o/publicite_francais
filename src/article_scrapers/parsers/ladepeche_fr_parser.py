from article_scrapers.parsers.base_parser import BaseParser
from article_scrapers.config.text_processing_config import SITE_CONFIGS
from datetime import datetime

class LadepecheFrArticleParser(BaseParser):
    def __init__(self):
        # Just pass the site domain - all config is handled by BaseParser
        super().__init__(site_domain='ladepeche.fr')
        
        # Get configuration for this site
        config = SITE_CONFIGS.get('ladepeche.fr', SITE_CONFIGS['default'])
        
        # Apply site-specific text processing settings
        if config['additional_stopwords']:
            self.add_custom_stopwords(config['additional_stopwords'])
        
        self.set_word_length_limits(
            min_length=config['min_word_length'], 
            max_length=config['max_word_length']
        )

    def parse_article_content(self, soup):
        """Parses article content and extracts metadata."""
        try:
            # Look for the main article content
            article = soup.find('article')
            if not article:
                # Fallback: look for main content div or section
                article = soup.find('div', class_='article-content') or soup.find('main')
                if not article:
                    self.logger.warning("No article content found — this might not be an article page")
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
        paragraphs = []
        
        # Look for paragraphs in the article
        p_tags = article.find_all('p')
        
        for p in p_tags:
            # Skip paragraphs that are likely navigation, ads, or metadata
            if p.get('class'):
                # Skip paragraphs with certain classes that might indicate non-content
                class_names = ' '.join(p.get('class', []))
                if any(skip_class in class_names.lower() for skip_class in 
                       ['nav', 'menu', 'sidebar', 'footer', 'ad', 'promo', 'share', 'social']):
                    continue
            
            text = p.get_text(separator=' ', strip=True)
            if text and len(text) > 20:  # Only include substantial paragraphs
                paragraphs.append(text)
        
        return paragraphs

    def extract_title(self, soup):
        """Extract the article's title."""
        # Try different selectors for the title
        title_selectors = [
            'h1',
            '.article-title',
            '.title',
            'title'
        ]
        
        for selector in title_selectors:
            title_tag = soup.select_one(selector)
            if title_tag:
                title = title_tag.get_text(strip=True)
                # Clean up title if it contains site name
                if ' - ' in title:
                    title = title.split(' - ')[0]
                return title
        
        return "Unknown title"

    def extract_date(self, soup):
        """Extract the article's date."""
        # Try different selectors for the date
        date_selectors = [
            'time',
            '.article-date',
            '.date',
            '[data-time]'
        ]
        
        for selector in date_selectors:
            date_tag = soup.select_one(selector)
            if date_tag:
                # Check for data-time attribute first (as seen in the HTML)
                if date_tag.get('data-time'):
                    date_str = date_tag.get('data-time')
                    # Format: 20250712190208 -> 2025-07-12 19:02:08
                    if len(date_str) == 14:
                        try:
                            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {date_str[8:10]}:{date_str[10:12]}:{date_str[12:14]}"
                            return formatted_date
                        except:
                            pass
                
                # Fallback to text content
                date_text = date_tag.get_text(strip=True)
                if date_text:
                    return date_text
        
        return "Unknown date"