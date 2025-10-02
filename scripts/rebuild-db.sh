#!/bin/bash
set -e

echo -e "\033[34m◆ Rebuilding database from scratch...\033[0m"

# Ensure database is running
make db-start > /dev/null 2>&1

# Drop all tables and reset migration history
echo -e "\033[33m◆ Dropping all tables...\033[0m"
PYTHONPATH=src ./venv/bin/python -c "
from database.database import get_session, initialize_database
from sqlalchemy import text

initialize_database(echo=False)
with get_session() as session:
    # Drop all tables and migration history
    session.execute(text('DROP TABLE IF EXISTS word_events CASCADE'))
    session.execute(text('DROP TABLE IF EXISTS raw_articles CASCADE'))
    session.execute(text('DROP TABLE IF EXISTS stop_words CASCADE'))
    session.execute(text('DROP TABLE IF EXISTS migration_history CASCADE'))
    session.commit()
"

# Run migrations
echo -e "\033[33m◆ Applying all migrations...\033[0m"
make db-migrate

echo -e "\033[32m✓ Database rebuild complete!\033[0m"