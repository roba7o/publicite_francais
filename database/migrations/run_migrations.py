#!/usr/bin/env python3
"""
Database Migration Runner for French News Scraper

This script handles database schema migrations safely and tracks which
migrations have been applied to prevent double-running.

Usage:
    python run_migrations.py [--dry-run] [--target=003]
    
Examples:
    python run_migrations.py                    # Run all pending migrations
    python run_migrations.py --dry-run          # Show what would run
    python run_migrations.py --target=002       # Run up to migration 002
"""

import sys
import argparse
from pathlib import Path
from typing import List, Tuple
import re

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from database.database import get_session, initialize_database
from sqlalchemy import text
from utils.structured_logger import MigrationLogger

logger = MigrationLogger(__name__)


class MigrationRunner:
    def __init__(self):
        self.migrations_dir = Path(__file__).parent
        # Ensure our logger's SQLAlchemy filter is applied BEFORE database initialization
        logger._configure()  # Re-run configuration to ensure filters are in place
        
        # Initialize database connection 
        if not initialize_database():
            print("\033[31m✗ Failed to initialize database connection\033[0m")
            sys.exit(1)
        self.ensure_migration_table()
    
    def ensure_migration_table(self) -> None:
        """Create migrations tracking table if it doesn't exist."""
        with get_session() as session:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS public.schema_migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    checksum VARCHAR(64)
                )
            """))
    
    def get_migration_files(self) -> List[Tuple[str, Path]]:
        """Get all migration files sorted by number."""
        migrations = []
        
        for file_path in self.migrations_dir.glob("*.sql"):
            if match := re.match(r"^(\d+)_.*\.sql$", file_path.name):
                number = match.group(1)
                migrations.append((number, file_path))
        
        return sorted(migrations, key=lambda x: int(x[0]))
    
    def get_applied_migrations(self) -> set:
        """Get list of already applied migrations."""
        with get_session() as session:
            result = session.execute(text("""
                SELECT migration_name FROM public.schema_migrations 
                ORDER BY migration_name
            """))
            return {row[0] for row in result}
    
    def calculate_checksum(self, content: str) -> str:
        """Calculate simple checksum for migration content."""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def run_migration(self, migration_name: str, file_path: Path, dry_run: bool = False) -> bool:
        """Run a single migration."""
        content = file_path.read_text()
        checksum = self.calculate_checksum(content)
        
        if dry_run:
            # Dry run - just return success, parent handles output
            return True
        
        try:
            with get_session() as session:
                # Run the migration
                session.execute(text(content))
                
                # Record that it was applied
                session.execute(text("""
                    INSERT INTO public.schema_migrations (migration_name, checksum)
                    VALUES (:name, :checksum)
                """), {"name": migration_name, "checksum": checksum})
            
            # Migration succeeded - no logging needed, parent will handle output
            return True
            
        except Exception as e:
            # Only show error for failed migrations
            print(f"\n\033[31m✗ Migration failed: {str(e)}\033[0m")
            return False
    
    def run_migrations(self, target: str = None, dry_run: bool = False) -> None:
        """Run all pending migrations up to target."""
        # Database already initialized in __init__
        
        migrations = self.get_migration_files()
        applied = self.get_applied_migrations()
        
        if not migrations:
            print("\033[33m⚠ No migration files found\033[0m")
            return
        
        pending = []
        for number, file_path in migrations:
            migration_name = file_path.stem  # filename without extension
            
            if target and int(number) > int(target):
                break
                
            if migration_name not in applied:
                pending.append((migration_name, file_path))
        
        if not pending:
            print("\033[32m✓ Database is up to date - no pending migrations\033[0m")
            return
        
        # Clean, focused output
        action = "DRY RUN" if dry_run else "APPLYING"
        print(f"\033[34m◆ {action}: {len(pending)} pending migration{'s' if len(pending) > 1 else ''}\033[0m")
        
        for migration_name, file_path in pending:
            if dry_run:
                print(f"\033[36m  • Would run: {migration_name}\033[0m")
            else:
                print(f"\033[36m  • Running: {migration_name}\033[0m", end="", flush=True)
                
                if self.run_migration(migration_name, file_path, dry_run):
                    print(" \033[32m✓\033[0m")
                else:
                    print(" \033[31m✗\033[0m")
                    sys.exit(1)
        
        if dry_run:
            print(f"\n\033[33m🔍 DRY RUN COMPLETE - {len(pending)} migrations would be applied\033[0m")
        else:
            print(f"\n\033[32m✅ SUCCESS - {len(pending)} migration{'s' if len(pending) > 1 else ''} applied\033[0m")


def main():
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--target", help="Run migrations up to this number (e.g., 003)")
    
    args = parser.parse_args()
    
    runner = MigrationRunner()
    runner.run_migrations(target=args.target, dry_run=args.dry_run)


if __name__ == "__main__":
    main()