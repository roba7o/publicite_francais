# csv_writer.py
import csv
import os
from datetime import datetime

CSV_FIELDS = ["word", "source", "article_date", "scraped_date", "title", "frequency"]

class DailyCSVWriter:
    def __init__(self, output_dir="output", debug=False):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.filename = self._get_filename()
        self.existing_keys = self._load_existing_keys()
        self.debug = debug

    def _get_filename(self):
        today = datetime.today().strftime('%Y-%m-%d')
        return os.path.join(self.output_dir, f"{today}.csv")

    def _load_existing_keys(self):
        existing = set()
        if os.path.isfile(self.filename):
            with open(self.filename, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = f"{row['title']}:{row['source']}"
                    existing.add(key)
        return existing

    def write_article(self, parsed_data, url, word_freqs):
        key = f"{parsed_data['title']}:{url}"
        if key in self.existing_keys:
            if self.debug:
                print(f"⚠️ Skipping duplicate: {parsed_data['title']} from {url}")
            return

        file_exists = os.path.isfile(self.filename)
        with open(self.filename, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if not file_exists:
                writer.writeheader()
            for word, freq in word_freqs.items():
                writer.writerow({
                    "word": word,
                    "source": url,
                    "article_date": parsed_data["article_date"],
                    "scraped_date": parsed_data["date_scraped"],
                    "title": parsed_data["title"],
                    "frequency": freq
                })

        if self.debug:
            print(f"✅ Article '{parsed_data['title']}' written to {self.filename}")
        self.existing_keys.add(key)
