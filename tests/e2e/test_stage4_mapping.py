"""
Stage 4: Fixture Processing Test

Goal: Verify that HTML fixture files are processed correctly.

Simple test that all fixture files become database entries.
"""

import subprocess
from pathlib import Path
from sqlalchemy import text

from database.database import get_session


def test_fixture_processing(clean_test_db):
    """Test that HTML fixtures are processed into database entries.

    Simple check: fixture count matches database article count.
    """

    print("\n=== Stage 4: Testing Fixture Processing ===")

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

    # Count expected fixture files
    fixture_dir = Path("tests/fixtures/test_html")
    expected_file_count = 0

    for site_dir in fixture_dir.iterdir():
        if site_dir.is_dir():
            html_files = list(site_dir.glob("*.html")) + list(site_dir.glob("*.php"))
            expected_file_count += len(html_files)

    print(f"Expected {expected_file_count} fixture files to be processed")

    # Verify database contains correct number of articles
    with get_session() as session:
        article_count = session.execute(text("SELECT COUNT(*) FROM raw_articles")).scalar()

        print(f"Found {article_count} articles in database")

        # Should match exactly
        assert article_count == expected_file_count, (
            f"Expected {expected_file_count} articles from fixtures, "
            f"but found {article_count} in database"
        )

        # Verify site distribution (4 files per site)
        site_counts = session.execute(
            text("SELECT site, COUNT(*) FROM raw_articles GROUP BY site ORDER BY site")
        ).fetchall()

        print("Site distribution:")
        for site, count in site_counts:
            print(f"  {site}: {count} articles")
            assert count == 4, f"Site {site} should have exactly 4 articles, but has {count}"

    print(f"✓ All {expected_file_count} fixture files correctly processed")
