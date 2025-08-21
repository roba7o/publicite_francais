# Makefile Commands Usage Guide

This guide explains when to use each `make` command and provides useful command combinations for common development workflows.

## Core Commands (Daily Usage)

### `make run`
**When to use:**
- Testing scraper changes (new parser, URL updates, error handling)
- Getting fresh articles without dbt processing
- Debugging scraper issues in isolation
- Quick data collection for testing

### `make pipeline` 
**When to use:**
- After changing dbt models (need fresh data + processing)
- Before committing major changes (full system test)
- Setting up data for Django app development
- Weekly/daily fresh data collection

### `make test`
**When to use:**
- Before every commit/push
- After any code changes
- When CI/CD fails and you need to debug locally
- Testing database schema changes

### `make help`
**When to use:**
- Onboarding new developers
- Forgetting command syntax
- Sharing project with others

## Database Utilities

### `make db-start`
**When to use:**
- Starting development session
- After `make db-stop` or system restart
- Before running any database-dependent tests
- Setting up for manual database queries

### `make db-stop` 
**When to use:**
- End of development session
- Freeing up system resources
- Before system updates/restarts

### `make db-clean`
**When to use:**
- Database corruption or weird state
- Testing fresh database setup
- Clearing test data completely
- After changing database schema

## Code Quality Utilities

### `make lint`
**When to use:**
- Quick code style check without fixes
- CI/CD debugging (checking what would fail)
- Code review preparation

### `make format`
**When to use:**
- You want formatting only (no linting fixes)
- Working with strict linting rules you don't want auto-fixed

### `make fix`
**When to use:**
- Before every commit
- After writing new code
- When CI/CD fails on style issues
- Daily cleanup of code style

### `make clean`
**When to use:**
- Weird Python import issues
- After test failures with cache corruption
- Before fresh test runs
- Disk space cleanup

## Development Utilities

### `make test-essential`
**When to use:**
- Quick smoke test without database overhead
- Testing core logic changes
- When database is down but you want to test

### `make test-pipeline`
**When to use:**
- Testing end-to-end flow with fresh data
- After database schema changes
- Verifying dbt model changes work correctly

### `make dbt-run`
**When to use:**
- After changing dbt models only
- Re-processing existing articles with new logic
- Testing dbt transformations in isolation

### `make dbt-debug`
**When to use:**
- Database connection issues
- After changing database credentials
- dbt setup troubleshooting

### `make version-check`
**When to use:**
- Debugging environment inconsistencies
- Verifying local/Docker version alignment
- Troubleshooting dependency issues

## Docker Utilities

### `make docker-build`
**When to use:**
- After changing Dockerfile or requirements
- Before deployment
- Testing containerized environment

### `make docker-pipeline`
**When to use:**
- Testing production-like environment
- CI/CD debugging
- Deployment verification

## Useful Command Combinations

### Daily Development Flow
```bash
make db-start && make fix && make test
```
*Start database, fix code style, run all tests*

### After Major Code Changes
```bash
make fix && make pipeline && make test
```
*Fix style, run full pipeline, verify with tests*

### Fresh Start
```bash
make db-clean && make db-start && make pipeline
```
*Clean database, start fresh, run full pipeline*

### Pre-Commit Workflow
```bash
make fix && make test-essential && make test-pipeline
```
*Fix style, quick test, full integration test*

### Debugging Pipeline Issues
```bash
make db-clean && make db-start && make run && make dbt-debug && make dbt-run
```
*Fresh database, scrape articles, check dbt connection, run transformations*

### Production Verification
```bash
make docker-build && make docker-pipeline
```
*Build containers, test full containerized pipeline*

### Post-Schema Changes
```bash
make db-clean && make db-start && make test && make pipeline
```
*Fresh database, test with new schema, run full pipeline*

## Common Workflow Patterns

### 1. Starting Development Session
```bash
make db-start
make fix
make test-essential
```

### 2. Before Committing Changes
```bash
make fix
make test
```

### 3. Testing New Feature
```bash
make db-clean
make db-start
make pipeline
make test
```

### 4. Debugging Failing Tests
```bash
make clean
make db-clean
make db-start
make test-essential
make test-pipeline
```

### 5. Preparing for Deployment
```bash
make fix
make test
make docker-build
make docker-pipeline
```

The most commonly used combinations are the daily development flow and pre-commit workflow patterns.