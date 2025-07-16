# Python Concepts - Technical Foundations

> [!abstract] Overview
> This document explains all the Python concepts, patterns, and techniques used in the French article scraper system. It serves as a technical reference for understanding the implementation details and learning the Python programming concepts demonstrated throughout the codebase.

## Table of Contents
- [[#Object-Oriented Programming|Object-Oriented Programming]]
- [[#Data Structures and Types|Data Structures and Types]]
- [[#Concurrency and Threading|Concurrency and Threading]]
- [[#Error Handling and Exceptions|Error Handling and Exceptions]]
- [[#Module and Package System|Module and Package System]]
- [[#File and I/O Operations|File and I/O Operations]]
- [[#String Processing and Regular Expressions|String Processing and Regular Expressions]]
- [[#Configuration and Environment|Configuration and Environment]]
- [[#Testing Frameworks|Testing Frameworks]]
- [[#External Libraries Integration|External Libraries Integration]]

---

## Object-Oriented Programming

The system extensively uses object-oriented programming concepts for code organization and modularity.

### Classes and Inheritance

#### Basic Class Definition
```python
class DailyCSVWriter:
    """Handles writing article word frequency data to daily CSV files."""
    
    # Class-level lock for thread safety during concurrent writes
    _write_lock = threading.Lock()

    def __init__(self, output_dir=None, debug=None):
        self.logger = get_structured_logger(self.__class__.__name__)
        self.output_dir = output_dir
        self.debug = debug if debug is not None else DEBUG
```

**Key Concepts:**
- **Class Definition**: `class ClassName:` defines a new class
- **Class Variables**: `_write_lock` is shared across all instances
- **Instance Variables**: `self.logger`, `self.output_dir` are unique per instance
- **Constructor**: `__init__` method initializes new instances
- **Self Parameter**: Refers to the current instance

#### Inheritance Example
```python
# Base class
class BaseParser(ABC):
    """Abstract base class for all article parsers."""
    
    def __init__(self, site_domain: str):
        self.site_domain = site_domain
        self.logger = get_structured_logger(f"{self.__class__.__name__}")
    
    @abstractmethod
    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Abstract method that must be implemented by subclasses."""
        pass

# Derived class
class SlateFrArticleParser(BaseParser):
    """Parser for Slate.fr articles."""
    
    def __init__(self):
        super().__init__(site_domain="slate.fr")
    
    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        # Implementation specific to Slate.fr
        pass
```

**Key Concepts:**
- **Abstract Base Class (ABC)**: Defines interface that subclasses must implement
- **Inheritance**: `SlateFrArticleParser(BaseParser)` inherits from BaseParser
- **super()**: Calls parent class methods
- **@abstractmethod**: Decorator requiring implementation in subclasses
- **Method Override**: Child class provides specific implementation

### Properties and Methods

#### Static Methods
```python
class DataValidator:
    @staticmethod
    def validate_url(url: str) -> Optional[str]:
        """Static method - doesn't need class or instance."""
        if not url or not isinstance(url, str):
            return None
        # Validation logic
        return url
```

#### Class Methods
```python
class ArticleProcessor:
    @classmethod
    def process_source(cls, config: ScraperConfig) -> Tuple[int, int]:
        """Class method - receives class as first parameter."""
        # Can create instances of the class
        instance = cls()
        return processed_count, total_attempted
```

**Key Concepts:**
- **@staticmethod**: Independent function within class namespace
- **@classmethod**: Receives class as first parameter (cls)
- **Instance Methods**: Regular methods that receive instance (self)

---

## Data Structures and Types

### Type Hints and Annotations

#### Basic Type Hints
```python
from typing import List, Dict, Optional, Tuple, Union, Any

def count_word_frequency(self, text: str) -> Dict[str, int]:
    """Function with type hints for parameters and return value."""
    word_counts: Dict[str, int] = {}
    return word_counts

def validate_text(self, text: str) -> Optional[str]:
    """Optional[str] means returns str or None."""
    if not text:
        return None
    return text.strip()
```

#### Complex Type Hints
```python
def get_article_urls(self, max_articles: int = 8) -> List[str]:
    """Returns list of strings."""
    urls: List[str] = []
    return urls

def process_source(cls, config: ScraperConfig) -> Tuple[int, int]:
    """Returns tuple of two integers."""
    return processed_count, total_attempted
```

**Key Concepts:**
- **Type Hints**: Specify expected types for better code clarity
- **Optional[T]**: Type T or None
- **List[T]**: List containing elements of type T
- **Dict[K, V]**: Dictionary with keys of type K, values of type V
- **Tuple[T1, T2]**: Tuple with specific types for each position

### Dataclasses

```python
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class ScraperConfig:
    """Configuration for a single news source."""
    name: str  # Required field
    enabled: bool  # Required field
    scraper_class: str  # Required field
    parser_class: str  # Required field
    scraper_kwargs: Optional[Dict] = None  # Optional with default
    parser_kwargs: Optional[Dict] = None  # Optional with default
```

**Key Concepts:**
- **@dataclass**: Automatically generates `__init__`, `__repr__`, etc.
- **Field Types**: Specify type for each field
- **Default Values**: Optional fields with default values
- **Automatic Methods**: Gets comparison, string representation methods

### Collections and Data Manipulation

#### Sets for Fast Lookups
```python
# Efficient membership testing
self.french_stopwords = {
    "le", "la", "les", "un", "une", "des", "du", "de",
    # ... more stopwords
}

# O(1) lookup time
if word in self.french_stopwords:
    continue
```

#### Dictionary Comprehensions
```python
# Filter words by frequency
filtered_words = {
    word: count for word, count in word_counts.items() 
    if count <= max_frequency
}

# Extract configuration values
validated = {
    field: value.strip()[:200] 
    for field in ["author", "category", "summary"]
    if (value := data.get(field, "")) and value.strip()
}
```

#### List Comprehensions
```python
# Extract and clean words
words = [
    word.strip().lower() 
    for word in text.split() 
    if len(word.strip()) >= 4
]

# Process multiple configurations
enabled_configs = [
    config for config in SCRAPER_CONFIGS 
    if config.enabled
]
```

**Key Concepts:**
- **Set**: Unordered collection for fast membership testing
- **Dictionary Comprehension**: Create dict with conditional logic
- **List Comprehension**: Create list with filtering and transformation
- **Walrus Operator** (`:=`): Assign and use value in same expression

---

## Concurrency and Threading

### Thread Safety with Locks

```python
import threading

class DailyCSVWriter:
    # Class-level lock shared by all instances
    _write_lock = threading.Lock()
    
    def write_article(self, parsed_data, url, word_freqs, word_contexts=None):
        # Use lock to ensure thread-safe file access
        with self._write_lock:
            # Critical section - only one thread can execute this
            with open(self.filename, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                # File writing operations
```

**Key Concepts:**
- **threading.Lock()**: Mutual exclusion lock
- **with lock**: Context manager automatically acquires and releases lock
- **Critical Section**: Code that must not run concurrently
- **Thread Safety**: Preventing race conditions in multi-threaded code

### ThreadPoolExecutor for Concurrent Processing

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def _get_live_sources_with_recovery(scraper, parser, source_name):
    max_concurrent_urls = min(len(urls), 3)
    
    # Create thread pool
    with ThreadPoolExecutor(max_workers=max_concurrent_urls) as executor:
        # Submit tasks to thread pool
        future_to_url = {
            executor.submit(fetch_single_url, (i, url)): url
            for i, url in enumerate(urls)
        }
        
        # Process completed tasks as they finish
        for future in as_completed(future_to_url):
            try:
                soup, processed_url, status = future.result()
                # Handle result
            except Exception as e:
                # Handle task failure
                pass
```

**Key Concepts:**
- **ThreadPoolExecutor**: Manages pool of worker threads
- **executor.submit()**: Submit task to thread pool, returns Future
- **as_completed()**: Iterator that yields futures as they complete
- **future.result()**: Get result from completed future
- **Context Manager**: `with` statement ensures proper cleanup

---

## Error Handling and Exceptions

### Try-Except Patterns

#### Basic Exception Handling
```python
def validate_date(date_str: str) -> Optional[str]:
    try:
        parsed_date = datetime.strptime(date_str, fmt)
        return parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        # Specific exception type
        continue
    except Exception as e:
        # Catch-all with error details
        logger.error(f"Unexpected error: {e}")
        return None
```

#### Multiple Exception Types
```python
try:
    response = requests.get(url, headers=self.headers, timeout=30)
    response.raise_for_status()
except requests.exceptions.Timeout:
    self.logger.warning(f"Timeout fetching {url}")
except requests.exceptions.ConnectionError:
    self.logger.warning(f"Connection error for {url}")
except requests.exceptions.RequestException as e:
    self.logger.error(f"Request failed for {url}: {e}")
```

#### Finally Blocks and Context Managers
```python
# Using finally for cleanup
try:
    process_articles()
except Exception as e:
    logger.error(f"Processing failed: {e}")
finally:
    cleanup_resources()

# Context manager (preferred)
with open(filename, 'r') as f:
    # File automatically closed even if exception occurs
    content = f.read()
```

### Custom Exception Handling Patterns

```python
def process_article_with_recovery(parser, soup, source_identifier, source_name):
    def process_article():
        parsed_content = parser.parse_article(soup)
        if not parsed_content:
            raise ValueError(f"No content extracted from {source_identifier}")
        return parsed_content
    
    try:
        return process_article()
    except Exception as e:
        logger.error("Article processing failed", extra_data={
            "source": source_name,
            "article_url": source_identifier,
            "error": str(e)
        }, exc_info=True)
        return False
```

**Key Concepts:**
- **Specific Exceptions**: Catch specific exception types first
- **Exception Hierarchy**: More specific exceptions before general ones
- **exc_info=True**: Include stack trace in logs
- **Nested Functions**: Inner function for clean error boundary
- **Graceful Degradation**: Continue processing despite individual failures

---

## Module and Package System

### Import Patterns

#### Absolute Imports
```python
# Import entire module
import requests
import threading
from datetime import datetime

# Import specific items
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
```

#### Relative Imports
```python
# Import from same package
from config.settings import DEBUG, OFFLINE
from utils.structured_logger import get_structured_logger
from utils.validators import DataValidator
```

#### Dynamic Imports
```python
import importlib

def import_class(class_path: str) -> type:
    """Dynamically import class from string path."""
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

# Usage
ScraperClass = import_class("scrapers.slate_fr_scraper.SlateFrURLScraper")
```

### Module Structure

```python
# Module docstring
"""
CSV writer utility for French article scraper output.

This module provides functionality to write processed article data
to daily CSV files with word frequency analysis results.
"""

# Imports organized by type
import csv
import os
import threading
from datetime import datetime
from typing import Optional

# Local imports
from config.settings import DEBUG
from utils.structured_logger import get_structured_logger

# Module-level constants
CSV_FIELDS = [
    "word", "context", "source", "article_date", 
    "scraped_date", "title", "frequency"
]

# Main classes and functions
class DailyCSVWriter:
    # Implementation
    pass

# Module-level functions
def helper_function():
    pass
```

**Key Concepts:**
- **Module Docstring**: Describes module purpose and usage
- **Import Organization**: Standard library, third-party, local imports
- **Module Constants**: ALL_CAPS naming convention
- **getattr()**: Get attribute by name from object
- **rsplit()**: Split string from right side

---

## File and I/O Operations

### File Operations with Context Managers

```python
def write_article(self, parsed_data, url, word_freqs):
    # Safe file writing with automatic cleanup
    with open(self.filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        
        if not file_exists:
            writer.writeheader()
        
        for word, freq in word_freqs.items():
            writer.writerow({
                "word": str(word)[:100],
                "context": str(context)[:500],
                "frequency": int(freq)
            })
```

### File Path Operations

```python
import os
from pathlib import Path

# Path construction
def _get_filename(self) -> str:
    today = datetime.today().strftime("%Y-%m-%d")
    return os.path.join(self.output_dir, f"{today}.csv")

# Directory creation
os.makedirs(self.output_dir, exist_ok=True)

# Path checking
if os.path.isfile(self.filename):
    # File exists
    pass

# Modern path handling with pathlib
log_path = Path(log_directory)
log_path.mkdir(parents=True, exist_ok=True)
```

### Backup and Recovery

```python
def write_with_backup(self):
    backup_filename = f"{self.filename}.backup"
    
    try:
        # Create backup before risky operation
        if file_exists:
            shutil.copy2(self.filename, backup_filename)
        
        # Perform operation
        write_data()
        
        # Clean up backup on success
        if os.path.exists(backup_filename):
            os.remove(backup_filename)
            
    except Exception as e:
        # Restore backup on failure
        if os.path.exists(backup_filename):
            shutil.move(backup_filename, self.filename)
        raise
```

**Key Concepts:**
- **Context Managers**: `with` statement ensures file closure
- **File Modes**: "a" (append), "r" (read), "w" (write)
- **Encoding**: Specify UTF-8 for Unicode text
- **os.path vs pathlib**: Traditional vs modern path handling
- **Backup Strategy**: Create backup before risky operations

---

## String Processing and Regular Expressions

### Regular Expressions

```python
import re
import unicodedata

def clean_text(self, text: str) -> str:
    # Unicode normalization
    text = unicodedata.normalize("NFD", text)
    
    # Character replacement with regex
    text = re.sub(r"[àâä]", "a", text)
    text = re.sub(r"[éèêë]", "e", text)
    
    # Character filtering
    text = re.sub(r"[^a-z0-9\s\'-]", " ", text)
    
    # Whitespace normalization
    text = re.sub(r"\s+", " ", text).strip()
    
    return text
```

### String Methods and Processing

```python
def tokenize_french_text(self, text: str) -> List[str]:
    words = []
    for word in text.split():
        word_clean = word.strip().lower()
        
        # String length and content checks
        if len(word_clean) < 4:
            continue
            
        if word_clean.isdigit():
            continue
            
        # Character analysis
        if sum(c.isdigit() for c in word_clean) / max(1, len(word_clean)) > 0.6:
            continue
            
        if not any(c.isalpha() for c in word_clean):
            continue
            
        words.append(word_clean)
    
    return words
```

### Unicode and Text Normalization

```python
import unicodedata

def normalize_french_text(text: str) -> str:
    # Normalize Unicode to decomposed form
    text = unicodedata.normalize("NFD", text)
    
    # Remove combining characters (accents)
    text = "".join(c for c in text if not unicodedata.combining(c))
    
    return text
```

**Key Concepts:**
- **re.sub()**: Regular expression substitution
- **Raw Strings**: `r"pattern"` for regex patterns
- **Unicode Normalization**: NFD (decomposed) vs NFC (composed)
- **String Methods**: `.isdigit()`, `.isalpha()`, `.strip()`, `.lower()`
- **Generator Expression**: `sum(c.isdigit() for c in word)`

---

## Configuration and Environment

### Environment Variables

```python
import os

# Reading environment variables with defaults
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
OFFLINE = os.getenv('OFFLINE', 'False').lower() in ('true', '1', 'yes')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'src/output')

# Type conversion
MAX_ARTICLES = int(os.getenv('MAX_ARTICLES_PER_SOURCE', '8'))
TIMEOUT = int(os.getenv('PROCESSING_TIMEOUT', '120'))
```

### Configuration Classes

```python
class EnvConfig:
    """Centralized environment configuration access."""
    
    # Class attributes as configuration
    DEBUG = EnvironmentConfig.get_bool('DEBUG', False)
    OFFLINE = EnvironmentConfig.get_bool('OFFLINE', False)
    OUTPUT_DIR = EnvironmentConfig.get_string('OUTPUT_DIR', 'src/output')
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            'debug': cls.DEBUG,
            'offline': cls.OFFLINE,
            'output_dir': cls.OUTPUT_DIR
        }
```

### Configuration Loading

```python
def load_configuration():
    """Load configuration with validation and fallbacks."""
    try:
        # Load from files
        from config.settings import DEBUG, OFFLINE
        from config.website_parser_scrapers_config import SCRAPER_CONFIGS
        
        # Validate configuration
        if not SCRAPER_CONFIGS:
            raise ValueError("No scraper configurations found")
            
        return {
            'global': {'debug': DEBUG, 'offline': OFFLINE},
            'sources': SCRAPER_CONFIGS
        }
        
    except Exception as e:
        logger.error(f"Configuration loading failed: {e}")
        # Return fallback configuration
        return get_default_config()
```

**Key Concepts:**
- **os.getenv()**: Get environment variable with default
- **Type Conversion**: Convert string env vars to appropriate types
- **Class Attributes**: Store configuration as class-level variables
- **Fallback Strategy**: Provide defaults when configuration fails

---

## Testing Frameworks

### Pytest Basics

```python
import pytest
import tempfile
from unittest.mock import Mock, patch

class TestEssential:
    """Essential tests that must pass for the system to work."""

    def test_csv_writer_initialization(self):
        """Test CSV writer can be initialized."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DailyCSVWriter(output_dir=temp_dir, debug=True)
            assert writer.output_dir == temp_dir
            assert writer.debug is True
```

### Fixtures and Mocking

```python
@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp(prefix='test_scraper_')
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_scraper_config():
    """Mock scraper configuration for testing."""
    return ScraperConfig(
        name="TestSource",
        enabled=True,
        scraper_class="tests.fixtures.mock_scraper.MockScraper",
        parser_class="tests.fixtures.mock_parser.MockParser"
    )

def test_with_mocking(self):
    """Test using mocks to isolate functionality."""
    with patch('core.processor.importlib.import_module') as mock_import:
        mock_module = Mock()
        mock_class = Mock()
        mock_module.TestClass = mock_class
        mock_import.return_value = mock_module
        
        result = ArticleProcessor.import_class("test.module.TestClass")
        assert result == mock_class
```

### Test Categories

```python
# Marking tests with categories
@pytest.mark.slow
def test_performance_intensive():
    """Test marked as slow for selective execution."""
    pass

@pytest.mark.integration
def test_component_interaction():
    """Integration test for component interaction."""
    pass

# Parametrized tests
@pytest.mark.parametrize("input,expected", [
    ("test text", {"test": 1, "text": 1}),
    ("", {}),
    ("word word", {"word": 2})
])
def test_word_counting(input, expected):
    processor = FrenchTextProcessor()
    result = processor.count_word_frequency(input)
    assert result == expected
```

**Key Concepts:**
- **@pytest.fixture**: Create reusable test data and setup
- **yield**: Fixture cleanup after test completes
- **Mock Objects**: Replace dependencies with controllable test doubles
- **@patch**: Replace functions/methods during testing
- **Test Markers**: Categorize tests for selective execution
- **Parametrization**: Run same test with different inputs

---

## External Libraries Integration

### Requests for HTTP

```python
import requests

def get_article_urls(self) -> List[str]:
    try:
        response = requests.get(
            self.base_url, 
            headers=self.headers, 
            timeout=30
        )
        response.raise_for_status()  # Raise exception for HTTP errors
        
        soup = BeautifulSoup(response.content, "html.parser")
        # Process response
        
    except requests.exceptions.Timeout:
        self.logger.warning(f"Timeout fetching {self.base_url}")
    except requests.exceptions.RequestException as e:
        self.logger.error(f"Request failed: {e}")
```

### BeautifulSoup for HTML Parsing

```python
from bs4 import BeautifulSoup, Tag

def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    # Find elements by CSS selector
    title_tag = soup.select_one("h1.article-title")
    
    # Find elements by attributes
    content_div = soup.find("div", class_="article-content")
    
    # Navigate DOM structure
    if content_div:
        paragraphs = content_div.find_all("p")
        text_content = "\n".join(p.get_text(strip=True) for p in paragraphs)
    
    # Extract attributes
    date_tag = soup.find("time")
    if date_tag and date_tag.has_attr("datetime"):
        date_value = date_tag["datetime"]
    
    return {
        "title": title_tag.get_text(strip=True) if title_tag else "",
        "content": text_content,
        "date": date_value
    }
```

### Collections Counter

```python
from collections import Counter

def count_word_frequency(self, text: str) -> Dict[str, int]:
    words = self.tokenize_french_text(text)
    
    # Counter automatically counts occurrences
    word_counts = dict(Counter(words))
    
    # Counter has useful methods
    most_common = Counter(words).most_common(10)  # Top 10 words
    
    return word_counts
```

**Key Concepts:**
- **requests.get()**: HTTP GET request with options
- **response.raise_for_status()**: Check for HTTP errors
- **BeautifulSoup**: Parse HTML/XML documents
- **CSS Selectors**: Find elements using CSS syntax
- **DOM Navigation**: Find elements by tag, class, attributes
- **Counter**: Count hashable objects efficiently

---

## Conclusion

This French article scraper system demonstrates **advanced Python programming concepts** applied to a real-world text processing application. The codebase showcases:

**Core Python Concepts:**
- ✅ **Object-Oriented Design**: Classes, inheritance, abstract base classes
- ✅ **Type System**: Type hints, dataclasses, optional types
- ✅ **Concurrency**: Threading, locks, thread pools, futures
- ✅ **Error Handling**: Exception hierarchies, recovery patterns
- ✅ **Module System**: Package organization, dynamic imports

**Advanced Techniques:**
- ✅ **Context Managers**: Safe resource management
- ✅ **Regular Expressions**: Text processing and normalization
- ✅ **Configuration Management**: Environment variables, dataclasses
- ✅ **Testing Patterns**: Fixtures, mocking, parametrization
- ✅ **External Libraries**: HTTP requests, HTML parsing, text analysis

**Professional Practices:**
- ✅ **Documentation**: Comprehensive docstrings and type hints
- ✅ **Error Recovery**: Graceful degradation and backup strategies
- ✅ **Thread Safety**: Proper synchronization for concurrent access
- ✅ **Configuration**: Flexible, environment-aware settings
- ✅ **Testing**: Multiple test categories with good coverage

This codebase serves as an excellent example of **production-quality Python** that combines multiple advanced concepts into a cohesive, maintainable system for French language text analysis and vocabulary extraction.