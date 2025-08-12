# PostgreSQL Database Setup

This document explains how to run the PostgreSQL database container for your French news scraper project.

## 📋 Prerequisites

- Docker installed and running
- Docker Compose V2 (modern `docker compose` command)

## 🚀 Quick Start

### 1. Start the Database Container

From your project root directory:

```bash
# Start PostgreSQL in the background
docker compose up -d postgres

# Check if the container is running
docker compose ps
```

### 2. Verify Database Connection

```bash
# Check container logs
docker compose logs postgres

# Connect to the database (optional)
docker compose exec postgres psql -U news_user -d french_news
```

### 3. Stop the Database

```bash
# Stop the container but keep data
docker compose stop postgres

# Stop and remove container (data persists in volume)
docker compose down

# Stop and remove everything INCLUDING data (careful!)
docker compose down -v
```

## 📊 Database Configuration

| Setting | Value |
|---------|-------|
| **Host** | localhost |
| **Port** | 5432 |
| **Database** | french_news |
| **Username** | news_user |
| **Password** | dev_password_123 |
| **Schema** | news_data |

## 🗄️ Database Structure

The initialization script creates these tables for future use:

- **`news_sources`** - Configuration for each news site
- **`articles`** - Article metadata and content
- **`word_frequencies`** - Word frequency analysis results
- **`processing_logs`** - Scraping run history and monitoring

## 🔍 Testing the Database

### Connect with psql
```bash
# Connect to database
docker compose exec postgres psql -U news_user -d french_news

# Once connected, you can run SQL commands:
\dt news_data.*    # List all tables
SELECT * FROM news_data.news_sources;  # View sample data
\q                 # Quit
```

### Connection String for Future Python Use
```
postgresql://news_user:dev_password_123@localhost:5432/french_news
```

## 🛠️ Troubleshooting

### Container Won't Start
```bash
# Check if port 5432 is already in use
lsof -i :5432

# View detailed error logs
docker compose logs postgres
```

### Reset Database
```bash
# Stop and remove everything
docker compose down -v

# Start fresh
docker compose up -d postgres
```

### Health Check
```bash
# Check if database is healthy
docker compose exec postgres pg_isready -U news_user -d french_news
```

## 📝 Notes

- **Data Persistence**: Database data is stored in a Docker volume and persists between container restarts
- **Development Only**: The current password is for development only - change for production
- **No Python Changes**: Your existing Python scraper continues to work unchanged
- **Future Ready**: Database schema is designed for your upcoming refactor

## 🔄 What's Next

Once you're ready to integrate with Python:
1. Install `psycopg2-binary` or `asyncpg`
2. Update your config to use the database connection
3. Gradually migrate from CSV to PostgreSQL storage

---

*Database is now ready for your French news scraper refactor!*