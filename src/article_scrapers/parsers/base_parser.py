import os
import time
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

import requests
from bs4 import BeautifulSoup

from article_scrapers.utils.csv_writer import DailyCSVWriter
from article_scrapers.utils.french_text_processor import FrenchTextProcessor
from article_scrapers.config.text_processing_config import SITE_CONFIGS
from article_scrapers.config.settings import DEBUG
from article_scrapers.utils.logger import get_logger


DEFAULT_SITE_CONFIG = {
    "min_word_frequency": 1,
    "min_word_length": 3,
    "max_word_length": 50,
    "additional_stopwords": [],
}


class BaseParser(ABC):
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/58.0.3029.110 Safari/537.3"
        )
    }

    def __init__(
        self, site_domain: str, debug: Optional[bool] = None, delay: float = 1.0
    ):
        self.logger = get_logger(self.__class__.__name__)
        self.site_domain = site_domain
        self.debug = debug if debug is not None else DEBUG
        self.delay = delay
        self.csv_writer = DailyCSVWriter(debug=self.debug)
        self.config = self._load_site_config(site_domain)
        self.text_processor = FrenchTextProcessor()
        self.min_word_frequency = self.config["min_word_frequency"]
        self._apply_text_processor_config()

    def _load_site_config(self, site_domain: str) -> Dict[str, Any]:
        config = SITE_CONFIGS.get(site_domain, DEFAULT_SITE_CONFIG)
        return config

    def _apply_text_processor_config(self) -> None:
        additional_stopwords = self.config.get("additional_stopwords")
        if additional_stopwords:
            self.text_processor.expand_stopwords(set(additional_stopwords))

        min_length = self.config.get(
            "min_word_length", DEFAULT_SITE_CONFIG["min_word_length"]
        )
        max_length = self.config.get(
            "max_word_length", DEFAULT_SITE_CONFIG["max_word_length"]
        )
        self.text_processor.set_word_length_limits(
            min_length=min_length, max_length=max_length
        )

    def get_soup_from_url(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            time.sleep(self.delay)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def get_soup_from_localfile(self, file_name: str) -> Optional[BeautifulSoup]:
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root_dir = os.path.abspath(os.path.join(current_file_dir, "..", ".."))
        test_file_path = os.path.join(project_root_dir, "test_data", file_name)

        if not os.path.exists(test_file_path):
            self.logger.error(f"Test file not found: {test_file_path}")
            return None

        try:
            with open(test_file_path, "r", encoding="utf-8") as f:
                return BeautifulSoup(f.read(), "html.parser")
        except Exception as e:
            self.logger.error(f"Error reading {test_file_path}: {e}")
            return None

    def count_word_frequency(self, text: str) -> Dict[str, int]:
        if not text:
            return {}

        word_frequencies = self.text_processor.count_word_frequency(text)

        if self.min_word_frequency > 1:
            word_frequencies = self.text_processor.filter_by_frequency(
                word_frequencies, self.min_word_frequency
            )

        return word_frequencies

    def to_csv(self, parsed_data: Dict[str, Any], url: str) -> None:
        if not parsed_data or not parsed_data.get("full_text"):
            return

        try:
            full_text = parsed_data["full_text"]
            word_freqs = self.count_word_frequency(full_text)

            if not word_freqs:
                return

            self.csv_writer.write_article(
                parsed_data=parsed_data, url=url, word_freqs=word_freqs
            )
        except Exception as e:
            self.logger.error(f"Error writing to CSV for {url}: {e}")

    def add_custom_stopwords(self, stopwords: List[str]) -> None:
        self.text_processor.expand_stopwords(set(stopwords))

    def set_word_length_limits(self, min_length: int = 3, max_length: int = 50) -> None:
        self.text_processor.set_word_length_limits(min_length, max_length)

    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        if not text:
            return {
                "total_unique_words": 0,
                "total_word_count": 0,
                "top_10_words": [],
                "average_word_length": 0,
            }

        word_freqs = self.count_word_frequency(text)
        top_words = self.text_processor.get_top_words(text, 10)
        total_word_count = sum(word_freqs.values())
        average_word_length = (
            sum(len(word) for word in word_freqs.keys()) / len(word_freqs)
            if word_freqs
            else 0
        )

        return {
            "total_unique_words": len(word_freqs),
            "total_word_count": total_word_count,
            "top_10_words": top_words,
            "average_word_length": average_word_length,
        }

    @abstractmethod
    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        pass
