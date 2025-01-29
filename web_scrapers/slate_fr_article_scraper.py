import requests
from bs4 import BeautifulSoup
import time

class ArticleParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        
    def get_article_content(self, url):
        """
        Extract the full text content from slate.fr article
        Returns: dict containing article text and metadata
        """

        try:
            # Adding a small delay to be nice to the server
            time.sleep(1)

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Finding the main article content
            article = soup.find('article')
            if not article:
                return None
            
            # Getting all paragraphs in the article
            # Targeting the main content div which (usually) comes after the header

            content_div = article.find('div', class_='content')
            if content_div:
                paragraphs = content_div.find_all(['p', 'h2', 'h3'])
            else:
                paragraphs = article.find_all(['p', 'h2', 'h3'])

            content = []
            for p in paragraphs:
                # Skiping certain classes that might contain unwanted content
                if p.get('class') and any(c in ['card-text', 'card-title'] for c in p['class']):
                    continue

                # Get the text, preserving some formatting
                text = p.get_text(separator=' ', strip=True)
                if text:    # only adding non-empty paragraphs
                    content.append(text)

            # Join all pargraphs with new lines
            full_text = '\n'.join(content)

            return {
                'url': url,
                'full_text': full_text,
                'num_paragraphs': len(content)
            }
        
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None 
        
def main():
    parser = ArticleParser()
    test_url = "https://www.slate.fr/monde/regle-baillon-mondial-trump-entraver-acces-avortement-mexico-city-policy-anti-ivg-dangers-mort-femmes-deces-grossesse"

    result = parser.get_article_content(test_url)

    if result:
        print(f"Successfully parsed article")
        print(f"number of paragraphs: {result['num_paragraphs']}")
        print("\nFirst 500 characters of content:")
        print(result['full_text'][:500])
    else:
        print("Failed to parse article")

if __name__ == "__main__":
    main()
    