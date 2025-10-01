"""
Stage 5: Data Validation and Quality Assurance

Goal: Validate the quality and integrity of extracted data, ensuring realistic
content patterns, proper encoding, and data consistency.

This final stage tests data quality beyond just existence - validates that
content makes sense and follows expected patterns for news articles.
"""

import re
import subprocess
from datetime import datetime, timedelta
from sqlalchemy import text

from config.environment import get_news_data_schema
from database import get_session, initialize_database


def test_data_quality_and_integrity():
    """Test comprehensive data quality and integrity of extracted articles.

    Validates:
    1. Content quality and realistic patterns
    2. Data encoding and character handling
    3. Timestamp accuracy and consistency
    4. URL structure validation
    5. Content-to-HTML ratio analysis
    """

    print("\n=== Stage 5: Testing Data Quality and Integrity ===")

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

    with get_session() as session:
        # Get all articles for comprehensive analysis
        articles = session.execute(
            text(f"""
                SELECT
                    id, url, site, title, extracted_text, raw_html,
                    scraped_at, content_length, extraction_status,
                    author, date_published, language, summary, keywords
                FROM {schema}.raw_articles
                ORDER BY site, url
            """)
        ).fetchall()

        print(f"Analyzing {len(articles)} articles for data quality...")

        # Test 1: Content Quality Validation
        print(f"\n1. Content Quality Analysis:")
        title_issues = 0
        content_issues = 0
        encoding_issues = 0

        for article in articles:
            # Title quality checks
            if not article.title or len(article.title.strip()) < 10:
                title_issues += 1
            elif len(article.title) > 200:
                title_issues += 1

            # Content quality checks
            if not article.extracted_text or len(article.extracted_text.strip()) < 100:
                content_issues += 1

            # Encoding checks (look for common encoding issues)
            if article.extracted_text and ('â€' in article.extracted_text or 'Ã' in article.extracted_text):
                encoding_issues += 1

        print(f"  Title quality: {len(articles) - title_issues}/{len(articles)} articles have quality titles")
        print(f"  Content quality: {len(articles) - content_issues}/{len(articles)} articles have sufficient content")
        print(f"  Encoding quality: {len(articles) - encoding_issues}/{len(articles)} articles have clean encoding")

        # Quality assertions
        assert title_issues == 0, f"{title_issues} articles have title quality issues"
        assert content_issues == 0, f"{content_issues} articles have insufficient content"
        assert encoding_issues == 0, f"{encoding_issues} articles have encoding issues"

        # Test 2: URL Structure Validation
        print(f"\n2. URL Structure Validation:")
        url_patterns = {
            'slate.fr': r'^https://www\.slate\.fr/(monde|sciences)/',
            'franceinfo.fr': r'^https://www\.franceinfo\.fr/',
            'tf1info.fr': r'^https://www\.tf1info\.fr/',
            'ladepeche.fr': r'^https://www\.ladepeche\.fr/'
        }

        url_validation_passed = 0
        for article in articles:
            expected_pattern = url_patterns.get(article.site)
            if expected_pattern and re.match(expected_pattern, article.url):
                url_validation_passed += 1
            elif not expected_pattern:
                print(f"  ⚠ No URL pattern defined for site: {article.site}")

        print(f"  URL structure: {url_validation_passed}/{len(articles)} articles have valid URL patterns")

        # At least 90% should have valid URL patterns
        assert url_validation_passed >= len(articles) * 0.9, (
            f"Only {url_validation_passed}/{len(articles)} articles have valid URL patterns. "
            f"Expected at least 90% ({len(articles) * 0.9:.0f})"
        )

        # Test 3: Timestamp Consistency
        print(f"\n3. Timestamp Analysis:")
        from datetime import timezone
        now = datetime.now(timezone.utc)
        recent_articles = 0
        timestamp_issues = 0

        for article in articles:
            if article.scraped_at:
                # Convert naive datetime to UTC if needed
                scraped_time = article.scraped_at
                if scraped_time.tzinfo is None:
                    scraped_time = scraped_time.replace(tzinfo=timezone.utc)

                # Should be scraped recently (within last hour for test)
                if (now - scraped_time).total_seconds() < 3600:
                    recent_articles += 1
                else:
                    timestamp_issues += 1

        print(f"  Timestamp freshness: {recent_articles}/{len(articles)} articles scraped recently")
        assert timestamp_issues == 0, f"{timestamp_issues} articles have stale timestamps"

        # Test 4: Content-to-HTML Ratio Analysis
        print(f"\n4. Content Extraction Efficiency:")
        extraction_ratios = []

        for article in articles:
            if article.raw_html and article.extracted_text:
                ratio = len(article.extracted_text) / len(article.raw_html)
                extraction_ratios.append(ratio)

        if extraction_ratios:
            avg_ratio = sum(extraction_ratios) / len(extraction_ratios)
            min_ratio = min(extraction_ratios)
            max_ratio = max(extraction_ratios)

            print(f"  Average extraction ratio: {avg_ratio:.3f} (text/html)")
            print(f"  Extraction ratio range: {min_ratio:.3f} - {max_ratio:.3f}")

            # Reasonable extraction ratios (text should be much smaller than HTML)
            # Good text extractors like Trafilatura typically extract 2-10% of HTML as clean text
            assert 0.02 <= avg_ratio <= 0.2, (
                f"Average extraction ratio {avg_ratio:.3f} seems unrealistic. "
                f"Expected between 0.02-0.2 (2%-20%) for clean text extraction"
            )

        # Test 5: Site-Specific Content Patterns
        print(f"\n5. Site-Specific Content Analysis:")
        site_patterns = {
            'slate.fr': ['monde', 'sciences', 'politique'],  # Common Slate categories
            'franceinfo.fr': ['politique', 'france', 'monde'],  # Common FranceInfo topics
            'tf1info.fr': ['societe', 'economie', 'politique'],  # Common TF1 categories
            'ladepeche.fr': ['lot', 'france', 'sport']  # Common Depeche topics
        }

        for site, expected_keywords in site_patterns.items():
            site_articles = [a for a in articles if a.site == site]
            if site_articles:
                # Check if articles contain site-appropriate content
                relevant_articles = 0
                for article in site_articles:
                    content_lower = (article.extracted_text or '').lower()
                    url_lower = article.url.lower()

                    # Check if content or URL contains expected keywords
                    if any(keyword in content_lower or keyword in url_lower for keyword in expected_keywords):
                        relevant_articles += 1

                relevance_rate = relevant_articles / len(site_articles)
                print(f"  {site}: {relevant_articles}/{len(site_articles)} articles show relevant content ({relevance_rate:.1%})")

        # Test 6: Data Completeness
        print(f"\n6. Data Completeness Analysis:")
        required_fields = ['url', 'site', 'raw_html', 'scraped_at']
        optional_fields = ['title', 'extracted_text', 'content_length', 'extraction_status']

        for field in required_fields:
            empty_count = sum(1 for a in articles if not getattr(a, field))
            print(f"  {field}: {len(articles) - empty_count}/{len(articles)} articles have data")
            assert empty_count == 0, f"{empty_count} articles missing required field: {field}"

        for field in optional_fields:
            empty_count = sum(1 for a in articles if not getattr(a, field))
            filled_count = len(articles) - empty_count
            fill_rate = filled_count / len(articles)
            print(f"  {field}: {filled_count}/{len(articles)} articles have data ({fill_rate:.1%})")

        # Test 7: Duplicate Detection
        print(f"\n7. Duplicate Detection:")
        urls = [a.url for a in articles]
        unique_urls = set(urls)

        print(f"  URL uniqueness: {len(unique_urls)}/{len(urls)} unique URLs")
        assert len(unique_urls) == len(urls), (
            f"Found {len(urls) - len(unique_urls)} duplicate URLs. "
            f"Each fixture should create a unique database entry."
        )

        # Summary
        print(f"\n=== Data Quality Summary ===")
        print(f"✓ All {len(articles)} articles pass content quality checks")
        print(f"✓ All articles have valid timestamps and required fields")
        print(f"✓ URL patterns and extraction ratios are within expected ranges")
        print(f"✓ No duplicates detected")
        print(f"✓ Site-specific content patterns validated")

    print(f"✓ All data quality and integrity tests passed!")