"""Clean migration runner for sequential SQL migrations."""

import re
import sys
from pathlib import Path

import sqlparse
from sqlalchemy import text

from database.database import get_session, initialize_database


class MigrationRunner:
    """Handles sequential SQL migration execution and tracking."""

    def __init__(self):
        self.migrations_dir = Path(__file__).parent

    def _ensure_migration_table(self):
        """Create migration history table if it doesn't exist."""
        with get_session() as session:
            session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS migration_history (
                    migration_name VARCHAR(255) NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            )

    def _get_migration_files(self) -> list[Path]:
        """Get all migration files in numbered order."""
        migrations = []
        for file_path in self.migrations_dir.glob("*.sql"):
            if re.match(r"^(\d{3})_.*\.sql$", file_path.name):
                migrations.append(file_path)
        return sorted(migrations)

    def _get_applied_migrations(self) -> set:
        """Get set of already applied migration names."""
        with get_session() as session:
            result = session.execute(
                text("SELECT migration_name FROM migration_history")
            )
            return {row[0] for row in result}

    def _apply_migration(self, migration_file: Path):
        """
        Apply a single migration file and record it as applied.
        1. Execute all SQL statements in the file.
        2. Insert a record into migration_history.
        """
        name = migration_file.stem
        content = migration_file.read_text()

        with get_session() as session:
            # Execute all SQL statements in the file
            statements = [s.strip() for s in sqlparse.split(content) if s.strip()]
            for statement in statements:
                session.execute(text(statement))

            # Record as applied into migration history
            session.execute(
                text("INSERT INTO migration_history (migration_name) VALUES (:name)"),
                {"name": name},
            )

    def _get_pending_migration_files(self) -> list[Path]:
        """Get list of pending migration files."""
        migration_files = self._get_migration_files()
        applied = self._get_applied_migrations()
        return [f for f in migration_files if f.stem not in applied]

    def get_pending_migrations(self) -> list[str]:
        """Get list of pending migration names."""
        if not initialize_database(echo=False):
            return []

        self._ensure_migration_table()
        pending_files = self._get_pending_migration_files()
        return [f.stem for f in pending_files]

    def run_all_migrations(self):
        """Apply all pending migrations in sequence."""
        if not initialize_database(echo=False):
            print("Failed to connect to database")
            sys.exit(1)

        self._ensure_migration_table()
        pending = self._get_pending_migration_files()

        if not pending:
            print("No pending migrations")
            return

        for migration_file in pending:
            name = migration_file.stem
            print(f"Applying {name}...")

            try:
                self._apply_migration(migration_file)
                print(f"✓ {name}")
            except Exception as e:
                print(f"✗ {name} failed: {e}")
                sys.exit(1)

        print(f"Applied {len(pending)} migrations successfully")


# Module-level instance for clean API without wrapper functions
_runner = MigrationRunner()  # only init is ran
"""
these create references to the instance methods:
    e.g from database.migrations.run_migrations import run_all_migrations
    e.g from database.migrations.run_migrations import get_pending_migrations

    pending = get_pending_migrations() -> when it actually runs, it calls the instance method
    run_all_migrations() -> when it actually runs, it calls the instance method
"""
run_all_migrations = _runner.run_all_migrations
get_pending_migrations = _runner.get_pending_migrations


if __name__ == "__main__":
    run_all_migrations()
