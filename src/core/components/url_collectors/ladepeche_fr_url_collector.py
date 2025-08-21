"""
Grabbing top 8 articles from ladepeche.fr which are then passed on to parser
"""

from urllib.parse import urljoin

from core.components.url_collectors.base_url_collector import BaseUrlCollector


class LadepecheFrUrlCollector(BaseUrlCollector):
    def __init__(self, debug=None):
        super().__init__(debug)
        self.base_url = "https://www.ladepeche.fr"

    def get_article_urls(self) -> list[str]:
        """
        Get the URLs of the top 8 articles from the Ladepeche.fr homepage.
        """
        try:
            response = self._make_request(self.base_url)
            soup = self.parse_html_fast(response.content)

            # Look for article links in the news section
            # Based on the HTML structure: <a class="new__title"
            # href="/2025/07/12/...">
            news_links = soup.select("a.new__title")

            urls = []
            # Get top 8 articles
            for link in news_links[:8]:
                href = link.get("href")
                if href and isinstance(href, str):
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

            self._log_results(unique_urls)
            return unique_urls

        except Exception as e:
            self.logger.error(f"Failed to fetch URL: {self.base_url} | Error: {e}")
            return []
