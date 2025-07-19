# Glossary of Terms and Acronyms

> [!abstract] Overview
> This glossary provides definitions of technical terms, acronyms, and project-specific concepts used throughout the French article scraper system documentation and codebase.

## Table of Contents
- [[#Technical Terms|Technical Terms]]
- [[#Architecture Components|Architecture Components]]
- [[#French Language Processing|French Language Processing]]
- [[#News Source Terms|News Source Terms]]
- [[#Development and Testing|Development and Testing]]
- [[#Configuration and Deployment|Configuration and Deployment]]
- [[#Acronyms and Abbreviations|Acronyms and Abbreviations]]

---

## Technical Terms

### Article Parser
A component that extracts structured data (title, content, date, author) from HTML article pages. Each news source has its own parser class that understands the specific HTML structure of that site.

### BeautifulSoup
A Python library for parsing HTML and XML documents. Used throughout the system for extracting content from web pages and test data files.

### CSV Writer
The `DailyCSVWriter` class that handles thread-safe writing of processed article data to CSV files, with automatic file rotation based on dates.

### Data Validation
The process of ensuring extracted article data meets quality standards before processing. Includes checking for required fields, content length, and data integrity.

### Debug Mode
Operational mode activated by setting `DEBUG=True` that provides detailed logging output, performance metrics, and diagnostic information.

### Dynamic Class Loading
The system's ability to load scraper and parser classes at runtime based on configuration strings, enabling flexible source management without code changes.

### HTML Downloader
Utility for downloading and saving HTML content from URLs, used for creating test data and offline mode support.

### Offline Mode
Operational mode activated by setting `OFFLINE=True` that processes pre-downloaded test data instead of making live web requests.

### Rate Limiting
The practice of adding delays between web requests to avoid overwhelming target servers and prevent being blocked.

### Structured Logger
A logging system that outputs JSON-formatted log messages with consistent fields for easy parsing and analysis.

### URL Scraper
A component that extracts article URLs from news source homepage or category pages. Each news source has its own scraper class.

---

## Architecture Components

### Article Processor
The main orchestration component (`ArticleProcessor`) that manages the entire scraping workflow, from URL discovery through content extraction to CSV output.

### Configuration System
The collection of configuration modules that manage global settings, source definitions, text processing parameters, and junk word patterns.

### Core Processor
The central processing engine that coordinates between scrapers, parsers, and utilities to process articles from multiple news sources.

### French Text Processor
The `FrenchTextProcessor` class that handles French-specific text analysis including word frequency counting, accent normalization, and stopword filtering.

### Mermaid Diagrams
Visual representations of system architecture, data flow, and component interactions used throughout the documentation.

### Modular Architecture
The system's design pattern where each component (scrapers, parsers, utilities) is self-contained and can be independently developed and tested.

### Source Configuration
The `ScraperConfig` dataclass that defines how each news source should be processed, including class paths, parameters, and settings.

### Test Data Infrastructure
The system of pre-downloaded HTML files and test utilities that enable offline development and testing.

### ThreadPoolExecutor
Python's concurrent execution framework used for parallel processing of multiple articles while maintaining thread safety.

### Validator System
Components that ensure data quality and integrity at various stages of processing, from raw HTML to final CSV output.

---

## French Language Processing

### Accent Normalization
The process of converting accented French characters (é, è, ê, ë) to their non-accented equivalents for consistent text processing.

### Context Extraction
The process of finding and extracting sentences that contain specific words, used for understanding word usage patterns in articles.

### French Stopwords
Common French words (le, la, les, de, du, que, etc.) that are filtered out during text analysis because they don't carry significant meaning.

### Junk Words
Non-meaningful words, phrases, or patterns that are filtered out during text processing, including UI elements, navigation terms, and technical artifacts.

### Lemmatization
The process of reducing French words to their base forms (e.g., "mangeons" → "manger") for more accurate frequency analysis.

### Minimum Word Frequency
The threshold below which words are excluded from analysis, used to filter out rare or potentially noisy terms.

### Site-Specific Stopwords
Additional stopwords tailored to specific news sources to filter out site-specific UI elements and branding terms.

### Text Normalization
The process of standardizing text by removing extra whitespace, converting to lowercase, and handling special characters.

### Word Context
The surrounding text (typically full sentences) in which a word appears, used for understanding word usage and meaning.

### Word Frequency Analysis
The process of counting how often each word appears in an article, used for content analysis and keyword extraction.

---

## News Source Terms

### Article Card
HTML elements on news homepages that contain article previews, typically including title, summary, and link to full article.

### Article Container
HTML elements that contain the main content of an article page, identified by CSS selectors like `.article-content` or `.content`.

### Article Slug
The URL-friendly version of an article title used in URLs (e.g., "politique-france-2025" for "Politique France 2025").

### Base URL
The root URL of a news source (e.g., "https://www.slate.fr/") used for constructing absolute URLs from relative links.

### CSS Selector
Patterns used to identify HTML elements, such as `article.news-item` or `h1.article-title`.

### Date Selector
CSS selector used to locate article publication dates, often targeting `<time>` elements or date-containing classes.

### Homepage Scraping
The process of extracting article URLs from a news source's main page or category pages.

### Link Pattern
The consistent URL structure used by a news source for articles (e.g., `/article/[slug]` or `/news/[id]/[title]`).

### News Source
A French news website integrated into the scraper system, such as Slate.fr, FranceInfo, TF1 Info, or La Dépêche.

### Scraper Class
The Python class responsible for extracting article URLs from a specific news source's homepage or category pages.

### User Agent
The browser identification string sent with HTTP requests to appear as a legitimate browser rather than a bot.

---

## Development and Testing

### Code Coverage
The percentage of code lines executed during testing, tracked to ensure comprehensive test coverage.

### Essential Tests
Quick tests (≤2 seconds) that validate core functionality and can be run frequently during development.

### Integration Tests
Tests that verify components work together correctly, including end-to-end workflow testing.

### Mock Objects
Test utilities that simulate external dependencies (like web requests) to enable predictable, isolated testing.

### Offline Mode Testing
Testing using pre-downloaded HTML files instead of live web requests, enabling consistent and fast test execution.

### Performance Testing
Tests that measure execution time, memory usage, and throughput to ensure system meets performance requirements.

### Pytest Framework
The testing framework used for running unit tests, integration tests, and test automation.

### Test Data
Pre-downloaded HTML files stored in `src/test_data/raw_url_soup/` directories for offline testing.

### Test-Driven Development (TDD)
The development approach where tests are written before implementation code.

### Unit Tests
Tests that verify individual components work correctly in isolation.

---

## Configuration and Deployment

### CI/CD Pipeline
Continuous Integration/Continuous Deployment system using GitHub Actions for automated testing and deployment.

### Cloud Run
Google's serverless container platform used for deploying the scraper system to the cloud.

### Configuration Module
Python modules in the `config/` directory that define system settings and parameters.

### Docker Container
A packaged version of the application with all dependencies, used for consistent deployment across environments.

### Environment Variables
System variables (DEBUG, OFFLINE, etc.) that control application behavior without code changes.

### GitHub Actions
The CI/CD platform used for automated testing, building, and deployment of the system.

### Health Check
An endpoint or process that verifies the system is running correctly and can process articles.

### Production Environment
The live deployment environment where the system processes real news articles.

### Rollback
The process of reverting to a previous version of the system if deployment issues occur.

### Staging Environment
A pre-production environment used for testing changes before deployment to production.

---

## Acronyms and Abbreviations

### API
Application Programming Interface - Standard interface for software components to communicate.

### BS4
BeautifulSoup4 - The Python library used for HTML parsing.

### CI/CD
Continuous Integration/Continuous Deployment - Automated development and deployment processes.

### CSV
Comma-Separated Values - The file format used for storing processed article data.

### CSS
Cascading Style Sheets - Used for CSS selectors to identify HTML elements.

### DEBUG
Debug mode flag - Environment variable that enables detailed logging and diagnostic output.

### DOM
Document Object Model - The structure of HTML documents that parsers navigate.

### GCP
Google Cloud Platform - Cloud infrastructure used for deployment.

### HTML
HyperText Markup Language - The markup language used by web pages.

### HTTP
HyperText Transfer Protocol - The protocol used for web requests.

### JSON
JavaScript Object Notation - Format used for structured logging and configuration.

### NLP
Natural Language Processing - The field of AI focused on processing human language.

### OFFLINE
Offline mode flag - Environment variable that enables test data processing mode.

### OOP
Object-Oriented Programming - Programming paradigm used throughout the system.

### RAM
Random Access Memory - System memory monitored during performance testing.

### REST
Representational State Transfer - Architectural style for web services.

### RSS
Really Simple Syndication - Feed format that could be used for article discovery.

### SLA
Service Level Agreement - Performance and availability commitments.

### SQL
Structured Query Language - Database query language (not used in current system).

### TDD
Test-Driven Development - Development methodology emphasizing tests first.

### UA
User Agent - Browser identification string used in HTTP requests.

### URL
Uniform Resource Locator - Web addresses used to identify articles and resources.

### UTF-8
Unicode Transformation Format 8-bit - Character encoding used for French text.

### XML
eXtensible Markup Language - Markup language similar to HTML.

---

## Project-Specific Terms

### DailyCSVWriter
The specific CSV writer class that creates date-based output files with thread-safe writing capabilities.

### FrenchTextProcessor
The specialized text processing class optimized for French language content analysis.

### ScraperConfig
The dataclass that defines configuration parameters for each news source.

### ArticleProcessor
The main orchestration class that manages the entire article processing workflow.

### SCRAPER_CONFIGS
The list of source configurations that defines which news sources are active and how they should be processed.

### SITE_CONFIGS
The dictionary of site-specific text processing configurations for different news sources.

### JUNK_WORDS
The collection of patterns and words that should be filtered out during text processing.

### get_structured_logger
The utility function that creates JSON-formatted loggers for consistent logging across components.

### import_class
The dynamic class loading utility that converts configuration strings into actual Python classes.

### validate_article_data
The function that ensures extracted article data meets quality standards before processing.

---

## Cross-References

- [[00-System-Architecture]] - Understanding system components and their relationships
- [[01-Scrapers]] - URL scraping implementations and patterns
- [[02-Parsers]] - Article parsing implementations and patterns
- [[03-Processor]] - Core processing orchestration
- [[04-Testing]] - Testing framework and methodologies
- [[05-Utils]] - Utility functions and support infrastructure
- [[06-Config]] - Configuration management system
- [[07-Python-Concepts]] - Python programming concepts used
- [[08-Adding-News-Source]] - Process for adding new sources
- [[09-Troubleshooting]] - Common issues and solutions
- [[10-CI-CD]] - Continuous integration and deployment
- [[11-Project-Maintenance]] - Maintenance and cleanup procedures