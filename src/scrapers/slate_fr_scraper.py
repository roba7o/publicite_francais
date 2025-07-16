import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from config.settings import DEBUG
from utils.structured_logger import get_structured_logger


class SlateFrURLScraper:
    def __init__(self, debug=None):
        self.logger = get_structured_logger(self.__class__.__name__)
        self.debug = debug if debug is not None else DEBUG
        self.base_url = "https://www.slate.fr"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            )
        }

    def get_article_urls(self):
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
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
            self.logger.info(f"Found {len(urls)} article URLs.")
            return urls

        except Exception as e:
            self.logger.error(
                f"Failed to fetch URL: {self.base_url} | Error: {e}"
            )
            return None
