#!/bin/bash
set -e

echo -e "\033[33m◆ Starting database for test data run...\033[0m"
make db-start > /dev/null 2>&1

echo -e "\033[33m◆ Running scraper with test data...\033[0m"
ENVIRONMENT=test PYTHONPATH=src ./venv/bin/python -m main

echo ""
echo -e "\033[32m✓ Test data processing complete\033[0m"
echo -e "\033[36m▶ Connect to DBeaver to analyze results\033[0m"