# Django Backend Integration Strategy

> [!abstract] Overview
> This document outlines what to consider when preparing your French article scraper for Django web application integration. It focuses on data modeling considerations and provides a prompt for future implementation.

## Table of Contents
- [[#Key Considerations Summary|Key Considerations Summary]]
- [[#Current Pipeline Modifications|Current Pipeline Modifications]]
- [[#Implementation Prompt|Implementation Prompt]]

---

## Key Considerations Summary

### 1. **Data Structure Enhancements**
Your current CSV output needs to be richer for Django:

**Current**: `word, context, source, article_date, scraped_date, title, frequency`

**Django Needs**: 
- **Article metadata**: `slug, source_name, reading_time, word_count, difficulty_level`
- **Word positioning**: `word_position, sentence_position` 
- **Relationships**: Separate tables for articles, words, and word occurrences
- **User features**: Fields for user progress, flashcards, learning analytics

### 2. **Database vs CSV**
- **Keep CSV**: For backup and data portability
- **Add Database**: PostgreSQL for Django integration
- **Dual Output**: Write to both simultaneously
- **Migration Plan**: Convert existing CSV data to database format

### 3. **API Design Planning**
- **RESTful Structure**: `/api/articles/`, `/api/words/`, `/api/flashcards/`
- **Search Capabilities**: Full-text search on articles and words
- **Filtering**: By difficulty, source, date, word frequency
- **Pagination**: Handle large datasets efficiently

### 4. **Authentication & Users**
- **User Profiles**: Learning levels (A1-C2), goals, preferences
- **Progress Tracking**: Word mastery, learning streaks, performance analytics
- **Personalization**: Difficulty-based word recommendations

### 5. **Performance Considerations**
- **Caching**: Redis for frequently accessed data
- **Database Indexing**: Optimize for search and filtering
- **Connection Pooling**: Handle concurrent requests efficiently

---

## Current Pipeline Modifications

### What to Modify in Your Scraper NOW:

1. **Expand ArticleData Model**
   ```python
   # Add these fields to your existing ArticleData:
   source_name: str      # "Slate.fr" vs full URL
   slug: str            # URL-friendly title
   reading_time: int    # Minutes to read
   word_count: int      # Total words
   difficulty_level: str # A1-C2 estimation
   ```

2. **Enhance CSV Output**
   ```python
   # Add these columns to CSV_FIELDS:
   "source_name", "article_slug", "word_position", 
   "difficulty_level", "reading_time", "word_count"
   ```

3. **Add Text Processing Methods**
   ```python
   # Add to FrenchTextProcessor:
   def create_slug(title: str) -> str
   def estimate_reading_time(text: str) -> int
   def estimate_difficulty(text: str) -> str
   def get_word_positions(text: str, words: List[str]) -> Dict
   ```

4. **Implement Article Deduplication**
   ```python
   # Prevent processing same article multiple times
   def generate_article_hash(title: str, content: str) -> str
   def is_duplicate(article_data: ArticleData) -> bool
   ```

---

## Implementation Prompt

When you're ready to implement these Django integration changes, provide this prompt:

---

### 🤖 **Implementation Prompt**

```
I'm ready to implement Django integration changes for my French article scraper. Based on the Django Backend Integration Strategy document, please help me:

1. **Modify Current Data Models**:
   - Expand ArticleData class with Django-friendly fields (slug, source_name, reading_time, word_count, difficulty_level)
   - Update CSV_FIELDS to include new columns
   - Modify existing CSV output to include enhanced data

2. **Enhance Text Processing**:
   - Add create_slug() method to FrenchTextProcessor
   - Add estimate_reading_time() method
   - Add estimate_difficulty() method (simple heuristic is fine)
   - Add get_word_positions() method for tracking word locations

3. **Update Base Parser**:
   - Modify to_csv() method to generate and include new fields
   - Add article deduplication logic
   - Ensure backward compatibility with existing CSV structure

4. **Add Configuration**:
   - Create django-compatible settings
   - Add new configuration options for enhanced features

Please provide the exact code changes needed for each file, maintaining my existing functionality while adding Django-ready features. Focus on minimal changes that enhance data richness without breaking current operations.

My current key files are:
- src/models.py (ArticleData class)
- src/utils/french_text_processor.py (text processing)
- src/parsers/base_parser.py (base parser with to_csv method)
- src/utils/csv_writer.py (CSV output)
- src/config/settings.py (configuration)
```

---

### 🎯 **Expected Outcome**

After implementation, your scraper will output enhanced data that includes:
- Article slugs for Django URL routing
- Reading time estimates for user experience
- Difficulty levels for personalized learning
- Word positions for advanced analytics
- Deduplication to prevent redundant processing
- Rich metadata for Django model population

This enhanced data structure will seamlessly integrate with Django models and provide the foundation for user features like progress tracking, personalized recommendations, and learning analytics.

---

> [!success] Django Integration Preparation
> This focused approach enhances your current scraper output to be Django-ready while maintaining existing functionality. Use the implementation prompt when you're ready to make these changes.

*Last updated: 2025-07-18*