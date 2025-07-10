from bs4 import BeautifulSoup
import requests
import os
import time
from article_scrapers.utils.csv_writer import DailyCSVWriter
from collections import Counter
from ..settings import DEBUG
from article_scrapers.utils.logger import get_logger

class BaseParser:
    def __init__(self, debug=None, delay=1):
        self.logger = get_logger(self.__class__.__name__)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        self.debug = debug if debug is not None else DEBUG
        self.delay = delay
        self.csv_writer = DailyCSVWriter(debug=True)

    def get_soup_from_url(self, url):
        """
        Get a BeautifulSoup object from a given URL.
        """
        if self.debug:
            self.logger.info(f"Fetching URL: {url}...")

        try:
            response = requests.get(url, headers=self.headers)
            time.sleep(self.delay)  # Politeness delay
            response.raise_for_status()
            
            self.logger.info(f"Successfully fetched URL: {url}")
            return BeautifulSoup(response.content, 'html.parser')

        except requests.exceptions.RequestException as e:
            status_code = getattr(response, 'status_code', 'N/A') if 'response' in locals() else 'N/A'
            self.logger.error(f"Failed to fetch URL: {url} | Status Code: {status_code} | Error: {e}")
            return None

    def get_soup_from_localfile(self, file_name):
        """
        Get a BeautifulSoup object from a local html file -> for testing purposes.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # root dir
        test_file_path = os.path.join(base_dir, "test_data", file_name)
        
        try:
            with open(test_file_path, "r", encoding="utf-8") as f:
                self.logger.debug(f"Loading local file for parsing: {test_file_path}")
                return BeautifulSoup(f.read(), 'html.parser')
        except Exception as e:
            self.logger.error(f"Failed to read local file: {test_file_path} | Error: {e}")
            return None

    def count_word_frequency(self, text):
        """
        Count word frequencies in text.
        """
        words = text.split()
        word_frequencies = Counter(words)
        if self.debug:
            self.logger.debug(f"Counted {len(word_frequencies)} unique words")
        return word_frequencies

    def to_csv(self, dict_content, url):
        try:
            word_freqs = self.count_word_frequency(dict_content["full_text"])
            self.csv_writer.write_article(
                parsed_data=dict_content,
                url=url,
                word_freqs=word_freqs
            )
            self.logger.info(f"Successfully wrote data to CSV for URL: {url}")
        except Exception as e:
            self.logger.error(f"Error writing to CSV for URL: {url} | Error: {e}")
