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
from utils.structured_logger import get_structured_logger

logger = get_structured_logger(__name__)


class MigrationRunner:
    def __init__(self):
        self.migrations_dir = Path(__file__).parent
        # Initialize database connection first
        if not initialize_database():
            logger.error("Failed to initialize database connection")
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
            logger.info("Migration tracking table ready")
    
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
            logger.info(f"DRY RUN: Would execute migration {migration_name}")
            logger.info(f"File: {file_path}")
            logger.info(f"Content preview: {content[:200]}...")
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
                
            logger.info(
                f"Migration {migration_name} applied successfully", 
                extra_data={"migration": migration_name, "checksum": checksum}
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Migration {migration_name} failed: {str(e)}", 
                extra_data={"migration": migration_name, "error": str(e)},
                exc_info=True
            )
            return False
    
    def run_migrations(self, target: str = None, dry_run: bool = False) -> None:
        """Run all pending migrations up to target."""
        # Database already initialized in __init__
        
        migrations = self.get_migration_files()
        applied = self.get_applied_migrations()
        
        if not migrations:
            logger.info("No migration files found")
            return
        
        pending = []
        for number, file_path in migrations:
            migration_name = file_path.stem  # filename without extension
            
            if target and int(number) > int(target):
                break
                
            if migration_name not in applied:
                pending.append((migration_name, file_path))
        
        if not pending:
            logger.info("No pending migrations")
            return
        
        logger.info(f"Found {len(pending)} pending migrations")
        
        for migration_name, file_path in pending:
            print(f"\n┌─ Running Migration: {migration_name}")
            print(f"└─ File: {file_path.name}")
            
            if self.run_migration(migration_name, file_path, dry_run):
                print(f"   ✓ Success")
            else:
                print(f"   ✗ Failed")
                if not dry_run:
                    sys.exit(1)
        
        if dry_run:
            print(f"\n🔍 DRY RUN COMPLETE - {len(pending)} migrations would be applied")
        else:
            print(f"\n✅ MIGRATION COMPLETE - {len(pending)} migrations applied")


def main():
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--target", help="Run migrations up to this number (e.g., 003)")
    
    args = parser.parse_args()
    
    runner = MigrationRunner()
    runner.run_migrations(target=args.target, dry_run=args.dry_run)


if __name__ == "__main__":
    main()