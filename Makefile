# ========= Makefile for French News Scraper =========

# Load .env if it exists (optional)
-include .env

# Default values (override with .env)
POSTGRES_USER ?= news_user
POSTGRES_DB ?= french_news

# Project configuration
PYTHON := ./venv/bin/python
PYTEST := ./venv/bin/pytest
RUFF := ./venv/bin/ruff
SRC := src
MAIN_MODULE := main

.DEFAULT_GOAL := help
.PHONY: run run-cloud docker-build docker-cloud run-test-data test test-unit test-integration test-e2e test-quick fix clean db-start db-init db-rebuild db-drop db-clear db-clean help

# ==================== CORE COMMANDS ====================

run:  ## Run scraper with live scrapes (use: make run ART_NUM=10 to limit per source)
	@echo "\033[34m◆ Running scraper in development mode...\033[0m"
	$(if $(ART_NUM),@echo "\033[33m  Limiting to $(ART_NUM) articles per source\033[0m",)
	ENVIRONMENT=development MAX_ARTICLES=$(or $(ART_NUM),) PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE)

run-cloud:  ## Run scraper using Cloud SQL (requires .env.cloud and proxy running)
	@echo "\033[35m◆ Running scraper with Cloud SQL...\033[0m"
	@if [ ! -f .env.cloud ]; then \
		echo "\033[31m✗ Error: .env.cloud not found\033[0m"; \
		exit 1; \
	fi
	@bash -c 'set -a; source .env.cloud; set +a; ENVIRONMENT=development PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE)'

docker-build:  ## Build Docker image for scraper
	@echo "\033[36m◆ Building Docker image...\033[0m"
	docker build -t french-news-scraper .
	@echo "\033[32m✓ Docker image built: french-news-scraper\033[0m"

docker-cloud:  ## Run scraper in Docker using Cloud SQL (requires .env.cloud.docker and proxy running)
	@echo "\033[35m◆ Running Docker container with Cloud SQL...\033[0m"
	$(if $(ART_NUM),@echo "\033[33m  Limiting to $(ART_NUM) articles per source\033[0m",)
	@if [ ! -f .env.cloud.docker ]; then \
		echo "\033[31m✗ Error: .env.cloud.docker not found\033[0m"; \
		echo "Create it with POSTGRES_HOST=127.0.0.1 (for --network host)"; \
		exit 1; \
	fi
	docker run --rm \
		--network host \
		-v $(PWD)/logs:/app/logs \
		-e MAX_ARTICLES=$(or $(ART_NUM),) \
		-e DEBUG=$(or $(DEBUG),false) \
		--env-file .env.cloud.prod \
		french-news-scraper

run-test-data:  ## Run scraper with test data (test environment)
	@echo "\033[33m◆ Starting test database...\033[0m"
	@$(MAKE) db-start ENV=test > /dev/null 2>&1
	@echo "\033[33m◆ Running scraper with test data...\033[0m"
	ENVIRONMENT=test PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE)
	@echo "\033[32m✓ Test data processing complete\033[0m"

test:  ## Run all tests
	@echo "\033[34m◆ Running complete test suite...\033[0m"
	ENVIRONMENT=test PYTHONPATH=$(SRC):. $(PYTEST) tests/ -v $(PYTEST_ARGS)

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

db-clean:  ## Remove all containers and volumes (DESTRUCTIVE!)
	@echo "\033[31m⚠ WARNING: This will destroy ALL data!\033[0m"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose down -v
	docker compose rm -f
	@echo "\033[32m✓ Cleanup complete!\033[0m"

# ==================== CODE QUALITY ====================

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
	@echo "\033[36mrun-cloud        \033[0m Run scraper with Cloud SQL"
	@echo "\033[36mrun-test-data    \033[0m Run scraper with test data"
	@echo ""
	@echo "\033[33mDocker:\033[0m"
	@echo "  \033[36mdocker-build   \033[0m Build Docker image"
	@echo "  \033[36mdocker-cloud   \033[0m Run scraper in Docker with Cloud SQL"
	@echo ""
	@echo "  Examples:"
	@echo "    make docker-cloud ART_NUM=10        # Limit articles"
	@echo "    make docker-cloud ART_NUM=5 DEBUG=true  # With debug"
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
	@echo "  \033[36mdb-clean       \033[0m Remove all data (DESTRUCTIVE!)"
	@echo ""
	@echo "  Examples:"
	@echo "    make db-drop ENV=dev   # Drop dev tables"
	@echo "    make db-drop ENV=test  # Drop test tables"
	@echo ""
	@echo "\033[33mCode Quality:\033[0m"
	@echo "  \033[36mfix            \033[0m Format + fix linting"
	@echo "  \033[36mclean          \033[0m Remove cache files"
	@echo ""
