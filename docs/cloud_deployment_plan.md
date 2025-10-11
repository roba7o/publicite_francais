# Cloud Deployment Plan - French News Scraper (Google Cloud Platform)

## Overview
Phased migration of Python scraper to GCP with Cloud SQL PostgreSQL.

**Current State:** Working locally with Docker PostgreSQL
**Target State:**
- Phase 1: Cloud SQL + Python running locally
- Phase 2: Python on Compute Engine + Cloud SQL

---

## Deployment Strategy

**Phase 1: Database Migration**
1. Set up Cloud SQL PostgreSQL
2. Apply schema to cloud database
3. Run Python scraper **locally**, writing to Cloud SQL
4. Validate data pipeline works

**Phase 2: Application Migration**
1. Dockerize Python application
2. Deploy to Compute Engine VM
3. Set up scheduled execution (cron)

---

## Phase 1: Cloud SQL Setup + Local Testing

### Prerequisites
- GCP Account with billing enabled
- `gcloud` CLI installed locally
- Budget: ~$10-15/month

---

## Step 1: GCP Project Setup

### 1.1 Create GCP Project
```bash
# Install gcloud CLI (if not installed)
# https://cloud.google.com/sdk/docs/install

# Login to GCP
gcloud auth login

# Create new project
gcloud projects create french-news-scraper --name="French News Scraper"

# Set as default project
gcloud config set project french-news-scraper

# Enable billing (required for Cloud SQL)
# Do this in GCP Console: https://console.cloud.google.com/billing

# Enable required APIs
gcloud services enable sqladmin.googleapis.com
gcloud services enable compute.googleapis.com
```

**Considerations:**
- ✅ Separate project = isolated billing and permissions
- ✅ Easy to delete everything if needed
- ⚠️ Need billing enabled for Cloud SQL
- ⚠️ API enablement can take 1-2 minutes

---

## Step 2: Set Up Cloud SQL (Managed PostgreSQL)

### 2.1 Create Cloud SQL Instance

```bash
# Create PostgreSQL instance (smallest tier for cost savings)
gcloud sql instances create french-news-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=CHANGE_THIS_PASSWORD \
    --database-flags=max_connections=100

# This takes ~5-10 minutes to provision
```

**Instance Options:**
- `db-f1-micro`: $7-10/month (0.6GB RAM, shared CPU) - **Start here**
- `db-g1-small`: $25-30/month (1.7GB RAM, shared CPU) - Better performance
- `db-custom-1-3840`: $50+/month (1 vCPU, 3.75GB RAM) - Production

### 2.2 Create Database and User

```bash
# Create database
gcloud sql databases create french_news_db \
    --instance=french-news-db

# Create user
gcloud sql users create news_user \
    --instance=french-news-db \
    --password=SECURE_PASSWORD_HERE

# Note: Save this password - you'll need it for secrets
```

### 2.3 Get Connection Details

```bash
# Get instance connection name (format: project:region:instance)
gcloud sql instances describe french-news-db \
    --format="value(connectionName)"

# Output example: french-news-scraper:us-central1:french-news-db

# Get public IP (if using direct connection)
gcloud sql instances describe french-news-db \
    --format="value(ipAddresses[0].ipAddress)"
```

### 2.4 Apply Schema ✅ COMPLETE

**Using Cloud SQL Proxy:**

```bash
# Navigate to project root
cd /Users/robertmatthew/Documents/programmingSelfStudy/projects/publicite_francais

# Download Cloud SQL Proxy (macOS)
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy

# Terminal 1: Start proxy (keeps running)
./cloud-sql-proxy french-news-scraper:us-central1:french-news-db

# Terminal 2: Apply schema
psql "host=127.0.0.1 port=5432 user=news_user dbname=french_news_db" \
    -f database/schema.sql
```

**Expected output:**
```
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
```

**Considerations:**
- ✅ Cloud SQL Proxy is most secure (encrypted connection)
- ✅ Automatic backups enabled by default
- ✅ Can scale up tier later without data migration
- ⚠️ db-f1-micro shares CPU (slower but cheap)

---

## Step 3: Test Local Python → Cloud SQL

### 3.1 Update Local Environment

Create `.env.cloud` for cloud database connection:

