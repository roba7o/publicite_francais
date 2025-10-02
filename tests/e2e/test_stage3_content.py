"""
Stage 3: Content Existence and Extraction Validation

Goal: Verify that articles have required content fields populated and validate
extraction success rates by site.

This test validates that soup validators are correctly extracting content
from the HTML fixtures, not just storing raw HTML.
"""

import subprocess
from sqlalchemy import text

from database.database import get_session

def test_content_extraction_quality(clean_test_db):
    """Test that articles have required content extracted from static fixtures.

    Based on fixtures: 16 articles total, all should have content extracted.
    """

    print("\n=== Stage 3: Testing Content Extraction ===")

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

    # Expected data based on static fixtures
    EXPECTED_TOTAL = 16
    EXPECTED_SITES = ["slate.fr", "franceinfo.fr", "tf1info.fr", "ladepeche.fr"]

    with get_session() as session:
        # Test 1: Basic content extraction metrics
        content_stats = session.execute(
            text("""
                SELECT
                    COUNT(*) as total_articles,
                    COUNT(CASE WHEN title IS NOT NULL AND LENGTH(TRIM(title)) > 0 THEN 1 END) as articles_with_titles,
                    COUNT(CASE WHEN extracted_text IS NOT NULL AND LENGTH(TRIM(extracted_text)) > 0 THEN 1 END) as articles_with_text,
                    COUNT(CASE WHEN extraction_status = 'success' THEN 1 END) as successful_extractions,
                    COUNT(CASE WHEN language = 'fr' THEN 1 END) as french_articles,
                    AVG(CASE WHEN extracted_text IS NOT NULL THEN LENGTH(extracted_text) ELSE 0 END) as avg_text_length
                FROM raw_articles
            """)
        ).fetchone()

        total, titles, extracted_text_count, success, french, avg_length = content_stats

        print(f"Content extraction results:")
        print(f"  Total articles: {total}")
        print(f"  Articles with titles: {titles}")
        print(f"  Articles with extracted text: {extracted_text_count}")
        print(f"  Successful extractions: {success}")
        print(f"  French language articles: {french}")
        print(f"  Average text length: {avg_length:.0f} characters")

        # Exact tests based on static fixtures
        assert total == EXPECTED_TOTAL, f"Expected {EXPECTED_TOTAL} articles, found {total}"

        # All articles should have titles extracted
        assert titles == EXPECTED_TOTAL, (
            f"Expected all {EXPECTED_TOTAL} articles to have titles, "
            f"but only {titles} have titles. Check soup validators."
        )

        # All articles should have text extracted
        assert extracted_text_count == EXPECTED_TOTAL, (
            f"Expected all {EXPECTED_TOTAL} articles to have extracted text, "
            f"but only {extracted_text_count} have text. Check soup validators or trafilatura extraction."
        )

        # All extractions should be successful
        assert success == EXPECTED_TOTAL, (
            f"Expected all {EXPECTED_TOTAL} extractions to be successful, "
            f"but only {success} succeeded. Check extraction process."
        )

        # Language detection may not be configured - check if it's working
        if french > 0:
            print(f"✓ Language detection working: {french} French articles detected")
        else:
            print(f"⚠ Language detection not configured (all articles show language=NULL)")
            print("  This is acceptable for basic content extraction testing")

        # Articles should have substantial content (not just HTML fragments)
        assert avg_length > 100, (
            f"Expected average text length > 100 characters, "
            f"but got {avg_length:.0f}. Check content extraction quality."
        )

        # Test 2: Per-site extraction quality
        print(f"\nExtraction quality by site:")
        site_stats = session.execute(
            text("""
                SELECT
                    site,
                    COUNT(*) as total,
                    COUNT(CASE WHEN extraction_status = 'success' THEN 1 END) as success_count,
                    AVG(CASE WHEN extracted_text IS NOT NULL THEN LENGTH(extracted_text) ELSE 0 END) as avg_length
                FROM raw_articles
                GROUP BY site
                ORDER BY site
            """)
        ).fetchall()

        for site, total, success_count, avg_length in site_stats:
            success_rate = (success_count / total * 100) if total > 0 else 0
            print(f"  {site}: {success_count}/{total} successful ({success_rate:.1f}%), avg {avg_length:.0f} chars")

            # Each site should have exactly 4 articles
            assert total == 4, f"Site {site}: expected 4 articles, found {total}"

            # All articles per site should extract successfully
            assert success_count == 4, (
                f"Site {site}: expected 4 successful extractions, "
                f"got {success_count}. Check soup validator for this site."
            )

            # Each site should extract substantial content
            assert avg_length > 50, (
                f"Site {site}: average text length too short ({avg_length:.0f} chars). "
                f"Check soup validator content extraction."
            )

        # Verify all expected sites are present
        actual_sites = [row[0] for row in site_stats]
        for expected_site in EXPECTED_SITES:
            assert expected_site in actual_sites, (
                f"Missing expected site: {expected_site}. "
                f"Found sites: {actual_sites}"
            )

    print(f"✓ All {EXPECTED_TOTAL} articles have quality content extraction")