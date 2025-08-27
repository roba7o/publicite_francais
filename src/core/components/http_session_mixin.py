"""
HTTP session management mixin for web scraping components.

This mixin provides shared HTTP session functionality including:
- Connection pooling and keep-alive
- Retry logic with exponential backoff
- Consistent headers across all web requests
- Request timeout handling
- Session lifecycle management

Used by both URL collectors and soup validators to eliminate code duplication.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.environment import FETCH_TIMEOUT


class HTTPSessionMixin:
    """
    Mixin class providing shared HTTP session management.

    Provides a shared session with connection pooling, retry logic,
    and consistent headers for all web scraping components.
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
        self, url: str, method: str = "GET", timeout: int = None, **kwargs
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

    def get_with_session(
        self, url: str, timeout: int = None, **kwargs
    ) -> requests.Response:
        """
        Convenience method for GET requests.

        Args:
            url: URL to get
            timeout: Request timeout in seconds
            **kwargs: Additional arguments passed to requests.get

        Returns:
            requests.Response: HTTP response object
        """
        return self.make_request(url, method="GET", timeout=timeout, **kwargs)

    @classmethod
    def close_session(cls):
        """Close the shared session and cleanup resources."""
        if cls._session is not None:
            cls._session.close()
            cls._session = None
