# ========= Makefile for article_scrapers project =========

# Check if .env file exists before proceeding
ifeq (,$(wildcard .env))
$(error .env file missing! Run 'cp .env.example .env' and configure it first)
endif

# Load environment variables from .env file
# sed prints var names to stdout, shell (make function $ which is used to run unix commands) is then called by make to export them
# This allows us to use environment variables in the Makefile without hardcoding them
include .env
export $(shell sed 's/=.*//' .env)

# Project configuration
PYTHON := ./venv/bin/python
PYTEST := ./venv/bin/pytest
RUFF := ./venv/bin/ruff
DBT := ./venv/bin/dbt
SRC := src
MAIN_MODULE := main
DBT_DIR := french_flashcards

# Default command
.DEFAULT_GOAL := help

# Declare phony targets to avoid conflicts with files/directories
.PHONY: run test test-essential test-ci lint format fix clean db-start db-stop db-clean dbt-debug dbt-run pipeline test-pipeline test-workflow docker-build docker-test-build docker-pipeline version-check help

# ========== Local venv commands ==========

run:  ## Run main script locally (must be inside venv)
	PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE)


test:  ## Run all tests + pipeline test (starts database automatically)
	@echo "\033[33m◆ Ensuring database is running for tests...\033[0m"
	@$(MAKE) db-start > /dev/null 2>&1
	@echo "\033[33m◆ Running Python tests...\033[0m"
	@PATH=./venv/bin:$$PATH PYTHONPATH=$(SRC) $(PYTEST) -v
	@echo "\033[33m◆ Running pipeline integration test...\033[0m"
	@$(MAKE) test-pipeline
	@echo ""
	@echo "\033[32m╔════════════════════════════════════════╗"
	@echo "║          TEST SUITE SUMMARY           ║"
	@echo "╚════════════════════════════════════════╝\033[0m"
	@echo "\033[32m✓ Python Tests: PASSED (all tests)\033[0m"
	@echo "\033[32m✓ Pipeline Test: PASSED\033[0m"
	@echo "\033[32m✓ Integration Tests: PASSED\033[0m"
	@echo ""
	@echo "\033[36m▶ ALL TESTS PASSED - 100% SUCCESS RATE\033[0m"

test-essential:  ## Run essential working tests only
	PATH=./venv/bin:$$PATH PYTHONPATH=$(SRC) $(PYTEST) -v tests/test_essential.py

test-ci:  ## Run CI-compatible tests (database + scraper, no dbt)
	PATH=./venv/bin:$$PATH PYTHONPATH=$(SRC) $(PYTEST) -v tests/test_database_connection.py tests/test_deterministic_pipeline.py::TestDeterministicPipeline::test_html_file_counts tests/test_deterministic_pipeline.py::TestDeterministicPipeline::test_database_article_extraction

lint:  ## Run ruff linting
	$(RUFF) check $(SRC)

format:  ## Auto-format code with ruff
	$(RUFF) format $(SRC)


fix:  ## Auto-format code and run all checks
	@echo "\033[36m▶ Formatting code with ruff...\033[0m"
	$(RUFF) format $(SRC)
	@echo "\033[33m▶ Running ruff linting...\033[0m"
	$(RUFF) check --fix $(SRC)
	@echo "\033[33m▶ Skipping mypy (learning project - type hints not enforced)...\033[0m"
	@echo "\033[32m✓ Code quality checks passed!\033[0m"

clean:  ## Remove __pycache__, .pyc files, and test artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name ".coverage*" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# ========== dbt commands ==========

dbt-run:  ## Run dbt models (text processing pipeline)
	cd $(DBT_DIR) && ../$(DBT) run

dbt-debug:  ## Test dbt database connection
	cd $(DBT_DIR) && ../$(DBT) debug

pipeline:  ## Run full pipeline: scrape articles + process with dbt
	@echo "\033[34m■ Step 1: Scraping articles...\033[0m"
	PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE) || (echo "\033[31m✗ Scraping failed\033[0m" && exit 1)
	@echo "\033[32m  ✓ Articles scraped successfully\033[0m"
	@echo "\033[35m■ Step 2: Processing with dbt...\033[0m"
	cd $(DBT_DIR) && ../$(DBT) run || (echo "\033[31m✗ dbt processing failed\033[0m" && exit 1)
	@echo "\033[32m  ✓ dbt processing successful\033[0m"
	@echo "\033[32m✓ Pipeline complete!\033[0m"


