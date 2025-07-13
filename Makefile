# ========= Makefile for article_scrapers project =========

# Python interpreter (uses virtualenv by default)
PYTHON := python
SRC := src
MAIN_MODULE := article_scrapers.main
SETTINGS_FILE := $(SRC)/article_scrapers/config/settings.py

# Docker image name
IMAGE := my-scraper

# Default command
.DEFAULT_GOAL := help

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

lint:  ## Run flake8 on the src directory
	flake8 $(SRC)

format:  ## Auto-format code with black
	black $(SRC)

check-format:  ## Check formatting without modifying files
	black --check $(SRC)

mypy:  ## Run static type checks
	mypy $(SRC)

clean:  ## Remove __pycache__ and .pyc files
	find . -type d -name "__pycache__" -exec rm -r {} + ;
	find . -name "*.pyc" -delete

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
# make test             # run tests
# make lint             # check code style
# make format           # auto-format code
# make mypy             # static type checks
# make clean            # remove pycache and .pyc files
# make help             # show all commands
