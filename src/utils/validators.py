import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from models import ArticleData


class DataValidator:

    @staticmethod
    def validate_url(url: str) -> Optional[str]:
        if not url or not isinstance(url, str):
            return None

        url = url.strip()
        if len(url) < 10 or len(url) > 2000:
            return None

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return None

            if parsed.scheme not in ["http", "https"]:
                return None

            # Basic domain validation
            if not re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", parsed.netloc):
                return None

            return url
        except Exception:
            return None

    @staticmethod
    def validate_title(title: str) -> Optional[str]:
        if not title or not isinstance(title, str):
            return None

        title = title.strip()
        if len(title) < 5 or len(title) > 500:
            return None

        # Check for reasonable character composition
        if not re.search(r"[a-zA-ZàâäéèêëîïôöûüùÿçÀÂÄÉÈÊËÎÏÔÖÛÜÙŸÇ]", title):
            return None

        return title

    @staticmethod
    def validate_date(date_str: str) -> Optional[str]:
        if not date_str or not isinstance(date_str, str):
            return datetime.now().strftime("%Y-%m-%d")

        date_str = date_str.strip()

        # Try common date formats
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%d-%m-%Y",
        ]

        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # Reject dates too far in future or past
                now = datetime.now()
                if parsed_date.year < 2020 or parsed_date > now:
                    continue
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Default to today if parsing fails
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def validate_article_data(data: ArticleData) -> Optional[ArticleData]:
        """
        Validate and normalize ArticleData.

        Args:
            data: ArticleData instance to validate

        Returns:
            Validated ArticleData instance or None if invalid
        """
        if not isinstance(data, ArticleData):
            return None  # type: ignore[unreachable]

        # Required fields with validation
        title = DataValidator.validate_title(data.title)
        if not title:
            return None  # Reject articles without valid titles

        full_text = data.full_text
        if not full_text or len(full_text.strip()) < 50:
            return None  # Reject articles with insufficient content

        # Optional fields with defaults
        article_date = DataValidator.validate_date(data.article_date)
        date_scraped = data.date_scraped or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Clean and limit other fields
        author = data.author[:200] if data.author else None
        category = data.category[:200] if data.category else None
        summary = data.summary[:200] if data.summary else None

        return ArticleData(
            title=title,
            full_text=full_text.strip(),
            article_date=article_date or "",
            date_scraped=date_scraped,
            num_paragraphs=data.num_paragraphs,
            author=author,
            category=category,
            summary=summary,
        )
