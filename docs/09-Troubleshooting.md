# Troubleshooting Common Issues

> [!abstract] Overview
> This document provides solutions to common issues encountered when developing, testing, and running the French article scraper system. It covers import errors, configuration problems, output issues, test failures, and cloud deployment challenges.

## Table of Contents
- [[#Quick Diagnosis Guide|Quick Diagnosis Guide]]
- [[#Import and Module Errors|Import and Module Errors]]
- [[#Configuration Issues|Configuration Issues]]
- [[#Scraping and Network Problems|Scraping and Network Problems]]
- [[#Parser and Content Extraction Issues|Parser and Content Extraction Issues]]
- [[#Output and File Issues|Output and File Issues]]
- [[#Test Failures|Test Failures]]
- [[#Performance and Memory Issues|Performance and Memory Issues]]
- [[#Cloud and Deployment Issues|Cloud and Deployment Issues]]
- [[#Logging and Debugging|Logging and Debugging]]

---

## Quick Diagnosis Guide

### System Won't Start

**Symptoms**: Script crashes immediately or imports fail

**Quick Checks**:
```bash
# Check Python version
python --version  # Should be 3.11+

# Check if virtual environment is active
which python  # Should point to venv/bin/python

# Test basic imports
python -c "import requests, bs4, csv"

# Check configuration
python -c "from config.settings import DEBUG, OFFLINE; print(f'DEBUG={DEBUG}, OFFLINE={OFFLINE}')"
```

**Most Common Causes**:
1. Virtual environment not activated
2. Missing dependencies
3. Import path issues
4. Configuration file problems

### No Output Generated

**Symptoms**: Script runs but creates no CSV files

**Quick Checks**:
```bash
# Check output directory
ls -la src/output/

# Check if sources are enabled
python -c "from config.source_configs import SCRAPER_CONFIGS; print([c['name'] for c in SCRAPER_CONFIGS if c['enabled']])"

# Test offline mode
OFFLINE=True DEBUG=True python -m main
```

**Most Common Causes**:
1. All sources disabled in configuration
2. Network connectivity issues
3. Output directory permission problems
4. Parser selector changes

### Tests Failing

**Symptoms**: Test suite fails with various errors

**Quick Checks**:
```bash
# Run essential tests only
make test-essential

# Check test data
ls -la src/test_data/raw_url_soup/

# Test individual components
# FrenchTextProcessor was replaced by dbt processing
make dbt-run
```

---

## Import and Module Errors

### ModuleNotFoundError

**Error**: `ModuleNotFoundError: No module named 'scrapers'`

**Cause**: Python can't find the module in the import path

**Solutions**:

1. **Check Working Directory**:
   ```bash
   # Make sure you're in the project root
   pwd
   # Should show: /path/to/publicite_francais
   
   # Check if main.py exists
   ls -la main.py
   ```

2. **Run as Module**:
   ```bash
   # Correct way to run
   python -m main
   
   # Instead of
   python main.py
   ```

3. **Check PYTHONPATH**:
   ```bash
   # Add current directory to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   
   # Or add to your shell profile
   echo 'export PYTHONPATH="${PYTHONPATH}:$(pwd)"' >> ~/.bashrc
   ```

4. **Virtual Environment Issues**:
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   pip install -e .
   ```

### ImportError: Dynamic Class Loading

**Error**: `ImportError: cannot import name 'ClassName' from 'module'`

**Cause**: Dynamic class loading failed

**Debug Steps**:

1. **Test Class Path**:
   ```python
   # Test the import manually
   from scrapers.slate_fr_scraper import SlateFrURLScraper
   print("Import successful")
   
   # Test dynamic import
   import importlib
   module = importlib.import_module("scrapers.slate_fr_scraper")
   cls = getattr(module, "SlateFrURLScraper")
   print("Dynamic import successful")
   ```

2. **Check Configuration**:
   ```python
   from config.source_configs import SCRAPER_CONFIGS
   for config in SCRAPER_CONFIGS:
       if config['enabled']:
           print(f"Source: {config['name']}")
           print(f"Scraper: {config['scraper_class']}")
           print(f"Parser: {config['parser_class']}")
   ```

3. **Verify File Structure**:
   ```bash
   # Check if files exist
   ls -la src/scrapers/
   ls -la src/parsers/
   
   # Check __init__.py files
   find src -name "__init__.py"
   ```

### Circular Import Issues

**Error**: `ImportError: cannot import name 'X' from partially initialized module`

**Cause**: Circular dependencies between modules

**Solutions**:

1. **Move Import Inside Function**:
   ```python
   # Instead of module-level import
   from config.settings import DEBUG
   
   # Use function-level import
   def get_debug_setting():
       from config.settings import DEBUG
       return DEBUG
   ```

2. **Use Import at Runtime**:
   ```python
   def process_source(config):
       # Import only when needed
       from core.component_loader import import_class
       ScraperClass = import_class(config['scraper_class'])
       ParserClass = import_class(config['parser_class'])
   ```

---

## Configuration Issues

### Configuration Not Found

**Error**: `AttributeError: module 'config.settings' has no attribute 'DEBUG'`

**Cause**: Configuration module is missing or malformed

**Solutions**:

1. **Check Configuration Files**:
   ```bash
   # Verify config files exist
   ls -la src/config/
   
   # Check file contents
   cat src/config/settings.py
   ```

2. **Create Missing Configuration**:
   ```python
   # Create minimal settings.py
   cat > src/config/settings.py << 'EOF'
   """Global settings for the French article scraping system."""
   
   # Enable debug logging for detailed output
   DEBUG = False
   
   # Switch between live scraping and offline test mode
   OFFLINE = False
   EOF
   ```

3. **Test Configuration Loading**:
   ```python
   # Test configuration import
   try:
       from config.settings import DEBUG, OFFLINE
       print(f"DEBUG={DEBUG}, OFFLINE={OFFLINE}")
   except Exception as e:
       print(f"Config error: {e}")
   ```

### Environment Variables Not Working

**Error**: Environment variables like `DEBUG=True` not taking effect

**Cause**: Environment variable parsing issues

**Solutions**:

1. **Check Environment Variable Format**:
   ```bash
   # Correct formats
   export DEBUG=True
   export OFFLINE=true
   export DEBUG=1
   
   # Incorrect formats
   export DEBUG=true  # Case sensitive
   export OFFLINE=True  # Case sensitive
   ```

2. **Debug Environment Loading**:
   ```python
   import os
   
   # Check raw environment values
   print(f"DEBUG env: '{os.getenv('DEBUG', 'NOT_SET')}'")
   print(f"OFFLINE env: '{os.getenv('OFFLINE', 'NOT_SET')}'")
   
   # Check parsed values
   DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
   OFFLINE = os.getenv('OFFLINE', 'False').lower() in ('true', '1', 'yes')
   print(f"DEBUG parsed: {DEBUG}")
   print(f"OFFLINE parsed: {OFFLINE}")
   ```

3. **Set Environment Variables Correctly**:
   ```bash
   # For single run
   DEBUG=True OFFLINE=True python -m main
   
   # For session
   export DEBUG=True
   export OFFLINE=True
   python -m main
   
   # For permanent
   echo 'export DEBUG=True' >> ~/.bashrc
   echo 'export OFFLINE=True' >> ~/.bashrc
   ```

### Source Configuration Issues

**Error**: `ValueError: No valid source configurations found`

**Cause**: All sources disabled or malformed configuration

**Solutions**:

1. **Check Source Configuration**:
   ```python
   from config.source_configs import SCRAPER_CONFIGS
   
   print(f"Total configs: {len(SCRAPER_CONFIGS)}")
   enabled = [c for c in SCRAPER_CONFIGS if c.enabled]
   print(f"Enabled configs: {len(enabled)}")
   
   for config in enabled:
       print(f"  - {config['name']}")
   ```

2. **Enable Sources**:
   ```python
   # Temporarily enable all sources
   from config.source_configs import SCRAPER_CONFIGS
   for config in SCRAPER_CONFIGS:
       config['enabled'] = True
   print("All sources enabled")
   ```

3. **Validate Configuration**:
   ```python
   from config.source_configs import SCRAPER_CONFIGS
   
   for config in SCRAPER_CONFIGS:
       # Check required fields
       assert config['name'], f"Missing name in config"
       assert config['scraper_class'], f"Missing scraper_class in {config['name']}"
       assert config['parser_class'], f"Missing parser_class in {config['name']}"
       print(f"✓ {config['name']} configuration valid")
   ```

---

## Scraping and Network Problems

### No URLs Found

**Error**: Scraper returns empty list of URLs

**Cause**: Website structure changed or network issues

**Debug Steps**:

1. **Test Network Connectivity**:
   ```python
   import requests
   
   # Test basic connectivity
   try:
       response = requests.get("https://www.slate.fr", timeout=10)
       print(f"Status: {response.status_code}")
       print(f"Content length: {len(response.content)}")
   except Exception as e:
       print(f"Network error: {e}")
   ```

2. **Check Website Structure**:
   ```python
   import requests
   from bs4 import BeautifulSoup
   
   # Get homepage content
   response = requests.get("https://www.slate.fr")
   soup = BeautifulSoup(response.content, "html.parser")
   
   # Check for expected elements
   articles = soup.find_all("article")
   print(f"Found {len(articles)} article tags")
   
   # Check specific selectors
   cards = soup.find_all("article", class_="node node--type-article")
   print(f"Found {len(cards)} article cards")
   ```

3. **Test Scraper Manually**:
   ```python
   from scrapers.slate_fr_scraper import SlateFrURLScraper
   
   scraper = SlateFrURLScraper(debug=True)
   urls = scraper.get_article_urls(max_articles=3)
   print(f"Found {len(urls)} URLs:")
   for url in urls:
       print(f"  - {url}")
   ```

### Rate Limiting Issues

**Error**: HTTP 429 errors or blocked requests

**Cause**: Making requests too quickly

**Solutions**:

1. **Increase Delays**:
   ```python
   # In scraper configuration
   ScraperConfig(
       name="Source Name",
       scraper_kwargs={"debug": True},
       parser_kwargs={"delay": 5.0}  # Increase delay
   )
   ```

2. **Implement Exponential Backoff**:
   ```python
   import time
   import random
   
   def request_with_backoff(url, max_retries=3):
       for attempt in range(max_retries):
           try:
               response = requests.get(url)
               if response.status_code == 429:
                   # Rate limited, wait longer
                   wait_time = (2 ** attempt) + random.uniform(0, 1)
                   time.sleep(wait_time)
                   continue
               return response
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               time.sleep(2 ** attempt)
   ```

3. **Use Different User Agents**:
   ```python
   user_agents = [
       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
       "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
   ]
   
   headers = {"User-Agent": random.choice(user_agents)}
   response = requests.get(url, headers=headers)
   ```

### Connection Timeouts

**Error**: `requests.exceptions.Timeout` or `requests.exceptions.ConnectionError`

**Cause**: Network issues or slow server response

**Solutions**:

1. **Increase Timeout Values**:
   ```python
   # In scraper code
   response = requests.get(url, timeout=30)  # Increase from 10 to 30 seconds
   ```

2. **Add Retry Logic**:
   ```python
   def robust_request(url, max_retries=3):
       for attempt in range(max_retries):
           try:
               response = requests.get(url, timeout=30)
               return response
           except requests.exceptions.Timeout:
               print(f"Timeout on attempt {attempt + 1}")
               if attempt == max_retries - 1:
                   raise
               time.sleep(5)
   ```

3. **Configure Requests Session**:
   ```python
   import requests
   from requests.adapters import HTTPAdapter
   from requests.packages.urllib3.util.retry import Retry
   
   session = requests.Session()
   
   # Configure retry strategy
   retry_strategy = Retry(
       total=3,
       backoff_factor=1,
       status_forcelist=[429, 500, 502, 503, 504],
   )
   
   adapter = HTTPAdapter(max_retries=retry_strategy)
   session.mount("http://", adapter)
   session.mount("https://", adapter)
   
   response = session.get(url, timeout=30)
   ```

---

## Parser and Content Extraction Issues

### Parser Returns None

**Error**: `parse_article()` returns None for valid articles

**Cause**: HTML selectors no longer match the page structure

**Debug Steps**:

1. **Test Parser with Known Good Data**:
   ```python
   from bs4 import BeautifulSoup
   from parsers.slate_fr_parser import SlateFrArticleParser
   
   # Load test data
   parser = SlateFrArticleParser()
   test_sources = parser.get_test_sources_from_directory("slate_fr")
   
   if test_sources:
       soup, identifier = test_sources[0]
       result = parser.parse_article(soup)
       print(f"Test data result: {result}")
   ```

2. **Check Current HTML Structure**:
   ```python
   import requests
   from bs4 import BeautifulSoup
   
   # Get current article page
   url = "https://example-article-url.com"
   response = requests.get(url)
   soup = BeautifulSoup(response.content, "html.parser")
   
   # Check for title
   title_selectors = ["h1", "h1.title", "h1.article-title", ".title"]
   for selector in title_selectors:
       title = soup.select_one(selector)
       if title:
           print(f"Title found with selector '{selector}': {title.get_text()}")
   
   # Check for content
   content_selectors = [".content", ".article-content", ".body", "article"]
   for selector in content_selectors:
       content = soup.select_one(selector)
       if content:
           print(f"Content found with selector '{selector}': {len(content.get_text())} chars")
   ```

3. **Update Selectors**:
   ```python
   # In parser code, update selectors based on current HTML
   def parse_article(self, soup):
       # Try multiple selectors
       title_tag = (
           soup.find("h1", class_="article-title") or
           soup.find("h1", class_="title") or
           soup.find("h1")
       )
       
       content_div = (
           soup.find("div", class_="article-content") or
           soup.find("div", class_="content") or
           soup.find("article")
       )
   ```

### Insufficient Content Extracted

**Error**: Articles have very short content or missing paragraphs

**Cause**: Content selector not capturing all text

**Solutions**:

1. **Inspect Content Structure**:
   ```python
   # Debug content extraction
   content_div = soup.find("div", class_="article-content")
   if content_div:
       # Check all paragraph tags
       paragraphs = content_div.find_all("p")
       print(f"Found {len(paragraphs)} paragraphs")
       
       # Check for other text containers
       divs = content_div.find_all("div")
       print(f"Found {len(divs)} div elements")
       
       # Print structure
       for i, p in enumerate(paragraphs[:3]):
           print(f"P{i}: {p.get_text()[:100]}...")
   ```

2. **Expand Content Selectors**:
   ```python
   def extract_content(self, soup):
       content_div = soup.find("div", class_="article-content")
       if not content_div:
           return ""
       
       # Get text from multiple elements
       text_elements = content_div.find_all(["p", "div", "span"])
       
       # Filter and join text
       full_text = []
       for elem in text_elements:
           text = elem.get_text(strip=True)
           if text and len(text) > 20:  # Skip short elements
               full_text.append(text)
       
       return "\n".join(full_text)
   ```

3. **Handle Different Content Types**:
   ```python
   def parse_article(self, soup):
       # Try different content structures
       content_selectors = [
           ".article-content",
           ".content",
           ".post-content",
           "article .body",
           ".article-body"
       ]
       
       for selector in content_selectors:
           content_div = soup.select_one(selector)
           if content_div:
               paragraphs = content_div.find_all("p")
               if paragraphs:
                   full_text = "\n".join(p.get_text(strip=True) for p in paragraphs)
                   if len(full_text) > 100:
                       return full_text
       
       return None
   ```

### Date Parsing Issues

**Error**: Article dates are incorrect or missing

**Cause**: Date format changes or selector issues

**Solutions**:

1. **Debug Date Extraction**:
   ```python
   # Check date elements
   date_selectors = ["time", ".date", ".publish-date", ".published"]
   for selector in date_selectors:
       date_elem = soup.select_one(selector)
       if date_elem:
           print(f"Date element: {date_elem}")
           print(f"Text: {date_elem.get_text()}")
           print(f"Datetime attr: {date_elem.get('datetime')}")
   ```

2. **Handle Multiple Date Formats**:
   ```python
   def parse_date(self, date_string):
       formats = [
           "%Y-%m-%d",
           "%Y-%m-%dT%H:%M:%S",
           "%Y-%m-%dT%H:%M:%SZ",
           "%d/%m/%Y",
           "%d-%m-%Y",
           "%B %d, %Y",
           "%d %B %Y"
       ]
       
       for fmt in formats:
           try:
               return datetime.strptime(date_string, fmt)
           except ValueError:
               continue
       
       # Return current date if parsing fails
       return datetime.now()
   ```

3. **Extract Date from URL**:
   ```python
   def extract_date_from_url(self, url):
       # Look for date patterns in URL
       import re
       
       # Pattern: /2025/01/15/article-title
       pattern = r'/(\d{4})/(\d{2})/(\d{2})/'
       match = re.search(pattern, url)
       if match:
           year, month, day = match.groups()
           return f"{year}-{month}-{day}"
       
       return datetime.now().strftime("%Y-%m-%d")
   ```

---

## Output and File Issues

### No CSV Files Created

**Error**: System runs but no output files are generated

**Cause**: Output directory issues or data validation failures

**Debug Steps**:

1. **Check Output Directory**:
   ```bash
   # Check if output directory exists
   ls -la src/output/
   
   # Check permissions
   ls -la src/
   
   # Create directory if missing
   mkdir -p src/output
   chmod 755 src/output
   ```

2. **Test CSV Writer Directly**:
   ```python
   from utils.csv_writer import DailyCSVWriter
   
   # Test CSV writer
   writer = DailyCSVWriter(output_dir="src/output", debug=True)
   
   # Test data
   test_data = {
       "title": "Test Article",
       "full_text": "This is test content in French.",
       "article_date": "2025-01-15",
       "date_scraped": "2025-01-15 10:00:00"
   }
   
   test_freqs = {"test": 1, "content": 1}
   test_contexts = {"test": "This is test content"}
   
   writer.write_article(test_data, "test-url", test_freqs, test_contexts)
   
   # Check if file was created
   import os
   print(f"Files in output: {os.listdir('src/output/')}")
   ```

3. **Check Data Validation**:
   ```python
   from utils.validators import DataValidator
   
   # Test data validation
   test_data = {
       "title": "Test Article",
       "full_text": "This is test content",
       "article_date": "2025-01-15"
   }
   
   validated = DataValidator.validate_article_data(test_data)
   print(f"Validation result: {validated}")
   ```

### Permission Denied Errors

**Error**: `PermissionError: [Errno 13] Permission denied`

**Cause**: Insufficient permissions to write to output directory

**Solutions**:

1. **Fix Directory Permissions**:
   ```bash
   # Change ownership
   sudo chown -R $USER:$USER src/output/
   
   # Set permissions
   chmod 755 src/output/
   chmod 644 src/output/*.csv
   ```

2. **Use Alternative Output Directory**:
   ```bash
   # Use temp directory
   export OUTPUT_DIR=/tmp/scraper_output
   mkdir -p $OUTPUT_DIR
   python -m main
   ```

3. **Check Disk Space**:
   ```bash
   # Check available space
   df -h
   
   # Check specific directory
   du -sh src/output/
   ```

### Corrupted CSV Files

**Error**: CSV files are truncated or corrupted

**Cause**: Concurrent write issues or system interruption

**Solutions**:

1. **Check for Backup Files**:
   ```bash
   # Look for backup files
   ls -la src/output/*.backup
   
   # Restore from backup if needed
   cp src/output/2025-01-15.csv.backup src/output/2025-01-15.csv
   ```

2. **Test CSV Integrity**:
   ```python
   import csv
   
   # Test CSV file integrity
   csv_file = "src/output/2025-01-15.csv"
   
   try:
       with open(csv_file, 'r', encoding='utf-8') as f:
           reader = csv.DictReader(f)
           rows = list(reader)
           print(f"CSV has {len(rows)} rows")
           print(f"Columns: {reader.fieldnames}")
   except Exception as e:
       print(f"CSV error: {e}")
   ```

3. **Enable Debug Mode**:
   ```bash
   # Run with debug to see detailed output
   DEBUG=True python -m main
   ```

---

## Test Failures

### Essential Tests Failing

**Error**: `make test-essential` fails

**Cause**: Core functionality broken

**Debug Steps**:

1. **Run Tests Individually**:
   ```bash
   # Run specific test
   pytest tests/test_essential.py::TestEssential::test_csv_writer_initialization -v
   
   # Run with more output
   pytest tests/test_essential.py -v -s
   ```

2. **Check Test Environment**:
   ```python
   # Test basic imports
   try:
       from utils.csv_writer import DailyCSVWriter
       # FrenchTextProcessor removed - use dbt instead
       from config.settings import DEBUG, OFFLINE
       print("All imports successful")
   except Exception as e:
       print(f"Import error: {e}")
   ```

3. **Fix Common Issues**:
   ```python
   # Ensure test directories exist
   import os
   import tempfile
   
   temp_dir = tempfile.mkdtemp()
   print(f"Using temp directory: {temp_dir}")
   
   # Test CSV writer with temp directory
   from utils.csv_writer import DailyCSVWriter
   writer = DailyCSVWriter(output_dir=temp_dir, debug=True)
   ```

### Integration Tests Failing

**Error**: `make test-integration` fails

**Cause**: Component integration issues

**Solutions**:

1. **Test Components Individually**:
   ```python
   # Test text processing via dbt
   import subprocess
   result = subprocess.run(['make', 'dbt-run'], capture_output=True, text=True)
   print(f"dbt processing result: {result.returncode}")
   
   # Test CSV writer
   from utils.csv_writer import DailyCSVWriter
   writer = DailyCSVWriter(debug=True)
   print(f"CSV writer initialized: {writer.output_dir}")
   ```

2. **Check Test Data**:
   ```bash
   # Verify test data exists
   ls -la src/test_data/raw_url_soup/
   
   # Check file contents
   head -5 src/test_data/raw_url_soup/slate_fr/*.html
   ```

3. **Run Specific Integration Tests**:
   ```bash
   pytest tests/integration/test_basic_functionality.py::TestBasicFunctionality::test_french_text_processor_basic -v
   ```

### Offline Mode Tests Failing

**Error**: `make test-offline` fails

**Cause**: Test data or offline mode issues

**Solutions**:

1. **Check Test Data Directory**:
   ```bash
   # Verify test data structure
   find src/test_data/raw_url_soup/ -name "*.html" | head -10
   
   # Check file sizes
   du -sh src/test_data/raw_url_soup/*/
   ```

2. **Test Offline Mode Manually**:
   ```bash
   # Run offline mode
   OFFLINE=True DEBUG=True python -m main
   ```

3. **Regenerate Test Data**:
   ```python
   # Use HTML downloader to get fresh test data
   from utils.html_downloader import download_html
   
   test_urls = [
       "https://www.slate.fr/monde/exemple-article-1",
       "https://www.slate.fr/monde/exemple-article-2"
   ]
   
   for i, url in enumerate(test_urls):
       output_path = f"src/test_data/raw_url_soup/slate_fr/test_{i}.html"
       download_html(url, output_path, overwrite=True)
   ```

---

## Performance and Memory Issues

### Slow Performance

**Error**: System takes too long to complete

**Cause**: Network delays or inefficient processing

**Solutions**:

1. **Profile Performance**:
   ```python
   import time
   import cProfile
   
   # Profile the main function
   cProfile.run('main()', 'profile_output.prof')
   
   # Or use time measurements
   start_time = time.time()
   # Your code here
   end_time = time.time()
   print(f"Execution time: {end_time - start_time:.2f} seconds")
   ```

2. **Optimize Network Requests**:
   ```python
   # Use session for connection pooling
   import requests
   
   session = requests.Session()
   
   # Configure connection pool
   session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=10))
   session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10))
   
   # Use session for all requests
   response = session.get(url)
   ```

3. **Reduce Concurrency**:
   ```python
   # In processor configuration
   max_concurrent_urls = min(len(urls), 2)  # Reduce from 3 to 2
   
   # Or increase delays
   base_delay = 3.0  # Increase from 1.0 to 3.0
   ```

### Memory Usage Issues

**Error**: System uses too much memory or crashes

**Cause**: Memory leaks or large data structures

**Solutions**:

1. **Monitor Memory Usage**:
   ```python
   import tracemalloc
   import psutil
   import os
   
   # Start memory tracing
   tracemalloc.start()
   
   # Your code here
   
   # Check memory usage
   current, peak = tracemalloc.get_traced_memory()
   print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
   print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
   
   # Check system memory
   process = psutil.Process(os.getpid())
   memory_info = process.memory_info()
   print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
   ```

2. **Optimize BeautifulSoup Usage**:
   ```python
   # Clear soup objects explicitly
   def parse_article(self, soup):
       try:
           # Parse article
           result = extract_data(soup)
           return result
       finally:
           # Clean up soup
           if soup:
               soup.decompose()
   ```

3. **Use Generators for Large Data**:
   ```python
   def process_articles_generator(sources):
       """Process articles one at a time instead of loading all."""
       for soup, identifier in sources:
           if soup:
               yield self.parse_article(soup)
   
   # Use generator
   for article_data in process_articles_generator(sources):
       if article_data:
           self.to_csv(article_data, identifier)
   ```

---

## Cloud and Deployment Issues

### Container Build Failures

**Error**: Docker build fails or container won't start

**Cause**: Missing dependencies or configuration issues

**Solutions**:

1. **Check Dockerfile**:
   ```dockerfile
   # Ensure proper base image
   FROM python:3.11-slim
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       && rm -rf /var/lib/apt/lists/*
   
   # Copy requirements first for better caching
   COPY pyproject.toml .
   RUN pip install .
   
   # Copy application code
   COPY . .
   ```

2. **Test Container Locally**:
   ```bash
   # Build container
   docker build -t french-scraper .
   
   # Run container
   docker run -e OFFLINE=True -e DEBUG=True french-scraper
   
   # Debug container
   docker run -it --entrypoint /bin/bash french-scraper
   ```

3. **Check Container Logs**:
   ```bash
   # View container logs
   docker logs <container-id>
   
   # Follow logs in real-time
   docker logs -f <container-id>
   ```

### Environment Variable Issues in Cloud

**Error**: Environment variables not working in cloud deployment

**Cause**: Cloud platform configuration issues

**Solutions**:

1. **Debug Environment Variables**:
   ```python
   # Add debug output to main.py
   import os
   print("Environment variables:")
   for key, value in os.environ.items():
       if key.startswith(('DEBUG', 'OFFLINE', 'OUTPUT')):
           print(f"  {key}={value}")
   ```

2. **Platform-Specific Configuration**:
   ```yaml
   # For Google Cloud Run
   apiVersion: serving.knative.dev/v1
   kind: Service
   spec:
     template:
       spec:
         containers:
         - image: gcr.io/project/french-scraper
           env:
           - name: DEBUG
             value: "True"
           - name: OFFLINE
             value: "True"
   ```

3. **Use Cloud Configuration Services**:
   ```python
   # For cloud configuration
   def get_cloud_config():
       try:
           # Try cloud config service
           from google.cloud import secretmanager
           client = secretmanager.SecretManagerServiceClient()
           # Get configuration from cloud
       except ImportError:
           # Fallback to environment variables
           pass
   ```

### Persistent Storage Issues

**Error**: Output files not persisting in cloud

**Cause**: Container filesystem not persistent

**Solutions**:

1. **Use Cloud Storage**:
   ```python
   # Example for Google Cloud Storage
   from google.cloud import storage
   
   def upload_to_cloud_storage(filename, bucket_name):
       client = storage.Client()
       bucket = client.bucket(bucket_name)
       blob = bucket.blob(filename)
       blob.upload_from_filename(filename)
   ```

2. **Configure Volume Mounts**:
   ```yaml
   # Kubernetes example
   apiVersion: v1
   kind: Pod
   spec:
     containers:
     - name: french-scraper
       image: french-scraper:latest
       volumeMounts:
       - name: output-storage
         mountPath: /app/src/output
     volumes:
     - name: output-storage
       persistentVolumeClaim:
         claimName: scraper-output-pvc
   ```

---

## Logging and Debugging

### Enable Debug Logging

**Enable comprehensive debug output**:

```bash
# Set debug mode
export DEBUG=True

# Run with debug
DEBUG=True python -m main

# View logs with timestamps
DEBUG=True python -m main 2>&1 | ts '[%Y-%m-%d %H:%M:%S]'
```

### Advanced Debugging

**Use Python debugger**:

```python
# Add to code for debugging
import pdb; pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()

# Debug specific function
def debug_function():
    import pdb; pdb.set_trace()
    # Your code here
```

### Logging Configuration

**Enable specific component logging**:

```python
# In main.py or debug script
import logging

# Set specific logger levels
logging.getLogger('scrapers').setLevel(logging.DEBUG)
logging.getLogger('parsers').setLevel(logging.DEBUG)
logging.getLogger('utils').setLevel(logging.DEBUG)

# Or set root logger to debug
logging.getLogger().setLevel(logging.DEBUG)
```

### Performance Debugging

**Monitor system resources**:

```python
# Monitor during execution
import psutil
import time

def monitor_resources():
    process = psutil.Process()
    
    while True:
        cpu_percent = process.cpu_percent()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        print(f"CPU: {cpu_percent}%, Memory: {memory_mb:.2f} MB")
        time.sleep(1)

# Run in background thread
import threading
monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
monitor_thread.start()
```

---

## Common Solutions Summary

### Quick Fixes

1. **Virtual Environment**: `source venv/bin/activate`
2. **Working Directory**: `cd /path/to/project && python -m main`
3. **Dependencies**: `pip install -e .`
4. **Permissions**: `chmod 755 src/output/`
5. **Test Mode**: `OFFLINE=True DEBUG=True python -m main`

### Emergency Debugging

```bash
# Nuclear option: fresh start
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e .
OFFLINE=True DEBUG=True python -m main
```

### Get Help

When all else fails:

1. **Check logs**: Look for error messages in debug output
2. **Test components**: Isolate the failing component
3. **Minimal example**: Create a simple test case
4. **Document steps**: Note exact steps to reproduce
5. **Check recent changes**: What changed since it last worked?

---

## Cross-References

- [[00-System-Architecture]] - Understanding system components
- [[04-Testing]] - Testing framework and patterns
- [[05-Utils]] - Utility functions and debugging tools
- [[06-Config]] - Configuration management
- [[08-Adding-News-Source]] - Adding new sources
- [[10-CI-CD]] - Continuous integration and deployment
- [[11-Project-Maintenance]] - Regular maintenance procedures