```bash
# In project root
cat > .env.cloud <<EOF
ENVIRONMENT=development
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=french_news_db
POSTGRES_USER=news_user
POSTGRES_PASSWORD=your_cloud_db_password
EOF

# Add to .gitignore
echo ".env.cloud" >> .gitignore
```

### 3.2 Test Connection

With Cloud SQL Proxy running in Terminal 1:

```bash
# Terminal 2: Run scraper with Cloud SQL
make run-cloud
```

**What `make run-cloud` does:**
- Loads `.env.cloud` automatically
- Runs Python scraper locally
- Writes data to Cloud SQL via proxy

### 3.3 Verify Data in Cloud SQL

```bash
# Check articles were inserted
psql "host=127.0.0.1 port=5432 user=news_user dbname=french_news_db" \
    -c "SELECT COUNT(*) FROM dim_articles;"

# Check word facts
psql "host=127.0.0.1 port=5432 user=news_user dbname=french_news_db" \
    -c "SELECT COUNT(*) FROM word_facts;"

# View recent articles
psql "host=127.0.0.1 port=5432 user=news_user dbname=french_news_db" \
    -c "SELECT url, site, scraped_at FROM dim_articles ORDER BY scraped_at DESC LIMIT 5;"
```

**Success criteria:**
- ✅ Python scraper runs without errors
- ✅ Data appears in Cloud SQL tables
- ✅ Can query data via psql

**✅ Phase 1 Complete!** You now have:
- ✅ Cloud SQL PostgreSQL running
- ✅ Schema applied
- ✅ Local Python writing to cloud database
- ✅ `make run-cloud` command working
- ✅ Data verified in Cloud SQL

**Current workflow:**
- Terminal 1: `./cloud-sql-proxy french-news-scraper:us-central1:french-news-db`
- Terminal 2: `make run-cloud`

---

## Phase 2: Deploy Python to Cloud (Future)

**Goal:** Move Python scraper from local machine to Compute Engine VM.

### Prerequisites for Phase 2
- ✅ Phase 1 complete (Cloud SQL working with local Python)
- ✅ Docker installed locally
- ✅ Application tested and stable

---

### 2.1 Create Dockerfile

**Using pyproject.toml dependencies:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/

# Install dependencies from pyproject.toml
RUN pip install --no-cache-dir -e .

# Set environment
ENV PYTHONPATH=/app/src

# Run scraper
CMD ["python", "-m", "main"]
```

### 2.2 Create `.dockerignore`

```
venv/
__pycache__/
*.pyc
.git/
.env
.env.*
tests/
docs/
*.md
.pytest_cache/
.ruff_cache/
docker-compose.yml
database/
cloud-sql-proxy
```

### 2.3 Test Docker Build Locally

```bash
# Build image
docker build -t french-news-scraper .

# Test run (connecting to Cloud SQL via proxy)
# Make sure Cloud SQL Proxy is running in another terminal
docker run --rm \
    --network host \
    -e POSTGRES_HOST=127.0.0.1 \
    -e POSTGRES_PORT=5432 \
    -e POSTGRES_DB=french_news_db \
    -e POSTGRES_USER=news_user \
    -e POSTGRES_PASSWORD=your_password \
    french-news-scraper
```

---

### 2.4 Deploy to Compute Engine VM

```bash
# Create small VM with Docker support
gcloud compute instances create french-news-vm \
    --zone=us-central1-a \
    --machine-type=e2-micro \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --scopes=cloud-platform

# SSH into VM
gcloud compute ssh french-news-vm --zone=us-central1-a
```

### 2.5 Setup on VM

**On the VM:**

```bash
# Install Docker
sudo apt update
sudo apt install -y docker.io git

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy
sudo mv cloud-sql-proxy /usr/local/bin/

# Start Cloud SQL Proxy as systemd service
sudo tee /etc/systemd/system/cloudsql-proxy.service > /dev/null <<'EOF'
[Unit]
Description=Cloud SQL Proxy
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/cloud-sql-proxy french-news-scraper:us-central1:french-news-db
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable cloudsql-proxy
sudo systemctl start cloudsql-proxy

# Verify proxy is running
sudo systemctl status cloudsql-proxy
```

### 2.6 Build and Run Docker Container on VM

```bash
# Clone your repo (or use Cloud Build to push image to registry)
git clone https://github.com/YOUR_USERNAME/publicite_francais.git
cd publicite_francais

