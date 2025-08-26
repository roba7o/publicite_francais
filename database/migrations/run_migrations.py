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
import re

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from database.database import get_session, initialize_database
from sqlalchemy import text
from utils.structured_logger import Logger

logger = Logger(__name__)


class MigrationRunner:
    def __init__(self):
        self.migrations_dir = Path(__file__).parent
        
        # Initialize database connection with silent SQLAlchemy
        if not initialize_database(echo=False):
            print("\033[31m✗ Failed to initialize database connection\033[0m")
            sys.exit(1)
        self.ensure_migration_table()
    
    def ensure_migration_table(self) -> None:
        """Create migrations tracking table if it doesn't exist (Django-style)."""
        with get_session() as session:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS migration_history (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) NOT NULL UNIQUE,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes if they don't exist
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_migration_history_name ON migration_history(migration_name)
            """))
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_migration_history_applied ON migration_history(applied_at)
            """))
    
    def get_migration_files(self) -> list[tuple[str, Path]]:
        """Get all migration files sorted by number."""
        migrations = []
        
        for file_path in self.migrations_dir.glob("*.sql"):
            # Skip rollback files - they're not regular migrations
            if "_rollback_" in file_path.name:
                continue
                
            if match := re.match(r"^(\d{3})_.*\.sql$", file_path.name):
                number = match.group(1)
                migrations.append((number, file_path))
        
        return sorted(migrations, key=lambda x: int(x[0]))
    
    def get_applied_migrations(self) -> set:
        """Get list of already applied migrations (Django-style)."""
        with get_session() as session:
            result = session.execute(text("""
                SELECT migration_name FROM migration_history
                ORDER BY migration_name
            """))
            return {row[0] for row in result}
    
    def run_migration(self, migration_name: str, file_path: Path, dry_run: bool = False) -> bool:
        """Run a single migration (Django-style)."""
        content = file_path.read_text()
        
        if dry_run:
            # Dry run - just return success, parent handles output
            return True
        
        try:
            with get_session() as session:
                # Run the migration
                session.execute(text(content))
                
                # Record that it was applied (Django-style)
                session.execute(text("""
                    INSERT INTO migration_history (migration_name)
                    VALUES (:name)
                """), {"name": migration_name})
            
            # Migration succeeded - no logging needed, parent will handle output
            return True
            
        except Exception as e:
            # Only show error for failed migrations
            print(f"\n\033[31m✗ Migration failed: {str(e)}\033[0m")
            return False
    
    def run_rollback(self, target: str, dry_run: bool = False) -> None:
        """Roll back migrations to target version."""
        migrations = self.get_migration_files()
        applied = self.get_applied_migrations()
        
        # Find target migration
        target_found = False
        rollback_migrations = []
        
        # Get migrations to roll back (in reverse order)
        for number, file_path in reversed(migrations):
            migration_name = file_path.stem
            if migration_name in applied:
                if number == target:
                    target_found = True
                    break
                rollback_migrations.append((migration_name, file_path, number))
        
        if not target_found:
            print(f"\033[31m✗ Target migration {target} not found or not applied\033[0m")
            return
        
        if not rollback_migrations:
            print(f"\033[32m✓ Already at target migration {target}\033[0m")
            return
        
        # Look for rollback files
        rollback_files = []
        for migration_name, file_path, number in rollback_migrations:
            # Extract the part after the number prefix (e.g., "003_example_add_tags" -> "example_add_tags")
            migration_suffix = file_path.stem[len(number) + 1:]  # Skip "003_"
            rollback_file = file_path.parent / f"{number}_rollback_{migration_suffix}.sql"
            if rollback_file.exists():
                rollback_files.append((migration_name, rollback_file))
            else:
                print(f"\033[31m✗ Rollback file missing: {rollback_file.name}\033[0m")
                print(f"\033[33m  Create this file to enable rollback of {migration_name}\033[0m")
                return
        
        # Execute rollbacks
        action = "DRY RUN ROLLBACK" if dry_run else "ROLLING BACK"
        print(f"\033[31m◆ {action}: {len(rollback_files)} migration{'s' if len(rollback_files) > 1 else ''}\033[0m")
        
        for migration_name, rollback_file in rollback_files:
            if dry_run:
                print(f"\033[36m  • Would rollback: {migration_name}\033[0m")
            else:
                print(f"\033[36m  • Rolling back: {migration_name}\033[0m", end="", flush=True)
                
                if self.run_rollback_file(migration_name, rollback_file):
                    print(" \033[32m✓\033[0m")
                else:
                    print(" \033[31m✗\033[0m")
                    return
        
        if dry_run:
            print(f"\n\033[31m🔍 DRY RUN COMPLETE - {len(rollback_files)} migrations would be rolled back\033[0m")
        else:
            print(f"\n\033[32m✅ ROLLBACK COMPLETE - rolled back to migration {target}\033[0m")
    
    def run_rollback_file(self, migration_name: str, rollback_file: Path) -> bool:
        """Execute a rollback file."""
        try:
            content = rollback_file.read_text()
            with get_session() as session:
                # Run the rollback SQL
                session.execute(text(content))
                
                # Remove from migration tracking (Django-style)
                session.execute(text("""
                    DELETE FROM migration_history
                    WHERE migration_name = :name
                """), {"name": migration_name})
            
            return True
            
        except Exception as e:
            print(f"\n\033[31m✗ Rollback failed: {str(e)}\033[0m")
            return False

    def run_migrations(self, target: str = None, dry_run: bool = False, rollback: str = None) -> None:
        """Run all pending migrations up to target or rollback to target."""
        # Handle rollback mode
        if rollback:
            self.run_rollback(rollback, dry_run)
            return
        
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
    parser.add_argument("--rollback", help="Roll back to this migration number (e.g., 001)")
    
    args = parser.parse_args()
    
    runner = MigrationRunner()
    runner.run_migrations(target=args.target, dry_run=args.dry_run, rollback=args.rollback)


if __name__ == "__main__":
    main()
