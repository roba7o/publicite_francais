# French News Scraper

A Python-based web scraping application that extracts French news articles and stores them in a PostgreSQL database. Built with modern Python practices and containerized infrastructure.

## Tech Stack

### Backend
- **Python 3.12+** - Modern Python with type hints and async capabilities
- **SQLAlchemy 2.0** - Modern ORM with async support
- **PostgreSQL 17** - Primary database (Alpine Docker container)
- **psycopg2** - PostgreSQL adapter for Python

### Web Scraping & Processing
- **BeautifulSoup4** - HTML parsing and extraction
- **Trafilatura** - Advanced text extraction and content cleaning
- **Requests** - HTTP client for web requests
- **lxml** - Fast XML/HTML processing
- **tldextract** - URL domain extraction

### Development & Testing
- **pytest** - Testing framework -> CURRENTLY REFACTORING
- **Ruff** - Modern Python linter and formatter (replaces Black + flake8)
- **Docker Compose** - Container orchestration
- **python-dotenv** - Environment variable management

### Architecture
```
Python Scraper → PostgreSQL Database
```

**Pipeline Flow:**
1. Web scrapers collect articles from French news sources
2. Content processors extract and clean article text
3. Database layer stores structured data with SQLAlchemy models
4. Component factory pattern for modular scraper architecture

### Key Features
- Modular scraper design with site-specific validators
- Structured logging with custom formatters
- Database migrations with version control
- Comprehensive test suite with fixtures
- Docker containerized PostgreSQL
- Environment-based configuration

### Development Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Start database
make db-start

# Run scraper
make run

# Run tests
make test

# Format and lint
make fix
```

### Supported News Sources
- Slate.fr
- France Info
- La Dépêche
- TF1 Info

## TODO

*Scrape traditional anki decks for top 6000 words and conjugations -> use to enrich static database*
*django/flask application (tempted to learn flask) for spaced repitition logic*
*use chatgpt API to generate flashcards for hot words from scraper*
*ALL FUTURE ENHANCEMENTS ARE LISTED IN ISSUES ON PROJECT*
