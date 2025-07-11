"""
Grabbing top 8 articles from slate.fr which are then passed on to parser
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from ..config.settings import DEBUG

from article_scrapers.utils.logger import get_logger


class SlateFrURLScraper:
    def __init__(self, debug=None):
        self.logger = get_logger(self.__class__.__name__)
        
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
            if self.debug:
                self.logger.info(f"Fetching homepage URL: {self.base_url}")

            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            cards = soup.select(".card--story")

            urls = []
            for card in cards[:8]:  # use 8 as per comment, was 2 in your snippet
                a_tag = card.find('a', href=True)
                if a_tag:
                    url = a_tag["href"]
                    if url.startswith("http://") or url.startswith("https://"):
                        full_url = url
                    else:
                        full_url = urljoin(self.base_url, url)
                    urls.append(full_url)

            urls = list(set(urls))  # remove duplicates

            self.logger.info(f"Found {len(urls)} article URLs.")
            if self.debug:
                for url in urls:
                    self.logger.debug(f"Article URL: {url}")

            return urls

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch URL: {self.base_url} | Error: {e}")
            return None
