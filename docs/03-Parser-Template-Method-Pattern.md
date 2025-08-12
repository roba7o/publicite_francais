# Parser Template Method Pattern

## How Site-Specific Parsing Works with Shared Infrastructure

This document explains the **Template Method pattern** implementation in the parser layer - how common functionality is shared while allowing site-specific customization.

## Template Method Pattern Overview

### **Problem Being Solved**
- Multiple news sites have different HTML structures
- Common operations: HTTP requests, session management, database storage
- Site-specific operations: CSS selectors, date parsing, text extraction

### **Solution Architecture**
```
DatabaseBaseParser (Template)
├── Common: HTTP session, rate limiting, database storage
├── Abstract: parse_article() - implemented by children
└── Children: Site-specific HTML parsing logic
```

## Base Class Template (`database_base_parser.py`)

### **Template Method Structure**
```python
class DatabaseBaseParser(ABC):
    # COMMON: Shared HTTP session (Singleton pattern)
    _session = None
    
    # COMMON: Initialization with shared dependencies
    def __init__(self, site_domain: str, source_id: str, delay: float = 1.0):
        self.logger = get_structured_logger(self.__class__.__name__)
        self.repository = ArticleRepository()
        self.source_id = source_id
        
    # COMMON: HTTP session management
    @classmethod
    def get_session(cls): # Shared session across all parsers
    
    # COMMON: Web scraping with retries and rate limiting  
    def get_soup_from_url(self, url: str) -> Optional[BeautifulSoup]:
    
    # COMMON: Offline testing support
    def get_test_sources_from_directory(self, source_name: str):
    
    # ABSTRACT: Site-specific implementation required
    @abstractmethod
    def parse_article(self, soup: BeautifulSoup) -> Optional[ArticleData]:
        pass
        
    # COMMON: Database storage using repository
    def to_database(self, article_data: ArticleData, url: str) -> bool:
```

### **What Base Class Provides (Don't Repeat)**

#### 1. **HTTP Session Management** (Lines 66-99)
```python
@classmethod
def get_session(cls):
    if cls._session is None:
        cls._session = requests.Session()
        
        # Retry strategy for resilience
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        # Connection pooling for performance
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,    # Up to 10 concurrent connections
            pool_maxsize=20,        # 20 connections per pool
            pool_block=False        # Don't block when pool full
        )
```

**Benefits:**
- **Singleton**: One session shared across all parser instances
- **Connection Pooling**: Reuse TCP connections for performance
- **Retry Logic**: Automatic retry on server errors
- **Rate Limiting**: Built-in delays between requests

#### 2. **Web Scraping with Error Handling** (Lines 101-146)
```python
def get_soup_from_url(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
    for attempt in range(max_retries):
        try:
            session = self.get_session()
            response = session.get(url, timeout=15)
            time.sleep(self.delay)  # Rate limiting
            response.raise_for_status()
            
            # Validate response quality
            if len(response.content) < 100:
                continue  # Try again if content too short
                
            return BeautifulSoup(response.content, "html.parser")
            
        except requests.exceptions.RequestException as e:
            # Log and retry
            if attempt < max_retries - 1:
                time.sleep(1 + attempt)  # Exponential backoff
```

**Error Handling Strategy:**
- **Timeout Protection**: 15-second request timeout
- **Content Validation**: Skip responses that are too short
- **Exponential Backoff**: Increasing delays between retries
- **Graceful Degradation**: Return None on complete failure

#### 3. **Offline Testing Support** (Lines 148-187)
```python
def get_test_sources_from_directory(self, source_name: str):
    # Load HTML files from src/test_data/raw_url_soup/[SourceName]/
    test_data_dir = project_root / "src" / "test_data" / "raw_url_soup"
    source_dir = test_data_dir / source_name
    
    # Map filenames to original URLs for testing
    from test_data.url_mapping import URL_MAPPING
    
    for file_path in source_dir.iterdir():
        if file_path.suffix in (".html", ".php"):
            filename = file_path.name
            original_url = URL_MAPPING.get(filename, f"test://{filename}")
            
            soup = BeautifulSoup(file.read(), "html.parser")
            soup_sources.append((soup, original_url))
```

#### 4. **Database Storage Interface** (Lines 211-222)
```python
def to_database(self, article_data: ArticleData, url: str) -> bool:
    return self.repository.store_article(article_data, url, self.source_id)
```

## Child Class Implementation Example

### **Slate.fr Parser** (`parsers/database_slate_fr_parser.py`)

