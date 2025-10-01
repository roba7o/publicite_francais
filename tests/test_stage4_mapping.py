"""
Stage 4: HTML-to-Database Matching Test

Goal: Verify that specific HTML fixture files create corresponding database entries
with correct URL mapping.

This test ensures the pipeline correctly processes individual fixture files and
maps them to the right URLs using the URL_MAPPING configuration.
"""

import subprocess
from pathlib import Path
from sqlalchemy import text

from config.environment import get_news_data_schema
from database import get_session, initialize_database
from utils.url_mapping import URL_MAPPING


def test_html_fixture_to_database_mapping():
    """Test that each HTML fixture file creates a corresponding database entry.

    Verifies:
    1. Each fixture file gets processed into a database record
    2. URL mapping works correctly (filename -> original URL)
    3. Site categorization is correct based on directory structure
    """

    print("\n=== Stage 4: Testing HTML Fixture to Database Mapping ===")

    # Initialize database connection
    success = initialize_database()
    assert success, "Failed to initialize database"

    # Get the schema name
    schema = get_news_data_schema()
    print(f"Using database schema: {schema}")

    # Clear and repopulate database for clean testing
    with get_session() as session:
        session.execute(text(f"TRUNCATE TABLE {schema}.raw_articles"))
        print("✓ Cleared test database for clean testing")

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

    # Get expected fixture files
    fixture_dir = Path("tests/fixtures/test_html")
    expected_files = []
    site_mapping = {
        "Slate.fr": "slate.fr",
        "FranceInfo.fr": "franceinfo.fr",
        "TF1 Info": "tf1info.fr",
        "Depeche.fr": "ladepeche.fr"
    }

    for site_dir in fixture_dir.iterdir():
        if site_dir.is_dir() and site_dir.name in site_mapping:
            expected_site = site_mapping[site_dir.name]
            for html_file in site_dir.iterdir():
                if html_file.suffix in ('.html', '.php'):
                    expected_files.append({
                        'filename': html_file.name,
                        'site': expected_site,
                        'expected_url': URL_MAPPING.get(html_file.name, f"test://{html_file.name}")
                    })

    print(f"Expected {len(expected_files)} fixture files to be processed")

    # Verify database contains all expected files
    with get_session() as session:
        # Get all articles from database
        articles = session.execute(
            text(f"""
                SELECT url, site, title, LENGTH(raw_html) as html_length, LENGTH(extracted_text) as text_length
                FROM {schema}.raw_articles
                ORDER BY site, url
            """)
        ).fetchall()

        print(f"Found {len(articles)} articles in database")

        # Verify we have the right number of articles
        assert len(articles) == len(expected_files), (
            f"Expected {len(expected_files)} articles from fixtures, "
            f"but found {len(articles)} in database"
        )

        # Check each expected file has a corresponding database entry
        article_urls = [article.url for article in articles]

        print("\nVerifying fixture-to-database mapping:")
        for expected_file in expected_files:
            expected_url = expected_file['expected_url']
            expected_site = expected_file['site']
            filename = expected_file['filename']

            # Find the matching article in database
            matching_articles = [a for a in articles if a.url == expected_url and a.site == expected_site]

            assert len(matching_articles) == 1, (
                f"Fixture file '{filename}' should create exactly 1 database entry "
                f"with URL '{expected_url}' and site '{expected_site}', "
                f"but found {len(matching_articles)} matches"
            )

            article = matching_articles[0]
            print(f"  ✓ {filename} -> {expected_site} -> {len(str(article.text_length))} chars extracted")

            # Verify article has substantial content
            assert article.html_length > 1000, (
                f"Article from {filename} has suspiciously short HTML ({article.html_length} chars). "
                f"Check if fixture file is properly loaded."
            )

            assert article.text_length > 100, (
                f"Article from {filename} has insufficient extracted text ({article.text_length} chars). "
                f"Check content extraction for this file."
            )

        # Verify site distribution is correct
        site_counts = {}
        for article in articles:
            site_counts[article.site] = site_counts.get(article.site, 0) + 1

        print(f"\nSite distribution verification:")
        for site, count in sorted(site_counts.items()):
            print(f"  {site}: {count} articles")
            assert count == 4, (
                f"Site {site} should have exactly 4 articles, but has {count}. "
                f"Check fixture files or URL mapping for this site."
            )

        # Test URL mapping accuracy
        print(f"\nURL mapping verification:")
        mapped_count = 0
        test_url_count = 0

        for article in articles:
            if article.url.startswith('http'):
                mapped_count += 1
                print(f"  ✓ Mapped URL: {article.url}")
            elif article.url.startswith('test://'):
                test_url_count += 1
                print(f"  ⚠ Test URL (no mapping): {article.url}")

        print(f"\nURL mapping summary:")
        print(f"  Properly mapped URLs: {mapped_count}")
        print(f"  Fallback test URLs: {test_url_count}")

        # At least some URLs should be properly mapped
        assert mapped_count > 0, (
            "No URLs were properly mapped from URL_MAPPING. "
            "Check URL_MAPPING configuration and filename matching."
        )

    print(f"✓ All {len(expected_files)} fixture files correctly processed and mapped to database")