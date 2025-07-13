"""
Grabbing top 8 articles from ladepeche.fr which are then passed on to parser
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from ..config.settings import DEBUG

from article_scrapers.utils.structured_logger import get_structured_logger


class LadepecheFrURLScraper:
    def __init__(self, debug=None):
        self.logger = get_structured_logger(self.__class__.__name__)

        self.debug = debug if debug is not None else DEBUG
        self.base_url = "https://www.ladepeche.fr"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

    def get_article_urls(self):
        """
        Get the URLs of the top 8 articles from the Ladepeche.fr homepage.
        """
        try:
            if self.debug:
                self.logger.info(f"Fetching homepage URL: {self.base_url}")

            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Look for article links in the news section
            # Based on the HTML structure: <a class="new__title" href="/2025/07/12/...">
            news_links = soup.select("a.new__title")

            urls = []
            for link in news_links[:8]:  # Get top 8 articles
                href = link.get("href")
                if href:
                    # Build full URL
                    if href.startswith("http://") or href.startswith("https://"):
                        full_url = href
                    else:
                        full_url = urljoin(self.base_url, href)
                    urls.append(full_url)

            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)

            self.logger.info(f"Found {len(unique_urls)} article URLs.")
            if self.debug:
                for url in unique_urls:
                    self.logger.debug(f"Article URL: {url}")

            return unique_urls

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch URL: {self.base_url} | Error: {e}")
            return None