```python
class DatabaseSlateFrParser(DatabaseBaseParser):
    def __init__(self, source_id: str):
        super().__init__("slate.fr", source_id, delay=1.0)
    
    def parse_article(self, soup: BeautifulSoup) -> Optional[ArticleData]:
        try:
            # Site-specific CSS selectors
            title_elem = soup.find("h1", class_="article-title")
            title = title_elem.get_text(strip=True) if title_elem else "No title found"
            
            # Extract article content
            content_elem = soup.find("div", class_="article-content")
            if not content_elem:
                return None
                
            paragraphs = content_elem.find_all("p")
            full_text = " ".join([p.get_text(strip=True) for p in paragraphs])
            
            # Extract publication date
            date_elem = soup.find("time", {"datetime": True})
            article_date = date_elem["datetime"][:10] if date_elem else "Unknown date"
            
            return ArticleData(
                title=title,
                full_text=full_text,
                article_date=article_date,
                num_paragraphs=len(paragraphs)
            )
            
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            return None
```

**Child Class Responsibilities:**
- **HTML Structure Knowledge**: Know site-specific CSS selectors
- **Content Extraction**: Extract title, text, date from HTML
- **Error Handling**: Handle malformed HTML gracefully
- **Data Transformation**: Convert HTML to `ArticleData` format

## Template Method Flow

### **Processing Workflow**
```python
# In DatabaseProcessor.process_article():
def process_article(self, parser, soup, url, source_name):
    # 1. Template method calls child implementation
    article_data = parser.parse_article(soup)  # CHILD IMPLEMENTS
    
    # 2. Template method handles storage
    return parser.to_database(article_data, url)  # BASE IMPLEMENTS
```

### **Complete Execution Trace**

1. **Setup**: `DatabaseBaseParser.__init__()` creates shared dependencies
2. **Content Acquisition**: `get_soup_from_url()` or `get_test_sources_from_directory()`
3. **Parsing**: Child's `parse_article()` extracts site-specific data
4. **Storage**: Base's `to_database()` stores via repository pattern

## Site-Specific Variations

### **Different CSS Selectors by Site**

#### **Slate.fr**
```python
title_elem = soup.find("h1", class_="article-title")
content_elem = soup.find("div", class_="article-content")
date_elem = soup.find("time", {"datetime": True})
```

#### **FranceInfo.fr**  
```python
title_elem = soup.find("h1", class_="headline")
content_elem = soup.find("div", class_="story-body")
date_elem = soup.find("span", class_="publication-date")
```

#### **TF1 Info**
```python
title_elem = soup.find("h1", class_="title")
content_elem = soup.find("article", class_="content")
date_elem = soup.find("div", {"data-testid": "date"})
```

### **Different Date Format Handling**

Each site publishes dates in different formats:
- **Slate.fr**: ISO format `"2025-01-15T14:30:00Z"`
- **FranceInfo.fr**: French format `"15 janvier 2025"`  
- **TF1 Info**: Relative format `"Il y a 2 heures"`

Child parsers handle these variations in `parse_article()`, while base class handles date normalization in the repository layer.

## Benefits of Template Method Pattern

### **Code Reuse** ✅
- HTTP session management shared across all sites
- Database storage logic written once
- Error handling and retry logic consistent

### **Separation of Concerns** ✅
- **Base class**: Infrastructure and common operations
- **Child classes**: Site-specific domain knowledge
- **Repository**: Database operations
- **Models**: Data structures

### **Testability** ✅
```python
# Mock only the abstract method for testing
class MockParser(DatabaseBaseParser):
    def parse_article(self, soup):
        return ArticleData(title="Test", full_text="Test content", ...)

# Base functionality (HTTP, database) remains real
```

### **Maintainability** ✅
- **Add new sites**: Only implement `parse_article()`
- **Change HTTP logic**: Modify base class only
- **Update database schema**: Change repository only

## Common Patterns in Child Classes

### **Error Handling Strategy**
```python
def parse_article(self, soup):
    try:
        # Attempt primary CSS selectors
        title = soup.find("h1", class_="main-title").get_text()
    except AttributeError:
        try:
            # Fallback selectors for different page layouts
            title = soup.find("h1").get_text()
        except AttributeError:
            # Last resort
            title = "No title found"
```

### **Content Validation**
```python
# Validate extracted content before returning
if not full_text or len(full_text) < 100:
    self.logger.warning("Article content too short, skipping")
    return None

if "404" in title.lower() or "not found" in title.lower():
    self.logger.warning("404 page detected, skipping")
    return None
```

### **Text Cleaning**
```python
# Clean up common HTML artifacts
full_text = re.sub(r'\s+', ' ', full_text)  # Normalize whitespace
full_text = full_text.replace('\xa0', ' ')  # Remove non-breaking spaces
full_text = html.unescape(full_text)        # Decode HTML entities
```

This template method implementation provides a robust foundation for parsing multiple news sites while keeping site-specific logic isolated and maintainable.