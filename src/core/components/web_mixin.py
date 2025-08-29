"""
Web processing mixin with lxml fast parsing and tldextract domain validation.

This mixin extends the HTTPSessionMixin to provide:
- Fast HTML parsing using lxml (3x speed improvement)
- Domain validation using tldextract
- URL canonicalization (handling www, mobile, amp subdomains)

Used by URL collectors and soup validators for improved performance and robustness.
"""

from urllib.parse import urlparse

import requests
import tldextract
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from tldextract import ExtractResult
from urllib3.util.retry import Retry

from config.environment import FETCH_TIMEOUT


class WebMixin:
    """
    Web processing mixin with HTTP session management and HTML parsing.

    Provides:
    - HTTP session management with connection pooling and retry logic
    - Fast HTML parsing using lxml (3x speed improvement)
    - Domain validation using tldextract
    - URL canonicalization (handling www, mobile, amp subdomains)
    """

    # Class-level shared session for all web scraping components
    _session = None

    @classmethod
    def get_session(cls):
        """
        Get or create shared HTTP session with connection pooling.

        Returns:
            requests.Session: Configured session with retry logic and pooling
        """
        if cls._session is None:
            cls._session = requests.Session()

            # Configure retry strategy
            retry_strategy = Retry(
                total=3,  # Total number of retries
                backoff_factor=1,  # Delay between retries (1s, 2s, 4s)
                status_forcelist=[429, 500, 502, 503, 504],  # HTTP codes to retry
                raise_on_status=False,  # Don't raise exception on retry exhaustion
            )

            # Configure HTTP adapter with connection pooling
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,  # Number of connection pools
                pool_maxsize=20,  # Max connections per pool
                pool_block=False,  # Don't block if pool is full
            )

            # Mount adapters for HTTP and HTTPS
            cls._session.mount("http://", adapter)
            cls._session.mount("https://", adapter)

            # Set default headers
            cls._session.headers.update(cls._get_default_headers())

        return cls._session

    @classmethod
    def _get_default_headers(cls) -> dict[str, str]:
        """
        Get default HTTP headers for web scraping.

        Returns:
            dict: Default headers including User-Agent and Accept headers
        """
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",  # Do Not Track
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def make_request(
        self,
        url: str,
        method: str = "GET",
        timeout: int | None = None,
        **kwargs,
    ) -> requests.Response:
        """
        Make HTTP request using shared session.

        Args:
            url: URL to request
            method: HTTP method (GET, POST, etc.)
            timeout: Request timeout in seconds
            **kwargs: Additional arguments passed to requests

        Returns:
            requests.Response: HTTP response object

        Raises:
            requests.RequestException: On request failure
        """
        if timeout is None:
            timeout = FETCH_TIMEOUT

        session = self.get_session()

        if method.upper() == "GET":
            return session.get(url, timeout=timeout, **kwargs)
        elif method.upper() == "POST":
            return session.post(url, timeout=timeout, **kwargs)
        else:
            return session.request(method, url, timeout=timeout, **kwargs)

    @classmethod
    def close_session(cls):
        """Close the shared session and cleanup resources."""
        if cls._session is not None:
            cls._session.close()
            cls._session = None

    def _extract_domain_parts(self, url: str) -> ExtractResult | None:
        """Extract domain components with error handling."""
        try:
            return tldextract.extract(url)
        except Exception:
            return None

    def _build_registered_domain(self, extracted) -> str:
        """Build registered domain string consistently."""
        return f"{extracted.domain}.{extracted.suffix}"

    def parse_html_fast(self, content: bytes) -> BeautifulSoup:
        """Parse HTML content using lxml parser for 3x speed improvement."""
        return BeautifulSoup(content, "lxml")

    def validate_url_domain(self, url: str, expected_domain: str) -> bool:
        """checks if url really belongs to expected domain"""
        url_extracted = self._extract_domain_parts(url)
        expected_extracted = self._extract_domain_parts(f"https://{expected_domain}")

        if not url_extracted or not expected_extracted:
            return False

        url_registered = self._build_registered_domain(url_extracted)
        expected_registered = self._build_registered_domain(expected_extracted)

        return url_registered == expected_registered

    def canonicalize_url(self, url: str) -> str:
        """
        Convert URL to canonical form by removing mobile/amp subdomains.

        Converts:
        - https://m.slate.fr/article -> https://slate.fr/article
        - https://amp.franceinfo.fr/page -> https://franceinfo.fr/page

        Args:
            url: URL to canonicalize

        Returns:
            Canonical URL without mobile/amp subdomains
        """
        extracted = self._extract_domain_parts(url)
        if not extracted:
            return url

        parsed = urlparse(url)

        # Remove mobile/amp subdomains
        if extracted.subdomain in ["m", "mobile", "amp", "www"]:
            canonical_domain = self._build_registered_domain(extracted)
            return f"{parsed.scheme}://{canonical_domain}{parsed.path}{parsed.query and '?' + parsed.query or ''}"

        return url

