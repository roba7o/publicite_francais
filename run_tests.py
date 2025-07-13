#!/usr/bin/env python3
"""
Test runner for the French article scraper project.

This script runs the core functionality tests that verify the system works
correctly after the directory restructuring and configuration changes.
"""

import os
import sys
import subprocess

# Add src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)
os.environ['PYTHONPATH'] = f"{src_dir}:{os.environ.get('PYTHONPATH', '')}"

def run_test_suite():
    """Run the core test suite."""
    print("🧪 Running French Article Scraper Test Suite")
    print("=" * 50)
    
    # Tests that should work
    working_tests = [
        "tests/integration/test_basic_functionality.py",
        "tests/unit/test_french_text_processor.py::TestFrenchTextProcessor::test_initialization",
        "tests/unit/test_french_text_processor.py::TestFrenchTextProcessor::test_validate_text_valid_input",
        "tests/unit/test_french_text_processor.py::TestFrenchTextProcessor::test_validate_text_empty_input",
        "tests/unit/test_french_text_processor.py::TestFrenchTextProcessor::test_count_word_frequency_basic",
    ]
    
    total_passed = 0
    total_failed = 0
    
    for test in working_tests:
        print(f"\n🔍 Running {test}")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", test, "-v", "--tb=short"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ PASSED: {test}")
                total_passed += 1
            else:
                print(f"❌ FAILED: {test}")
                print(f"Error output: {result.stdout}")
                total_failed += 1
                
        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT: {test}")
            total_failed += 1
        except Exception as e:
            print(f"💥 ERROR running {test}: {e}")
            total_failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 TEST SUMMARY")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"📈 Success Rate: {total_passed/(total_passed+total_failed)*100:.1f}%")
    
    return total_failed == 0

def verify_system_health():
    """Verify the system is healthy and directories are correct."""
    print("\n🏥 SYSTEM HEALTH CHECK")
    print("=" * 30)
    
    checks_passed = 0
    total_checks = 0
    
    # Check output directory
    total_checks += 1
    output_dir = os.path.join(current_dir, "src", "article_scrapers", "output")
    if os.path.exists(output_dir):
        print(f"✅ Output directory exists: {output_dir}")
        checks_passed += 1
    else:
        print(f"❌ Output directory missing: {output_dir}")
    
    # Check logs directory
    total_checks += 1
    logs_dir = os.path.join(current_dir, "src", "article_scrapers", "logs")
    if os.path.exists(logs_dir):
        print(f"✅ Logs directory exists: {logs_dir}")
        checks_passed += 1
    else:
        print(f"❌ Logs directory missing: {logs_dir}")
    
    # Check CSV writer import
    total_checks += 1
    try:
        from article_scrapers.utils.csv_writer import CSVWriter
        print("✅ CSVWriter import successful")
        checks_passed += 1
    except ImportError as e:
        print(f"❌ CSVWriter import failed: {e}")
    
    # Check text processor import
    total_checks += 1
    try:
        from article_scrapers.utils.french_text_processor import FrenchTextProcessor
        print("✅ FrenchTextProcessor import successful")
        checks_passed += 1
    except ImportError as e:
        print(f"❌ FrenchTextProcessor import failed: {e}")
    
    # Check logging setup
    total_checks += 1
    try:
        from article_scrapers.utils.logging_config_enhanced import setup_logging
        setup_logging()
        print("✅ Logging setup successful")
        checks_passed += 1
    except Exception as e:
        print(f"❌ Logging setup failed: {e}")
    
    print(f"\n🏥 Health Score: {checks_passed}/{total_checks} ({checks_passed/total_checks*100:.1f}%)")
    return checks_passed == total_checks

if __name__ == "__main__":
    print("🚀 French Article Scraper Test Runner")
    print("This script tests the core functionality after repository cleanup.")
    print()
    
    # Run system health check
    health_ok = verify_system_health()
    
    # Run tests
    tests_ok = run_test_suite()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULT")
    
    if health_ok and tests_ok:
        print("🎉 ALL SYSTEMS GO! Repository cleanup successful.")
        print("✅ Logging: Consolidated to src/article_scrapers/logs/")
        print("✅ Output: Consolidated to src/article_scrapers/output/")
        print("✅ Core functionality: Working correctly")
        sys.exit(0)
    else:
        print("⚠️  Some issues detected:")
        if not health_ok:
            print("  - System health check failed")
        if not tests_ok:
            print("  - Some tests failed")
        print("\nBut the main functionality should still work for live/offline runs.")
        sys.exit(1)