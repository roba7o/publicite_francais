# ========= Makefile for French News Scraper =========

# Check if .env file exists
ifeq (,$(wildcard .env))
$(error .env file missing! Run 'cp .env.example .env' and configure it first)
endif

# Load environment variables from .env
include .env
export $(shell sed 's/=.*//' .env)

# Project configuration
PYTHON := ./venv/bin/python
PYTEST := ./venv/bin/pytest
RUFF := ./venv/bin/ruff
SRC := src
MAIN_MODULE := main

.DEFAULT_GOAL := help
.PHONY: run run-cloud run-test-data test test-unit test-integration test-e2e test-quick lint format fix clean db-start db-init db-rebuild db-drop db-clear db-stop db-clean help

# Database environment configuration (empty by default, requires ENV flag)

# ==================== CORE COMMANDS ====================

run:  ## Run scraper in development mode (live scraping)
	@echo "\033[34m◆ Running scraper in development mode...\033[0m"
	ENVIRONMENT=development PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE)

run-cloud:  ## Run scraper using Cloud SQL (requires .env.cloud and proxy running)
	@echo "\033[35m◆ Running scraper with Cloud SQL...\033[0m"
	@if [ ! -f .env.cloud ]; then \
		echo "\033[31m✗ Error: .env.cloud not found\033[0m"; \
		exit 1; \
	fi
	@bash -c 'set -a; source .env.cloud; set +a; ENVIRONMENT=development PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE)'

run-test-data:  ## Run scraper with test data (test environment)
	@echo "\033[33m◆ Starting test database...\033[0m"
	@$(MAKE) db-start ENV=test > /dev/null 2>&1
	@echo "\033[33m◆ Running scraper with test data...\033[0m"
	ENVIRONMENT=test PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE)
	@echo "\033[32m✓ Test data processing complete\033[0m"

test:  ## Run all tests
	@echo "\033[34m◆ Running complete test suite...\033[0m"
	ENVIRONMENT=test PYTHONPATH=$(SRC):. $(PYTEST) tests/ -v

test-unit:  ## Run unit tests only
	@echo "\033[34m◆ Running unit tests...\033[0m"
	ENVIRONMENT=test PYTHONPATH=$(SRC):. $(PYTEST) tests/unit/ -v

test-integration:  ## Run integration tests only
	@echo "\033[34m◆ Running integration tests...\033[0m"
	ENVIRONMENT=test PYTHONPATH=$(SRC):. $(PYTEST) tests/integration/ -v

test-e2e:  ## Run E2E pipeline tests
	@echo "\033[34m◆ Running E2E pipeline tests...\033[0m"
	ENVIRONMENT=test PYTHONPATH=$(SRC):. $(PYTEST) tests/e2e/ -v

test-quick:  ## Run unit + integration (skip E2E)
	@echo "\033[34m◆ Running quick test suite...\033[0m"
	ENVIRONMENT=test PYTHONPATH=$(SRC):. $(PYTEST) tests/unit/ tests/integration/ -v

# ==================== DATABASE UTILITIES ====================

db-start:  ## Start database (requires ENV=dev or ENV=test)
	@if [ -z "$(ENV)" ] || ([ "$(ENV)" != "dev" ] && [ "$(ENV)" != "test" ]); then \
		echo "\033[31m✗ Error: ENV flag required\033[0m"; \
		echo "Usage: make db-start ENV=dev  or  make db-start ENV=test"; \
		exit 1; \
	fi
	@echo "\033[34m◆ Starting $(ENV) database...\033[0m"
	@if [ "$(ENV)" = "test" ]; then \
		docker compose up -d postgres-test; \
		sleep 2; \
		docker compose exec postgres-test sh -c 'until pg_isready -U news_user -d french_news_test; do sleep 1; done' 2>/dev/null || true; \
		echo "\033[32m✓ Database ready on port 5433!\033[0m"; \
	else \
		docker compose up -d postgres-dev; \
		sleep 2; \
		docker compose exec postgres-dev sh -c 'until pg_isready -U $(POSTGRES_USER) -d $(POSTGRES_DB); do sleep 1; done' 2>/dev/null || true; \
		echo "\033[32m✓ Database ready on port 5432!\033[0m"; \
	fi

