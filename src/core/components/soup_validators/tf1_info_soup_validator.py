"""
Pure ELT TF1 Info parser for raw HTML storage.

Handles TF1 Info domain-specific HTML structure identification
but stores only raw HTML. All content extraction happens in dbt.
"""

import re

from bs4 import BeautifulSoup, Tag

from database.models import RawArticle
from core.components.soup_validators.base_soup_validator import BaseSoupValidator


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
            # Domain-specific validation: TF1 Info uses various content containers
            content_div = soup.find(
                "div", class_=re.compile(r"article-body|content-body|main-content")
            )
            if not content_div:
                content_div = soup.find("article")
                
            if not content_div or not isinstance(content_div, Tag):
                self.logger.warning(
                    "No content div or article tag found - not a valid TF1 Info article",
                    extra_data={"url": url, "site": "tf1info.fr"}
                )
                return None

            # Additional validation: Check for title structure
            title_tag = soup.find("h1")
            if not title_tag or not isinstance(title_tag, Tag):
                self.logger.warning(
                    "No h1 tag found - possibly not an article page",
                    extra_data={"url": url, "site": "tf1info.fr"}
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
                exc_info=True
            )
            return None