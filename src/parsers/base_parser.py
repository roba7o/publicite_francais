import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

from utils.csv_writer import DailyCSVWriter
from utils.french_text_processor import FrenchTextProcessor
from config.text_processing_config import SITE_CONFIGS
from config.settings import DEBUG, OFFLINE
from utils.structured_logger import get_structured_logger

DEFAULT_SITE_CONFIG = {
    "min_word_frequency": 1,
    "min_word_length": 3,
    "max_word_length": 50,
    "additional_stopwords": [],
}


class BaseParser(ABC):
    """
    Abstract base class for all article parsers.

    This class provides the common infrastructure and utilities needed by all
    news source parsers. It handles HTTP requests, connection pooling, text
    processing, CSV output, and both live and offline modes.

    Features:
    - Shared HTTP session with connection pooling and retry logic
    - Configurable text processing with site-specific rules
    - Support for both live web scraping and offline testing
    - Word frequency analysis with French language support
    - CSV output with duplicate detection
    - Comprehensive error handling and logging

    Attributes:
        HEADERS (Dict): Standard HTTP headers for web requests
        _session (requests.Session): Shared session for connection pooling

    Subclasses must implement:
        parse_article(soup): Extract content and metadata from article HTML

    Example:
        >>> class MyParser(BaseParser):
        ...     def __init__(self):
        ...         super().__init__("example.com")
        ...     def parse_article(self, soup):
        ...         return {
        ...             "title": soup.title.text,
        ...             "full_text": soup.get_text()
        ...         }
    """

    # Standard headers for web requests
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        )
    }

    # Shared session with connection pooling
    _session = None

    @classmethod
    def get_session(cls):
        """
        Get or create a shared requests session with connection pooling.

        This method implements a singleton pattern for HTTP sessions to enable
        connection reuse across all parser instances. The session includes:
        - Automatic retry logic with exponential backoff
        - Connection pooling for improved performance
        - Standard user agent headers
        - Proper timeout and error handling

        Returns:
            requests.Session: Configured session ready for HTTP requests

        Note:
            The session is shared across all parser instances to maximize
            connection reuse and improve overall scraping performance.
        """
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
                pool_maxsize=20,  # Max connections per pool
                pool_block=False,
            )

            cls._session.mount("http://", adapter)
            cls._session.mount("https://", adapter)
            cls._session.headers.update(cls.HEADERS)

        return cls._session

    def __init__(
        self,
        site_domain: str,
        debug: Optional[bool] = None,
        delay: float = 1.0
    ):
        self.logger = get_structured_logger(self.__class__.__name__)
        self.site_domain = site_domain
        self.debug = debug if debug is not None else DEBUG
        self.delay = delay

        # CSV writer now handles output directory automatically
        self.csv_writer = DailyCSVWriter(debug=self.debug)

        self.config = SITE_CONFIGS.get(site_domain, DEFAULT_SITE_CONFIG)
        self.text_processor = FrenchTextProcessor()
        self.min_word_frequency = self.config["min_word_frequency"]

        if self.config.get("additional_stopwords"):
            self.text_processor.expand_stopwords(
                set(self.config["additional_stopwords"])
            )

        min_length = self.config.get("min_word_length", 3)
        max_length = self.config.get("max_word_length", 50)
        self.text_processor.set_word_length_limits(min_length, max_length)

    def get_soup_from_url(
        self, url: str, max_retries: int = 3
    ) -> Optional[BeautifulSoup]:
        """
        Fetch and parse HTML content from a URL with retry logic.

        Downloads content from the specified URL and parses it into a
        BeautifulSoup object. Includes comprehensive error handling,
        retry logic with exponential backoff, and various failure modes.

        Args:
            url: The URL to fetch content from
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            BeautifulSoup object of the parsed HTML, or None if failed

        Raises:
            No exceptions - all errors are caught and logged

        Note:
            - Respects self.delay for rate limiting
            - Automatically retries on timeout, connection, and server errors
            - Validates response content length to detect blocking
            - Returns None in offline mode with a warning

        Example:
            >>> parser = SomeParser("example.com")
            >>> soup = parser.get_soup_from_url("https://example.com/article")
            >>> if soup:
            ...     title = soup.find("title").text
        """
        if OFFLINE:
            self.logger.warning(
                "URL fetch attempted in offline mode",
                extra_data={
                    "url": url,
                    "mode": "offline",
                    "action": "skipped"
                },
            )
            return None

        for attempt in range(max_retries):
            try:
                session = self.get_session()
                response = session.get(url, timeout=15)
                time.sleep(self.delay)
                response.raise_for_status()

                content_length = len(response.content)
                if content_length < 100:
                    self.logger.warning(
                        "Response content too short",
                        extra_data={
                            "url": url,
                            "content_length": content_length,
                            "threshold": 100,
                            "status_code": response.status_code,
                        },
                    )
                    raise ValueError(
                        "Response too short, likely blocked or empty"
                    )

                return BeautifulSoup(response.content, "html.parser")

            except requests.exceptions.Timeout:
                self.logger.warning(
                    "URL fetch timeout",
                    extra_data={
                        "url": url,
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "error_type": "timeout",
                    },
                )
            except requests.exceptions.ConnectionError:
                self.logger.warning(
                    "URL fetch connection error",
                    extra_data={
                        "url": url,
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "error_type": "connection",
                    },
                )
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [429, 503, 502]:
                    self.logger.warning(
                        "Server error during URL fetch",
                        extra_data={
                            "url": url,
                            "status_code": e.response.status_code,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "error_type": "server_error",
                        },
                    )
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    self.logger.error(
                        "HTTP error during URL fetch",
                        extra_data={
                            "url": url,
                            "status_code": e.response.status_code,
                            "error_type": "http_error",
                        },
                    )
                    return None
            except Exception as e:
                self.logger.warning(
                    "Unexpected error during URL fetch",
                    extra_data={
                        "url": url,
                        "error": str(e),
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "error_type": "unexpected",
                    },
                    exc_info=True,
                )

            if attempt < max_retries - 1:
                time.sleep(1 + attempt)

        self.logger.error(
            "URL fetch failed after all retries",
            extra_data={
                "url": url,
                "max_retries": max_retries,
                "final_result": "failed",
            },
        )
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
        project_root_dir = os.path.abspath(
            os.path.join(current_file_dir, "..")
        )
        test_data_dir = os.path.join(
            project_root_dir, "test_data", "raw_url_soup"
        )

        # Map source names to directory names
        source_to_dir = {
            "Slate.fr": "slate_fr",
            "FranceInfo.fr": "france_info_fr",
            "TF1 Info": "tf1_fr",
            "Depeche.fr": "depeche_fr",
            "LeMonde.fr": "lemonde_fr",
        }

        dir_name = source_to_dir.get(
            source_name, source_name.lower().replace(" ", "_")
        )
        source_dir = os.path.join(test_data_dir, dir_name)

        if not os.path.exists(source_dir):
            self.logger.warning(
                "Test directory not found",
                extra_data={
                    "source_name": source_name,
                    "directory_path": source_dir,
                    "mapped_dir_name": dir_name,
                },
            )
            return []

        # Import URL mapping
        try:
            from test_data.url_mapping import URL_MAPPING
        except ImportError:
            self.logger.error(
                "URL mapping import failed",
                extra_data={
                    "module": "test_data/url_mapping.py",
                    "required_variable": "URL_MAPPING",
                    "impact": "test_mode_disabled",
                },
            )
            return []

        soup_sources = []
        try:
            for filename in os.listdir(source_dir):
                if filename.endswith((".html", ".php")):
                    file_path = os.path.join(source_dir, filename)

                    # Get original URL from mapping
                    original_url = URL_MAPPING.get(
                        filename, f"test://{filename}"
                    )

                    with open(file_path, "r", encoding="utf-8") as f:
                        soup = BeautifulSoup(f.read(), "html.parser")
                        soup_sources.append((soup, original_url))
                        self.logger.debug(
                            "Test file loaded",
                            extra_data={
                                "filename": filename,
                                "original_url": original_url,
                                "source": source_name,
                            },
                        )
        except Exception as e:
            self.logger.error(
                "Error reading test files",
                extra_data={
                    "source_directory": source_dir,
                    "source_name": source_name,
                    "error": str(e),
                },
                exc_info=True,
            )

        return soup_sources

    def count_word_frequency(self, text: str) -> Dict[str, int]:
        """
        Analyze text and return word frequency dictionary.

        Processes the input text through the French text processing pipeline
        to extract meaningful word frequencies. Includes text validation,
        cleaning, tokenization, and filtering based on configured parameters.

        Args:
            text: Raw text content to analyze

        Returns:
            Dictionary mapping words to their frequencies

        Note:
            - Applies site-specific text processing rules
            - Filters by minimum frequency if configured
            - Handles French language specifics (accents, stopwords)
            - Returns empty dict for invalid/insufficient text

        Example:
            >>> parser = SomeParser("example.com")
            >>> frequencies = parser.count_word_frequency("Le chat mange.")
            >>> # Returns {"chat": 1, "mange": 1} (stopwords filtered)
        """
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
        """
        Process article data and write word frequencies to CSV.

        Takes parsed article data, extracts word frequencies, and writes
        the results to a daily CSV file. Includes context extraction for
        each word and handles duplicate detection.

        Args:
            parsed_data: Dictionary containing article metadata and full_text
            url: Source URL or identifier for the article

        Note:
            - Automatically extracts sentence contexts for each word
            - Writes to date-stamped CSV files
            - Includes duplicate detection based on title and URL
            - Handles errors gracefully with logging
            - CSV format: word, context, source, article_date, scraped_date,
              title, frequency

        Example:
            >>> parsed = {
            ...     "title": "News Title",
            ...     "full_text": "Article content..."
            ... }
            >>> parser.to_csv(parsed, "https://example.com/article")
        """
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
                word_contexts=word_contexts,
            )
        except Exception as e:
            self.logger.error(
                "CSV writing error",
                extra_data={
                    "url": url,
                    "error": str(e),
                    "has_word_frequencies": bool(word_freqs),
                },
                exc_info=True,
            )

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
