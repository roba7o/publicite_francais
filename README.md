# French Article Scraper

A Python-based web scraping system designed to extract and analyze French news articles from multiple sources. The system scrapes articles, performs text analysis, and generates word frequency reports in CSV format.

## Features

- **Multi-source scraping**: Supports multiple French news websites
- **Word frequency analysis**: Extracts and analyzes word frequencies from articles
- **Offline mode**: Test and develop using local HTML files
- **Configurable processing**: Site-specific text processing rules
- **CSV output**: Daily CSV files with word frequency data
- **Duplicate prevention**: Avoids processing the same article multiple times

## Supported News Sources

- **Slate.fr** - French news and opinion website
- **FranceInfo.fr** - French public news service
- **TF1 Info** - TF1 television news website
- **La Dépêche** - Regional French newspaper

## Project Structure

```
src/
├── article_scrapers/
│   ├── config/                 # Configuration files
│   │   ├── settings.py         # Global settings (DEBUG, OFFLINE)
│   │   ├── text_processing_config.py  # Site-specific text processing rules
│   │   └── website_parser_scrapers_config.py  # Scraper/parser configurations
│   ├── core/
│   │   └── processor.py        # Main processing orchestration
│   ├── parsers/                # Article content extractors
│   │   ├── base_parser.py      # Abstract base parser
│   │   ├── slate_fr_parser.py  # Slate.fr specific parser
│   │   ├── france_info_parser.py
│   │   ├── tf1_info_parser.py
│   │   └── ladepeche_fr_parser.py
│   ├── scrapers/               # URL extractors
│   │   ├── slate_fr_scraper.py
│   │   ├── france_info_scraper.py
│   │   ├── tf1_info_scraper.py
│   │   └── ladepeche_fr_scraper.py
│   ├── test_data/              # Test HTML files
│   │   ├── raw_url_soup/       # Downloaded test articles
│   │   └── test_output/        # Offline mode output
│   ├── utils/                  # Utility modules
│   │   ├── csv_writer.py       # CSV output handling
│   │   ├── french_text_processor.py  # Text processing utilities
│   │   ├── logger.py           # Logging utilities
│   │   └── logging_config.py   # Logging configuration
│   └── main.py                 # Main entry point
├── output/                     # Live mode output directory
└── requirements.txt            # Python dependencies
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd publicite_francais
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Live Mode (Default)

To scrape live websites:

1. **Configure settings** in `src/article_scrapers/config/settings.py`:
   ```python
   DEBUG = False
   OFFLINE = False
   ```

2. **Run the scraper**:
   ```bash
   cd src
   python -m article_scrapers.main
   ```

3. **Check results** in `output/YYYY-MM-DD.csv`

### Offline Mode (Testing)

To use local test files:

1. **Set offline mode** in `src/article_scrapers/config/settings.py`:
   ```python
   DEBUG = False
   OFFLINE = True
   ```

2. **Run the scraper**:
   ```bash
   cd src
   python -m article_scrapers.main
   ```

3. **Check results** in `src/article_scrapers/test_data/test_output/YYYY-MM-DD.csv`

### Adding Test Data

Use the provided HTML downloader to create test data:

```bash
cd src/article_scrapers/test_data/raw_url_soup
python html_downloader.py
```

This will download sample articles from each news source for offline testing.

## Configuration

### Global Settings (`settings.py`)

- `DEBUG`: Enable debug logging
- `OFFLINE`: Switch between live and offline modes

### Site-Specific Configuration (`text_processing_config.py`)

Each news source can have custom text processing rules:

```python
SITE_CONFIGS = {
    "slate.fr": {
        "additional_stopwords": ["slate", "article", "lire"],
        "min_word_frequency": 2,
        "min_word_length": 4,
        "max_word_length": 30,
    },
    # ... other sites
}
```

### Scraper Configuration (`website_parser_scrapers_config.py`)

Configure which sources to process:

```python
SCRAPER_CONFIGS = [
    ScraperConfig(
        name="Slate.fr",
        enabled=True,
        scraper_class="article_scrapers.scrapers.slate_fr_scraper.SlateFrURLScraper",
        parser_class="article_scrapers.parsers.slate_fr_parser.SlateFrArticleParser",
        scraper_kwargs={"debug": True},
    ),
    # ... other sources
]
```

## Output Format

The system generates CSV files with the following columns:

- `word`: The analyzed word
- `source`: Article URL or filename
- `article_date`: Publication date of the article
- `scraped_date`: Date when the article was scraped
- `title`: Article title
- `frequency`: Number of times the word appears in the article

## Adding New Sources

To add a new news source:

1. **Create a scraper** in `scrapers/`:
   ```python
   class NewSourceURLScraper:
       def get_article_urls(self):
           # Extract article URLs from homepage
           pass
   ```

2. **Create a parser** in `parsers/`:
   ```python
   class NewSourceArticleParser(BaseParser):
       def parse_article(self, soup):
           # Extract article content and metadata
           pass
   ```

3. **Add configuration** in `website_parser_scrapers_config.py`

4. **Add text processing rules** in `text_processing_config.py`

## Performance Optimizations

- **Reduced stopwords**: Essential French stopwords only for faster processing
- **Efficient text processing**: Optimized regex patterns and string operations
- **Duplicate prevention**: Tracks processed articles to avoid re-processing
- **Rate limiting**: Built-in delays between requests to be respectful to servers

## Error Handling

The system includes comprehensive error handling:

- Network request failures
- HTML parsing errors
- File I/O errors
- Configuration errors
- Graceful degradation when sources are unavailable

## Logging

The system provides detailed logging at different levels:

- **INFO**: Processing progress and results
- **WARNING**: Non-critical issues (missing test files, duplicates)
- **ERROR**: Critical failures that prevent processing

## Dependencies

- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `lxml`: XML/HTML parser backend
- Standard library modules: `csv`, `os`, `datetime`, `logging`, etc.

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here] 