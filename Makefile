# ========= Makefile for article_scrapers project =========

# Python interpreter (uses virtualenv by default)
PYTHON := python3
SRC := src
MAIN_MODULE := main
SETTINGS_FILE := $(SRC)/config/settings.py

# Docker image name
IMAGE := my-scraper

# Default command
.DEFAULT_GOAL := help

# Declare phony targets to avoid conflicts with files/directories
.PHONY: run run-live run-offline test tests test-essential test-integration test-offline lint format check-format mypy fix clean docker-build docker-pipeline docker-clean dbt-run dbt-test dbt-debug pipeline help tree

# ========== Local venv commands ==========

run:  ## Run main script locally (must be inside venv)
	cd $(SRC) && $(PYTHON) -m $(MAIN_MODULE)

run-live:  ## Run script in live mode (OFFLINE = False)
	@echo "Setting OFFLINE = False and running in live mode..."
	@sed -i.bak 's/OFFLINE = True/OFFLINE = False/' $(SETTINGS_FILE)
	cd $(SRC) && $(PYTHON) -m $(MAIN_MODULE)
	@sed -i.bak 's/OFFLINE = False/OFFLINE = True/' $(SETTINGS_FILE)
	@rm -f $(SETTINGS_FILE).bak

run-offline:  ## Run script in offline mode (OFFLINE = True)
	@echo "Setting OFFLINE = True and running in offline mode..."
	@sed -i.bak 's/OFFLINE = False/OFFLINE = True/' $(SETTINGS_FILE)
	cd $(SRC) && $(PYTHON) -m $(MAIN_MODULE)
	@sed -i.bak 's/OFFLINE = True/OFFLINE = False/' $(SETTINGS_FILE)
	@rm -f $(SETTINGS_FILE).bak

test:  ## Run all tests + pipeline test
	@echo "\033[33m◆ Running Python tests...\033[0m"
	PYTHONPATH=$(SRC) pytest -v
	@echo "\033[33m◆ Running pipeline integration test...\033[0m"
	$(MAKE) test-pipeline

tests:  ## Run all tests (alias for test)
	$(MAKE) test

test-essential:  ## Run essential working tests only
	PYTHONPATH=$(SRC) pytest -v tests/test_essential.py

test-integration:  ## Run integration tests only
	PYTHONPATH=$(SRC) pytest -v tests/integration/

test-offline:  ## Run the offline mode integration test
	PYTHONPATH=$(SRC) pytest -v tests/integration/test_offline_mode.py::TestOfflineMode::test_make_run_offline_integration

lint:  ## Run ruff linting
	ruff check $(SRC)

format:  ## Auto-format code with ruff
	ruff format $(SRC)

check-format:  ## Check formatting without modifying files
	ruff format --check $(SRC)

mypy:  ## Run static type checks
	mypy $(SRC)

fix:  ## Auto-format code and run all checks
	@echo "\033[36m▶ Formatting code with ruff...\033[0m"
	ruff format $(SRC)
	@echo "\033[33m▶ Running ruff linting...\033[0m"
	ruff check --fix $(SRC)
	@echo "\033[33m▶ Running mypy type checks...\033[0m"
	mypy $(SRC)
	@echo "\033[32m✓ All checks passed!\033[0m"

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
	cd french_flashcards && ../venv/bin/dbt run

dbt-test:  ## Run dbt tests  
	cd french_flashcards && ../venv/bin/dbt test

dbt-debug:  ## Test dbt database connection
	cd french_flashcards && ../venv/bin/dbt debug

pipeline:  ## Run full pipeline: scrape articles + process with dbt
	@echo "\033[34m■ Step 1: Scraping articles...\033[0m"
	$(PYTHON) database_main.py
	@echo "\033[35m■ Step 2: Processing with dbt...\033[0m"
	cd french_flashcards && ../venv/bin/dbt run
	@echo "\033[32m✓ Pipeline complete! Check database for word frequencies.\033[0m"

