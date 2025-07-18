"""
CSV writer utility for French article scraper output.

This module provides functionality to write processed article data
to daily CSV files with word frequency analysis results. Includes
duplicate detection, data validation, and error recovery features.

The CSV format is designed for vocabulary learning and text analysis,
with each row representing a word occurrence with its context and metadata.

Example usage:
    >>> from utils.csv_writer import DailyCSVWriter
    >>> writer = DailyCSVWriter(debug=True)
    >>> writer.write_article(article_data, url, frequencies, contexts)
"""

import csv
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from models import ArticleData
from config.settings import DEBUG
from utils.structured_logger import get_structured_logger

CSV_FIELDS = [
    "word",
    "context",
    "source",
    "article_date",
    "scraped_date",
    "title",
    "frequency",
]


class DailyCSVWriter:
    """Handles writing article word frequency data to daily CSV files."""

    # Class-level lock for thread safety during concurrent writes
    _write_lock = threading.Lock()

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        debug: Optional[bool] = None,
    ) -> None:
        self.logger = get_structured_logger(self.__class__.__name__)

        # Set default output directory to src/output
        if output_dir is None:
            current_dir = Path(__file__).parent
            output_dir = current_dir / ".." / "output"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.filename = self._get_filename()
        self.existing_keys = self._load_existing_keys()
        self.debug = DEBUG if debug is None else debug

    def _get_filename(self) -> Path:
        """Generate filename based on current date."""
        today = datetime.today().strftime("%Y-%m-%d")
        return self.output_dir / f"{today}.csv"

    def _load_existing_keys(self) -> set:
        """Load existing article keys to prevent duplicates."""
        existing = set()
        if self.filename.is_file():
            try:
                with open(self.filename, mode="r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        key = f"{row['title']}:{row['source']}"
                        existing.add(key)
            except Exception as e:
                self.logger.error(f"Error loading existing keys: {e}")
        return existing

    def write_article(
        self,
        parsed_data: ArticleData,
        url: str,
        word_freqs: dict,
        word_contexts: Optional[dict] = None,
    ) -> None:
        if not word_freqs or not isinstance(word_freqs, dict):
            self.logger.warning(
                f"No valid word frequencies for " f"{parsed_data.title}"
            )
            return

        # Validate word frequencies
        valid_freqs = {}
        for word, freq in word_freqs.items():
            if (
                isinstance(word, str)
                and isinstance(freq, (int, float))
                and freq > 0
                and len(word.strip()) >= 2
            ):
                valid_freqs[word.strip()] = int(freq)

        if not valid_freqs:
            self.logger.warning(
                f"No valid word frequencies after validation for "
                f"{parsed_data.title}"
            )
            return

        key = f"{parsed_data.title}:{url}"

        if key in self.existing_keys:
            if self.debug:
                self.logger.warning(
                    f"Skipping duplicate: '{parsed_data.title}' from {url}"
                )
            return

        backup_filename = self.filename.with_suffix(".csv.backup")

        # Use class-level lock to prevent concurrent file access issues
        with self._write_lock:
            file_exists = self.filename.is_file()

            try:
                if file_exists:
                    shutil.copy2(self.filename, backup_filename)

                with open(self.filename, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                    if not file_exists:
                        writer.writeheader()

                    rows_written = 0
                    for word, freq in valid_freqs.items():
                        try:
                            # Get context for this word, or empty string if not
                            # available
                            context = (
                                word_contexts.get(word, "") if word_contexts else ""
                            )

                            writer.writerow(
                                {
                                    "word": str(word)[:100],  # Truncate long words
                                    "context": str(context)[
                                        :500
                                    ],  # Truncate long contexts
                                    "source": str(url)[:500],
                                    "article_date": parsed_data.article_date,
                                    "scraped_date": parsed_data.date_scraped,
                                    "title": str(parsed_data.title)[
                                        :200
                                    ],  # Truncate long titles
                                    "frequency": (
                                        int(freq)
                                        if isinstance(freq, (int, float))
                                        else 1
                                    ),
                                }
                            )
                            rows_written += 1
                        except (ValueError, TypeError) as e:
                            self.logger.warning(f"Skipping invalid word '{word}': {e}")

                if self.debug:
                    self.logger.info(
                        f"Wrote {rows_written} word frequencies for "
                        f"'{parsed_data.title}'"
                    )
                self.existing_keys.add(key)

                if backup_filename.exists():
                    backup_filename.unlink()

            except PermissionError:
                self.logger.error(f"Permission denied writing to {self.filename}")
            except OSError as e:
                self.logger.error(f"File system error writing CSV: {e}")
                if backup_filename.exists():
                    shutil.move(str(backup_filename), str(self.filename))
                    self.logger.info("Restored backup file")
            except Exception as e:
                self.logger.error(
                    f"Error writing '{parsed_data.title}' to CSV: " f"{e}"
                )
                if backup_filename.exists():
                    shutil.move(str(backup_filename), str(self.filename))


# Alias for backward compatibility with tests
CSVWriter = DailyCSVWriter
