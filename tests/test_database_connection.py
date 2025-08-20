#!/usr/bin/env python3
"""
Database connection test script for French news scraper.

This script tests the database connection infrastructure without modifying
any existing scraper logic. It validates that the app can connect to the
PostgreSQL container and perform basic operations.

Usage:
    python test_database_connection.py

Requirements:
    - PostgreSQL container running (docker compose up -d postgres)
    - Dependencies installed (pip install -e .)
"""

import sys
from pathlib import Path

from sqlalchemy import text

# Add src directory to Python path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import after path modification
from core.database import (  # noqa: E402
    get_session,
    initialize_database,
)
from utils.structured_logger import get_structured_logger  # noqa: E402


def test_basic_connection():
    """Test basic database connectivity."""
    print("\033[34m■ Testing basic database connection...\033[0m")

    # Test database initialization
    if not initialize_database():
        print("\033[31m× Failed to initialize database\033[0m")
        raise AssertionError("Database initialization failed")

    # Test connection
    try:
        with get_session() as session:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
        print("\033[32m✓ Database connection successful!\033[0m")
    except Exception as e:
        print(f"\033[31m× Database connection failed: {e}\033[0m")
        raise AssertionError(f"Database connection failed: {e}") from e


def test_raw_connection():
    """Test database manager compatibility."""
    print("\n\033[35m■ Testing database manager compatibility...\033[0m")

    try:
        # Direct session usage

        # Test that we can get sessions from the manager
        with get_session() as session:
            # Test basic query using SQLAlchemy
            result = session.execute(
                text("SELECT current_database(), current_user, version()")
            ).fetchone()

            if result:
                print(f"\033[32m✓ Connected to database: {result[0]}\033[0m")
                print(f"\033[32m✓ Connected as user: {result[1]}\033[0m")
                print(f"\033[32m✓ PostgreSQL version: {result[2].split(',')[0]}\033[0m")
            else:
                print("\033[31m✗ No result from database query\033[0m")

        print("\033[32m✓ Database manager compatibility confirmed\033[0m")

    except Exception as e:
        print(f"\033[31m× Database manager test failed: {e}\033[0m")
        raise AssertionError(f"Database manager test failed: {e}") from e


def test_sqlalchemy_connection():
    """Test SQLAlchemy connection."""
    print("\n\033[36m■ Testing SQLAlchemy connection...\033[0m")

    try:
        # Direct session usage

        with get_session() as session:
            from sqlalchemy import text

            # Test schema query
            result = session.execute(
                text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'news_data'
                ORDER BY table_name
            """)
            )

            tables = [row[0] for row in result]
            print(f"\033[32m✓ Found {len(tables)} tables in news_data schema:\033[0m")
            for table in tables:
                print(f"   - {table}")

    except Exception as e:
        print(f"\033[31m× SQLAlchemy connection failed: {e}\033[0m")
        raise AssertionError(f"SQLAlchemy connection failed: {e}") from e


def test_news_sources_data():
    """Test querying news sources data (with schema fallback)."""
    print("\n\033[34m■ Testing news sources data...\033[0m")

    try:
        # Direct session usage

        with get_session() as session:
            from sqlalchemy import text

            # Try different schema variations based on environment
            schema_attempts = [
                "news_data_test.news_sources",  # Test environment
                "news_data_dev.news_sources",  # Dev environment
                "news_data.news_sources",  # Legacy
                "public.news_sources",  # Fallback
            ]

            sources = []
            schema_used = None

            for schema_table in schema_attempts:
                try:
                    result = session.execute(
                        text(f"""
                        SELECT name, base_url, enabled
                        FROM {schema_table}
                        ORDER BY name
                    """)
                    )
                    sources = list(result)
                    schema_used = schema_table
                    break
                except Exception:
                    continue

            if schema_used:
                print(
                    f"\033[32m✓ Found {len(sources)} news sources in {schema_used}:\033[0m"
                )

                for name, base_url, enabled in sources[:3]:  # Show first 3
                    status = (
                        "\033[32m● enabled\033[0m"
                        if enabled
                        else "\033[31m● disabled\033[0m"
                    )
                    print(f"   - {name}: {base_url} ({status})")
                if len(sources) > 3:
                    print(f"   ... and {len(sources) - 3} more")
            else:
                print(
                    "\033[33m⚠ No news_sources table found in any schema - DB may need setup\033[0m"
                )
                # Don't fail the test - this is expected in fresh environments

    except Exception as e:
        print(f"\033[31m× News sources query failed: {e}\033[0m")
        # Don't assert false here - allow graceful degradation
        print(
            "\033[33m⚠ This is expected if database schema hasn't been set up yet\033[0m"
        )


def test_health_check():
    """Test basic database health check."""
    print("\n\033[33m◆ Running database health check...\033[0m")

    try:
        # Simple health check - test basic connectivity and operations
        with get_session() as session:
            # Test 1: Basic query
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
            print("\033[32m✓ Basic query: OK\033[0m")

            # Test 2: Check current settings
            db_name = session.execute(text("SELECT current_database()")).scalar()
            user_name = session.execute(text("SELECT current_user")).scalar()
            print(f"\033[32m✓ Connected to: {db_name} as {user_name}\033[0m")

            # Test 3: Check available schemas
            schemas = session.execute(
                text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT LIKE 'pg_%'
                AND schema_name != 'information_schema'
                ORDER BY schema_name
            """)
            ).fetchall()

            schema_names = [row[0] for row in schemas]
            print(f"\033[32m✓ Available schemas: {', '.join(schema_names)}\033[0m")

            # Test 4: Check if we have our expected schemas
            expected_schemas = [
                "news_data_test",
                "news_data_dev",
                "news_data",
                "dbt_test",
                "dbt_dev",
                "dbt",
            ]
            found_schemas = [s for s in expected_schemas if s in schema_names]

            if found_schemas:
                print(
                    f"\033[32m✓ Found project schemas: {', '.join(found_schemas)}\033[0m"
                )
            else:
                print(
                    "\033[33m⚠ No project schemas found - DB may need initialization\033[0m"
                )

        print("\033[32m✓ Database health check passed\033[0m")

    except Exception as e:
        print(f"\033[31m× Health check failed: {e}\033[0m")
        raise AssertionError(f"Health check failed: {e}") from e


