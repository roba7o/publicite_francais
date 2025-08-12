# Adding a New News Source - Complete Workflow Guide

> [!abstract] Overview
> This document provides a step-by-step guide for adding a new French news source to the scraper system. It covers the complete workflow from initial analysis through testing and deployment, ensuring new sources integrate seamlessly with the existing architecture.

## Table of Contents
- [[#Prerequisites|Prerequisites]]
- [[#Step 1: Analyze the Target Website|Step 1: Analyze the Target Website]]
- [[#Step 2: Create the Scraper|Step 2: Create the Scraper]]
- [[#Step 3: Create the Parser|Step 3: Create the Parser]]
- [[#Step 4: Update Configuration|Step 4: Update Configuration]]
- [[#Step 5: Add Stopwords and Text Processing|Step 5: Add Stopwords and Text Processing]]
- [[#Step 6: Create Test Data|Step 6: Create Test Data]]
- [[#Step 7: Write Tests|Step 7: Write Tests]]
- [[#Step 8: Integration Testing|Step 8: Integration Testing]]
- [[#Step 9: Performance Validation|Step 9: Performance Validation]]
- [[#Step 10: Documentation Updates|Step 10: Documentation Updates]]

---

## Prerequisites

Before adding a new news source, ensure you have:

- **Understanding of the existing architecture** (see [[00-System-Architecture]])
- **Local development environment** set up and working
- **Access to the target website** for analysis and testing
- **Basic French language knowledge** for content validation
- **Familiarity with HTML/CSS selectors** for content extraction

### Tools You'll Need

```bash
# Browser developer tools for HTML inspection
# Python development environment
# Network monitoring tools (optional)
```

---

## Step 1: Analyze the Target Website

### Website Structure Analysis

> [!example] Target Website: `https://example-news.fr`

1. **Manual Homepage Inspection**
   ```
   Visit: https://example-news.fr
   - Note the overall layout and structure
   - Identify article listing areas
   - Check for consistent URL patterns
   - Examine article card structure
   ```

2. **Identify Article Containers**
   ```html
   <!-- Look for patterns like: -->
   <article class="news-item">
       <h3><a href="/article/123">Article Title</a></h3>
   </article>
   
   <!-- Or: -->
   <div class="article-card">
       <a href="/story/article-slug">Title</a>
   </div>
   ```

3. **Test CSS Selectors**
   ```javascript
   // In browser console:
   document.querySelectorAll('article.news-item a');
   document.querySelectorAll('.article-card a[href*="/article/"]');
   ```

4. **Analyze Individual Articles**
   ```
   Visit several article pages to identify:
   - Title selectors (h1, .article-title, etc.)
   - Content selectors (.article-body, .content, etc.)
   - Date selectors (time, .date, .publish-date, etc.)
   - URL patterns and consistency
   ```

### Document Your Findings

Create a file `research-notes-[source].md`:

```markdown
# Source Analysis: Example News

## Homepage Structure
- Base URL: https://example-news.fr
- Article containers: `article.news-item`
- Article links: `article.news-item h3 a`
- URL pattern: `/article/[slug]`

## Article Page Structure
- Title: `h1.article-title`
- Content: `.article-content p`
- Date: `time.publish-date[datetime]`
- Author: `.author-name`

## Special Considerations
- Rate limiting: 2-3 second delays recommended
- User agent requirements: Standard browser UA
- Potential anti-bot measures: None observed
```

---

## Step 2: Create the Scraper

### Scraper Implementation

Create `src/scrapers/example_news_scraper.py`:

```python
"""
URL scraper for Example News (https://example-news.fr).

This scraper extracts article URLs from the Example News homepage
following the established pattern for French news sources.
"""

import time
import random
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from config.settings import DEBUG
from utils.structured_logger import get_structured_logger


class ExampleNewsURLScraper:
    """Scraper for Example News article URLs."""
    
    def __init__(self, debug=None):
        """Initialize scraper with logging and configuration."""
        self.logger = get_structured_logger(self.__class__.__name__)
        self.debug = debug if debug is not None else DEBUG
        self.base_url = "https://example-news.fr/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def get_article_urls(self, max_articles: int = 8) -> List[str]:
        """
        Extract article URLs from Example News homepage.
        
        Args:
            max_articles: Maximum number of URLs to return
            
        Returns:
            List of article URLs
        """
        try:
            # Rate limiting to be respectful
            time.sleep(random.uniform(1, 3))
            
            # Fetch homepage
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find article containers based on your analysis
            article_containers = soup.find_all("article", class_="news-item")
            
            if not article_containers:
                self.logger.warning("No article containers found on homepage")
                return []
            
            urls = []
            for container in article_containers[:max_articles]:
                if isinstance(container, Tag):
                    # Extract link based on your HTML structure analysis
                    link = container.find("h3").find("a") if container.find("h3") else None
                    if link and link.has_attr("href"):
                        url = str(link["href"])
                        
                        # Convert relative URLs to absolute
                        if not url.startswith("http"):
                            url = urljoin(self.base_url, url)
                        
                        urls.append(url)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = [url for url in urls if not (url in seen or seen.add(url))]
            
            self.logger.info(f"Extracted {len(unique_urls)} URLs from Example News")
            return unique_urls
            
        except Exception as e:
            self.logger.error(f"Failed to scrape Example News: {e}")
            return []
```

### Testing the Scraper

Create a quick test script:

```python
# test_scraper.py
from scrapers.example_news_scraper import ExampleNewsURLScraper

scraper = ExampleNewsURLScraper(debug=True)
urls = scraper.get_article_urls(max_articles=5)
print(f"Found {len(urls)} URLs:")
for url in urls:
    print(f"  - {url}")
```

---

## Step 3: Create the Parser

### Parser Implementation

Create `src/parsers/example_news_parser.py`:

```python
"""
Article parser for Example News (https://example-news.fr).

This parser extracts article content from Example News article pages,
following the established pattern for French news sources.
"""

import os
import time
import random
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag

from config.settings import DEBUG, OFFLINE
from utils.structured_logger import get_structured_logger
from utils.validators import DataValidator
from utils.csv_writer import DailyCSVWriter
from utils.french_text_processor import FrenchTextProcessor


class ExampleNewsArticleParser:
    """Parser for Example News articles."""
    
    def __init__(self, delay: float = 2.0):
        """Initialize parser with configuration."""
        self.logger = get_structured_logger(self.__class__.__name__)
        self.delay = delay
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.debug = DEBUG
        
        # Initialize utilities
        self.csv_writer = DailyCSVWriter()
        self.text_processor = FrenchTextProcessor()
    
    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Parse article content from BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object of article page
            
        Returns:
            Dictionary with article data or None if parsing fails
        """
        try:
            # Extract title
            title_tag = soup.find("h1", class_="article-title")
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            if not title:
                self.logger.warning("No title found in article")
                return None
            
            # Extract main content
            content_container = soup.find("div", class_="article-content")
            if not content_container:
                self.logger.warning("No content container found")
                return None
            
            # Get text from paragraphs
            paragraphs = content_container.find_all("p")
            full_text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            if not full_text or len(full_text) < 100:
                self.logger.warning("Insufficient content extracted")
                return None
            
            # Extract date
            date_tag = soup.find("time", class_="publish-date")
            article_date = ""
            if date_tag and date_tag.has_attr("datetime"):
                try:
                    date_str = date_tag["datetime"]
                    # Parse ISO format date
                    parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    article_date = parsed_date.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    article_date = datetime.now().strftime("%Y-%m-%d")
            else:
                article_date = datetime.now().strftime("%Y-%m-%d")
            
            # Extract author (optional)
            author_tag = soup.find("span", class_="author-name")
            author = author_tag.get_text(strip=True) if author_tag else ""
            
            return {
                "title": title,
                "full_text": full_text,
                "article_date": article_date,
                "author": author,
                "date_scraped": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing article: {e}")
            return None
    
    def get_soup_from_url(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse article from URL.
        
        Args:
            url: Article URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            # Rate limiting
            time.sleep(random.uniform(self.delay, self.delay + 1))
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, "html.parser")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def get_test_sources_from_directory(self, source_name: str) -> List[Tuple[Optional[BeautifulSoup], str]]:
        """
        Load test data for offline mode.
        
        Args:
            source_name: Name of the source
            
        Returns:
            List of (soup, identifier) tuples
        """
        test_data_dir = os.path.join(
            os.path.dirname(__file__), "..", "test_data", "raw_url_soup", "example_news"
        )
        
        if not os.path.exists(test_data_dir):
            self.logger.warning(f"Test data directory not found: {test_data_dir}")
            return []
        
        sources = []
        for filename in os.listdir(test_data_dir):
            if filename.endswith(".html"):
                file_path = os.path.join(test_data_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    soup = BeautifulSoup(content, "html.parser")
                    identifier = f"test-{filename}"
                    sources.append((soup, identifier))
                    
                except Exception as e:
                    self.logger.error(f"Failed to load test file {filename}: {e}")
        
        return sources
    
    def to_csv(self, parsed_data: Dict[str, Any], source_identifier: str) -> None:
        """
        Process article data and write to CSV.
        
        Args:
            parsed_data: Parsed article data
            source_identifier: Source URL or identifier
        """
        try:
            # Process French text
            word_frequencies = self.text_processor.count_word_frequency(parsed_data["full_text"])
            
            if not word_frequencies:
                self.logger.warning(f"No word frequencies extracted for {parsed_data['title']}")
                return
            
            # Extract contexts for top words
            top_words = [word for word, _ in sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:20]]
            contexts = self.text_processor.extract_sentences_with_words(
                parsed_data["full_text"], top_words
            )
            
            # Write to CSV
            self.csv_writer.write_article(parsed_data, source_identifier, word_frequencies, contexts)
            
        except Exception as e:
            self.logger.error(f"Error writing article to CSV: {e}")
```

---

## Step 4: Update Configuration

### Add to Scraper Configuration

Edit `src/config/website_parser_scrapers_config.py`:

```python
# Add to SCRAPER_CONFIGS list
ScraperConfig(
    name="Example News",
    enabled=True,  # Set to False initially for testing
    scraper_class="scrapers.example_news_scraper.ExampleNewsURLScraper",
    parser_class="parsers.example_news_parser.ExampleNewsArticleParser",
    scraper_kwargs={"debug": True},
    parser_kwargs={"delay": 2.0}
),
```

### Initial Testing Configuration

For initial testing, keep the source disabled:

```python
ScraperConfig(
    name="Example News",
    enabled=False,  # Keep disabled during development
    scraper_class="scrapers.example_news_scraper.ExampleNewsURLScraper",
    parser_class="parsers.example_news_parser.ExampleNewsArticleParser",
    scraper_kwargs={"debug": True},
    parser_kwargs={"delay": 3.0}  # Longer delay during testing
),
```

---

## Step 5: Add Stopwords and Text Processing

### Update Text Processing Configuration

Edit `src/config/text_processing_config.py`:

```python
# Add to SITE_CONFIGS
"example-news.fr": {
    "additional_stopwords": {
        "example",      # Site name
        "news",         # Generic news terms
        "article",      # Content type labels
        "lire",         # French UI elements
        "plus",         # Navigation terms
        "voir",         # Action words
        "commentaire",  # Comment-related terms
        "partager",     # Social sharing
        "abonnement",   # Subscription terms
    },
    "min_word_frequency": 2,    # Adjust based on content quality
    "min_word_length": 4,       # Longer words for quality
    "max_word_length": 30,      # Reasonable upper bound
},
```

### Test Text Processing

Create a test script:

```python
# test_text_processing.py
from config.text_processing_config import get_site_config
from utils.french_text_processor import FrenchTextProcessor

# Test site-specific configuration
config = get_site_config("example-news.fr")
print("Site config:", config)

# Test text processing
processor = FrenchTextProcessor()
sample_text = "Voici un exemple d'article de Example News avec du contenu français."
frequencies = processor.count_word_frequency(sample_text)
print("Word frequencies:", frequencies)
```

---

## Step 6: Create Test Data

### Download Test Articles

Create a script to download test data:

```python
# download_test_data.py
import os
from utils.html_downloader import download_html

# Create test data directory
test_dir = "src/test_data/raw_url_soup/example_news"
os.makedirs(test_dir, exist_ok=True)

# Test URLs (manually collected)
test_urls = [
    "https://example-news.fr/article/politique-france-2025",
    "https://example-news.fr/article/economie-budget-gouvernement",
    "https://example-news.fr/article/societe-education-reforme",
    "https://example-news.fr/article/international-europe-relations",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

for i, url in enumerate(test_urls):
    filename = f"article_{i+1}.html"
    save_path = os.path.join(test_dir, filename)
    
    success = download_html(url, save_path, headers=headers, overwrite=True)
    if success:
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download: {url}")
```

### Validate Test Data

```python
# validate_test_data.py
import os
from bs4 import BeautifulSoup
from parsers.example_news_parser import ExampleNewsArticleParser

parser = ExampleNewsArticleParser()
test_dir = "src/test_data/raw_url_soup/example_news"

for filename in os.listdir(test_dir):
    if filename.endswith(".html"):
        file_path = os.path.join(test_dir, filename)
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        soup = BeautifulSoup(content, "html.parser")
        parsed = parser.parse_article(soup)
        
        if parsed:
            print(f"✓ {filename}: {parsed['title'][:50]}...")
        else:
            print(f"✗ {filename}: Failed to parse")
```

---

## Step 7: Write Tests

### Unit Tests

Create `tests/test_example_news.py`:

```python
"""Tests for Example News scraper and parser."""

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from scrapers.example_news_scraper import ExampleNewsURLScraper
from parsers.example_news_parser import ExampleNewsArticleParser


class TestExampleNewsScraper:
    """Test Example News URL scraper."""
    
    def test_scraper_initialization(self):
        """Test scraper can be initialized."""
        scraper = ExampleNewsURLScraper(debug=True)
        assert scraper.debug is True
        assert scraper.base_url == "https://example-news.fr/"
    
    @patch('scrapers.example_news_scraper.requests.get')
    def test_get_article_urls_success(self, mock_get):
        """Test successful URL extraction."""
        # Mock HTML response
        mock_response = Mock()
        mock_response.content = b'''
        <html>
            <body>
                <article class="news-item">
                    <h3><a href="/article/test-1">Test Article 1</a></h3>
                </article>
                <article class="news-item">
                    <h3><a href="/article/test-2">Test Article 2</a></h3>
                </article>
            </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        scraper = ExampleNewsURLScraper(debug=True)
        urls = scraper.get_article_urls(max_articles=2)
        
        assert len(urls) == 2
        assert "https://example-news.fr/article/test-1" in urls
        assert "https://example-news.fr/article/test-2" in urls
    
    @patch('scrapers.example_news_scraper.requests.get')
    def test_get_article_urls_no_articles(self, mock_get):
        """Test handling of pages with no articles."""
        mock_response = Mock()
        mock_response.content = b'<html><body><p>No articles</p></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        scraper = ExampleNewsURLScraper(debug=True)
        urls = scraper.get_article_urls()
        
        assert len(urls) == 0


class TestExampleNewsParser:
    """Test Example News article parser."""
    
    def test_parser_initialization(self):
        """Test parser can be initialized."""
        parser = ExampleNewsArticleParser(delay=1.0)
        assert parser.delay == 1.0
    
    def test_parse_article_success(self):
        """Test successful article parsing."""
        html_content = '''
        <html>
            <body>
                <h1 class="article-title">Test Article Title</h1>
                <time class="publish-date" datetime="2025-01-15T10:00:00Z"></time>
                <div class="article-content">
                    <p>Premier paragraphe du contenu français.</p>
                    <p>Deuxième paragraphe avec plus de contenu intéressant.</p>
                    <p>Troisième paragraphe pour avoir suffisamment de texte.</p>
                </div>
                <span class="author-name">Jean Dupont</span>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_content, "html.parser")
        parser = ExampleNewsArticleParser()
        result = parser.parse_article(soup)
        
        assert result is not None
        assert result["title"] == "Test Article Title"
        assert result["article_date"] == "2025-01-15"
        assert result["author"] == "Jean Dupont"
        assert "Premier paragraphe" in result["full_text"]
        assert len(result["full_text"]) > 100
    
    def test_parse_article_no_title(self):
        """Test handling of articles without title."""
        html_content = '''
        <html>
            <body>
                <div class="article-content">
                    <p>Content without title</p>
                </div>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_content, "html.parser")
        parser = ExampleNewsArticleParser()
        result = parser.parse_article(soup)
        
        assert result is None
    
    def test_parse_article_insufficient_content(self):
        """Test handling of articles with insufficient content."""
        html_content = '''
        <html>
            <body>
                <h1 class="article-title">Title</h1>
                <div class="article-content">
                    <p>Short.</p>
                </div>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_content, "html.parser")
        parser = ExampleNewsArticleParser()
        result = parser.parse_article(soup)
        
        assert result is None
```

### Integration Tests

Add to `tests/integration/test_basic_functionality.py`:

```python
def test_example_news_integration(self):
    """Test Example News integration with text processing."""
    from scrapers.example_news_scraper import ExampleNewsURLScraper
    from parsers.example_news_parser import ExampleNewsArticleParser
    from utils.french_text_processor import FrenchTextProcessor
    
    # Test scraper
    scraper = ExampleNewsURLScraper(debug=True)
    assert scraper.base_url == "https://example-news.fr/"
    
    # Test parser
    parser = ExampleNewsArticleParser()
    assert parser.delay == 2.0
    
    # Test text processing integration
    processor = FrenchTextProcessor()
    sample_text = "Voici un exemple d'article français avec vocabulaire intéressant."
    frequencies = processor.count_word_frequency(sample_text)
    assert isinstance(frequencies, dict)
    assert len(frequencies) > 0
```

---

## Step 8: Integration Testing

### Test with Offline Mode

```bash
# Enable your new source
# Set enabled=True in config
# Run offline mode test
OFFLINE=True DEBUG=True python -m main
```

### Test Individual Components

```python
# test_integration.py
from config.website_parser_scrapers_config import get_source_config
from core.processor import ArticleProcessor

# Test configuration loading
config = get_source_config("Example News")
if config:
    print(f"Config found: {config.name}")
    print(f"Enabled: {config.enabled}")
    print(f"Scraper: {config.scraper_class}")
    print(f"Parser: {config.parser_class}")
    
    # Test dynamic class loading
    try:
        ScraperClass = ArticleProcessor.import_class(config.scraper_class)
        ParserClass = ArticleProcessor.import_class(config.parser_class)
        print("✓ Classes loaded successfully")
        
        # Test instantiation
        scraper = ScraperClass(**(config.scraper_kwargs or {}))
        parser = ParserClass(**(config.parser_kwargs or {}))
        print("✓ Instances created successfully")
        
    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print("✗ Config not found")
```

### Run Full Integration Test

```bash
# Test just your source
python -c "
from config.website_parser_scrapers_config import SCRAPER_CONFIGS
from core.processor import ArticleProcessor

# Find your config
config = next((c for c in SCRAPER_CONFIGS if c.name == 'Example News'), None)
if config:
    config.enabled = True
    processed, attempted = ArticleProcessor.process_source(config)
    print(f'Processed: {processed}/{attempted}')
"
```

---

## Step 9: Performance Validation

### Performance Testing

Create `test_performance.py`:

```python
"""Performance tests for Example News source."""

import time
from scrapers.example_news_scraper import ExampleNewsURLScraper
from parsers.example_news_parser import ExampleNewsArticleParser

def test_scraper_performance():
    """Test scraper performance."""
    scraper = ExampleNewsURLScraper(debug=True)
    
    start_time = time.time()
    urls = scraper.get_article_urls(max_articles=5)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Scraper took {duration:.2f} seconds")
    print(f"Found {len(urls)} URLs")
    
    # Performance expectations
    assert duration < 30  # Should complete within 30 seconds
    assert len(urls) > 0  # Should find at least some URLs

def test_parser_performance():
    """Test parser performance with test data."""
    parser = ExampleNewsArticleParser()
    
    # Load test data
    test_sources = parser.get_test_sources_from_directory("example_news")
    
    if not test_sources:
        print("No test data found")
        return
    
    start_time = time.time()
    
    parsed_count = 0
    for soup, identifier in test_sources:
        if soup:
            parsed_data = parser.parse_article(soup)
            if parsed_data:
                parsed_count += 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Parser processed {parsed_count}/{len(test_sources)} articles in {duration:.2f} seconds")
    
    # Performance expectations
    assert duration < 10  # Should complete within 10 seconds
    assert parsed_count / len(test_sources) > 0.5  # Should parse >50% successfully

if __name__ == "__main__":
    test_scraper_performance()
    test_parser_performance()
```

### Memory Usage Testing

```python
# test_memory_usage.py
import tracemalloc
from scrapers.example_news_scraper import ExampleNewsURLScraper
from parsers.example_news_parser import ExampleNewsArticleParser

def test_memory_usage():
    """Test memory usage of scraper and parser."""
    
    tracemalloc.start()
    
    # Test scraper memory usage
    scraper = ExampleNewsURLScraper(debug=True)
    urls = scraper.get_article_urls(max_articles=8)
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Scraper memory - Current: {current / 1024 / 1024:.2f} MB, Peak: {peak / 1024 / 1024:.2f} MB")
    
    # Test parser memory usage
    parser = ExampleNewsArticleParser()
    test_sources = parser.get_test_sources_from_directory("example_news")
    
    for soup, identifier in test_sources[:3]:  # Test first 3 articles
        if soup:
            parsed_data = parser.parse_article(soup)
            if parsed_data:
                parser.to_csv(parsed_data, identifier)
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Parser memory - Current: {current / 1024 / 1024:.2f} MB, Peak: {peak / 1024 / 1024:.2f} MB")
    
    tracemalloc.stop()
    
    # Memory usage should be reasonable
    assert peak < 100 * 1024 * 1024  # Less than 100MB peak

if __name__ == "__main__":
    test_memory_usage()
```

---

## Step 10: Documentation Updates

### Update Related Documentation

1. **Update [[01-Scrapers]]**:
   ```markdown
   ### 5. Example News Scraper
   
   > [!example] Example News Implementation
   > **File**: `src/scrapers/example_news_scraper.py`
   > **Target**: https://example-news.fr/
   > **Strategy**: Extract from article cards with news-item class
   ```

2. **Update [[02-Parsers]]**:
   ```markdown
   ### 5. Example News Parser
   
   Parser for Example News articles with support for:
   - Article title extraction from h1.article-title
   - Content extraction from .article-content paragraphs
   - Date parsing from time.publish-date datetime attribute
   - Author extraction from .author-name span
   ```

3. **Update [[06-Config]]**:
   ```markdown
   ### Example News Configuration
   
   Site-specific configuration for Example News:
   - Additional stopwords for site-specific terms
   - Frequency thresholds adjusted for content quality
   - Word length limits optimized for French content
   ```

### Create Source-Specific Documentation

Create `docs/sources/example-news.md`:

```markdown
# Example News Source Documentation

## Source Information
- **Name**: Example News
- **URL**: https://example-news.fr
- **Language**: French
- **Content Focus**: General news, politics, economy
- **Update Frequency**: Multiple times daily

## Technical Implementation

### Scraper Details
- **Class**: `ExampleNewsURLScraper`
- **Homepage Structure**: Article cards with `news-item` class
- **Link Pattern**: `/article/[slug]`
- **Rate Limiting**: 1-3 second delays

### Parser Details
- **Class**: `ExampleNewsArticleParser`
- **Title Selector**: `h1.article-title`
- **Content Selector**: `.article-content p`
- **Date Selector**: `time.publish-date[datetime]`
- **Author Selector**: `.author-name`

## Configuration

### Text Processing
- **Min Word Frequency**: 2
- **Min Word Length**: 4
- **Max Word Length**: 30
- **Additional Stopwords**: example, news, article, lire, plus, voir

### Performance
- **Expected Articles**: 8-15 per scrape
- **Processing Time**: ~10-15 seconds
- **Success Rate**: >80%

## Testing

### Test Data Location
- **Directory**: `src/test_data/raw_url_soup/example_news/`
- **Files**: `article_1.html`, `article_2.html`, etc.

### Test Commands
```bash
# Run offline mode test
OFFLINE=True DEBUG=True python -m main

# Run specific tests
pytest tests/test_example_news.py -v

# Performance test
python test_performance.py
```

## Troubleshooting

### Common Issues
1. **No URLs Found**: Check if homepage structure changed
2. **Parse Failures**: Verify article selectors are still correct
3. **Rate Limiting**: Increase delay between requests
4. **Content Quality**: Adjust word frequency thresholds

### Debug Commands
```python
# Test scraper
from scrapers.example_news_scraper import ExampleNewsURLScraper
scraper = ExampleNewsURLScraper(debug=True)
urls = scraper.get_article_urls(max_articles=3)
print(urls)

# Test parser
from parsers.example_news_parser import ExampleNewsArticleParser
parser = ExampleNewsArticleParser()
soup = parser.get_soup_from_url(urls[0])
parsed = parser.parse_article(soup)
print(parsed)
```

## Maintenance

### Regular Checks
- Monthly: Verify selectors still work
- Quarterly: Update stopwords if needed
- As needed: Adjust rate limiting based on site behavior

### Update Process
1. Check for HTML structure changes
2. Update selectors if needed
3. Run tests to verify functionality
4. Deploy changes
```

---

## Final Validation Checklist

Before considering the new source complete:

- [ ] **Scraper works**: Returns 5+ URLs consistently
- [ ] **Parser works**: Extracts title, content, date successfully
- [ ] **Configuration added**: Source appears in config with correct paths
- [ ] **Test data created**: At least 4 test HTML files
- [ ] **Tests written**: Unit tests for scraper and parser
- [ ] **Integration tested**: Works in offline mode
- [ ] **Performance validated**: Completes within time limits
- [ ] **Documentation updated**: All relevant docs include new source
- [ ] **Stopwords configured**: Site-specific terms filtered
- [ ] **Live test completed**: Works with actual website

## Next Steps

1. **Monitor in Production**: Watch for any issues after deployment
2. **Adjust Configuration**: Fine-tune based on real-world performance
3. **Update Documentation**: Keep docs current with any changes
4. **Share Knowledge**: Document any special considerations for team

---

> [!success] Congratulations!
> You've successfully added a new news source to the French article scraper system. The source is now integrated with all system components and ready for production use.

## Cross-References

- [[01-Scrapers]] - Scraper implementation patterns
- [[02-Parsers]] - Parser implementation patterns
- [[03-Processor]] - Dynamic class loading system
- [[04-Testing]] - Testing framework and patterns
- [[05-Utils]] - Text processing and CSV writing
- [[06-Config]] - Configuration management
- [[09-Troubleshooting]] - Common issues and solutions