from parsers.base_parser import BaseParser

class SlateFrArticleParser(BaseParser):

    def parse_article_content(self, soup):
        try:
            # First check for article tag to validate we're on an article page
            article = soup.find('article')
            if not article:
                print("WARNING: No <article> tag found - this might not be an article page")
                return None

            # Get all text in the article -> relevent text exclusively wrapped as <p> tags
            paragraphs = article.find_all('p')
            if self.debug:
                print(f"\nFound {len(paragraphs)} total paragraphs in article")
                print("First few paragraphs:")
                for i, p in enumerate(paragraphs[:3]):
                    print(f"{i+1}. First 50 chars: {p.get_text()[:50]}...")

            # Filter out paragraphs with classes (these are usually metadata, not article content)
            content = []
            for p in paragraphs:
                # Skip paragraphs with classes like 'reading-time', etc. (exclusive <p> tags)
                if not p.get('class'):
                    text = p.get_text(separator=' ', strip=True)
                    if text:  # Only add non-empty paragraphs
                        content.append(text)

            if not content:
                print("WARNING: No content extracted from paragraphs")
                return None

            return {
                'full_text': '\n\n'.join(content),
                'num_paragraphs': len(content)
            }
                
        except Exception as e:
            print(f"Error parsing article: {e}")
            return None

