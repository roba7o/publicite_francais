"""
Enhanced web processing mixin with lxml fast parsing and tldextract domain validation.

This mixin extends the HTTPSessionMixin to provide:
- Fast HTML parsing using lxml (3x speed improvement)
- Domain validation using tldextract
- URL canonicalization (handling www, mobile, amp subdomains)
- Enhanced link extraction and validation

Used by URL collectors and soup validators for improved performance and robustness.
"""

from urllib.parse import urljoin, urlparse

import tldextract
from bs4 import BeautifulSoup

from core.components.http_session_mixin import HTTPSessionMixin


class EnhancedWebMixin(HTTPSessionMixin):
    """
    Enhanced web processing mixin with fast parsing and domain validation.

    Combines HTTPSessionMixin with lxml parsing and tldextract domain handling
    for improved performance and URL validation capabilities.
    """

    def parse_html_fast(self, content: bytes) -> BeautifulSoup:
        """
        Parse HTML content using lxml parser for 3x speed improvement.

        Args:
            content: Raw HTML content as bytes

        Returns:
            BeautifulSoup object with lxml parser backend
        """
        return BeautifulSoup(content, "lxml")

    def validate_url_domain(self, url: str, expected_domain: str) -> bool:
        """
        Validate URL matches expected domain using tldextract.

        Handles subdomains (www, m, mobile, amp) by comparing registered domains.

        Args:
            url: Full URL to validate
            expected_domain: Expected domain (e.g., "slate.fr")

        Returns:
            True if URL belongs to expected domain, False otherwise
        """
        try:
            url_extracted = tldextract.extract(url)
            expected_extracted = tldextract.extract(f"https://{expected_domain}")

            # Compare registered domains (domain.suffix)
            url_registered = f"{url_extracted.domain}.{url_extracted.suffix}"
            expected_registered = (
                f"{expected_extracted.domain}.{expected_extracted.suffix}"
            )

            return url_registered == expected_registered
        except Exception:
            # If extraction fails, assume invalid
            return False

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
        try:
            extracted = tldextract.extract(url)
            parsed = urlparse(url)

            # Remove mobile/amp subdomains
            if extracted.subdomain in ["m", "mobile", "amp", "www"]:
                canonical_domain = f"{extracted.domain}.{extracted.suffix}"
                return f"{parsed.scheme}://{canonical_domain}{parsed.path}{parsed.query and '?' + parsed.query or ''}"

            return url
        except Exception:
            # If processing fails, return original URL
            return url

    def extract_domain_info(self, url: str) -> dict:
        """
        Extract detailed domain information using tldextract.

        Args:
            url: URL to analyze

        Returns:
            Dictionary with domain components:
            - subdomain: www, m, etc.
            - domain: main domain name
            - suffix: .com, .fr, etc.
            - registered_domain: domain.suffix
        """
        try:
            extracted = tldextract.extract(url)
            return {
                "subdomain": extracted.subdomain,
                "domain": extracted.domain,
                "suffix": extracted.suffix,
                "registered_domain": f"{extracted.domain}.{extracted.suffix}",
                "full_domain": f"{extracted.subdomain}.{extracted.domain}.{extracted.suffix}"
                if extracted.subdomain
                else f"{extracted.domain}.{extracted.suffix}",
            }
        except Exception:
            return {
                "subdomain": "",
                "domain": "",
                "suffix": "",
                "registered_domain": "",
                "full_domain": "",
            }

    def filter_same_domain_links(self, links: list[str], base_url: str) -> list[str]:
        """
        Filter links to only include those from the same registered domain.

        Args:
            links: List of URLs to filter
            base_url: Base URL to compare domains against

        Returns:
            Filtered list containing only same-domain links
        """
        try:
            base_extracted = tldextract.extract(base_url)
            base_registered = f"{base_extracted.domain}.{base_extracted.suffix}"

            same_domain_links = []

            for link in links:
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, link)

                if self.validate_url_domain(full_url, base_registered):
                    canonical_url = self.canonicalize_url(full_url)
                    same_domain_links.append(canonical_url)

            # Remove duplicates while preserving order
            seen = set()
            filtered_links = []
            for link in same_domain_links:
                if link not in seen:
                    seen.add(link)
                    filtered_links.append(link)

            return filtered_links
        except Exception:
            # If filtering fails, return original links
            return links

    def get_with_session_enhanced(
        self,
        url: str,
        timeout: int | None = None,
        **kwargs,
    ) -> tuple[bytes, str]:
        """
        Enhanced GET request that returns content and canonical URL.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            **kwargs: Additional arguments passed to requests

        Returns:
            Tuple of (response_content, canonical_url)

        Raises:
            requests.RequestException: On request failure
        """
        if timeout is None:
            response = self.get_with_session(url, **kwargs)
        else:
            response = self.get_with_session(url, timeout=timeout, **kwargs)
        canonical_url = self.canonicalize_url(response.url)
        return response.content, canonical_url
