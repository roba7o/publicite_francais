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
    - Dependencies installed (pip install -r requirements.txt)
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from database import DatabaseManager, get_database_manager, initialize_database
from utils.structured_logger import get_structured_logger


def test_basic_connection():
    """Test basic database connectivity."""
    print("\033[34m■ Testing basic database connection...\033[0m")
    
    db = DatabaseManager()
    
    if not db.initialize():
        print("\033[31m× Failed to initialize database manager\033[0m")
        return False
    
    if db.test_connection():
        print("\033[32m✓ Database connection successful!\033[0m")
        return True
    else:
        print("\033[31m× Database connection failed\033[0m")
        return False


def test_raw_connection():
    """Test raw psycopg2 connection."""
    print("\n\033[35m■ Testing raw psycopg2 connection...\033[0m")
    
    try:
        db = get_database_manager()
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT current_database(), current_user, version()")
            result = cursor.fetchone()
            
            print(f"\033[32m✓ Connected to database: {result[0]}\033[0m")
            print(f"\033[32m✓ Connected as user: {result[1]}\033[0m")
            print(f"\033[32m✓ PostgreSQL version: {result[2].split(',')[0]}\033[0m")
            
            cursor.close()
            
        return True
        
    except Exception as e:
        print(f"\033[31m× Raw connection failed: {e}\033[0m")
        return False


def test_sqlalchemy_connection():
    """Test SQLAlchemy connection."""
    print("\n\033[36m■ Testing SQLAlchemy connection...\033[0m")
    
    try:
        db = get_database_manager()
        
        with db.get_session() as session:
            from sqlalchemy import text
            
            # Test schema query
            result = session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'news_data'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            print(f"\033[32m✓ Found {len(tables)} tables in news_data schema:\033[0m")
            for table in tables:
                print(f"   - {table}")
                
        return True
        
    except Exception as e:
        print(f"\033[31m× SQLAlchemy connection failed: {e}\033[0m")
        return False


def test_news_sources_data():
    """Test querying news sources data."""
    print("\n\033[34m■ Testing news sources data...\033[0m")
    
    try:
        db = get_database_manager()
        
        with db.get_session() as session:
            from sqlalchemy import text
            
            result = session.execute(text("""
                SELECT name, base_url, enabled 
                FROM news_data.news_sources 
                ORDER BY name
            """))
            
            sources = list(result)
            print(f"\033[32m✓ Found {len(sources)} news sources:\033[0m")
            
            for name, base_url, enabled in sources:
                status = "\033[32m● enabled\033[0m" if enabled else "\033[31m● disabled\033[0m"
                print(f"   - {name}: {base_url} ({status})")
                
        return True
        
    except Exception as e:
        print(f"\033[31m× News sources query failed: {e}\033[0m")
        return False


def test_health_check():
    """Test comprehensive health check."""
    print("\n\033[33m◆ Running database health check...\033[0m")
    
    try:
        db = get_database_manager()
        health = db.health_check()
        
        print(f"\033[32m✓ Health status: {health['status']}\033[0m")
        print(f"\033[32m✓ Connection pool: {health['connection_pool_status']}\033[0m")
        print(f"\033[32m✓ SQLAlchemy: {health['sqlalchemy_status']}\033[0m")
        print(f"\033[32m✓ News sources count: {health['news_sources_count']}\033[0m")
        
        if health['errors']:
            print("\033[33m⚠ Errors found:\033[0m")
            for error in health['errors']:
                print(f"   - {error}")
                
        return health['status'] in ['healthy', 'degraded']
        
    except Exception as e:
        print(f"\033[31m× Health check failed: {e}\033[0m")
        return False


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
    print("   - Dependencies installed: pip install -r requirements.txt")
    print()
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Raw psycopg2", test_raw_connection), 
        ("SQLAlchemy", test_sqlalchemy_connection),
        ("News Sources Data", test_news_sources_data),
        ("Health Check", test_health_check)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        result = test_func()
        test_results.append((test_name, result))
    
    # Summary
    # ASCII art for completion
    print(f"""
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
                "success_rate": f"{passed/len(test_results)*100:.1f}%"
            }
        )
        return 0
    else:
        print("\033[31m× Some tests failed. Check your PostgreSQL container and configuration.\033[0m")
        print("\033[35m◆ Try: docker compose up -d postgres\033[0m")
        logger.error(
            "Database connection tests failed",
            extra_data={
                "tests_passed": passed,
                "total_tests": len(test_results),
                "failed_tests": [name for name, result in test_results if not result]
            }
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())