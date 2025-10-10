#!/bin/bash
# Clear all data from tables (TRUNCATE) without dropping schema
set -e

# Usage check
if [ -z "$CONTAINER_NAME" ] || [ -z "$PGDATABASE" ] || [ -z "$PGUSER" ]; then
    echo "Error: Missing required environment variables (CONTAINER_NAME, PGDATABASE, PGUSER)"
    exit 1
fi

# Truncate tables with CASCADE
docker exec "$CONTAINER_NAME" psql -U "$PGUSER" -d "$PGDATABASE" -c "TRUNCATE TABLE dim_articles CASCADE" > /dev/null 2>&1

exit 0
