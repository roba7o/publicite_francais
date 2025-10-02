"""
Database Migration Runner - Clean SQL Execution.

Simple migration runner that executes SQL files against the configured database.
No environment switching or schema logic - just runs migrations against the current database.

Usage:
    from database.migration_runner import MigrationRunner

    runner = MigrationRunner()
    runner.run_migration('001')
    runner.run_all_migrations()
"""

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from config.environment import DATABASE_CONFIG
from utils.structured_logger import get_logger

logger = get_logger(__name__)


class MigrationRunner:
    """Executes clean SQL migrations against the configured database."""

    def __init__(self, migration_dir: Path | None = None):
        """Initialize migration runner.

        Args:
            migration_dir: Path to migrations directory. Defaults to project migrations.
        """
        if migration_dir is None:
            # Default to project migrations directory
            project_root = Path(__file__).parent.parent.parent
            migration_dir = project_root / "database" / "migrations"

        self.migration_dir = Path(migration_dir)
        self.logger = logger

    def get_session(self) -> sessionmaker:
        """Create database session for the configured database.

        Returns:
            SQLAlchemy session factory for the database
        """
        db_config = DATABASE_CONFIG
        database_url = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

        engine = create_engine(
            database_url,
            echo=False,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
        )

        return sessionmaker(bind=engine)

    def load_migration_sql(self, migration_name: str) -> str:
        """Load SQL from migration file.

        Args:
            migration_name: Name like '001' or '001_add_fields'

        Returns:
            Raw SQL string

        Raises:
            FileNotFoundError: If migration file doesn't exist
        """
        # Handle both '001' and '001_filename' formats
        migration_files = list(self.migration_dir.glob(f"{migration_name}*.sql"))

        if not migration_files:
            raise FileNotFoundError(f"Migration {migration_name} not found in {self.migration_dir}")

        if len(migration_files) > 1:
            # If multiple matches, prefer exact match
            exact_match = self.migration_dir / f"{migration_name}.sql"
            if exact_match.exists():
                migration_file = exact_match
            else:
                migration_file = migration_files[0]
                self.logger.warning(f"Multiple migrations match {migration_name}, using {migration_file.name}")
        else:
            migration_file = migration_files[0]

        return migration_file.read_text(encoding='utf-8')

    def run_migration(self, migration_name: str) -> bool:
        """Run a single migration against the configured database.

        Args:
            migration_name: Migration identifier like '001'

        Returns:
            True if migration succeeded, False otherwise
        """
        try:
            # Get database session
            SessionClass = self.get_session()

            # Load migration SQL
            migration_sql = self.load_migration_sql(migration_name)

            # Execute migration
            with SessionClass() as session:
                # Execute the migration SQL directly
                session.execute(text(migration_sql))
                session.commit()

                self.logger.info(f"Migration {migration_name} applied successfully")
                return True

        except Exception as e:
            self.logger.error(f"Migration {migration_name} failed: {str(e)}")
            return False

    def run_all_migrations(self) -> dict[str, bool]:
        """Run all migrations against the database.

        Returns:
            Dict mapping migration -> success status
        """
        # Find all migration files
        migration_files = sorted(self.migration_dir.glob("*.sql"))
        migration_names = [f.stem.split('_')[0] for f in migration_files]

        results = {}

        self.logger.info("Running all migrations")

        for migration_name in migration_names:
            success = self.run_migration(migration_name)
            results[migration_name] = success

            if not success:
                self.logger.error(f"Migration {migration_name} failed, stopping")
                break

        return results

    def check_database_structure(self) -> dict[str, bool]:
        """Check database structure for expected tables.

        Returns:
            Dict mapping table names to existence status
        """
        SessionClass = self.get_session()

        with SessionClass() as session:
            # Check for expected tables in public schema
            result = session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('raw_articles', 'word_events', 'stop_words')
                ORDER BY table_name
            """)).fetchall()

            found_tables = {row[0] for row in result}
            expected_tables = {'raw_articles', 'word_events', 'stop_words'}

            return {
                table: table in found_tables
                for table in expected_tables
            }


def run_migration_cli():
    """CLI entry point for running migrations."""
    import argparse

    parser = argparse.ArgumentParser(description='Run database migrations')
    parser.add_argument('migration', help='Migration number (e.g., 001)')
    parser.add_argument('--all', action='store_true', help='Run all migrations')

    args = parser.parse_args()

    runner = MigrationRunner()

    if args.all:
        results = runner.run_all_migrations()
        for migration, success in results.items():
            status = "✓" if success else "✗"
            print(f"{status} {migration}")
    else:
        success = runner.run_migration(args.migration)
        status = "✓" if success else "✗"
        print(f"{status} Migration {args.migration}")


if __name__ == '__main__':
    run_migration_cli()
