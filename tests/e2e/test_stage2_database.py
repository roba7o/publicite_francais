"""
Stage 2: Database Connection Test

Goal: Verify that articles are stored in the database after pipeline runs.

This test connects to the database and counts articles to confirm
the pipeline is actually saving data.

Note: ENVIRONMENT=test is automatically set by tests/conftest.py
"""

from sqlalchemy import text

from database.database import get_session


def test_articles_exist_in_database(clean_test_db):
    """Test that pipeline stores exact number of articles from static fixtures.

    Based on fixtures: 4 sites × 4 files each = 16 total articles expected.
    This test clears the database first to ensure deterministic results.
    """

    print("\n=== Stage 2: Testing Database Storage ===")

    print("✓ Database already cleaned by clean_test_db fixture")

    # Run the test data pipeline to populate with fixtures
    import subprocess
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
    EXPECTED_PER_SITE = 4
    EXPECTED_SITES = {
        "slate.fr": EXPECTED_PER_SITE,
        "franceinfo.fr": EXPECTED_PER_SITE,
        "tf1info.fr": EXPECTED_PER_SITE,
        "ladepeche.fr": EXPECTED_PER_SITE
    }

    # Connect and count articles using application's database layer
    with get_session() as session:
        total_count = session.execute(
            text("SELECT COUNT(*) FROM raw_articles")
        ).scalar()

        print(f"Articles found in database: {total_count}")

        # Exact count test - should be deterministic with static fixtures
        assert total_count == EXPECTED_TOTAL, (
            f"Expected exactly {EXPECTED_TOTAL} articles from static fixtures, "
            f"but found {total_count}. Check if fixtures are missing or pipeline failed."
        )

        # Verify each site has exact expected count
        sites = session.execute(
            text(
                "SELECT site, COUNT(*) FROM raw_articles GROUP BY site ORDER BY site"
            )
        ).fetchall()

        print("Articles by site:")
        actual_sites = {}
        for site, site_count in sites:
            print(f"  {site}: {site_count} articles")
            actual_sites[site] = site_count

        # Test each site individually
        for expected_site, expected_count in EXPECTED_SITES.items():
            actual_count = actual_sites.get(expected_site, 0)
            assert actual_count == expected_count, (
                f"Site {expected_site}: expected {expected_count} articles, "
                f"but found {actual_count}. Check soup validator for this site."
            )

        # Verify no unexpected sites
        unexpected_sites = set(actual_sites.keys()) - set(EXPECTED_SITES.keys())
        assert not unexpected_sites, (
            f"Found unexpected sites: {unexpected_sites}. "
            f"Expected only: {list(EXPECTED_SITES.keys())}"
        )

    print(f"✓ Database contains exactly {EXPECTED_TOTAL} articles from static fixtures")
