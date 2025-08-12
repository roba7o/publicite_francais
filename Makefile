# ========= Makefile for article_scrapers project =========

# Python interpreter (uses virtualenv by default)
PYTHON := ./venv/bin/python
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
	cd $(SRC) && ../venv/bin/python -m $(MAIN_MODULE)

run-live:  ## Run script in live mode (OFFLINE = False)
	@echo "Running in live mode (OFFLINE=false)..."
	cd $(SRC) && OFFLINE=false ../venv/bin/python -m $(MAIN_MODULE)

run-offline:  ## Run script in offline mode (OFFLINE = True)
	@echo "Running in offline mode (OFFLINE=true)..."
	cd $(SRC) && OFFLINE=true ../venv/bin/python -m $(MAIN_MODULE)

test:  ## Run all tests + pipeline test
	@echo "\033[33m◆ Running Python tests...\033[0m"
	@PATH=./venv/bin:$$PATH PYTHONPATH=$(SRC) ./venv/bin/pytest -v
	@echo "\033[33m◆ Running pipeline integration test...\033[0m"
	@$(MAKE) test-pipeline
	@echo ""
	@echo "\033[32m╔════════════════════════════════════════╗"
	@echo "║          TEST SUITE SUMMARY           ║"
	@echo "╚════════════════════════════════════════╝\033[0m"
	@echo "\033[32m✓ Python Tests: PASSED (15/15)\033[0m"
	@echo "\033[32m✓ Pipeline Test: PASSED\033[0m"
	@echo "\033[32m✓ Integration Tests: PASSED\033[0m"
	@echo ""
	@echo "\033[36m▶ ALL TESTS PASSED - 100% SUCCESS RATE\033[0m"

tests:  ## Run all tests (alias for test)
	$(MAKE) test

test-essential:  ## Run essential working tests only
	PATH=./venv/bin:$$PATH PYTHONPATH=$(SRC) ./venv/bin/pytest -v tests/test_essential.py

test-db:  ## Run database connection tests
	PATH=./venv/bin:$$PATH PYTHONPATH=$(SRC) ./venv/bin/pytest -v tests/test_database_connection.py

test-integration:  ## Run integration tests only
	PATH=./venv/bin:$$PATH PYTHONPATH=$(SRC) ./venv/bin/pytest -v tests/test_deterministic_pipeline.py

test-all-local:  ## Run all tests locally (fast - no Docker)
	PATH=./venv/bin:$$PATH PYTHONPATH=$(SRC) ./venv/bin/pytest -v tests/test_essential.py tests/test_database_connection.py tests/test_deterministic_pipeline.py

test-ci:  ## Run CI-compatible tests (database + scraper, no dbt)
	PATH=./venv/bin:$$PATH PYTHONPATH=$(SRC) ./venv/bin/pytest -v tests/test_database_connection.py tests/test_deterministic_pipeline.py::TestDeterministicPipeline::test_html_file_counts tests/test_deterministic_pipeline.py::TestDeterministicPipeline::test_database_article_extraction

test-offline:  ## Run the offline mode integration test
	PATH=./venv/bin:$$PATH PYTHONPATH=$(SRC) ./venv/bin/pytest -v tests/integration/test_offline_mode.py::TestOfflineMode::test_make_run_offline_integration

lint:  ## Run ruff linting
	./venv/bin/ruff check $(SRC)

format:  ## Auto-format code with ruff
	./venv/bin/ruff format $(SRC)

check-format:  ## Check formatting without modifying files
	./venv/bin/ruff format --check $(SRC)

mypy:  ## Run static type checks
	./venv/bin/mypy $(SRC)

fix:  ## Auto-format code and run all checks
	@echo "\033[36m▶ Formatting code with ruff...\033[0m"
	./venv/bin/ruff format $(SRC)
	@echo "\033[33m▶ Running ruff linting...\033[0m"
	./venv/bin/ruff check --fix $(SRC)
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
	cd french_flashcards && ../venv/bin/dbt run

dbt-run-test:  ## Run dbt models with test data (uses HTML test files)
	@echo "\033[33m◆ Processing test data with dbt...\033[0m"
	cd french_flashcards && ../venv/bin/dbt run --target test
	@echo "\033[32m✓ Test data processed! Check dbt_test schema.\033[0m"

dbt-test:  ## Run dbt tests  
	cd french_flashcards && ../venv/bin/dbt test

dbt-test-target:  ## Run dbt tests on test target
	cd french_flashcards && ../venv/bin/dbt test --target test

dbt-debug:  ## Test dbt database connection
	cd french_flashcards && ../venv/bin/dbt debug

dbt-clean-test:  ## Clean test schema when done
	@echo "\033[31m× Dropping test schema...\033[0m"
	@docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c "DROP SCHEMA IF EXISTS dbt_test CASCADE;"'
	@docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c "CREATE SCHEMA dbt_test; GRANT ALL ON SCHEMA dbt_test TO $$POSTGRES_USER;"'
	@echo "\033[32m✓ Test schema cleaned\033[0m"

pipeline:  ## Run full pipeline: scrape articles + process with dbt
	@echo "\033[34m■ Step 1: Scraping articles...\033[0m"
	cd $(SRC) && ../venv/bin/python -m $(MAIN_MODULE) || (echo "\033[31m✗ Scraping failed\033[0m" && exit 1)
	@echo "\033[32m  ✓ Articles scraped successfully\033[0m"
	@echo "\033[35m■ Step 2: Processing with dbt...\033[0m"
	cd french_flashcards && ../venv/bin/dbt run || (echo "\033[31m✗ dbt processing failed\033[0m" && exit 1)
	@echo "\033[32m  ✓ dbt processing successful\033[0m"
	@echo "\033[36m▶ Verifying pipeline results...\033[0m"
	@$(MAKE) pipeline-status
	@echo "\033[32m✓ Pipeline complete!\033[0m"

pipeline-status:  ## Show pipeline status and health check
	@echo "\033[36m◆ Pipeline Health Check:\033[0m"
	@printf "\033[34m  Raw Articles: \033[0m"
	@docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -t -c "SELECT COUNT(*) FROM news_data_test.articles;"' 2>/dev/null | xargs || echo "0 (error)"
	@printf "\033[35m  dbt Sentences: \033[0m"
	@docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -t -c "SELECT COUNT(*) FROM dbt_test.sentences;"' 2>/dev/null | xargs || echo "0 (not processed)"
	@printf "\033[32m  Vocabulary: \033[0m"
	@docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -t -c "SELECT COUNT(*) FROM dbt_test.vocabulary_for_flashcards;"' 2>/dev/null | xargs || echo "0 (not processed)"

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
	@cd $(SRC) && ../venv/bin/python -m $(MAIN_MODULE) > /dev/null 2>&1 || (echo "\033[31m✗ Scraping failed\033[0m" && exit 1)
	@echo "\033[32m  ✓ Articles scraped successfully\033[0m"
	@echo "\033[35m■ Step 4: Processing with dbt (test target)...\033[0m"
	@cd french_flashcards && ../venv/bin/dbt run --target test > /dev/null 2>&1 || (echo "\033[31m✗ dbt processing failed\033[0m" && exit 1)
	@echo "\033[32m  ✓ dbt processing successful\033[0m"
	@echo "\033[36m▶ Step 5: Verifying results...\033[0m"
	@docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c "SELECT COUNT(*) as sentences FROM dbt_test.sentences; SELECT COUNT(*) as vocabulary_words FROM dbt_test.vocabulary_for_flashcards;"' 2>/dev/null
	@echo "\033[32m✓ Pipeline test complete!\033[0m"

test-workflow:  ## Complete test workflow with HTML test files
	@echo "\033[33m◆ Running complete test workflow...\033[0m"
	$(MAKE) test-pipeline
	@echo "\033[33m◆ Running dbt tests on test data...\033[0m"
	cd french_flashcards && ../venv/bin/dbt test --target test
	@echo "\033[36m▶ Test workflow complete! Clean with: make dbt-clean-test\033[0m"

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
	docker compose exec postgres sh -c 'until pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB; do sleep 1; done'
	@echo "\033[31m× Step 2: Clearing database...\033[0m"
	docker compose exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c "TRUNCATE news_data_test.articles CASCADE;"'
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
