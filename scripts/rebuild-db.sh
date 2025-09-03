#!/bin/bash
set -e

echo -e "\033[34m◆ Rebuilding database from scratch...\033[0m"

# Ensure database is running
make db-start > /dev/null 2>&1

# Drop and recreate schemas, and reset migration history
echo -e "\033[33m◆ Dropping and recreating schemas...\033[0m"
PYTHONPATH=src python3 -c "
from database.database import get_session, initialize_database
from sqlalchemy import text

initialize_database(echo=False)
with get_session() as session:
    # Drop schemas and migration history
    session.execute(text('DROP SCHEMA IF EXISTS news_data_dev CASCADE'))
    session.execute(text('DROP SCHEMA IF EXISTS news_data_test CASCADE'))
    session.execute(text('DROP TABLE IF EXISTS migration_history CASCADE'))
    
    # Recreate schemas
    session.execute(text('CREATE SCHEMA news_data_dev'))
    session.execute(text('CREATE SCHEMA news_data_test'))
    session.commit()
"

# Run migrations
echo -e "\033[33m◆ Applying all migrations...\033[0m"
make db-migrate

echo -e "\033[32m✓ Database rebuild complete!\033[0m"