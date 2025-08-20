"""
TF1 Info UrlCollector - Extracts article URLs from TF1 Info homepage
"""

import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from url_collectors.base_url_collector import BaseUrlCollector


class TF1InfoUrlCollector(BaseUrlCollector):
    def __init__(self, debug=None):
        super().__init__(debug)
        self.base_url = "https://www.tf1info.fr/"

    def get_article_urls(self, max_articles=8) -> list[str]:
        """
        Extract article URLs from TF1 Info homepage
        Args:
            max_articles (int): Maximum number of articles to return
        Returns:
            List[str]: List of article URLs
        """
        try:
            response = self._make_request(self.base_url)
            soup = BeautifulSoup(response.text, "html.parser")

            # Method 1: Try to extract from JSON-LD in script tag
            urls = self._extract_from_json_ld(soup)

            # Method 2: Fallback to direct HTML parsing if JSON-LD fails
            if not urls:
                urls = self._extract_from_html(soup)

            # Return unique URLs up to max_articles
            unique_urls = list(set(urls))[:max_articles]
            self._log_results(unique_urls)
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