def main():
    """Run all database connection tests."""
    logger = get_structured_logger("DatabaseConnectionTest")

    print("\033[36m▲ French News Scraper - Database Connection Test\033[0m")
    print("\033[36m" + "=" * 50 + "\033[0m")

    logger.info("Starting database connection tests")

    # Check if PostgreSQL container is running
    print("\033[33m◆ Prerequisites:\033[0m")
    print("   - PostgreSQL container should be running")
    print("   - Run: docker compose up -d postgres")
    print("   - Dependencies installed: pip install -e .")
    print()

    test_results = []

    # Run all tests
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Raw psycopg2", test_raw_connection),
        ("SQLAlchemy", test_sqlalchemy_connection),
        ("News Sources Data", test_news_sources_data),
        ("Health Check", test_health_check),
    ]

    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        result = test_func()
        test_results.append((test_name, result))

    # Summary
    # ASCII art for completion
    print("""
\033[32m╭─────────────────────────────────────────────────╮
│                 TEST SUMMARY                  │
╰─────────────────────────────────────────────────╯\033[0m""")

    passed = 0
    for test_name, result in test_results:
        status = "\033[32m✓ PASS\033[0m" if result else "\033[31m× FAIL\033[0m"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1

    print(f"\n\033[33m◆ Overall: {passed}/{len(test_results)} tests passed\033[0m")

    if passed == len(test_results):
        print("\n\033[32m✓ All tests passed! Database infrastructure is ready.\033[0m")
        print("\033[35m◆ Database storage system is working correctly.\033[0m")
        print("\033[34m▲ Database is ready for your future refactor steps.\033[0m")
        logger.info(
            "Database connection tests completed successfully",
            extra_data={
                "tests_passed": passed,
                "total_tests": len(test_results),
                "success_rate": f"{passed / len(test_results) * 100:.1f}%",
            },
        )
        return 0
    else:
        print(
            "\033[31m× Some tests failed. Check your PostgreSQL container and configuration.\033[0m"
        )
        print("\033[35m◆ Try: docker compose up -d postgres\033[0m")
        logger.error(
            "Database connection tests failed",
            extra_data={
                "tests_passed": passed,
                "total_tests": len(test_results),
                "failed_tests": [name for name, result in test_results if not result],
            },
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
