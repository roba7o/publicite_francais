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
# ensures the Makefile uses the virtual environment's Python and tools
PYTHON := ./venv/bin/python
PYTEST := ./venv/bin/pytest
RUFF := ./venv/bin/ruff

# Project structure variables
SRC := src
MAIN_MODULE := main

# Default command
.DEFAULT_GOAL := help

# Declare phony targets to avoid conflicts with files/directories
.PHONY: run run-test-data test test-unit test-integration test-e2e test-quick lint format fix clean db-start db-start-test db-stop db-clean db-migrate db-migrate-dry db-rebuild db-restart version-check

# ==================== CORE COMMANDS (Daily Usage) ====================

run:  ## Run scraper locally (live mode)
	ENVIRONMENT=development PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE)

run-test-data:  ## Run scraper with test data (offline mode)
	@./scripts/run-test-data.sh

test:  ## Run all tests (unit + integration + e2e)
	@echo "\033[34m◆ Running complete test suite...\033[0m"
	PYTHONPATH=$(SRC):. $(PYTEST) tests/ -v
	@echo "\033[32m✓ Complete test suite passed!\033[0m"

test-unit:  ## Run unit tests only (fast feedback)
	@echo "\033[34m◆ Running unit tests...\033[0m"
	PYTHONPATH=$(SRC):. $(PYTEST) tests/unit/ -v
	@echo "\033[32m✓ Unit tests passed!\033[0m"

test-integration:  ## Run integration tests only
	@echo "\033[34m◆ Running integration tests...\033[0m"
	PYTHONPATH=$(SRC):. $(PYTEST) tests/integration/ -v
	@echo "\033[32m✓ Integration tests passed!\033[0m"

