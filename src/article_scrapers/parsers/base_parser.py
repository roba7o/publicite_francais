import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

from article_scrapers.utils.csv_writer import DailyCSVWriter
from article_scrapers.utils.french_text_processor import FrenchTextProcessor
from article_scrapers.config.text_processing_config import SITE_CONFIGS
from article_scrapers.config.settings import DEBUG, OFFLINE
from article_scrapers.utils.logger import get_logger

DEFAULT_SITE_CONFIG = {
    "min_word_frequency": 1,
    "min_word_length": 3,
    "max_word_length": 50,
    "additional_stopwords": [],
}


class BaseParser(ABC):
    """Abstract base class for all article parsers."""
    
    # Standard headers for web requests
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    
    # Shared session with connection pooling
    _session = None
    
    @classmethod
    def get_session(cls):
        """Get or create a shared requests session with connection pooling"""
        if cls._session is None:
            cls._session = requests.Session()
            
            # Configure retry strategy
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            
            # Configure HTTP adapter with connection pooling
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,  # Number of connection pools
                pool_maxsize=20,     # Max connections per pool
                pool_block=False
            )
            
            cls._session.mount("http://", adapter)
            cls._session.mount("https://", adapter)
            cls._session.headers.update(cls.HEADERS)
            
        return cls._session

    def __init__(self, site_domain: str, debug: Optional[bool] = None, delay: float = 1.0):
        self.logger = get_logger(self.__class__.__name__)
        self.site_domain = site_domain
        self.debug = debug if debug is not None else DEBUG
        self.delay = delay

        if OFFLINE:
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root_dir = os.path.abspath(os.path.join(current_file_dir, ".."))
            output_dir = os.path.join(project_root_dir, "test_data", "test_output")
        else:
            output_dir = "output"
        self.csv_writer = DailyCSVWriter(debug=self.debug, output_dir=output_dir)

        self.config = SITE_CONFIGS.get(site_domain, DEFAULT_SITE_CONFIG)
        self.text_processor = FrenchTextProcessor()
        self.min_word_frequency = self.config["min_word_frequency"]

        if self.config.get("additional_stopwords"):
            self.text_processor.expand_stopwords(set(self.config["additional_stopwords"]))

        min_length = self.config.get("min_word_length", 3)
        max_length = self.config.get("max_word_length", 50)
        self.text_processor.set_word_length_limits(min_length, max_length)

    def get_soup_from_url(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        if OFFLINE:
            self.logger.warning(f"Attempted to fetch URL in offline mode: {url}")
            return None

        for attempt in range(max_retries):
            try:
                session = self.get_session()
                response = session.get(url, timeout=15)
                time.sleep(self.delay)
                response.raise_for_status()
                
                if len(response.content) < 100:
                    raise ValueError("Response too short, likely blocked or empty")
                
                return BeautifulSoup(response.content, "html.parser")
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout fetching {url}, attempt {attempt + 1}/{max_retries}")
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error for {url}, attempt {attempt + 1}/{max_retries}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [429, 503, 502]:
                    self.logger.warning(f"Server error {e.response.status_code} for {url}, attempt {attempt + 1}/{max_retries}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"HTTP error {e.response.status_code} for {url}")
                    return None
            except Exception as e:
                self.logger.warning(f"Unexpected error fetching {url}: {e}, attempt {attempt + 1}/{max_retries}")
            
            if attempt < max_retries - 1:
                time.sleep(1 + attempt)
        
        self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None

    def get_soup_from_localfile(self, file_name: str) -> Optional[BeautifulSoup]:
        """Load HTML content from a local test file."""
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root_dir = os.path.abspath(os.path.join(current_file_dir, ".."))
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

    def get_test_sources_from_directory(
        self, source_name: str
    ) -> List[Tuple[Optional[BeautifulSoup], str]]:
        """
        Auto-discover and load test files from the test_data directory.
        
        Args:
            source_name: Name of the news source to map to directory
            
        Returns:
            List of (soup, url) tuples with original URLs
        """
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root_dir = os.path.abspath(os.path.join(current_file_dir, ".."))
        test_data_dir = os.path.join(project_root_dir, "test_data", "raw_url_soup")

        # Map source names to directory names
        source_to_dir = {
            "Slate.fr": "slate_fr",
            "FranceInfo.fr": "france_info_fr",
            "TF1 Info": "tf1_fr",
            "Depeche.fr": "depeche_fr",
            "LeMonde.fr": "lemonde_fr",
        }
        
        dir_name = source_to_dir.get(source_name, source_name.lower().replace(" ", "_"))
        source_dir = os.path.join(test_data_dir, dir_name)
        
        if not os.path.exists(source_dir):
            self.logger.warning(f"Test directory not found: {source_dir}")
            return []

        # Import URL mapping
        try:
            from article_scrapers.test_data.url_mapping import URL_MAPPING
        except ImportError:
            self.logger.error("Could not import URL_MAPPING from test_data/url_mapping.py")
            return []

        soup_sources = []
        try:
            for filename in os.listdir(source_dir):
                if filename.endswith((".html", ".php")):
                    file_path = os.path.join(source_dir, filename)
                    
                    # Get original URL from mapping
                    original_url = URL_MAPPING.get(filename, f"test://{filename}")
                    
                    with open(file_path, "r", encoding="utf-8") as f:
                        soup = BeautifulSoup(f.read(), "html.parser")
                        soup_sources.append((soup, original_url))
                        self.logger.info(f"Loaded test file: {filename} -> {original_url}")
        except Exception as e:
            self.logger.error(f"Error reading test files from {source_dir}: {e}")

        return soup_sources

    def count_word_frequency(self, text: str) -> Dict[str, int]:
        """Analyze text and return word frequency dictionary."""
        if not text:
            return {}

        word_frequencies = self.text_processor.count_word_frequency(text)

        # Filter by minimum frequency if configured
        if self.min_word_frequency > 1:
            word_frequencies = self.text_processor.filter_by_frequency(
                word_frequencies, self.min_word_frequency
            )

        return word_frequencies

    def to_csv(self, parsed_data: Dict[str, Any], url: str) -> None:
        """Process article data and write word frequencies to CSV."""
        if not parsed_data or not parsed_data.get("full_text"):
            return

        try:
            full_text = parsed_data["full_text"]
            word_freqs = self.count_word_frequency(full_text)

            if not word_freqs:
                return

            # Extract sentence contexts for each word
            word_contexts = self.text_processor.extract_sentences_with_words(
                full_text, list(word_freqs.keys())
            )

            self.csv_writer.write_article(
                parsed_data=parsed_data, 
                url=url, 
                word_freqs=word_freqs,
                word_contexts=word_contexts
            )
        except Exception as e:
            self.logger.error(f"Error writing to CSV for {url}: {e}")

    @abstractmethod
    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Abstract method that must be implemented by subclasses.
        
        Args:
            soup: BeautifulSoup object of the article page
            
        Returns:
            Dictionary with article data or None if parsing fails
        """
        pass
