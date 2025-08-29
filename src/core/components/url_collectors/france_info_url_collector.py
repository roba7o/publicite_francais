import random
import time
from urllib.parse import urljoin

from bs4 import Tag

from core.components.url_collectors.base_url_collector import BaseUrlCollector


class FranceInfoUrlCollector(BaseUrlCollector):
    def __init__(self, debug=None):
        super().__init__(debug)
        self.base_url = "https://www.franceinfo.fr/"

    def get_article_urls(self, max_articles=8) -> list[str]:
        try:
            time.sleep(random.uniform(1, 3))
            response = self._make_request(self.base_url)

            soup = self.parse_html_fast(response.content)
            article_cards = soup.find_all("article", {"data-cy": "card-article-m"})

            if not article_cards:
                return []

            urls = []
            for card in article_cards[:max_articles]:
                if isinstance(card, Tag):
                    link = card.find("a", class_="card-article-m__link")
                    if link and isinstance(link, Tag) and link.has_attr("href"):
                        url = str(link["href"])
                        if not url.startswith("http"):
                            url = urljoin(self.base_url, url)
                        urls.append(url)

            # Remove duplicates while preserving order
            unique_urls = self._deduplicate_urls(urls)

            self._log_results(unique_urls)
            return unique_urls

        except Exception as e:
            self.logger.error(f"Failed to fetch URL: {self.base_url} | Error: {e}")
            return []
