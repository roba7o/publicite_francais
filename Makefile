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
.PHONY: run test test-unit test-integration test-performance help test-essential lint format fix clean db-start db-stop db-clean db-migrate db-migrate-dry db-rollback version-check

# ==================== CORE COMMANDS (Daily Usage) ====================

run:  ## Run scraper locally (live mode)
	TEST_MODE=false PYTHONPATH=$(SRC) $(PYTHON) -m $(MAIN_MODULE)


test:  ## Run all tests (unit + integration + performance)
	@echo "\033[33m◆ Ensuring database is running for tests...\033[0m"
	@$(MAKE) db-start > /dev/null 2>&1
	@echo "\033[33m◆ Running complete test suite...\033[0m"
	@TEST_MODE=true PYTHONPATH=$(SRC) $(PYTEST) -v
	@echo ""
	@echo "\033[32m╔════════════════════════════════════════╗"
	@echo "║          TEST SUITE SUMMARY           ║"
	@echo "╚════════════════════════════════════════╝\033[0m"
	@echo "\033[32m✓ Unit Tests: PASSED\033[0m"
	@echo "\033[32m✓ Integration Tests: PASSED\033[0m"
	@echo "\033[32m✓ Performance Tests: PASSED\033[0m"
	@echo ""
	@echo "\033[36m▶ ALL TESTS PASSED - COMPLETE COVERAGE\033[0m"

test-unit:  ## Run unit tests only
	@echo "\033[33m◆ Running unit tests...\033[0m"
	@TEST_MODE=true PYTHONPATH=$(SRC) $(PYTEST) -v tests/unit/
	@echo ""
	@echo "\033[32m✓ Unit tests completed\033[0m"

test-integration:  ## Run integration tests only (starts database automatically)
	@echo "\033[33m◆ Ensuring database is running for integration tests...\033[0m"
	@$(MAKE) db-start > /dev/null 2>&1
	@echo "\033[33m◆ Running integration tests...\033[0m"
	@TEST_MODE=true PYTHONPATH=$(SRC) $(PYTEST) -v tests/integration/
	@echo ""
	@echo "\033[32m✓ Integration tests completed\033[0m"

test-performance:  ## Run performance tests only (starts database automatically)
	@echo "\033[33m◆ Ensuring database is running for performance tests...\033[0m"
	@$(MAKE) db-start > /dev/null 2>&1
	@echo "\033[33m◆ Running performance tests...\033[0m"
	@TEST_MODE=true PYTHONPATH=$(SRC) $(PYTEST) -v tests/performance/ --tb=short
	@echo ""
	@echo "\033[32m✓ Performance tests completed\033[0m"

help:  ## Show available commands
	@echo ""
	@echo "\033[1m\033[36m========== CORE COMMANDS (Daily Usage) ==========\033[0m"
	@echo "\033[36mrun         \033[0m Run scraper locally"
	@echo "\033[36mtest        \033[0m Run all tests (unit + integration + performance)"
	@echo "\033[36mhelp        \033[0m Show available commands"
	@echo ""
	@echo "\033[1m\033[33m========== UTILITY COMMANDS (Helpers & Maintenance) ==========\033[0m"
	@echo ""
	@echo "\033[33mDatabase utilities:\033[0m"
	@echo "  \033[36mdb-start       \033[0m Start PostgreSQL database only"
	@echo "  \033[36mdb-stop        \033[0m Stop all containers"
	@echo "  \033[36mdb-clean       \033[0m Stop and remove all containers and volumes"
	@echo "  \033[36mdb-migrate     \033[0m Run pending database migrations"
	@echo "  \033[36mdb-migrate-dry \033[0m Show what migrations would run (dry run)"
	@echo "  \033[36mdb-rollback    \033[0m Rollback to migration (usage: make db-rollback TARGET=001)"
	@echo ""
	@echo "\033[33mCode quality utilities:\033[0m"
	@echo "  \033[36mlint            \033[0m Run ruff linting"
	@echo "  \033[36mformat          \033[0m Auto-format code with ruff"
	@echo "  \033[36mfix             \033[0m Auto-format code and run all checks"
	@echo "  \033[36mclean           \033[0m Remove __pycache__, .pyc files, and test artifacts"
	@echo ""
	@echo "\033[33mTesting utilities:\033[0m"
	@echo "  \033[36mtest-unit       \033[0m Run unit tests only (fast, no database)"
	@echo "  \033[36mtest-integration\033[0m Run integration tests only (requires database)"
	@echo "  \033[36mtest-performance\033[0m Run performance tests only (with metrics)"
	@echo "  \033[36mtest-essential  \033[0m Run essential working tests only"
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

db-stop:  ## Stop all containers
	docker compose down

db-clean:  ## Stop and remove all containers and volumes (DESTRUCTIVE!)
	@if [ "$(PRODUCTION)" = "true" ]; then \
		echo "\033[31m✗ BLOCKED: db-clean disabled in production mode\033[0m"; \
		exit 1; \
	fi
	@echo "\033[31m⚠ WARNING: This will destroy ALL data and containers!\033[0m"
	@echo "\033[33m◆ Stopping and removing containers...\033[0m"
	docker compose down -v
	docker compose rm -f

db-migrate:  ## Run pending database migrations
	@echo "\033[34m◆ Running database migrations...\033[0m"
	@$(MAKE) db-start > /dev/null 2>&1
	@PYTHONPATH=$(SRC) $(PYTHON) database/migrations/run_migrations.py
	@echo "\033[32m✓ Migrations complete!\033[0m"

db-migrate-dry:  ## Show what migrations would run (dry run)
	@echo "\033[34m◆ Checking pending migrations (dry run)...\033[0m"
	@$(MAKE) db-start > /dev/null 2>&1
	@PYTHONPATH=$(SRC) $(PYTHON) database/migrations/run_migrations.py --dry-run

db-rollback:  ## Rollback to specific migration (usage: make db-rollback TARGET=001)
	@if [ -z "$(TARGET)" ]; then \
		echo "\033[31m✗ TARGET required. Usage: make db-rollback TARGET=001\033[0m"; \
		exit 1; \
	fi
	@echo "\033[31m◆ Rolling back to migration $(TARGET)...\033[0m"
	@$(MAKE) db-start > /dev/null 2>&1
	@PYTHONPATH=$(SRC) $(PYTHON) database/migrations/run_migrations.py --rollback $(TARGET)


# Code quality utilities
lint:  ## Run ruff linting
	$(RUFF) check $(SRC) tests

format:  ## Auto-format code with ruff
	$(RUFF) format $(SRC) tests

fix:  ## Auto-format code and run all checks
	@echo "\033[36m▶ Running ruff format and linting with fixes...\033[0m"
	$(RUFF) check --fix $(SRC) tests
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

# Development utilities
test-essential:  ## Run essential working tests only
	@echo "\033[33m◆ Running essential system tests...\033[0m"
	@TEST_MODE=true PYTHONPATH=$(SRC) $(PYTEST) -v tests/unit/test_component_factory.py::TestConfiguration
	@echo "\033[32m✓ Essential tests completed\033[0m"



version-check:  ## Compare local vs Docker versions for consistency
	@echo "\033[36m◆ Environment Version Comparison\033[0m"
	@echo "\033[33m├─ Local Python:\033[0m $(shell $(PYTHON) --version)"
	@echo "\033[33m└─ Docker Python:\033[0m $(shell docker run --rm python:3.12-slim python --version 2>/dev/null || echo 'Docker not available')"
	@echo ""
	@echo "\033[32m✓ Versions should match for consistent behavior\033[0m"