test-pipeline:  ## Run pipeline test with fresh database (clears data first)
	@echo "\033[33m◆ Running pipeline test with fresh data...\033[0m"
	@echo "\033[31m× Step 1: Clearing database...\033[0m"
	@docker compose exec postgres psql -U news_user -d french_news -c "TRUNCATE news_data.articles CASCADE;" > /dev/null 2>&1 || echo "Database not running - will start fresh"
	@echo "\033[34m■ Step 2: Scraping test articles...\033[0m"
	$(PYTHON) database_main.py
	@echo "\033[35m■ Step 3: Processing with dbt...\033[0m"
	cd french_flashcards && ../venv/bin/dbt run
	@echo "\033[36m▶ Step 4: Verifying results...\033[0m"
	@docker compose exec postgres psql -U news_user -d french_news -c "SELECT COUNT(*) as articles FROM dbt_staging.cleaned_articles; SELECT COUNT(*) as words FROM dbt_staging.word_frequency_overall;"
	@echo "\033[32m✓ Pipeline test complete!\033[0m"

# ========== Docker commands ==========

docker-build:  ## Build all Docker images
	docker compose build

docker-pipeline:  ## Run full containerized pipeline (scraper + dbt)
	@echo "\033[35m▲ Starting full Docker pipeline...\033[0m"
	@echo "\033[34m□ Step 1: Starting database...\033[0m"
	docker compose up -d postgres
	@echo "\033[33m⧗ Waiting for database to be ready...\033[0m"
	docker compose exec postgres sh -c 'until pg_isready -U news_user -d french_news; do sleep 1; done'
	@echo "\033[34m■ Step 2: Running scraper...\033[0m"
	docker compose run --rm scraper
	@echo "\033[35m■ Step 3: Running dbt transformations...\033[0m"
	docker compose run --rm dbt
	@echo "\033[32m✓ Pipeline complete! Check database for results.\033[0m"

docker-test-pipeline:  ## Run pipeline test in Docker with fresh data
	@echo "\033[35m◆ Running Docker pipeline test with fresh data...\033[0m"
	@echo "\033[34m□ Step 1: Starting database...\033[0m"
	docker compose up -d postgres
	@echo "\033[33m⧗ Waiting for database...\033[0m"
	docker compose exec postgres sh -c 'until pg_isready -U news_user -d french_news; do sleep 1; done'
	@echo "\033[31m× Step 2: Clearing database...\033[0m"
	docker compose exec postgres psql -U news_user -d french_news -c "TRUNCATE news_data.articles CASCADE;"
	@echo "\033[34m■ Step 3: Running scraper...\033[0m"
	docker compose run --rm scraper
	@echo "\033[35m■ Step 4: Running dbt...\033[0m"
	docker compose run --rm dbt
	@echo "\033[36m▶ Step 5: Verifying results...\033[0m"
	@docker compose exec postgres psql -U news_user -d french_news -c "SELECT COUNT(*) as articles FROM dbt_staging.cleaned_articles; SELECT COUNT(*) as words FROM dbt_staging.word_frequency_overall;"
	@echo "\033[32m✓ Docker pipeline test complete!\033[0m"

docker-clean:  ## Stop and remove all containers
	docker compose down
	docker compose rm -f

# ========== Utilities ==========

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'


# ========== Random commands ==========

tree:  ## Show directory tree
	tree -L 4 -I venv    
	

# make run              # run script locally
# make run-live         # run script in live mode (OFFLINE = False)
# make run-offline      # run script in offline mode (OFFLINE = True)
# make docker-build     # build docker image
# make docker-run       # run script inside docker
# make test             # run all tests
# make tests            # run all tests (alias)
# make test-essential   # run essential working tests only
# make test-integration # run integration tests only
# make test-offline     # run offline mode integration test
# make lint             # check code style
# make format           # auto-format code
# make mypy             # static type checks
# make clean            # remove pycache and .pyc files
# make help             # show all commands
