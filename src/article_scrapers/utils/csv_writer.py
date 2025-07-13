"""
CSV writer module for saving article word frequency data.

This module handles the creation and management of daily CSV files containing
word frequency analysis from scraped articles.
"""

import csv
import os
from datetime import datetime

from ..config.settings import DEBUG
from article_scrapers.utils.logger import get_logger

# CSV column headers
CSV_FIELDS = ["word", "source", "article_date", "scraped_date", "title", "frequency"]


class DailyCSVWriter:
    """Handles writing article word frequency data to daily CSV files."""

    def __init__(self, output_dir="output", debug=None):
        """
        Initialize the CSV writer.
        
        Args:
            output_dir: Directory to save CSV files
            debug: Override debug setting
        """
        self.logger = get_logger(self.__class__.__name__)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.filename = self._get_filename()
        self.existing_keys = self._load_existing_keys()
        self.debug = DEBUG if debug is None else debug

    def _get_filename(self) -> str:
        """Generate filename based on current date."""
        today = datetime.today().strftime("%Y-%m-%d")
        return os.path.join(self.output_dir, f"{today}.csv")

    def _load_existing_keys(self) -> set:
        """Load existing article keys to prevent duplicates."""
        existing = set()
        if os.path.isfile(self.filename):
            try:
                with open(self.filename, mode="r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        key = f"{row['title']}:{row['source']}"
                        existing.add(key)
            except Exception as e:
                self.logger.error(f"Error loading existing keys: {e}")
        return existing

    def write_article(self, parsed_data: dict, url: str, word_freqs: dict) -> None:
        """
        Write article word frequencies to CSV file.
        
        Args:
            parsed_data: Article metadata (title, date, etc.)
            url: Article URL or filename
            word_freqs: Dictionary of word frequencies
        """
        key = f"{parsed_data['title']}:{url}"

        # Skip if article already processed
        if key in self.existing_keys:
            if self.debug:
                self.logger.warning(
                    f"Skipping duplicate article: '{parsed_data['title']}' from {url}"
                )
            return

        file_exists = os.path.isfile(self.filename)

        try:
            with open(self.filename, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                if not file_exists:
                    writer.writeheader()
                
                # Write each word frequency as a separate row
                for word, freq in word_freqs.items():
                    writer.writerow(
                        {
                            "word": word,
                            "source": url,
                            "article_date": parsed_data["article_date"],
                            "scraped_date": parsed_data["date_scraped"],
                            "title": parsed_data["title"],
                            "frequency": freq,
                        }
                    )
            
            if self.debug:
                self.logger.info(
                    f"Article '{parsed_data['title']}' written to {self.filename}"
                )
            self.existing_keys.add(key)
        except Exception as e:
            self.logger.error(
                f"Error writing article '{parsed_data['title']}' to CSV: {e}"
            )
