"""
Pure ELT FranceInfo.fr soup validator for raw HTML storage.

Handles FranceInfo.fr domain-specific HTML structure validation
but stores only raw HTML. All content extraction happens in dbt.
"""

from bs4 import BeautifulSoup, Tag

from core.components.soup_validators.base_soup_validator import BaseSoupValidator
from database.models import RawArticle


class FranceInfoSoupValidator(BaseSoupValidator):
    """
    Pure ELT soup validator for FranceInfo.fr articles.
    Responsibility: Validate FranceInfo.fr articles and store raw HTML.
    Domain logic: Understands FranceInfo.fr HTML structure for validation.
    No text processing - that's handled by dbt downstream.
    """

    def __init__(self, site_name: str, debug: bool = False) -> None:
        """
        Initialize FranceInfo.fr soup validator.

        Args:
            site_name: Name of the source (should be "FranceInfo.fr")
            debug: Enable debug logging (default: False)
        """
        super().__init__(site_domain="franceinfo.fr", site_name=site_name)
        self.debug = debug

    def validate_and_extract(self, soup: BeautifulSoup, url: str) -> RawArticle | None:
        """
        Validate FranceInfo.fr article structure and store raw HTML.

        Domain-specific logic:
        - Checks for content div with class "c-body" (FranceInfo.fr structure)
        - Validates basic article structure exists
        - Stores complete HTML for dbt processing

        Args:
            soup: BeautifulSoup object of FranceInfo.fr article page
            url: Article URL

        Returns:
            RawArticle with raw HTML or None if not a valid article
        """
        try:
            # Enhanced validation: Check URL domain using tldextract
            if not self.validate_url_domain(url, "franceinfo.fr"):
                self.logger.warning(
                    "URL domain validation failed",
                    extra_data={
                        "url": url,
                        "expected_domain": "franceinfo.fr",
                        "site": "franceinfo.fr",
                    },
                )
                return None
            # Domain-specific validation: FranceInfo.fr uses div.c-body for content
            content_div = soup.find("div", class_="c-body")
            if not content_div or not isinstance(content_div, Tag):
                self.logger.warning(
                    "No c-body div found - not a valid FranceInfo.fr article",
                    extra_data={"url": url, "site": "franceinfo.fr"},
                )
                return None

            # Additional validation: Check for title structure
            title_tag = soup.find("h1")
            if not title_tag or not isinstance(title_tag, Tag):
                self.logger.warning(
                    "No h1 tag found - possibly not an article page",
                    extra_data={"url": url, "site": "franceinfo.fr"},
                )
                return None

            # Store raw HTML - let dbt handle all content extraction
            return RawArticle(
                url=url,
                raw_html=str(soup),  # Complete HTML including all metadata
                site="franceinfo.fr",
            )

        except Exception as e:
            self.logger.error(
                f"Error validating FranceInfo.fr article structure: {e}",
                extra_data={"url": url, "site": "franceinfo.fr"},
                exc_info=True,
            )
            return None
