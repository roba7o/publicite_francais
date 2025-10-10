#!/bin/bash
# Rebuild database from scratch (DROP + CREATE)
set -e

# Usage check
if [ -z "$CONTAINER_NAME" ] || [ -z "$PGDATABASE" ] || [ -z "$PGUSER" ]; then
    echo "Error: Missing required environment variables (CONTAINER_NAME, PGDATABASE, PGUSER)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Rebuilding database: $PGDATABASE"

# Drop tables
echo "  ◆ Dropping tables..."
"$SCRIPT_DIR/drop_tables.sh"

# Apply schema
echo "  ◆ Applying schema..."
"$SCRIPT_DIR/apply_schema.sh"

echo "✓ Database rebuild complete!"
