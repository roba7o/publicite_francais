"""
TF1 Info Scraper - Extracts article URLs from TF1 Info homepage
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from article_scrapers.utils.structured_logger import get_structured_logger
import json
from ..config.settings import DEBUG


class TF1InfoURLScraper:
    def __init__(self, debug=False):
        self.logger = get_structured_logger(self.__class__.__name__)
        self.debug = debug if debug is not None else DEBUG
        self.base_url = "https://www.tf1info.fr/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def get_article_urls(self, max_articles=8):
        """
        Extract article URLs from TF1 Info homepage
        Args:
            max_articles (int): Maximum number of articles to return
        Returns:
            list: List of article URLs
        """
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Method 1: Try to extract from JSON-LD in script tag
            urls = self._extract_from_json_ld(soup)

            # Method 2: Fallback to direct HTML parsing if JSON-LD fails
            if not urls:
                urls = self._extract_from_html(soup)

            # Return unique URLs up to max_articles
            unique_urls = list(set(urls))[:max_articles]

            if self.debug:
                self.logger.info(f"Found {len(unique_urls)} TF1 Info articles")
                for url in unique_urls:
                    self.logger.debug(f"TF1 Info URL: {url}")

            return unique_urls

        except Exception as e:
            self.logger.error(f"Error scraping TF1 Info: {e}")
            return []

    def _extract_from_json_ld(self, soup):
        """Extract article URLs from JSON-LD structured data"""
        urls = []
        script_tags = soup.find_all("script", type="application/ld+json")

        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "ItemList":
                            for element in item.get("itemListElement", []):
                                if url := element.get("url"):
                                    urls.append(url)
            except json.JSONDecodeError:
                continue

        return urls

    def _extract_from_html(self, soup):
        """Fallback method to extract URLs directly from HTML"""
        urls = []

        # Try different selectors that might contain article links
        selectors = [
            'article a[href*="/"]',  # Generic article links
            "a.card-article",  # Card articles
            "a.article-link",  # Article links
            "h2 a",  # Headline links
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                if href := link.get("href"):
                    full_url = urljoin(self.base_url, href)
                    if full_url not in urls:
                        urls.append(full_url)
            if urls:  # Stop at first successful selector
                break

        return urls
