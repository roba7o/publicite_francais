# article_scrapers/parsers/base_parser.py

"""
Base class for web article parsers.

This module provides a foundational class `BaseParser` with common
functionality for fetching, parsing, and processing text from web articles.
It includes methods for fetching content from URLs or local files,
applying site-specific configurations, and integrating with a text processor.
"""

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


# Define a default configuration for sites not explicitly listed
DEFAULT_SITE_CONFIG = {
    'min_word_frequency': 1,
    'min_word_length': 3,
    'max_word_length': 50,
    'additional_stopwords': []
}


class BaseParser(ABC):
    """
    Abstract base class for article parsers.

    Provides common functionalities for fetching HTML, parsing content into
    a BeautifulSoup object, managing site-specific configurations,
    and processing text with a FrenchTextProcessor.
    """

    HEADERS = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/58.0.3029.110 Safari/537.3')
    }

    def __init__(self, site_domain: str, debug: Optional[bool] = None, delay: float = 1.0):
        """
        Initializes the BaseParser.

        Args:
            site_domain (str): The domain of the site being parsed (e.g., "franceinfo.fr").
            debug (Optional[bool]): If True, enables debug logging. Defaults to the global DEBUG setting.
            delay (float): Delay in seconds between HTTP requests to be polite. Defaults to 1.0.
        """
        self.logger = get_logger(self.__class__.__name__)

        if not site_domain:
            self.logger.warning("No site_domain provided, falling back to default configuration.")

        self.site_domain = site_domain
        self.debug = debug if debug is not None else DEBUG
        self.delay = delay
        self.csv_writer = DailyCSVWriter(debug=self.debug) # Pass debug flag to CSVWriter

        # Load site-specific configuration or default
        self.config = self._load_site_config(site_domain)

        # Initialize French text processor with initial configuration
        self.text_processor = FrenchTextProcessor()
        self.min_word_frequency = self.config['min_word_frequency']
        self._apply_text_processor_config()

        self.logger.info(f"Initialized parser for domain: {self.site_domain}")
        if self.debug:
            self.logger.debug(f"Parser debug mode: {self.debug}, Request delay: {self.delay}s")


    def _load_site_config(self, site_domain: str) -> Dict[str, Any]:
        """
        Loads configuration for the specific site from SITE_CONFIGS.

        Args:
            site_domain (str): The domain of the site.

        Returns:
            Dict[str, Any]: The configuration dictionary for the site.
        """
        config = SITE_CONFIGS.get(site_domain, DEFAULT_SITE_CONFIG)
        self.logger.debug(f"Loaded config for {site_domain}: {config}")
        return config

    def _apply_text_processor_config(self) -> None:
        """
        Applies site-specific configuration to the text processor.
        This includes stopwords and word length limits.
        """
        # Add site-specific stopwords
        additional_stopwords = self.config.get('additional_stopwords')
        if additional_stopwords:
            self.text_processor.expand_stopwords(set(additional_stopwords))
            self.logger.debug(f"Added {len(additional_stopwords)} custom stopwords.")

        # Set word length limits
        min_length = self.config.get('min_word_length', DEFAULT_SITE_CONFIG['min_word_length'])
        max_length = self.config.get('max_word_length', DEFAULT_SITE_CONFIG['max_word_length'])
        self.text_processor.set_word_length_limits(min_length=min_length, max_length=max_length)

        if self.debug:
            self.logger.info(f"Text processor config for {self.site_domain or 'default'}: "
                           f"min_freq={self.config['min_word_frequency']}, "
                           f"word_length={min_length}-{max_length}, "
                           f"custom_stopwords={len(additional_stopwords) if additional_stopwords else 0}")

    def get_soup_from_url(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetches content from a URL and returns a BeautifulSoup object.

        Args:
            url (str): The URL to fetch.

        Returns:
            Optional[BeautifulSoup]: A BeautifulSoup object if successful, else None.
        """
        self.logger.info(f"Fetching URL: {url}...")
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10) # Added timeout
            time.sleep(self.delay)  # Politeness delay
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

            self.logger.info(f"Successfully fetched URL: {url} (Status: {response.status_code})")
            return BeautifulSoup(response.content, 'html.parser')

        except requests.exceptions.Timeout as e:
            self.logger.error(f"Timeout fetching URL: {url} | Error: {e}")
            return None
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error fetching URL: {url} | Status Code: {e.response.status_code} | Error: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error fetching URL: {url} | Error: {e}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"An unexpected request error occurred for URL: {url} | Error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while getting soup from URL: {url} | Error: {e}", exc_info=True)
            return None

    def get_soup_from_localfile(self, file_name: str) -> Optional[BeautifulSoup]:
        """
        Reads content from a local HTML file and returns a BeautifulSoup object.
        Primarily used for testing purposes.

        Args:
            file_name (str): The name of the local HTML file in the 'test_data' directory.

        Returns:
            Optional[BeautifulSoup]: A BeautifulSoup object if successful, else None.
        """
        # Assumes test_data is parallel to article_scrapers (or in its parent)
        # Adjust base_dir calculation if your project structure differs
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root_dir = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
        test_file_path = os.path.join(project_root_dir, "test_data", file_name)

        if not os.path.exists(test_file_path):
            self.logger.error(f"Test file not found: {test_file_path}")
            return None

        try:
            with open(test_file_path, "r", encoding="utf-8") as f:
                self.logger.debug(f"Loading local file for parsing: {test_file_path}")
                return BeautifulSoup(f.read(), 'html.parser')
        except FileNotFoundError:
            self.logger.error(f"File not found during local file read: {test_file_path}")
            return None
        except IOError as e:
            self.logger.error(f"I/O error reading local file: {test_file_path} | Error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to read local file: {test_file_path} | Error: {e}", exc_info=True)
            return None

    def count_word_frequency(self, text: str) -> Dict[str, int]:
        """
        Counts word frequencies in the given text using the configured text processor.

        Args:
            text (str): The input text.

        Returns:
            Dict[str, int]: A dictionary where keys are words and values are their frequencies.
        """
        if not text:
            self.logger.warning("Attempted to count word frequency on empty text.")
            return {}

        word_frequencies = self.text_processor.count_word_frequency(text)

        if self.min_word_frequency > 1:
            word_frequencies = self.text_processor.filter_by_frequency(
                word_frequencies, self.min_word_frequency
            )

        if self.debug:
            self.logger.debug(f"Counted {len(word_frequencies)} unique words (after filtering).")

        return word_frequencies

    def to_csv(self, parsed_data: Dict[str, Any], url: str) -> None:
        """
        Writes parsed article data and word frequencies to a CSV file.

        Args:
            parsed_data (Dict[str, Any]): Dictionary containing parsed article data.
            url (str): The URL of the article.
        """
        if not parsed_data or not parsed_data.get("full_text"):
            self.logger.warning(f"No parsed data or full_text provided for CSV export for URL: {url}")
            return

        try:
            full_text = parsed_data["full_text"]
            word_freqs = self.count_word_frequency(full_text)

            if not word_freqs:
                self.logger.warning(f"No significant words found after processing for URL: {url}. Not writing to CSV.")
                return

            self.csv_writer.write_article(
                parsed_data=parsed_data,
                url=url,
                word_freqs=word_freqs
            )
            self.logger.info(f"Successfully wrote {len(word_freqs)} unique words to CSV for URL: {url}")
        except Exception as e:
            self.logger.error(f"Error writing to CSV for URL: {url} | Error: {e}", exc_info=True)

    def add_custom_stopwords(self, stopwords: List[str]) -> None:
        """
        Adds custom stopwords to the text processor.

        Args:
            stopwords (List[str]): A list of additional stopwords.
        """
        self.text_processor.expand_stopwords(set(stopwords))
        self.logger.debug(f"Added {len(stopwords)} custom stopwords.")

    def set_word_length_limits(self, min_length: int = 3, max_length: int = 50) -> None:
        """
        Sets minimum and maximum word length limits for the text processor.

        Args:
            min_length (int): Minimum word length. Defaults to 3.
            max_length (int): Maximum word length. Defaults to 50.
        """
        self.text_processor.set_word_length_limits(min_length, max_length)
        self.logger.debug(f"Set word length limits: min={min_length}, max={max_length}.")

    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        Generates and returns statistics about the processed text.

        Args:
            text (str): The text to analyze.

        Returns:
            Dict[str, Any]: A dictionary containing various text statistics.
        """
        if not text:
            return {
                'total_unique_words': 0,
                'total_word_count': 0,
                'top_10_words': [],
                'average_word_length': 0
            }

        word_freqs = self.count_word_frequency(text)
        top_words = self.text_processor.get_top_words(text, 10)
        total_word_count = sum(word_freqs.values())
        average_word_length = sum(len(word) for word in word_freqs.keys()) / len(word_freqs) if word_freqs else 0

        return {
            'total_unique_words': len(word_freqs),
            'total_word_count': total_word_count,
            'top_10_words': top_words,
            'average_word_length': average_word_length
        }

    @abstractmethod
    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Abstract method to be implemented by subclasses for specific article parsing.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the article page.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the parsed article data, or None if parsing fails.
        """
        pass