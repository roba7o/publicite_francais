#!/bin/bash
set -e

echo -e "\033[34m◆ Rebuilding database from scratch...\033[0m"

# Ensure database is running
make db-start > /dev/null 2>&1

# Drop and recreate clean public schema
echo -e "\033[33m◆ Dropping and recreating public schema...\033[0m"
PYTHONPATH=src python3 -c "
from database.database import get_session, initialize_database
from sqlalchemy import text

initialize_database(echo=False)
with get_session() as session:
    # Drop all tables in public schema
    session.execute(text('DROP TABLE IF EXISTS word_facts CASCADE'))
    session.execute(text('DROP TABLE IF EXISTS raw_articles CASCADE'))
    session.commit()
"

# Apply schema
echo -e "\033[33m◆ Applying schema...\033[0m"
PYTHONPATH=src python3 -c "
from database.database import get_session
from sqlalchemy import text
from pathlib import Path

schema_sql = Path('database/schema.sql').read_text()
with get_session() as session:
    session.execute(text(schema_sql))
    session.commit()
"

echo -e "\033[32m✓ Database rebuild complete!\033[0m"