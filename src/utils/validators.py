import re
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse


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
    def validate_article_data(data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return {}

        validated = {}

        # Required fields with validation
        title = DataValidator.validate_title(data.get("title", ""))
        if not title:
            return {}  # Reject articles without valid titles
        validated["title"] = title

        full_text = data.get("full_text", "")
        if not full_text or len(full_text.strip()) < 50:
            return {}  # Reject articles with insufficient content
        validated["full_text"] = full_text.strip()

        # Optional fields with defaults
        validated["article_date"] = DataValidator.validate_date(
            data.get("article_date", "")
        )
        validated["date_scraped"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Clean and limit other fields
        for field in ["author", "category", "summary"]:
            value = data.get(field, "")
            if isinstance(value, str) and value.strip():
                validated[field] = value.strip()[:200]  # Limit length

        return validated
