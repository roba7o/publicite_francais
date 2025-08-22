#!/usr/bin/env python3
"""
Clear test data for fresh test data loading.

This script is used by `make run-test-data` to clear existing data from the test table.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.database import get_session, initialize_database
from sqlalchemy import text
from config.environment import env_config


def main():
    """Clear test data from existing table."""
    try:
        # Initialize database connection
        if not initialize_database():
            print("✗ Database initialization failed")
            return 1
        
        # Get test schema name
        schema = env_config.get_news_data_schema()
        print(f"Clearing data from {schema}.raw_articles")
        
        # Clear data from existing table
        with get_session() as session:
            result = session.execute(text(f"DELETE FROM {schema}.raw_articles"))
            count = result.rowcount
        
        print(f"✓ Cleared {count} records from {schema}.raw_articles")
        return 0
        
    except Exception as e:
        print(f"✗ Error clearing data: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())