test-e2e:  ## Run E2E pipeline tests (stages 1-5)
	@echo "\033[34m◆ Running E2E pipeline tests...\033[0m"
	PYTHONPATH=$(SRC):. $(PYTEST) tests/e2e/*.py -v
	@echo "\033[32m✓ E2E pipeline tests passed!\033[0m"

test-quick:  ## Run unit + integration (skip E2E for speed)
	@echo "\033[34m◆ Running quick test suite...\033[0m"
	PYTHONPATH=$(SRC):. $(PYTEST) tests/unit/ tests/integration/ -v
	@echo "\033[32m✓ Quick test suite passed!\033[0m"

help:  ## Show available commands
	@echo ""
	@echo "\033[1m\033[36m========== CORE COMMANDS (Daily Usage) ==========\033[0m"
	@echo "\033[36mrun              \033[0m Run scraper locally (live mode)"
	@echo "\033[36mrun-test-data    \033[0m Run scraper with test data (offline mode)"
	@echo ""
	@echo "\033[33mTesting commands:\033[0m"
	@echo "  \033[36mtest           \033[0m Run all tests (unit + integration + e2e)"
	@echo "  \033[36mtest-unit      \033[0m Run unit tests only (fast feedback)"
	@echo "  \033[36mtest-integration\033[0m Run integration tests only"
	@echo "  \033[36mtest-e2e       \033[0m Run E2E pipeline tests (stages 1-5)"
	@echo "  \033[36mtest-quick     \033[0m Run unit + integration (skip E2E)"
	@echo ""
	@echo "\033[36mhelp             \033[0m Show available commands"
	@echo ""
	@echo "\033[1m\033[33m========== UTILITY COMMANDS (Helpers & Maintenance) ==========\033[0m"
	@echo ""
	@echo "\033[33mDatabase utilities:\033[0m"
	@echo "  \033[36mdb-start       \033[0m Start PostgreSQL database only"
	@echo "  \033[36mdb-start-test  \033[0m Start both main and test databases"
	@echo "  \033[36mdb-stop        \033[0m Stop all containers"
	@echo "  \033[36mdb-clean       \033[0m Stop and remove all containers and volumes"
	@echo "  \033[36mdb-migrate     \033[0m Run pending database migrations"
	@echo "  \033[36mdb-migrate-dry \033[0m Show what migrations would run (dry run)"
	@echo "  \033[36mdb-rebuild     \033[0m Drop all tables and rebuild from scratch (DESTRUCTIVE!)"
	@echo "  \033[36mdb-restart     \033[0m Clean database and apply all migrations (DESTRUCTIVE!)"
	@echo ""
	@echo ""
	@echo "\033[33mCode quality utilities:\033[0m"
	@echo "  \033[36mlint            \033[0m Run ruff linting"
	@echo "  \033[36mformat          \033[0m Auto-format code with ruff"
	@echo "  \033[36mfix             \033[0m Auto-format code and run all checks"
	@echo "  \033[36mclean           \033[0m Remove __pycache__, .pyc files, and test artifacts"
	@echo ""
	@echo ""
	@echo "\033[33mDevelopment utilities:\033[0m"
	@echo "  \033[36mversion-check   \033[0m Compare local vs Docker versions for consistency"
	@echo ""
	@echo ""

# ==================== UTILITY COMMANDS (Helpers & Maintenance) ====================

# Database utilities
db-start:  ## Start PostgreSQL database only
	@echo "\033[34m◆ Starting PostgreSQL database...\033[0m"
	docker compose up -d postgres
	@echo "\033[33m⧗ Waiting for database to be ready...\033[0m"
	@docker compose exec postgres sh -c 'until pg_isready -U news_user -d french_news; do sleep 1; done'
	@echo "\033[32m✓ Database ready!\033[0m"

db-start-test:  ## Start both main and test databases
	@echo "\033[34m◆ Starting both databases...\033[0m"
	docker compose up -d postgres postgres-test
	@echo "\033[33m⧗ Waiting for databases to be ready...\033[0m"
	@docker compose exec postgres sh -c 'until pg_isready -U news_user -d french_news; do sleep 1; done'
	@echo "\033[32m✓ Both databases ready!\033[0m"

db-stop:  ## Stop all containers
	docker compose down

db-clean:  ## Stop and remove all containers and volumes (DESTRUCTIVE!)
	@if [ "$(PRODUCTION)" = "true" ]; then \
		echo "\033[31m✗ BLOCKED: db-clean disabled in production mode\033[0m"; \
		exit 1; \
	fi
	@echo "\033[31m⚠ WARNING: This will destroy ALL data and containers!\033[0m"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "\033[33m◆ Stopping and removing containers...\033[0m"
	docker compose down -v
	docker compose rm -f

db-migrate:  ## Run pending database migrations
	@echo "\033[34m◆ Running database migrations...\033[0m"
	@$(MAKE) db-start > /dev/null 2>&1
	@PYTHONPATH=$(SRC) $(PYTHON) database/migrations/run_migrations.py
	@echo "\033[32m✓ Migrations complete!\033[0m"

db-migrate-dry:  ## Show what migrations would run (dry run)
	@./scripts/check-migrations.sh

db-rebuild:  ## Drop all tables and rebuild from scratch (DESTRUCTIVE!)
	@if [ "$(PRODUCTION)" = "true" ]; then \
		echo "\033[31m✗ BLOCKED: db-rebuild disabled in production mode\033[0m"; \
		exit 1; \
	fi
	@echo "\033[31m⚠ WARNING: This will destroy ALL data and rebuild from scratch!\033[0m"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@./scripts/rebuild-db.sh

db-restart:  ## Clean database and apply all migrations (DESTRUCTIVE!)
	@if [ "$(PRODUCTION)" = "true" ]; then \
		echo "\033[31m✗ BLOCKED: db-restart disabled in production mode\033[0m"; \
		exit 1; \
	fi
	@echo "\033[31m⚠ WARNING: This will destroy ALL data and restart fresh!\033[0m"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "\033[34m◆ Restarting database from scratch...\033[0m"
	@echo "\033[33m◆ Stopping and removing containers...\033[0m"
	@docker compose down -v
	@docker compose rm -f
	@$(MAKE) db-migrate
	@echo "\033[32m✓ Database restart complete!\033[0m"



# Code quality utilities
lint:  ## Run ruff linting
	$(RUFF) check $(SRC) tests

format:  ## Auto-format code with ruff
	$(RUFF) format $(SRC) tests

fix:  ## Auto-format code and run all checks
	@echo "\033[36m▶ Running ruff format and linting with fixes...\033[0m"
	$(RUFF) check --fix $(SRC) tests
	@echo "\033[32m✓ Code quality checks passed!\033[0m"

clean:  ## Remove __pycache__, .pyc files, and test artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name ".coverage*" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

version-check:  ## Compare local vs Docker versions for consistency
	@echo "\033[36m◆ Environment Version Comparison\033[0m"
	@echo "\033[33m├─ Local Python:\033[0m $(shell $(PYTHON) --version)"
	@echo "\033[33m└─ Docker Python:\033[0m $(shell docker run --rm python:3.12-slim python --version 2>/dev/null || echo 'Docker not available')"
	@echo ""
	@echo "\033[32m✓ Versions should match for consistent behavior\033[0m"