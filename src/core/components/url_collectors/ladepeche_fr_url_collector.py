"""
URL collector for ladepeche.fr articles
"""

from urllib.parse import urljoin

from config.environment import MAX_ARTICLES
from core.components.url_collectors.base_url_collector import BaseUrlCollector


class LadepecheFrUrlCollector(BaseUrlCollector):
    def __init__(self, debug=None):
        super().__init__(debug)
        self.base_url = "https://www.ladepeche.fr"

    def get_article_urls(self, max_articles=None) -> list[str]:
        """
        Get article URLs from Ladepeche.fr homepage.

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
            soup = self.parse_html_fast(response.content)

            # Look for article links in the news section
            # Based on the HTML structure: <a class="new__title"
            # href="/2025/07/12/...">
            news_links = soup.select("a.new__title")

            urls = []
            # Apply limit if specified, otherwise get all links
            links_to_process = news_links[:max_articles] if max_articles else news_links
            for link in links_to_process:
                href = link.get("href")
                if href and isinstance(href, str):
                    # Build full URL
                    if href.startswith("http://") or href.startswith("https://"):
                        full_url = href
                    else:
                        full_url = urljoin(self.base_url, href)
                    urls.append(full_url)

            # Remove duplicates while preserving order
            unique_urls = self._deduplicate_urls(urls)

            self._log_results(unique_urls)
            return unique_urls

        except Exception as e:
            self.logger.error(f"Failed to fetch URL: {self.base_url} | Error: {e}")
            return []