# Build Docker image
docker build -t french-news-scraper .

# Create .env file for production
cat > .env.prod <<'EOF'
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=french_news_db
POSTGRES_USER=news_user
POSTGRES_PASSWORD=your_cloud_db_password
EOF

# Test run
docker run --rm \
    --network host \
    --env-file .env.prod \
    french-news-scraper

# Verify data was inserted
/usr/local/bin/cloud-sql-proxy french-news-scraper:us-central1:french-news-db &
sleep 2
psql "host=127.0.0.1 port=5432 user=news_user dbname=french_news_db" \
    -c "SELECT COUNT(*) FROM dim_articles;"
```

### 2.7 Set Up Scheduled Execution (Cron)

```bash
# Create wrapper script
cat > ~/run-scraper.sh <<'EOF'
#!/bin/bash
cd /home/$(whoami)/publicite_francais
docker run --rm \
    --network host \
    --env-file .env.prod \
    french-news-scraper >> /var/log/french-news-scraper.log 2>&1
EOF

chmod +x ~/run-scraper.sh

# Add to crontab (runs daily at 2 AM)
crontab -e
# Add this line:
0 2 * * * /home/$(whoami)/run-scraper.sh

# Test wrapper script
~/run-scraper.sh

# View logs
tail -f /var/log/french-news-scraper.log
```

**Considerations:**
- ✅ Simple, familiar environment
- ✅ Docker isolates dependencies
- ✅ Easy to SSH and debug
- ✅ Can run other services
- ✅ Cron handles scheduling
- ⚠️ Always running = ~$5-7/month
- ⚠️ Need to manage OS updates
- ⚠️ Manual Docker image rebuilds for updates

---

## Step 4: Verify End-to-End Pipeline

### From Your Local Machine

```bash
# Start Cloud SQL Proxy
./cloud-sql-proxy french-news-scraper:us-central1:french-news-db

# Check latest data
psql "host=127.0.0.1 port=5432 user=news_user dbname=french_news_db" \
    -c "SELECT url, site, scraped_at FROM dim_articles ORDER BY scraped_at DESC LIMIT 10;"

# Monitor cron logs from VM
gcloud compute ssh french-news-vm --zone=us-central1-a --command "tail -20 /var/log/french-news-scraper.log"
```

**Success Criteria:**
- ✅ Cron runs daily at 2 AM
- ✅ Docker container executes successfully
- ✅ New articles appear in Cloud SQL
- ✅ No errors in logs

---

## Step 7: Monitoring & Logging

### 7.1 View Logs in Cloud Console

```bash
# View Cloud Run job logs
gcloud logging read "resource.type=cloud_run_job" \
    --limit 100 \
    --format json

# Filter for errors only
gcloud logging read "resource.type=cloud_run_job AND severity>=ERROR" \
    --limit 50

# Live tail logs
gcloud logging tail "resource.type=cloud_run_job"
```

### 7.2 Set Up Alerts

**In GCP Console:**
1. Go to **Monitoring > Alerting**
2. Create alert policy:
   - **Condition:** Cloud Run Job execution failures
   - **Notification:** Email
   - **Threshold:** > 1 failure in 1 day

### 7.3 Monitor Database Size

```bash
# Check database size
gcloud sql instances describe french-news-db \
    --format="value(settings.dataDiskSizeGb)"

# Set up storage auto-increase
gcloud sql instances patch french-news-db \
    --storage-auto-increase
