import requests
from bs4 import BeautifulSoup
import time

class ArticleParser:
    def __init__(self):
        # This user-agent header is used to mimic a browser visit
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        

    def get_soup_from_url(self, url):
        """
        Get a BeautifulSoup object from a given url
        """
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    
    def get_soup_from_localfile(self, filepath):
        """
        Get a BeautifulSoup object from a local html file
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), 'html.parser')

    def parse_article_content(self, soup):
        """
        Parse article content from a BeautifulSoup object
        """

        try:
            article = soup.find('article') # for this website the main content is in an article tag <article>
            if not article:
                return None

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
                    
            full_text = '\n\n'.join(content)

            return {
                'full_text': full_text,
                'num_paragraphs': len(content)
            }
        except Exception as e:
            print(f"Error parsing article content: {e}")
            return None
        
    def get_article_content(self, source, is_local=False):
        """
        Parse article content from a given url or local file
        Args:
            source: str, url or filepath
            is_local: bool, whether the source is a local file or a url
        """

        try:
            if is_local:
                soup = self.get_soup_from_localfile(source)
            else:
                time.sleep(1)   #only sleep for html requests
                soup = self.get_soup_from_url(source)

            result = self.parse_article_content(soup)
            if result and not is_local:
                result['url'] = source

            return result
        
        except Exception as e:
            print(f"Error proccessing {'file' if is_local else 'url'}: {source}: {e}")
            return None


def main():
    parser = ArticleParser()

    test_url = "https://www.slate.fr/monde/regle-baillon-mondial-trump-entraver-acces-avortement-mexico-city-policy-anti-ivg-dangers-mort-femmes-deces-grossesse"

    #TODO Remove on final version
    # For development purposes, you can save the html content of the page to a local file
    result = parser.get_article_content("test_article.html", is_local=True)

    # For production, you can use the url directly
    # result = parser.get_article_content(test_url)


    if result:
        print(f"Successfully parsed article")
        print(f"number of paragraphs: {result['num_paragraphs']}")
        print("\nFirst 500 characters of content:")
        print(result['full_text'][:500])
    else:
        print("Failed to parse article")

if __name__ == "__main__":
    main()
