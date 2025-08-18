from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from scrapers.base_scraper import BaseScraper


class SlateFrURLScraper(BaseScraper):
    def __init__(self, debug: bool | None = None) -> None:
        super().__init__(debug)
        self.base_url = "https://www.slate.fr"

    def get_article_urls(self) -> list[str]:
        try:
            response = self._make_request(self.base_url)
            soup = BeautifulSoup(response.content, "html.parser")

            cards = soup.select(".card--story")
            urls = []
            for card in cards[:8]:
                a_tag = card.find("a", href=True)
                if a_tag and isinstance(a_tag, Tag):
                    url = str(a_tag["href"])
                    if not url.startswith("http"):
                        url = urljoin(self.base_url, url)
                    urls.append(url)

            urls = list(set(urls))
            self._log_results(urls)
            return urls

        except Exception as e:
            self.logger.error(f"Failed to fetch URL: {self.base_url} | Error: {e}")
            return []
