"""
Stage 5: Basic Data Quality Check

Goal: Validate basic data quality - content exists and no encoding issues.

Simple validation that extracted data is usable.
"""

import subprocess
from sqlalchemy import text

from database.database import get_session


def test_basic_data_quality(clean_test_db):
    """Test basic data quality of extracted articles.

    Simple checks:
    1. Content extraction worked
    2. No encoding issues
    3. No duplicates
    """

    print("\n=== Stage 5: Testing Basic Data Quality ===")

    print("✓ Database already cleaned by clean_test_db fixture")

    # Run the test data pipeline to populate with fixtures
    print("Running test data pipeline...")
    result = subprocess.run(
        ["make", "run-test-data"],
        capture_output=True,
        text=True,
        timeout=60
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"
    print("✓ Test data pipeline completed")

    with get_session() as session:
        # Get all articles
        articles = session.execute(
            text("""
                SELECT id, url, site, title, extracted_text, extraction_status
                FROM raw_articles
                ORDER BY site, url
            """)
        ).fetchall()

        print(f"Analyzing {len(articles)} articles for basic quality...")

        # Test 1: Content extraction worked
        extraction_failures = 0
        encoding_issues = 0

        for article in articles:
            # Check extraction status
            if article.extraction_status != 'success':
                extraction_failures += 1

            # Check for encoding issues
            if article.extracted_text and ('â€' in article.extracted_text or 'Ã' in article.extracted_text):
                encoding_issues += 1

        print(f"  Extraction success: {len(articles) - extraction_failures}/{len(articles)} articles")
        print(f"  Encoding quality: {len(articles) - encoding_issues}/{len(articles)} articles clean")

        # Basic assertions
        assert extraction_failures == 0, f"{extraction_failures} articles failed extraction"
        assert encoding_issues == 0, f"{encoding_issues} articles have encoding issues"

        # Test 2: No duplicates
        urls = [a.url for a in articles]
        unique_urls = set(urls)

        print(f"  URL uniqueness: {len(unique_urls)}/{len(urls)} unique URLs")
        assert len(unique_urls) == len(urls), f"Found {len(urls) - len(unique_urls)} duplicate URLs"

    print(f"✓ Basic data quality checks passed!")