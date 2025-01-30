import requests
from bs4 import BeautifulSoup
import time
import os

class ArticleParser:
    def __init__(self, debug=False):
        # This user-agent header is used to mimic a browser visit
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        self.debug = debug
        

    def get_soup_from_url(self, url):
        """
        Get a BeautifulSoup object from a given url
        """
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    
    def get_soup_from_localfile(self, file_name):
        """
        Get a BeautifulSoup object from a local html file
        """

        # Get the absolute path to the test file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get root dir
        test_file_path = os.path.join(base_dir, "test_data", file_name)
        
        with open(test_file_path, "r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), 'html.parser')




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

def main():
    parser = ArticleParser()

    test_url = "https://www.slate.fr/monde/regle-baillon-mondial-trump-entraver-acces-avortement-mexico-city-policy-anti-ivg-dangers-mort-femmes-deces-grossesse"

    # TODO change for live version

    live = False

    if live:
        soup = parser.get_soup_from_url(test_url)
    else:
        soup = parser.get_soup_from_localfile("test_slate_article.html")

    result = parser.parse_article_content(soup)

    if result:
        print(f"Successfully parsed article")
        print(f"number of paragraphs: {result['num_paragraphs']}")
        print("\nFirst 500 characters of content:")
        print(result['full_text'][:500])
    else:
        print("Failed to parse article")

if __name__ == "__main__":
    main()
