"""
Pure ELT Slate.fr soup validator for raw HTML storage.

Handles Slate.fr domain-specific HTML structure validation
but stores only raw HTML. All content extraction happens downstream.
"""

from bs4 import BeautifulSoup, Tag

from core.components.soup_validators.base_soup_validator import BaseSoupValidator
from database.models import RawArticle


class SlateFrSoupValidator(BaseSoupValidator):
    """
    Pure ELT soup validator for Slate.fr articles.
    Responsibility: Validate Slate.fr articles and store raw HTML.
    Domain logic: Understands Slate.fr HTML structure for validation.
    No text processing - that's handled by downstream processing.
    """

    def __init__(self, site_name: str, debug: bool = False) -> None:
        """
        Initialize Slate.fr soup validator.

        Args:
            site_name: Name of the source (should be "Slate.fr")
            debug: Enable debug logging (default: False)
        """
        super().__init__(site_domain="slate.fr", site_name=site_name)
        self.debug = debug

    def validate_and_extract(self, soup: BeautifulSoup, url: str) -> RawArticle | None:
        """
        Validate Slate.fr article structure and store raw HTML.

        Domain-specific logic:
        - Validates URL belongs to slate.fr domain using tldextract
        - Checks for article tag (Slate.fr uses <article> wrapper)
        - Validates basic structure exists
        - Stores complete HTML for downstream processing

        Args:
            soup: BeautifulSoup object of Slate.fr article page
            url: Article URL

        Returns:
            RawArticle with raw HTML or None if not a valid article
        """
        try:
            # Enhanced validation: Check URL domain using tldextract
            if not self._validate_domain_and_log(url, "slate.fr"):
                return None
            # Domain-specific validation: Slate.fr articles use <article> tag
            article_tag = soup.find("article")
            if not article_tag or not isinstance(article_tag, Tag):
                self.logger.warning(
                    "No article tag found - not a valid Slate.fr article"
                )
                return None

            # Additional validation: Check for title structure
            if not self._validate_title_structure(soup, url):
                return None

            # Store raw HTML - let downstream processing handle all content extraction
            return RawArticle(
                url=url,
                raw_html=str(soup),  # Complete HTML including all metadata
                site="slate.fr",
            )

        except Exception as e:
            self.logger.error(f"Error validating Slate.fr article structure: {e}")
            return None
