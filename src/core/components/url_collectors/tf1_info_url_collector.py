"""
TF1 Info UrlCollector - Extracts article URLs from TF1 Info homepage
"""

import json
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config.environment import MAX_ARTICLES
from core.components.url_collectors.base_url_collector import BaseUrlCollector


class TF1InfoUrlCollector(BaseUrlCollector):
    def __init__(self, debug=None):
        super().__init__(debug)
        self.base_url = "https://www.tf1info.fr/"

    def _make_request(self, url: str, timeout: int = 60) -> requests.Response:
        """
        Override base class request method to avoid anti-bot detection.

        TF1Info has sophisticated anti-bot protection that returns truncated
        content. Use a clean session with browser-like behavior.
        """
        import time

        try:
            # Create a fresh session for each request to avoid tracking
            session = requests.Session()

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                # Don't specify Accept-Encoding to let requests handle compression automatically
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            # Add small delay to mimic human behavior
            time.sleep(1)

            response = session.get(
                url, headers=headers, timeout=timeout, allow_redirects=True
            )
            response.raise_for_status()

            # Close session to avoid tracking
            session.close()

            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {str(e)}")
            raise

    def get_article_urls(self, max_articles=None) -> list[str]:
        """
        Extract article URLs from TF1 Info homepage

        Args:
            max_articles: Maximum number of articles to return.
                         If None, uses MAX_ARTICLES from config (default: unlimited)

        Returns:
            List of article URLs
        """
        if max_articles is None:
            max_articles = MAX_ARTICLES
        try:
            response = self._make_request(self.base_url)
            # Use html.parser instead of lxml to avoid parsing issues
            soup = BeautifulSoup(response.text, "html.parser")

            # Method 1: Try to extract from JSON-LD in script tag
            urls = self._extract_from_json_ld(soup)

            # Method 2: Fallback to direct HTML parsing if JSON-LD fails
            if not urls:
                urls = self._extract_from_html(soup)

            # Return unique URLs up to max_articles (or all if max_articles is None)
            unique_urls = self._deduplicate_urls(urls)
            if max_articles:
                unique_urls = unique_urls[:max_articles]
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
        """Extract URLs from TF1Info's specific HTML structure"""
        urls = []

        # TF1Info uses LinkArrowButton__Content__Title in h3 elements within links
        # Look for links containing these title elements
        title_elements = soup.find_all(
            attrs={
                "class": lambda x: x
                and "LinkArrowButton__Content__Title" in " ".join(x)
                if isinstance(x, list)
                else "LinkArrowButton__Content__Title" in str(x)
                if x
                else False
            }
        )

        for title_elem in title_elements:
            # Find the parent link
            parent = title_elem.parent
            while parent and parent.name != "a":
                parent = parent.parent
                if not parent:
                    break

            if parent and parent.name == "a":
                if href := parent.get("href"):
                    full_url = urljoin(self.base_url, href)
                    if full_url not in urls:
                        urls.append(full_url)

        # Fallback to generic selectors if the specific method fails
        if not urls:
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
