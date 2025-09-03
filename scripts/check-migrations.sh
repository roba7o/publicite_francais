#!/bin/bash
set -e

echo -e "\033[34m◆ Checking pending migrations (dry run)...\033[0m"

# Ensure database is running
make db-start > /dev/null 2>&1

# Check for pending migrations
PYTHONPATH=src python3 -c "
import sys
sys.path.insert(0, 'database/migrations')
from run_migrations import get_pending_migrations

pending = get_pending_migrations()
if pending:
    print('Pending migrations:')
    for migration in pending:
        print(f'  - {migration}')
    print(f'\nTotal: {len(pending)} migration(s) pending')
else:
    print('No pending migrations')
"