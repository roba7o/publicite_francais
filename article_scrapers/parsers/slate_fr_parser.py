from parsers.base_parser import BaseParser

class SlateFrArticleParser(BaseParser):
        def __init__(self):
            super().__init__()

        def parse_article_content(self, soup):
            """ parses the article content from a Slate.fr article page and extracts metadata """
            try:
                # First check for article tag to validate we're on an <article> page
                article = soup.find('article')
                if not article:
                    print("WARNING: No <article> tag found - this might not be an <article> page")
                    return None

                # Checking if paragraphs are nested the <article> tag
                paragraphs = self.extract_paragraphs(article)
                if not paragraphs:
                    print("WARNING: No content extracted from paragraphs")
                    return None
                
                return {
                    'full_text': '\n\n'.join(paragraphs) if paragraphs else "No content",
                    'num_paragraphs': len(paragraphs) if paragraphs else 0,
                    'title': self.extract_title(soup) or "Unknown title",
                    'date': self.extract_date(soup) or "Unknown date",
                }
            
            except Exception as e:
                print(f"Error parsing article: {e}")
                return None

                    
        def extract_paragraphs(self, article):
            """Extracts text from paragraphs in the article"""
            paragraphs = article.find_all('p')
            return [p.get_text(separator=' ', strip=True) for p in paragraphs if not p.get('class')]

        def extract_title(self, soup):
            """Extracts the title of the article"""
            title_tag = soup.find('h1')
            return title_tag.get_text(strip=True) if title_tag else "Unknown title"
        
        def extract_date(self, soup):
            """Extracts the date of the article"""
            date_tag = soup.find('time')
            return date_tag.get_text(strip=True) if date_tag else "Unknown date"
