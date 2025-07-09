

"""
Grabbing top 8 artcilces from slate.fr which are then passed on to parser
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..settings import DEBUG
class SlateFrURLScraper:
    def __init__(self, debug=None):
        self.debug = debug if debug is not None else DEBUG
        self.base_url = "https://www.slate.fr"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

    def get_article_urls(self):
        """
        Get the URLs of the top 8 articles from the Slate.fr homepage.
        """
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
            soup = BeautifulSoup(response.content, 'html.parser')

            # All relevant hrefs are in .card class
            cards = soup.select(".card--story")

            urls = []
            for card in cards[:2]:
                a_tag = card.find('a', href=True) #first <a> tag with href
                if a_tag:
                    url = a_tag["href"]
                    # Check if the URL is already absolute
                    if url.startswith("http://") or url.startswith("https://"):
                        full_url = url  # No need to join, it's already an absolute URL
                    else:
                        full_url = urljoin(self.base_url, url)  # Join with the base URL for relative URLs
                    urls.append(full_url)
            
            urls = list(set(urls))  #remove duplicates

            return urls
        
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch URL: {self.base_url} | Error: {e}")
            return None

