#!/bin/bash
# Database initialization script
# Applies schema to database specified by connection parameters

set -e

# Usage check
if [ -z "$PGHOST" ] || [ -z "$PGDATABASE" ] || [ -z "$PGUSER" ]; then
    echo "Error: Missing required environment variables (PGHOST, PGDATABASE, PGUSER)"
    exit 1
fi

echo "Initializing database: $PGDATABASE on $PGHOST:${PGPORT:-5432}"

# Apply schema
PGPASSWORD="${PGPASSWORD:-}" psql -h "$PGHOST" -p "${PGPORT:-5432}" -U "$PGUSER" -d "$PGDATABASE" -f "$(dirname "$0")/schema.sql"

echo "✓ Database initialized successfully"
