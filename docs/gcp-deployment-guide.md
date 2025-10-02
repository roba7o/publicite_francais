# GCP Deployment Guide - Fully Managed Serverless Architecture

This guide explains how to deploy your French news scraper to Google Cloud Platform using fully managed services for autonomous operation.

## Architecture Overview

```
┌─────────────────────────────────────────┐
│             FULLY MANAGED GCP           │
├─────────────────────────────────────────┤
│ Cloud Scheduler                         │
│ └─ Triggers scraping every X hours      │
├─────────────────────────────────────────┤
│ Cloud Run (Serverless Container)       │
│ ├─ Runs your Python scraper            │
│ ├─ Auto-scales to zero when idle       │
│ └─ Pay only for actual runtime          │
├─────────────────────────────────────────┤
│ Cloud SQL PostgreSQL                   │
│ ├─ Managed database                    │
│ ├─ Automatic backups                   │
│ └─ High availability                   │
├─────────────────────────────────────────┤
│ Cloud Build (Optional)                 │
│ └─ Auto-deploy from GitHub commits     │
└─────────────────────────────────────────┘
```

## Prerequisites

1. Google Cloud Platform account
2. `gcloud` CLI installed and configured
3. Docker installed locally for testing
4. Your current codebase (already production-ready data architecture)

## Step 1: Project Setup

```bash
# Create new GCP project
gcloud projects create your-french-scraper --name="French News Scraper"

# Set project as default
gcloud config set project your-french-scraper

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Step 2: Create Cloud SQL Database

```bash
# Create PostgreSQL instance
gcloud sql instances create french-news-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --storage-type=SSD \
    --storage-size=10GB

# Create database
gcloud sql databases create french_news_prod --instance=french-news-db

# Create user
gcloud sql users create news_user \
    --instance=french-news-db \
    --password=your_secure_password

# Get connection string
gcloud sql instances describe french-news-db --format="value(connectionName)"
```

## Step 3: Add Production Configuration

Update your `src/config/database_config.py`:

```python
CONFIGS = {
    "dev": {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "database": os.getenv("POSTGRES_DB", "french_news_db"),
        "user": os.getenv("POSTGRES_USER", "news_user"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    },
    "test": {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT_TEST", "5433")),
        "database": os.getenv("POSTGRES_DB_TEST", "french_news_test_db"),
        "user": os.getenv("POSTGRES_USER", "news_user"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    },
    "production": {
        "host": "/cloudsql/" + os.getenv("CLOUD_SQL_CONNECTION_NAME", ""),
        "port": 5432,
        "database": os.getenv("POSTGRES_DB_PROD", "french_news_prod"),
        "user": os.getenv("POSTGRES_USER_PROD", "news_user"),
        "password": os.getenv("POSTGRES_PASSWORD_PROD", ""),
    }
}

@classmethod
def get_config(cls, test_mode: bool = False) -> Dict[str, Any]:
    """Get database configuration for the specified environment."""
    if os.getenv("PRODUCTION", "false").lower() == "true":
        env = "production"
    elif test_mode:
        env = "test"
    else:
        env = "dev"
    return cls.CONFIGS[env].copy()
```

## Step 4: Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy source code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src

# Run the scraper
CMD ["python", "-m", "main"]
```

Create `.dockerignore`:

```
.git
.env
.env.example
venv/
__pycache__/
*.pyc
tests/
docs/
.pytest_cache/
.coverage
docker-compose.yml
Makefile
README.md
```

## Step 5: Build and Deploy to Cloud Run

```bash
# Build and submit to Cloud Build
gcloud builds submit --tag gcr.io/your-french-scraper/french-scraper

# Deploy to Cloud Run
gcloud run deploy french-scraper \
    --image gcr.io/your-french-scraper/french-scraper \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --timeout 900 \
    --set-env-vars PRODUCTION=true \
    --set-env-vars CLOUD_SQL_CONNECTION_NAME=your-project:us-central1:french-news-db \
    --set-env-vars POSTGRES_DB_PROD=french_news_prod \
    --set-env-vars POSTGRES_USER_PROD=news_user \
    --set-env-vars POSTGRES_PASSWORD_PROD=your_secure_password \
    --add-cloudsql-instances your-project:us-central1:french-news-db
```

## Step 6: Run Database Migrations

```bash
# Trigger Cloud Run to run migrations
curl -X POST "https://french-scraper-xxx-uc.a.run.app"
```

Alternatively, run migrations locally against Cloud SQL:

```bash
# Install Cloud SQL Proxy
gcloud sql instances describe french-news-db --format="value(connectionName)"

# Connect through proxy
./cloud_sql_proxy -instances=your-connection-string=tcp:5432 &

# Run migrations locally
PRODUCTION=true CLOUD_SQL_CONNECTION_NAME=localhost:5432 make db-migrate
```

## Step 7: Set Up Scheduled Execution

```bash
# Create Cloud Scheduler job to run every 6 hours
gcloud scheduler jobs create http french-scraper-schedule \
    --schedule="0 */6 * * *" \
    --uri="https://french-scraper-xxx-uc.a.run.app" \
    --http-method=POST \
    --time-zone="Europe/Paris"
```

## Step 8: Monitoring and Logs

```bash
# View logs
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=french-scraper"

# View metrics in Cloud Console
# Navigate to: Cloud Run > french-scraper > Metrics
```

## Cost Estimation (Personal Project)

- **Cloud SQL (db-f1-micro)**: ~$7-10/month
- **Cloud Run**: ~$0.50-2/month (pay per request)
- **Cloud Scheduler**: Free (up to 3 jobs)
- **Cloud Build**: Free tier covers small projects
- **Total**: ~$8-12/month

## Maintenance Commands

```bash
# Update deployment
gcloud builds submit --tag gcr.io/your-french-scraper/french-scraper
gcloud run deploy french-scraper --image gcr.io/your-french-scraper/french-scraper

# View service info
gcloud run services describe french-scraper --region us-central1

# Manual trigger
curl -X POST "https://your-cloud-run-url"

# Scale to zero (stop costs)
gcloud run services update french-scraper --region us-central1 --min-instances 0

# Database backup
gcloud sql backups list --instance=french-news-db
```

## Benefits of This Architecture

1. **Zero Server Management**: No VMs to patch or maintain
2. **Pay-per-Use**: Only costs when scraper is running
3. **Auto-Scaling**: Handles load spikes automatically
4. **Managed Database**: Automatic backups, updates, HA
5. **Integrated Monitoring**: Built-in logs and metrics
6. **Security**: IAM handles all permissions
7. **Reliability**: Google's infrastructure SLA

## Troubleshooting

**Connection Issues**: Ensure Cloud SQL instance allows Cloud Run connections
**Memory Issues**: Increase memory allocation in Cloud Run
**Timeout Issues**: Increase timeout (max 900 seconds)
**Permission Issues**: Check IAM roles for Cloud Run service account

Your existing code architecture is already production-ready - this deployment strategy just moves it to fully managed GCP services for autonomous operation.