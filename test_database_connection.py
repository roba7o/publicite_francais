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
    print("🔌 Testing basic database connection...")
    
    db = DatabaseManager()
    
    if not db.initialize():
        print("❌ Failed to initialize database manager")
        return False
    
    if db.test_connection():
        print("✅ Database connection successful!")
        return True
    else:
        print("❌ Database connection failed")
        return False


def test_raw_connection():
    """Test raw psycopg2 connection."""
    print("\n🔧 Testing raw psycopg2 connection...")
    
    try:
        db = get_database_manager()
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT current_database(), current_user, version()")
            result = cursor.fetchone()
            
            print(f"✅ Connected to database: {result[0]}")
            print(f"✅ Connected as user: {result[1]}")
            print(f"✅ PostgreSQL version: {result[2].split(',')[0]}")
            
            cursor.close()
            
        return True
        
    except Exception as e:
        print(f"❌ Raw connection failed: {e}")
        return False


def test_sqlalchemy_connection():
    """Test SQLAlchemy connection."""
    print("\n⚡ Testing SQLAlchemy connection...")
    
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
            print(f"✅ Found {len(tables)} tables in news_data schema:")
            for table in tables:
                print(f"   - {table}")
                
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False


def test_news_sources_data():
    """Test querying news sources data."""
    print("\n📰 Testing news sources data...")
    
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
            print(f"✅ Found {len(sources)} news sources:")
            
            for name, base_url, enabled in sources:
                status = "🟢 enabled" if enabled else "🔴 disabled"
                print(f"   - {name}: {base_url} ({status})")
                
        return True
        
    except Exception as e:
        print(f"❌ News sources query failed: {e}")
        return False


def test_health_check():
    """Test comprehensive health check."""
    print("\n🏥 Running database health check...")
    
    try:
        db = get_database_manager()
        health = db.health_check()
        
        print(f"✅ Health status: {health['status']}")
        print(f"✅ Connection pool: {health['connection_pool_status']}")
        print(f"✅ SQLAlchemy: {health['sqlalchemy_status']}")
        print(f"✅ News sources count: {health['news_sources_count']}")
        
        if health['errors']:
            print("⚠️  Errors found:")
            for error in health['errors']:
                print(f"   - {error}")
                
        return health['status'] in ['healthy', 'degraded']
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def main():
    """Run all database connection tests."""
    logger = get_structured_logger("DatabaseConnectionTest")
    
    print("🧪 French News Scraper - Database Connection Test")
    print("=" * 50)
    
    logger.info("Starting database connection tests")
    
    # Check if PostgreSQL container is running
    print("📋 Prerequisites:")
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
    print("\n" + "="*50)
    print("📊 Test Summary:")
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 All tests passed! Database infrastructure is ready.")
        print("💡 Your existing CSV scraper continues to work unchanged.")
        print("🚀 Database is ready for your future refactor steps.")
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
        print("❌ Some tests failed. Check your PostgreSQL container and configuration.")
        print("💡 Try: docker compose up -d postgres")
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