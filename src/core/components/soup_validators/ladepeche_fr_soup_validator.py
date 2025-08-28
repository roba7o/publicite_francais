"""
Pure ELT Ladepeche.fr parser for raw HTML storage.

Handles Ladepeche.fr domain-specific HTML structure identification
but stores only raw HTML. All content extraction happens in dbt.
"""

from bs4 import BeautifulSoup, Tag

from core.components.soup_validators.base_soup_validator import BaseSoupValidator
from database.models import RawArticle


class LadepecheFrSoupValidator(BaseSoupValidator):
    """
    Pure ELT parser for Ladepeche.fr articles.
    Responsibility: Identify valid Ladepeche.fr articles and store raw HTML.
    Domain logic: Understands Ladepeche.fr HTML structure for validation.
    No text processing - that's handled by dbt downstream.
    """

    def __init__(self, site_name: str, debug: bool = False) -> None:
        """
        Initialize Ladepeche.fr parser.

        Args:
            site_name: Name of the source (should be "Ladepeche.fr")
            debug: Enable debug logging (default: False)
        """
        super().__init__(site_domain="ladepeche.fr", site_name=site_name)
        self.debug = debug

    def validate_and_extract(self, soup: BeautifulSoup, url: str) -> RawArticle | None:
        """
        Validate Ladepeche.fr article structure and store raw HTML.

        Domain-specific logic:
        - Checks for article content area (various patterns for Ladepeche.fr)
        - Validates basic article structure exists
        - Stores complete HTML for dbt processing

        Args:
            soup: BeautifulSoup object of Ladepeche.fr article page
            url: Article URL

        Returns:
            RawArticle with raw HTML or None if not a valid article
        """
        try:
            # Enhanced validation: Check URL domain using tldextract
            if not self.validate_url_domain(url, "ladepeche.fr"):
                self.logger.warning(
                    "URL domain validation failed",
                    extra_data={
                        "url": url,
                        "expected_domain": "ladepeche.fr",
                        "site": "ladepeche.fr",
                    },
                )
                return None
            # Domain-specific validation: Ladepeche.fr uses various content containers
            article_content_area = (
                soup.find("article")
                or soup.find("div", class_="article-content")
                or soup.find("main")
            )

            if not article_content_area or not isinstance(article_content_area, Tag):
                self.logger.warning(
                    "No article content area found - not a valid Ladepeche.fr article",
                    extra_data={"url": url, "site": "ladepeche.fr"},
                )
                return None

            # Additional validation: Check for title structure
            title_tag = soup.find("h1")
            if not title_tag or not isinstance(title_tag, Tag):
                self.logger.warning(
                    "No h1 tag found - possibly not an article page",
                    extra_data={"url": url, "site": "ladepeche.fr"},
                )
                return None

            # Store raw HTML - let dbt handle all content extraction
            return RawArticle(
                url=url,
                raw_html=str(soup),  # Complete HTML including all metadata
                site="ladepeche.fr",
            )

        except Exception as e:
            self.logger.error(
                f"Error validating Ladepeche.fr article structure: {e}",
                extra_data={"url": url, "site": "ladepeche.fr"},
            )
            return None
