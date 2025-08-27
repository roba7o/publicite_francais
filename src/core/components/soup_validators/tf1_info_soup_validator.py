"""
Pure ELT TF1 Info parser for raw HTML storage.

Handles TF1 Info domain-specific HTML structure identification
but stores only raw HTML. All content extraction happens in dbt.
"""

import time

import requests
from bs4 import BeautifulSoup

from core.components.soup_validators.base_soup_validator import BaseSoupValidator
from database.models import RawArticle


class tf1infoSoupValidator(BaseSoupValidator):
    """
    Pure ELT parser for TF1 Info articles.
    Responsibility: Identify valid TF1 Info articles and store raw HTML.
    Domain logic: Understands TF1 Info HTML structure for validation.
    No text processing - that's handled by dbt downstream.
    """

    def __init__(self, site_name: str, debug: bool = False) -> None:
        """
        Initialize TF1 Info parser.

        Args:
            site_name: Name of the source (should be "TF1 Info")
            debug: Enable debug logging (default: False)
        """
        super().__init__(site_domain="tf1info.fr", site_name=site_name)
        self.debug = debug

    def get_soup_from_url(self, url: str, max_retries: int = 3) -> BeautifulSoup | None:
        """
        Override base method to bypass TF1Info anti-bot protection.
        TF1Info has sophisticated anti-bot protection that returns truncated
        content. Use the same bypass technique as the URL collector.
        """
        from config.environment import TEST_MODE

        if TEST_MODE:
            self.logger.warning("URL fetch attempted in offline mode")
            return None

        for attempt in range(max_retries):
            try:
                # Create a fresh session for each request to avoid tracking
                session = requests.Session()

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                    # Don't specify Accept-Encoding to let requests handle compression automatically
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }

                # Add small delay to mimic human behavior
                time.sleep(1)

                response = session.get(
                    url, headers=headers, timeout=15, allow_redirects=True
                )
                response.raise_for_status()

                # Close session to avoid tracking
                session.close()

                if len(response.content) < 100:
                    self.logger.warning(
                        f"Response content too short: {len(response.content)} bytes"
                    )
                    continue

                return self.parse_html_fast(response.content)

            except requests.exceptions.RequestException as e:
                self.logger.warning(
                    f"URL fetch failed (attempt {attempt + 1}): {str(e)}"
                )

            if attempt < max_retries - 1:
                time.sleep(1 + attempt)

        self.logger.error(f"URL fetch failed after {max_retries} retries")
        return None

    def validate_and_extract(self, soup: BeautifulSoup, url: str) -> RawArticle | None:
        """
        Validate TF1 Info article structure and store raw HTML.

        Domain-specific logic:
        - Checks for content div with article-body, content-body, or main-content classes
        - Falls back to article tag (TF1 Info structure variations)
        - Validates basic article structure exists
        - Stores complete HTML for dbt processing

        Args:
            soup: BeautifulSoup object of TF1 Info article page
            url: Article URL

        Returns:
            RawArticle with raw HTML or None if not a valid article
        """
        try:
            # Enhanced validation: Check URL domain using tldextract
            if not self.validate_url_domain(url, "tf1info.fr"):
                self.logger.warning(
                    "URL domain validation failed",
                    extra_data={
                        "url": url,
                        "expected_domain": "tf1info.fr",
                        "site": "tf1info.fr",
                    },
                )
                return None
            # Domain-specific validation: TF1 Info uses specific class structure
            # Check for TF1Info title structure
            title_wrapper = soup.select(".ArticleHeaderTitle__Wrapper h1")
            if not title_wrapper:
                self.logger.warning(
                    "No TF1 Info title structure found (.ArticleHeaderTitle__Wrapper h1)",
                    extra_data={"url": url, "site": "tf1info.fr"},
                )
                return None

            # Check for TF1Info content structure
            content_elements = soup.select(".ArticleChapo__Point")
            if not content_elements:
                self.logger.warning(
                    "No TF1 Info content structure found (.ArticleChapo__Point)",
                    extra_data={"url": url, "site": "tf1info.fr"},
                )
                return None

            # Store raw HTML - let dbt handle all content extraction
            return RawArticle(
                url=url,
                raw_html=str(soup),  # Complete HTML including all metadata
                site="tf1info.fr",
            )

        except Exception as e:
            self.logger.error(
                f"Error validating TF1 Info article structure: {e}",
                extra_data={"url": url, "site": "tf1info.fr"},
            )
            return None
