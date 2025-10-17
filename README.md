# French News Scraper

Python scraper that collects French news articles and stores them in PostgreSQL. Scrapes 4 news sites, extracts article text and individual French words for vocabulary tracking.

## What It Does

Scrapes French news websites daily and stores:
1. **Articles** - URL, site, scrape timestamp
2. **Words** - Every French word found, with position in article

Originally built for learning French vocabulary from real news sources.

## How It Works

### Entry Point
```
src/main.py → ArticleOrchestrator → ComponentFactory
```

**main.py** loads environment, initializes database, starts the pipeline.

**ArticleOrchestrator** (`src/core/orchestrator.py`) controls the flow:
1. For each enabled news site in `site_configs.py`
2. Create URL collector (finds article links on homepage)
3. Create soup validator (validates and extracts article content)
4. Fetch URLs concurrently (3 workers, configurable)
5. Extract articles into `RawArticle` objects
6. Extract French words from articles
7. Batch insert to database

**ComponentFactory** (`src/core/component_factory.py`) dynamically loads site-specific components based on configuration.

### Key Components

**URL Collectors** (`src/core/components/url_collectors/`)
- Each site has its own collector (e.g., `slate_fr_url_collector.py`)
- Finds article links from homepage HTML
- Returns list of URLs to scrape

**Soup Validators** (`src/core/components/soup_validators/`)
- Site-specific HTML parsing logic
- Validates article structure
- Extracts raw HTML content
- Returns `RawArticle` with URL, site, timestamp

**Word Extractor** (`src/services/word_extractor.py`)
- Takes article HTML, extracts French text
- Splits into individual words
- Tracks word position in article
- Returns `WordFact` objects

### Configuration Levers

**Environment Selection** (`src/config/environment.py`):
```python
ENVIRONMENT = "development"  # or "test"
```
- `development` - Uses local Docker Postgres or Cloud SQL
- `test` - Uses in-memory test database, runs on test fixtures

**Site Configuration** (`src/config/site_configs.py`):
```python
{
    "site": "slate.fr",
    "enabled": True,  # Toggle scraping on/off
    "url_collector_class": "...",
    "soup_validator_class": "..."
}
```

**Scraping Controls** (environment variables):
- `MAX_ARTICLES` - Limit articles per site (default: unlimited)
- `CONCURRENT_FETCHERS` - Parallel URL fetchers (default: 3)
- `FETCH_TIMEOUT` - Seconds per URL request (default: 30)
- `DEBUG` - Verbose logging (default: false)

### Database Schema

**dim_articles** - Article metadata
```sql
id              UUID PRIMARY KEY
url             TEXT UNIQUE
site            VARCHAR(100)
scraped_at      TIMESTAMP
response_status INTEGER
```

**word_facts** - Individual words extracted
```sql
id                    UUID PRIMARY KEY
word                  TEXT
article_id            UUID REFERENCES dim_articles(id)
position_in_article   INTEGER
scraped_at            TIMESTAMP
```

Indexes on: `word`, `article_id`, `scraped_at` for fast queries.

## Environments

### Local Development
```bash
# Uses local Docker PostgreSQL (port 5432)
make db-start ENV=dev
make run
```

**Database:** `french_news` on `localhost:5432`
**Purpose:** Live scraping, real data
**Storage:** Docker volume (persistent)

### Test Environment
```bash
# Uses local Docker PostgreSQL (port 5433)
make db-start ENV=test
make test
```

**Database:** `french_news_test` on `localhost:5433`
**Purpose:** Automated tests with fixtures
**Storage:** tmpfs (in-memory, fast, wiped on stop)

### Cloud Production
```bash
# Uses Google Cloud SQL via proxy
./cloud-sql-proxy french-news-scraper:us-central1:french-news-db &
make run-cloud
```

**Database:** Cloud SQL Postgres in GCP (us-central1)
**Purpose:** Production scraping on VM
**Storage:** Managed PostgreSQL, backups enabled

## Data Output

Running `make run` produces:

