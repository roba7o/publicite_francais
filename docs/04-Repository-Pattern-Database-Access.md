# Repository Pattern: Database Access Layer

## How Database Operations Are Abstracted and Centralized

This document explains the **Repository pattern** implementation - how database operations are separated from business logic and centralized in dedicated classes.

## Repository Pattern Overview

### **Problem Being Solved**
- Business logic mixed with SQL queries makes code hard to test
- Database operations scattered throughout codebase
- Multiple places need similar database operations (duplicated queries)
- Difficult to change database schema or switch databases

### **Solution Architecture**
```
Business Logic (Parsers, Processors) → Repository Interface → Database Implementation
```

## Repository Interface Design

### **ArticleRepository Class** (`database/article_repository.py`)

```python
class ArticleRepository:
    """Repository for article database operations."""
    
    def __init__(self):
        from database import get_database_manager
        self.db = get_database_manager()
        self.schema_name = NEWS_DATA_SCHEMA
    
    # PUBLIC INTERFACE - What other classes use
    def get_source_id(self, source_name: str) -> Optional[str]
    def store_article(self, article_data: ArticleData, url: str, source_id: str) -> bool
    
    # PRIVATE HELPERS - Internal implementation details
    def _parse_article_date(self, date_str: str) -> Optional[str]
```

### **Clean Interface Boundaries**

#### **What Clients See** (Simple)
```python
# In DatabaseBaseParser.to_database():
return self.repository.store_article(article_data, url, self.source_id)
```

#### **What Repository Handles** (Complex)
- SQL query construction
- Transaction management  
- Error handling
- Data validation and transformation
- Duplicate detection
- Date parsing and normalization

## Core Repository Operations

### 1. **Source ID Lookup** (`get_source_id()` - Lines 29-49)

```python
def get_source_id(self, source_name: str) -> Optional[str]:
    try:
        with self.db.get_session() as session:
            result = session.execute(
                text(f"""
                SELECT id FROM {self.schema_name}.news_sources
                WHERE name = :name
            """),
                {"name": source_name},
            )
            
            row = result.fetchone()
            return str(row[0]) if row else None
            
    except Exception as e:
        self.logger.error(
            "Failed to get source ID",
            extra_data={"source_name": source_name, "error": str(e)}
        )
        return None
```

**Repository Benefits Here:**
- **Error Isolation**: Database errors don't crash business logic
- **Logging Centralization**: All database errors logged consistently
- **Query Centralization**: Source lookup logic in one place
- **Type Safety**: Returns Optional[str] with clear None semantics

### 2. **Article Storage** (`store_article()` - Lines 101-212)

#### **Transaction Management**
```python
def store_article(self, article_data, url, source_id):
    with self.db.get_session() as session:
        # All operations in single transaction
        check_url_duplicates()
        check_title_date_duplicates() 
        insert_article()
        session.commit()  # Atomic - all operations succeed or all fail
```

#### **Duplicate Detection Strategy**
```python
# 1. URL-based duplicate detection
existing_url = session.execute(
    text(f"SELECT id FROM {self.schema_name}.articles WHERE source_id = :source_id AND url = :url"),
    {"source_id": source_id, "url": url}
)

# 2. Title+Date duplicate detection (for URL changes)
if parsed_article_date:
    existing_title_date = session.execute(
        text(f"SELECT id FROM {self.schema_name}.articles WHERE source_id = :source_id AND title = :title AND article_date = :article_date"),
        {"source_id": source_id, "title": article_data.title, "article_date": parsed_article_date}
    )
```

**Why Two Duplicate Checks?**
- **URL-based**: Catches exact same article reprocessed
- **Title+Date**: Catches same article with different URL (URL structure changes)

#### **Data Transformation Layer**
```python
# Repository handles messy date parsing
parsed_article_date = self._parse_article_date(article_data.article_date)

# Repository generates UUIDs
article_id = uuid4()

# Repository handles database field mapping
session.execute(
    text(f"""INSERT INTO {self.schema_name}.articles
    (id, source_id, title, url, article_date, scraped_at, full_text, num_paragraphs)
    VALUES (:id, :source_id, :title, :url, :article_date, :scraped_at, :full_text, :num_paragraphs)"""),
    {
        "id": str(article_id),
        "source_id": source_id,
        "title": article_data.title,
        "url": url,
        "article_date": parsed_article_date,      # Transformed
        "scraped_at": datetime.now(),             # Added by repository
        "full_text": article_data.full_text,
        "num_paragraphs": article_data.num_paragraphs,
    }
)
```

### 3. **Date Parsing Logic** (`_parse_article_date()` - Lines 51-99)

```python
def _parse_article_date(self, date_str: str) -> Optional[str]:
    # Handle common "no date" cases
    if not date_str or date_str.lower() in ["unknown date", "no date found", "unknown", ""]:
        return None

    # Validate YYYY-MM-DD format
    if len(date_str) == 10 and date_str.count("-") == 2:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            pass

    # Try multiple date formats
    date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]
    
    for fmt in date_formats:
        try:
            clean_date = date_str.split("T")[0].split(" ")[0]  # Handle datetime strings
            dt = datetime.strptime(clean_date, fmt)
            return dt.strftime("%Y-%m-%d")  # Normalize to YYYY-MM-DD
        except ValueError:
            continue
    
    # Log unparseable dates for debugging
    self.logger.warning(f"Could not parse article date: '{date_str}', storing as NULL")
    return None
```