db-init:  ## Initialize database schema (requires ENV=dev or ENV=test)
	@if [ -z "$(ENV)" ] || ([ "$(ENV)" != "dev" ] && [ "$(ENV)" != "test" ]); then \
		echo "\033[31m✗ Error: ENV flag required\033[0m"; \
		echo "Usage: make db-init ENV=dev  or  make db-init ENV=test"; \
		exit 1; \
	fi
	@echo "\033[34m◆ Initializing $(ENV) database...\033[0m"
	@$(MAKE) db-start ENV=$(ENV) > /dev/null 2>&1
	@if [ "$(ENV)" = "test" ]; then \
		CONTAINER_NAME=french_news_test_db PGDATABASE=french_news_test PGUSER=news_user ./scripts/sh/apply_schema.sh; \
	else \
		CONTAINER_NAME=french_news_dev_db PGDATABASE=$(POSTGRES_DB) PGUSER=$(POSTGRES_USER) ./scripts/sh/apply_schema.sh; \
	fi
	@echo "\033[32m✓ Database initialized!\033[0m"

db-rebuild:  ## Rebuild database from scratch (requires ENV=dev or ENV=test) DESTRUCTIVE!
	@if [ -z "$(ENV)" ] || ([ "$(ENV)" != "dev" ] && [ "$(ENV)" != "test" ]); then \
		echo "\033[31m✗ Error: ENV flag required\033[0m"; \
		echo "Usage: make db-rebuild ENV=dev  or  make db-rebuild ENV=test"; \
		exit 1; \
	fi
	@echo "\033[31m◆ Rebuilding $(ENV) database...\033[0m"
	@$(MAKE) db-start ENV=$(ENV) > /dev/null 2>&1
	@if [ "$(ENV)" = "test" ]; then \
		CONTAINER_NAME=french_news_test_db PGDATABASE=french_news_test PGUSER=news_user ./scripts/sh/rebuild_db.sh; \
	else \
		CONTAINER_NAME=french_news_dev_db PGDATABASE=$(POSTGRES_DB) PGUSER=$(POSTGRES_USER) ./scripts/sh/rebuild_db.sh; \
	fi
	@echo "\033[32m✓ Database rebuilt!\033[0m"

db-drop:  ## Drop all tables (requires ENV=dev or ENV=test)
	@if [ -z "$(ENV)" ] || ([ "$(ENV)" != "dev" ] && [ "$(ENV)" != "test" ]); then \
		echo "\033[31m✗ Error: ENV flag required\033[0m"; \
		echo "Usage: make db-drop ENV=dev  or  make db-drop ENV=test"; \
		exit 1; \
	fi
	@$(MAKE) db-start ENV=$(ENV) > /dev/null 2>&1
	@echo "\033[31m◆ Dropping all tables from $(ENV) database...\033[0m"
	@if [ "$(ENV)" = "test" ]; then \
		CONTAINER_NAME=french_news_test_db PGDATABASE=french_news_test PGUSER=news_user ./scripts/sh/drop_tables.sh; \
	else \
		CONTAINER_NAME=french_news_dev_db PGDATABASE=$(POSTGRES_DB) PGUSER=$(POSTGRES_USER) ./scripts/sh/drop_tables.sh; \
	fi
	@echo "\033[32m✓ Tables dropped!\033[0m"

