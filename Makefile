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
.PHONY: run run-test-data test test-unit test-integration test-e2e test-quick lint format fix clean db-start db-start-test db-init db-init-test db-stop db-clean help

# ==================== CORE COMMANDS ====================

run:  ## Run scraper in development mode (live scraping)
	@echo "\033[34m◆ Running scraper in development mode...\033[0m"
	ENVIRONMENT=development PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE)

run-test-data:  ## Run scraper with test data (test environment)
	@echo "\033[33m◆ Starting test database...\033[0m"
	@$(MAKE) db-start-test > /dev/null 2>&1
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

db-start:  ## Start development database (port 5432)
	@echo "\033[34m◆ Starting development database...\033[0m"
	docker compose up -d postgres-dev
	@sleep 2
	@docker compose exec postgres-dev sh -c 'until pg_isready -U $(POSTGRES_USER) -d $(POSTGRES_DB); do sleep 1; done' 2>/dev/null || true
	@echo "\033[32m✓ Development database ready on port 5432!\033[0m"

db-start-test:  ## Start test database (port 5433)
	@echo "\033[34m◆ Starting test database...\033[0m"
	docker compose up -d postgres-test
	@sleep 2
	@docker compose exec postgres-test sh -c 'until pg_isready -U news_user -d french_news_test; do sleep 1; done' 2>/dev/null || true
	@echo "\033[32m✓ Test database ready on port 5433!\033[0m"

db-init:  ## Initialize development database schema
	@echo "\033[34m◆ Initializing development database...\033[0m"
	@$(MAKE) db-start > /dev/null 2>&1
	CONTAINER_NAME=french_news_dev_db PGDATABASE=$(POSTGRES_DB) PGUSER=$(POSTGRES_USER) PGPASSWORD=$(POSTGRES_PASSWORD) ./database/init.sh
	@echo "\033[32m✓ Development database initialized!\033[0m"

db-init-test:  ## Initialize test database schema
	@echo "\033[34m◆ Initializing test database...\033[0m"
	@$(MAKE) db-start-test > /dev/null 2>&1
	CONTAINER_NAME=french_news_test_db PGDATABASE=french_news_test PGUSER=news_user PGPASSWORD=test_password ./database/init.sh
	@echo "\033[32m✓ Test database initialized!\033[0m"

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
	@echo "\033[33mDatabase:\033[0m"
	@echo "  \033[36mdb-start       \033[0m Start dev database (5432)"
	@echo "  \033[36mdb-start-test  \033[0m Start test database (5433)"
	@echo "  \033[36mdb-init        \033[0m Initialize dev database schema"
	@echo "  \033[36mdb-init-test   \033[0m Initialize test database schema"
	@echo "  \033[36mdb-stop        \033[0m Stop all databases"
	@echo "  \033[36mdb-clean       \033[0m Remove all data (DESTRUCTIVE!)"
	@echo ""
	@echo "\033[33mCode Quality:\033[0m"
	@echo "  \033[36mlint           \033[0m Run ruff linting"
	@echo "  \033[36mformat         \033[0m Auto-format code"
	@echo "  \033[36mfix            \033[0m Format + fix linting"
	@echo "  \033[36mclean          \033[0m Remove cache files"
	@echo ""
