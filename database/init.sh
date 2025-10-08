#!/bin/bash
# Database initialization script
# Applies schema to database via Docker container

set -e

# Usage check
if [ -z "$CONTAINER_NAME" ] || [ -z "$PGDATABASE" ] || [ -z "$PGUSER" ]; then
    echo "Error: Missing required environment variables (CONTAINER_NAME, PGDATABASE, PGUSER)"
    exit 1
fi

echo "Initializing database: $PGDATABASE in container $CONTAINER_NAME"

# Copy schema to container and apply it
docker cp "$(dirname "$0")/schema.sql" "$CONTAINER_NAME:/tmp/schema.sql"
docker exec -e PGPASSWORD="${PGPASSWORD:-}" "$CONTAINER_NAME" \
    psql -U "$PGUSER" -d "$PGDATABASE" -f /tmp/schema.sql

echo "✓ Database initialized successfully"