db-clear:  ## Clear all data (requires ENV=dev or ENV=test)
	@if [ -z "$(ENV)" ] || ([ "$(ENV)" != "dev" ] && [ "$(ENV)" != "test" ]); then \
		echo "\033[31m✗ Error: ENV flag required\033[0m"; \
		echo "Usage: make db-clear ENV=dev  or  make db-clear ENV=test"; \
		exit 1; \
	fi
	@echo "\033[33m◆ Clearing all data from $(ENV) database...\033[0m"
	@$(MAKE) db-start ENV=$(ENV) > /dev/null 2>&1
	@if [ "$(ENV)" = "test" ]; then \
		CONTAINER_NAME=french_news_test_db PGDATABASE=french_news_test PGUSER=news_user ./scripts/sh/clear_tables.sh; \
	else \
		CONTAINER_NAME=french_news_dev_db PGDATABASE=$(POSTGRES_DB) PGUSER=$(POSTGRES_USER) ./scripts/sh/clear_tables.sh; \
	fi
	@echo "\033[32m✓ Data cleared!\033[0m"

db-stop:  ## Stop all databases
	@echo "\033[33m◆ Stopping all databases...\033[0m"
	docker compose down

db-clean:  ## Remove all containers and volumes (DESTRUCTIVE!)
	@echo "\033[31m⚠ WARNING: This will destroy ALL data!\033[0m"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose down -v
	docker compose rm -f
	@echo "\033[32m✓ Cleanup complete!\033[0m"

# ==================== CODE QUALITY ====================

lint:  ## Run ruff linting
	$(RUFF) check $(SRC) tests

format:  ## Auto-format code
	$(RUFF) format $(SRC) tests

fix:  ## Auto-format and fix linting issues
	@echo "\033[36m▶ Running ruff...\033[0m"
	$(RUFF) check --fix $(SRC) tests
	$(RUFF) format $(SRC) tests
	@echo "\033[32m✓ Code quality checks complete!\033[0m"

clean:  ## Remove cache and test artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name ".coverage*" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# ==================== HELP ====================

help:  ## Show available commands
	@echo ""
	@echo "\033[1m\033[36m========== CORE COMMANDS ==========\033[0m"
	@echo "\033[36mrun              \033[0m Run scraper in development mode"
	@echo "\033[36mrun-test-data    \033[0m Run scraper with test data"
	@echo ""
	@echo "\033[33mTesting:\033[0m"
	@echo "  \033[36mtest           \033[0m Run all tests"
	@echo "  \033[36mtest-unit      \033[0m Run unit tests only"
	@echo "  \033[36mtest-integration\033[0m Run integration tests"
	@echo "  \033[36mtest-e2e       \033[0m Run E2E tests"
	@echo "  \033[36mtest-quick     \033[0m Run unit + integration"
	@echo ""
	@echo "\033[1m\033[33m========== UTILITIES ==========\033[0m"
	@echo "\033[33mDatabase (requires ENV=dev or ENV=test):\033[0m"
	@echo "  \033[36mdb-start       \033[0m Start database"
	@echo "  \033[36mdb-init        \033[0m Initialize database schema"
	@echo "  \033[36mdb-rebuild     \033[0m Rebuild database (DESTRUCTIVE!)"
	@echo "  \033[36mdb-drop        \033[0m Drop all tables"
	@echo "  \033[36mdb-clear       \033[0m Clear all data"
	@echo "  \033[36mdb-stop        \033[0m Stop all databases"
	@echo "  \033[36mdb-clean       \033[0m Remove all data (DESTRUCTIVE!)"
	@echo ""
	@echo "  Examples:"
	@echo "    make db-drop ENV=dev   # Drop dev tables"
	@echo "    make db-drop ENV=test  # Drop test tables"
	@echo ""
	@echo "\033[33mCode Quality:\033[0m"
	@echo "  \033[36mlint           \033[0m Run ruff linting"
	@echo "  \033[36mformat         \033[0m Auto-format code"
	@echo "  \033[36mfix            \033[0m Format + fix linting"
	@echo "  \033[36mclean          \033[0m Remove cache files"
	@echo ""
