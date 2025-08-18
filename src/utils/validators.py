import re
from datetime import datetime
from urllib.parse import urlparse


class DataValidator:
    @staticmethod
    def validate_url(url: str) -> str | None:
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
    def validate_title(title: str) -> str | None:
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
    def validate_date(date_str: str) -> str | None:
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

    # validate_article_data removed - never used in codebase
