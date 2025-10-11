from urllib.parse import urljoin

from bs4 import Tag

from config.environment import MAX_ARTICLES
from core.components.url_collectors.base_url_collector import BaseUrlCollector


class SlateFrUrlCollector(BaseUrlCollector):
    def __init__(self, debug: bool | None = None) -> None:
        super().__init__(debug)
        self.base_url = "https://www.slate.fr"

    def get_article_urls(self, max_articles=None) -> list[str]:
        """
        Get article URLs from Slate.fr homepage.

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

            cards = soup.select(".card--story")
            urls = []
            # Apply limit if specified, otherwise get all cards
            cards_to_process = cards[:max_articles] if max_articles else cards
            for card in cards_to_process:
                a_tag = card.find("a", href=True)
                if a_tag and isinstance(a_tag, Tag):
                    url = str(a_tag["href"])
                    if not url.startswith("http"):
                        url = urljoin(self.base_url, url)
                    urls.append(url)

            urls = self._deduplicate_urls(urls)
            self._log_results(urls)
            return urls

        except Exception as e:
            self.logger.error(f"Failed to fetch URL: {self.base_url} | Error: {e}")
            return []