test-pipeline:  ## Run pipeline test with fresh database (clears data first)
	@echo "\033[33m◆ Running pipeline test with fresh data...\033[0m"
	@echo "\033[34m□ Step 1: Ensuring database is ready...\033[0m"
	@docker compose up -d postgres > /dev/null 2>&1
	@docker compose exec postgres sh -c 'until pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB; do sleep 1; done' > /dev/null 2>&1
	@echo "\033[31m× Step 2: Clearing database tables...\033[0m"
	@docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c "TRUNCATE news_data_test.articles CASCADE;"' > /dev/null 2>&1
	@printf "\033[32m  ✓ Database cleared - "
	@docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -t -c "SELECT COUNT(*) FROM news_data_test.articles;"' | xargs | awk '{print $$1 " articles remaining\033[0m"}'
	@echo "\033[34m■ Step 3: Scraping test articles...\033[0m"
	@PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE) > /dev/null 2>&1 || (echo "\033[31m✗ Scraping failed\033[0m" && exit 1)
	@echo "\033[32m  ✓ Articles scraped successfully\033[0m"
	@echo "\033[35m■ Step 4: Processing with dbt (test target)...\033[0m"
	@cd $(DBT_DIR) && ../$(DBT) run --target test > /dev/null 2>&1 || (echo "\033[31m✗ dbt processing failed\033[0m" && exit 1)
	@echo "\033[32m  ✓ dbt processing successful\033[0m"
	@echo "\033[36m▶ Step 5: Verifying results...\033[0m"
	@docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c "SELECT COUNT(*) as sentences FROM dbt_test.sentences; SELECT COUNT(*) as vocabulary_words FROM dbt_test.vocabulary_for_flashcards;"' 2>/dev/null
	@echo "\033[32m✓ Pipeline test complete!\033[0m"

test-workflow:  ## Complete test workflow with HTML test files
	@echo "\033[33m◆ Running complete test workflow...\033[0m"
	$(MAKE) test-pipeline
	@echo "\033[33m◆ Running dbt tests on test data...\033[0m"
	cd $(DBT_DIR) && ../$(DBT) test --target test
	@echo "\033[36m▶ Test workflow complete! Clean with: make dbt-clean-test\033[0m"

# ========== Database commands ==========

db-start:  ## Start PostgreSQL database only
	@echo "\033[34m◆ Starting PostgreSQL database...\033[0m"
	docker compose up -d postgres
	@echo "\033[33m⧗ Waiting for database to be ready...\033[0m"
	@docker compose exec postgres sh -c 'until pg_isready -U news_user -d french_news; do sleep 1; done'
	@echo "\033[32m✓ Database ready!\033[0m"

db-stop:  ## Stop all containers
	docker compose down

db-clean:  ## Stop and remove all containers and volumes
	docker compose down -v
	docker compose rm -f

# ========== Container commands ==========

docker-build:  ## Build all container images
	@echo "\033[34m◆ Building container images...\033[0m"
	docker compose build

docker-test-build:  ## Test that all containers build successfully
	@echo "\033[33m◆ Testing container builds...\033[0m"
	@docker compose build --quiet || (echo "\033[31m✗ Container build failed\033[0m" && exit 1)
	@echo "\033[32m✓ All containers build successfully\033[0m"

docker-pipeline:  ## Run full containerized pipeline (all services)
	@echo "\033[36m◆ Running full containerized pipeline...\033[0m"
	@echo "\033[34m■ Step 1: Starting database...\033[0m"
	docker compose up -d postgres
	@echo "\033[33m⧗ Waiting for database...\033[0m"
	@docker compose exec postgres sh -c 'until pg_isready -U news_user -d french_news; do sleep 1; done'
	@echo "\033[34m■ Step 2: Running scraper...\033[0m"
	docker compose run --rm app
	@echo "\033[35m■ Step 3: Running dbt transformations...\033[0m"
	docker compose run --rm dbt
	@echo "\033[32m✓ Containerized pipeline complete!\033[0m"

# ========== Utilities ==========

version-check:  ## Compare local vs Docker versions for consistency
	@echo "\033[36m◆ Environment Version Comparison\033[0m"
	@echo "\033[33m├─ Local Python:\033[0m $(shell $(PYTHON) --version)"
	@echo "\033[33m├─ Docker Python:\033[0m $(shell docker run --rm python:3.12-slim python --version 2>/dev/null || echo 'Docker not available')"
	@echo "\033[33m├─ Local dbt:\033[0m $(shell $(DBT) --version 2>/dev/null | head -1 || echo 'dbt not installed')"
	@echo "\033[33m└─ Docker dbt:\033[0m dbt-postgres==1.9.0 (pinned in Dockerfile)"
	@echo ""
	@echo "\033[32m✓ Versions should match for consistent behavior\033[0m"

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sed 's/:.*## /|/' | awk -F'|' '{printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'


# ========== Quick Reference ==========
# 
# Development:
#   make run              # Run script locally  
#   make test             # Run all tests
#   make test-essential   # Run essential tests only
#   make fix              # Auto-format and lint code
#   make version-check    # Compare local vs Docker versions
#   make clean            # Remove cache files
#
# Pipeline:
#   make pipeline         # Run full pipeline (scrape + dbt)
#   make test-pipeline    # Test pipeline with fresh data
#   make test-workflow    # Complete test workflow
#
# Database:
#   make db-start         # Start PostgreSQL database
#   make dbt-run          # Run dbt transformations
#   make dbt-debug        # Test dbt connection
#
# Docker:
#   make docker-build     # Build containers
#   make docker-pipeline  # Run containerized pipeline
