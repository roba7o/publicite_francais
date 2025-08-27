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
import sqlalchemy
import sqlalchemy.exc
import sqlparse

from database.database import get_session, initialize_database
from sqlalchemy import text
from utils.structured_logger import Logger


logger = Logger(__name__)


class MigrationRunner:
    def __init__(self):
        self.migrations_dir = Path(__file__).parent
        
        # Initialize database connection with silent SQLAlchemy
        if not initialize_database(echo=False):
            logger.error("Failed to initialize database connection")
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
    
    def run_migration(
        self,
        migration_name: str,
        file_path: Path,
        dry_run: bool = False
        ) -> bool:
        """Run a single migration atomically."""
        content = file_path.read_text()
        
        if dry_run:
            # Dry run - just return success, parent handles output
            return True
        
        try:
            with get_session() as session:  # Already atomic!
                # Split content into individual statements using sqlparse
                statements = [s.strip() for s in sqlparse.split(content) if s.strip()]
                
                # Execute each statement in the same transaction
                for statement in statements:
                    session.execute(text(statement))
                
                # Record that it was applied
                session.execute(text("""
                    INSERT INTO migration_history (migration_name)
                    VALUES (:name)
                """), {"name": migration_name})
            
            # All statements auto-commit together
            return True
        
        except sqlalchemy.exc.SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error during migration {migration_name}: {str(e)}")
            return False
            
        except Exception as e:
            # All statements auto-rollback together
            logger.error(f"Unexpected error during migration {migration_name}: {str(e)}")
            return False
    

    def run_migrations(
            self,
            target: str | None = None,
            dry_run: bool = False
        ) -> None:
        """Run all pending migrations up to target."""
        
        # Database already initialized in __init__
        
        migrations = self.get_migration_files()
        applied = self.get_applied_migrations()
        
        if not migrations:
            logger.error("\033[33m⚠ No migration files found\033[0m")
            return
        
        # Validate migration numbering
        expected = [str(i).zfill(3) for i in range(0, len(migrations))]
        found = [num for num, _ in migrations]
        if expected != found:
            logger.error("\033[31m✗ Migration numbering issue:\033[0m")
            logger.error(f"  Expected: {expected}")
            logger.error(f"  Found:    {found}")
            logger.error("  \033[31mFix numbering before running migrations.\033[0m")
            sys.exit(1)
        
        pending = []
        for number, file_path in migrations:
            migration_name = file_path.stem  # filename without extension
            
            # if target is set (exists in cli arg), skip migrations beyond it
            if target and int(number) > int(target):
                break
                
            if migration_name not in applied:
                pending.append((migration_name, file_path))
        
        if not pending:
            logger.info("\033[32m✓ Database is up to date - no pending migrations\033[0m")
            return
        
        # Clean, focused output
        action = "DRY RUN" if dry_run else "APPLYING"
        logger.info(f"\033[34m◆ {action}: {len(pending)} pending migration{'s' if len(pending) > 1 else ''}\033[0m")
        
        for migration_name, file_path in pending:
            if dry_run:
                logger.info(f"\033[36m  • Would run: {migration_name}\033[0m")
            else:
                print(f"\033[36m  • Running: {migration_name}\033[0m", end="", flush=True)
                
                if self.run_migration(migration_name, file_path, dry_run):
                    print(" \033[32m✓\033[0m")
                else:
                    print(" \033[31m✗\033[0m")
                    sys.exit(1)
        
        if dry_run:
            logger.info(f"\n\033[33m🔍 DRY RUN COMPLETE - {len(pending)} migrations would be applied\033[0m")
        else:
            logger.info(f"\n\033[32m✅ SUCCESS - {len(pending)} migration{'s' if len(pending) > 1 else ''} applied\033[0m")


def main():
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--target", help="Run migrations up to this number (e.g., 003)")
    
    args = parser.parse_args()
    
    runner = MigrationRunner()
    runner.run_migrations(target=args.target, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