**Articles Table:**
```
┌──────────────────────────────────┬─────────────────────┬─────────────┬────────────────────┐
│ id                               │ url                 │ site        │ scraped_at         │
├──────────────────────────────────┼─────────────────────┼─────────────┼────────────────────┤
│ a1b2c3d4-...                     │ https://slate.fr/.. │ slate.fr    │ 2025-10-11 08:00   │
│ e5f6g7h8-...                     │ https://france...   │ franceinfo  │ 2025-10-11 08:01   │
└──────────────────────────────────┴─────────────────────┴─────────────┴────────────────────┘
```

**Words Table:**
```
┌──────────────────────────────────┬──────────┬──────────────────────────────────┬──────────┐
│ id                               │ word     │ article_id                       │ position │
├──────────────────────────────────┼──────────┼──────────────────────────────────┼──────────┤
│ 1a2b3c4d-...                     │ le       │ a1b2c3d4-...                     │ 1        │
│ 2b3c4d5e-...                     │ président│ a1b2c3d4-...                     │ 2        │
│ 3c4d5e6f-...                     │ annonce  │ a1b2c3d4-...                     │ 3        │
└──────────────────────────────────┴──────────┴──────────────────────────────────┴──────────┘
```

**Typical Run Output:**
- 30-50 articles per site (varies by homepage)
- ~500-1000 words per article
- Total: ~15,000-40,000 words per run
- Duration: ~2-5 minutes depending on site responsiveness

## Quick Start

```bash
# Setup
source venv/bin/activate
make db-start ENV=dev

# Run scraper (development mode)
make run

# Run tests
make test

# Clean code
make fix
```

## Supported News Sources

- **Slate.fr** - Cultural/political commentary
- **FranceInfo.fr** - Public broadcaster news
- **LaDépêche.fr** - Regional news
- **TF1Info.fr** - Commercial TV news

Each site requires its own URL collector and soup validator due to different HTML structures.

## Cloud Deployment

**Current Setup:**
- Database: Cloud SQL (PostgreSQL 15, db-f1-micro, us-central1)
- Application: Docker on Compute Engine VM (e2-micro)
- Cost: ~$15/month
- Connection: Cloud SQL Proxy (secure tunnel)

**Deployment:**
```bash
# SSH to VM
gcloud compute ssh french-news-vm --zone=us-central1-a

# Pull latest
cd publicite_francais && git pull origin main

# Rebuild and run
docker build -t french-news-scraper .
~/run-scraper.sh
```

**Logs:**
```bash
# View in GCP Console
https://console.cloud.google.com/logs?project=french-news-scraper

# Or via CLI
gcloud logging read "resource.type=gce_instance" --limit 50
```

**Health Check:**
```bash
make health-check  # Verifies DB connection without running full scraper
```

## Project Structure

```
src/
├── main.py                          # Entry point
├── config/
│   ├── environment.py               # Environment variables and database config
│   └── site_configs.py              # Enabled sites and component paths
├── core/
│   ├── orchestrator.py              # Main pipeline controller
│   ├── component_factory.py         # Dynamic component loader
│   └── components/
│       ├── url_collectors/          # Site-specific URL scrapers
│       └── soup_validators/         # Site-specific HTML parsers
├── database/
│   ├── database.py                  # Connection pool and CRUD operations
│   └── models.py                    # RawArticle and WordFact data classes
├── services/
│   └── word_extractor.py            # French word extraction logic
└── utils/
    └── structured_logger.py         # Logging setup

tests/
├── unit/                            # Component tests
├── integration/                     # Database + component tests
└── e2e/                             # Full pipeline tests

database/
└── schema.sql                       # PostgreSQL DDL
```

## Development

**Run linter:**
```bash
make fix
```

**Run specific tests:**
```bash
make test-unit          # Fast, no database
make test-integration   # Database required
make test-e2e          # Full pipeline
```

**Add new news source:**
1. Create `src/core/components/url_collectors/mynews_url_collector.py`
2. Create `src/core/components/soup_validators/mynews_soup_validator.py`
3. Add to `src/config/site_configs.py`
4. Run `make test` to verify

**Environment variables:**
Set in `.env` (gitignored):
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=french_news
POSTGRES_USER=news_user
POSTGRES_PASSWORD=your_password

# Optional tuning
MAX_ARTICLES=50              # Limit per site
CONCURRENT_FETCHERS=5        # Parallel workers
FETCH_TIMEOUT=60             # Seconds per URL
DEBUG=true                   # Verbose logs
```

## TODO