```

---

## Cost Breakdown (Monthly Estimates)

### Phase 1 Only (Cloud SQL + Local Python)
- Cloud SQL db-f1-micro: **$7-10**
- Cloud SQL storage (10GB): **$1.70**
- **Total: ~$10/month**

### Phase 2 (VM + Cloud SQL)
- Cloud SQL db-f1-micro: **$7-10**
- Cloud SQL storage (10GB): **$1.70**
- e2-micro VM: **$6-7**
- **Total: ~$15-20/month**

---

## Migration Checklist

### Phase 1: Cloud SQL Setup ✅ COMPLETE
- [x] GCP account created, billing enabled
- [x] `gcloud` CLI installed and authenticated
- [x] Project created: `french-news-scraper`
- [x] Required APIs enabled (Cloud SQL, Compute)
- [x] Cloud SQL instance created
- [x] Database and user created
- [x] Cloud SQL Proxy downloaded
- [x] Schema applied to Cloud SQL
- [x] `.env.cloud` created with connection details
- [x] Fixed transaction abort bug in `store_word_facts_batch()`
- [x] Added `make run-cloud` command
- [x] Local Python tested → Cloud SQL
- [x] Data verified in Cloud SQL tables

### Phase 2: VM Deployment (Future)
- [ ] Dockerfile created
- [ ] `.dockerignore` created
- [ ] Docker tested locally
- [ ] VM created and running
- [ ] SSH access working
- [ ] Docker installed on VM
- [ ] Cloud SQL Proxy running as systemd service
- [ ] Docker container running on VM
- [ ] Cron job configured
- [ ] Scheduled run verified
- [ ] Storage auto-increase enabled on Cloud SQL

---

## Recommended Deployment Path

### Phase 1: Cloud SQL Setup ✅ COMPLETE
1. ✅ Create GCP project and enable APIs
2. ✅ Set up Cloud SQL (db-f1-micro)
3. ✅ Apply schema via Cloud SQL Proxy
4. ✅ Create `.env.cloud` with credentials
5. ✅ Add `make run-cloud` command
6. ✅ Test local Python → Cloud SQL
7. ✅ Verify data in cloud database
**Status: Phase 1 complete!**

### Phase 2: VM Deployment (Ready to start)
1. Create Dockerfile
2. Test Docker locally
3. Create VM instance
4. Deploy Docker + cron to VM
5. Verify scheduled execution
**Estimated time: 2-3 hours**

### Future: Optimization
1. Consider upgrading Cloud SQL tier if needed
2. Set up automated backups
3. Implement data retention policy

---

## Troubleshooting

### Issue: Can't connect to Cloud SQL
**Solution:**
```bash
# Check Cloud SQL Proxy is running
ps aux | grep cloud-sql-proxy

# Check instance status
gcloud sql instances describe french-news-db --format="value(state)"

# Test connection
gcloud sql connect french-news-db --user=news_user
```

### Issue: Secret Manager access denied
**Solution:**
```bash
# Check service account has proper role
gcloud secrets get-iam-policy db-password

# Re-grant access
gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
```

### Issue: Cloud Run Job times out
**Solution:**
```bash
# Increase timeout to max (1 hour)
gcloud run jobs update french-news-job \
    --region us-central1 \
    --task-timeout 3600

# Check logs for actual error
gcloud logging read "resource.type=cloud_run_job AND severity>=ERROR" --limit 10
```

### Issue: Out of memory on Cloud Run
**Solution:**
```bash
# Increase memory allocation
gcloud run jobs update french-news-job \
    --region us-central1 \
    --memory 1Gi
```

---

## Next Steps

Once deployed, you can:
1. **Add monitoring dashboard:** Track scraping metrics over time
2. **Set up data exports:** BigQuery for analysis, Cloud Storage for backups
3. **Scale up:** Increase Cloud SQL tier or Cloud Run resources
4. **Add CI/CD:** Auto-deploy on git push using Cloud Build triggers
5. **Multi-region:** Deploy to multiple regions for redundancy

---

## Useful Commands Reference

```bash
# View all Cloud Run jobs
gcloud run jobs list --region us-central1

# Execute job manually
gcloud run jobs execute french-news-job --region us-central1

# View job execution history
gcloud run jobs executions list --job french-news-job --region us-central1

# View logs
gcloud logging read "resource.type=cloud_run_job" --limit 50

# Connect to Cloud SQL
gcloud sql connect french-news-db --user=news_user

# List secrets
gcloud secrets list

# View secret value
gcloud secrets versions access latest --secret=db-password

# Check costs
gcloud billing accounts list
gcloud billing budgets list --billing-account=BILLING_ACCOUNT_ID
```

---

## Support Resources

- **GCP Documentation:** https://cloud.google.com/docs
- **Cloud SQL Guide:** https://cloud.google.com/sql/docs/postgres
- **Cloud Run Jobs:** https://cloud.google.com/run/docs/create-jobs
- **Secret Manager:** https://cloud.google.com/secret-manager/docs
- **Cloud Scheduler:** https://cloud.google.com/scheduler/docs
- **Pricing Calculator:** https://cloud.google.com/products/calculator

---

**Last Updated:** 2025-10-10
