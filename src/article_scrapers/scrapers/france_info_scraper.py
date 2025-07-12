import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from ..config.settings import DEBUG
from article_scrapers.utils.logger import get_logger
import random
import time


class FranceInfoURLScraper:
    def __init__(self, debug=None):
        self.logger = get_logger(self.__class__.__name__)
        self.debug = debug if debug is not None else DEBUG
        self.base_url = "https://www.franceinfo.fr/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/",
            "DNT": "1",
        }

    def get_article_urls(self, max_articles=8):
        try:
            time.sleep(random.uniform(1, 3))

            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            if "text/html" not in response.headers.get("Content-Type", ""):
                return []

            soup = BeautifulSoup(response.content, "html.parser")
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

            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)

            self.logger.info(f"Found {len(unique_urls)} article URLs.")
            return unique_urls

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch URL: {self.base_url} | Error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []
