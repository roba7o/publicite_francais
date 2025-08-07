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
.PHONY: run run-live run-offline test tests test-essential test-integration test-offline lint format check-format mypy fix clean docker-build docker-run help tree

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

test:  ## Run all tests
	PYTHONPATH=$(SRC) pytest -v

tests:  ## Run all tests (alias for test)
	PYTHONPATH=$(SRC) pytest -v

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
	@echo "🔧 Formatting code with ruff..."
	ruff format $(SRC)
	@echo "🔍 Running ruff linting..."
	ruff check --fix $(SRC)
	@echo "🔍 Running mypy type checks..."
	mypy $(SRC)
	@echo "✅ All checks passed!"

clean:  ## Remove __pycache__, .pyc files, and test artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name ".coverage*" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# ========== Docker commands ==========

docker-build:  ## Build Docker image
	docker build -t $(IMAGE) .

docker-run:  ## Run app using Docker
	docker run --rm \
	  -v ${PWD}/src:/app/src \
	  -v ${PWD}/output:/app/output \
	  $(IMAGE)

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
