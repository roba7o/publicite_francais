#!/bin/bash
# Drop all tables from database (DESTRUCTIVE!)
set -e

# Usage check
if [ -z "$CONTAINER_NAME" ] || [ -z "$PGDATABASE" ] || [ -z "$PGUSER" ]; then
    echo "Error: Missing required environment variables (CONTAINER_NAME, PGDATABASE, PGUSER)"
    exit 1
fi

echo "Dropping all tables from $PGDATABASE in container $CONTAINER_NAME"

# Drop tables with CASCADE
docker exec "$CONTAINER_NAME" psql -U "$PGUSER" -d "$PGDATABASE" -c "DROP TABLE IF EXISTS word_facts CASCADE"
docker exec "$CONTAINER_NAME" psql -U "$PGUSER" -d "$PGDATABASE" -c "DROP TABLE IF EXISTS dim_articles CASCADE"

echo "✓ Tables dropped successfully"