**Date Parsing Strategy:**
- **Normalize Format**: All dates stored as YYYY-MM-DD or NULL
- **Handle Variations**: ISO format, US format, European format, datetime strings
- **Graceful Degradation**: Store NULL for unparseable dates rather than failing
- **Debugging Support**: Log unparseable formats for investigation

## Repository Pattern Benefits

### 1. **Separation of Concerns** ✅

#### **Business Logic** (In Parsers)
```python
# Parser focuses on HTML extraction
article_data = ArticleData(
    title=title_elem.get_text(),
    full_text=content_elem.get_text(),
    article_date=date_elem.get("datetime"),
    num_paragraphs=len(paragraphs)
)

# Simple storage call
success = self.repository.store_article(article_data, url, self.source_id)
```

#### **Data Access Logic** (In Repository)
- SQL query construction
- Transaction boundaries
- Error handling and recovery
- Data validation and transformation
- Database schema knowledge

### 2. **Testability** ✅

#### **Easy Mocking for Unit Tests**
```python
class MockArticleRepository:
    def store_article(self, article_data, url, source_id):
        return True  # Always succeed for testing
    
    def get_source_id(self, source_name):
        return "test-uuid-12345"
```

#### **Integration Tests with Real Database**
```python
def test_duplicate_detection():
    repo = ArticleRepository()
    
    # Store article first time
    result1 = repo.store_article(test_article, "http://test.com", source_id)
    assert result1 is True
    
    # Store same article again - should be rejected
    result2 = repo.store_article(test_article, "http://test.com", source_id)
    assert result2 is False
```

### 3. **Query Centralization** ✅

All article-related database operations in one place:
- Easy to optimize queries
- Consistent error handling
- Single place to add caching
- Clear performance monitoring

### 4. **Database Independence** ✅

```python
# Repository uses SQLAlchemy text() - database agnostic
session.execute(text("SELECT id FROM articles WHERE url = :url"), {"url": url})

# Could switch to different database with same repository interface:
# - PostgreSQL → MySQL: Change connection string only
# - SQL → NoSQL: Reimplement repository, keep same interface
```

## Advanced Repository Features

### **Connection Management**
```python
def __init__(self):
    from database import get_database_manager
    self.db = get_database_manager()  # Dependency injection of database manager
```

**Benefits:**
- **Lazy Loading**: Database connection created only when needed
- **Connection Pooling**: SQLAlchemy handles connection reuse
- **Configuration Driven**: Database settings from environment variables

### **Structured Logging Integration**
```python
self.logger.info(
    "Raw article stored successfully",
    extra_data={
        "article_id": str(article_id),
        "title": article_data.title[:50] + "..." if len(article_data.title) > 50 else article_data.title,
        "url": url,
        "text_length": len(article_data.full_text),
    }
)
```

**Monitoring Benefits:**
- **Structured Data**: Machine-readable logs for monitoring
- **Performance Tracking**: Log article processing metrics
- **Error Analysis**: Detailed error context for debugging

### **Graceful Error Handling**
```python
try:
    # Database operations
    session.commit()
    return True
except Exception as e:
    self.logger.error(
        "Failed to store raw article",
        extra_data={"url": url, "error": str(e)},
        exc_info=True  # Include full stack trace
    )
    return False  # Don't crash - let processing continue
```

## Repository Usage Patterns

### **In Parsers** (Primary Usage)
```python
class DatabaseBaseParser:
    def __init__(self, site_domain, source_id):
        self.repository = ArticleRepository()  # Dependency
    
    def to_database(self, article_data, url):
        return self.repository.store_article(article_data, url, self.source_id)
```

### **In Services** (Orchestration)
```python
class DatabaseProcessor:
    def get_source_id(self, source_name):
        source_id = self.article_repo.get_source_id(source_name)
        if not source_id:
            self.output.error(f"Source not found: {source_name}")
        return source_id
```

### **In Tests** (Validation)
```python
def test_article_storage():
    repo = ArticleRepository()
    test_article = ArticleData(title="Test", full_text="Content", ...)
    
    success = repo.store_article(test_article, "http://test.com", source_id)
    assert success is True
```

## Alternative Patterns

### **Active Record Pattern** (Not Used)
```python
# Articles would have database methods
class Article:
    def save(self):
        # SQL logic mixed with model
        
    def find_duplicates(self):
        # Query logic in model class
```

**Why Repository is Better:**
- **Single Responsibility**: Models are data, repositories are persistence
- **Testability**: Easy to mock repository, hard to mock Active Record
- **Query Complexity**: Repository can have complex queries without bloating models

### **Data Mapper Pattern** (More Complex)
```python
# Separate mapper classes for each entity type
class ArticleMapper:
    def insert(article): # Implementation
    def find_by_url(url): # Implementation
    
class SourceMapper:
    def find_by_name(name): # Implementation
```

**Repository vs Data Mapper:**
- **Repository**: Higher-level, domain-focused operations
- **Data Mapper**: Lower-level, CRUD-focused operations
- **Current Choice**: Repository is simpler for this application's needs

This repository implementation provides clean separation between business logic and data access, making the codebase more maintainable, testable, and flexible.