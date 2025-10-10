#!/bin/bash
# Apply database schema from schema.sql file
set -e

# Usage check
if [ -z "$CONTAINER_NAME" ] || [ -z "$PGDATABASE" ] || [ -z "$PGUSER" ]; then
    echo "Error: Missing required environment variables (CONTAINER_NAME, PGDATABASE, PGUSER)"
    exit 1
fi

echo "Applying schema to $PGDATABASE in container $CONTAINER_NAME"

# Copy schema file to container and execute
docker cp database/schema.sql "$CONTAINER_NAME:/tmp/schema.sql"
docker exec "$CONTAINER_NAME" psql -U "$PGUSER" -d "$PGDATABASE" -f /tmp/schema.sql

echo "✓ Schema applied successfully"
