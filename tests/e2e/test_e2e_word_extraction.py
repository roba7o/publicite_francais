"""
E2E Test: Word Extraction Pipeline

Tests the complete pipeline from HTML fixtures to word_facts table.
Validates the star schema architecture with real French articles.
"""

import subprocess

from sqlalchemy import text

from database.database import get_session


def test_pipeline_processes_all_fixtures(clean_test_db):
    """Test that pipeline processes all 12 HTML fixtures."""
    print("\n=== E2E: Pipeline Processing ===")

    # Run the pipeline
    result = subprocess.run(
        ["make", "run-test-data"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, f"Pipeline failed: {result.returncode}"
    print("✓ Pipeline completed successfully")

    # Verify articles stored
    with get_session() as session:
        count = session.execute(text("SELECT COUNT(*) FROM raw_articles")).scalar()

    assert count >= 12, f"Expected at least 12 articles, got {count}"
    print(f"✓ At least 12 fixtures processed and stored (got {count})")


def test_articles_have_required_fields(clean_test_db):
    """Test that raw_articles have all required fields."""
    print("\n=== E2E: Article Schema Validation ===")

    # Run pipeline first
    subprocess.run(["make", "run-test-data"], capture_output=True, timeout=60)

    with get_session() as session:
        # Check all fields exist and are populated
        result = session.execute(
            text("""
                SELECT id, url, raw_html, site, scraped_at, content_length
                FROM raw_articles
                LIMIT 1
            """)
        ).fetchone()

    assert result is not None, "No articles found"
    assert result[0] is not None, "id is NULL"
    assert result[1] is not None, "url is NULL"
    assert result[2] is not None, "raw_html is NULL"
    assert result[3] is not None, "site is NULL"
    assert result[4] is not None, "scraped_at is NULL"
    assert result[5] is not None, "content_length is NULL"
    print("✓ All required fields present and populated")


def test_url_uniqueness_enforced(clean_test_db):
    """Test that URL UNIQUE constraint works."""
    print("\n=== E2E: URL Uniqueness ===")

    # Run pipeline
    subprocess.run(["make", "run-test-data"], capture_output=True, timeout=60)

    with get_session() as session:
        # Check for duplicate URLs
        result = session.execute(
            text("""
                SELECT url, COUNT(*) as count
                FROM raw_articles
                GROUP BY url
                HAVING COUNT(*) > 1
            """)
        ).fetchall()

    assert len(result) == 0, f"Found duplicate URLs: {result}"
    print("✓ URL uniqueness constraint enforced")


def test_word_facts_extracted(clean_test_db):
    """Test that word_facts are extracted and stored."""
    print("\n=== E2E: Word Facts Extraction ===")

    # Run pipeline
    subprocess.run(["make", "run-test-data"], capture_output=True, timeout=60)

    with get_session() as session:
        count = session.execute(text("SELECT COUNT(*) FROM word_facts")).scalar()

    assert count > 0, "No word_facts extracted"
    print(f"✓ Word facts extracted: {count} words")


def test_word_facts_minimum_per_article(clean_test_db):
    """Test that each article has a reasonable minimum number of words."""
    print("\n=== E2E: Minimum Words Per Article ===")

    # Run pipeline
    subprocess.run(["make", "run-test-data"], capture_output=True, timeout=60)

    with get_session() as session:
        # Check minimum words per article
        result = session.execute(
            text("""
                SELECT COUNT(*) as word_count
                FROM word_facts
                GROUP BY article_id
                ORDER BY word_count ASC
                LIMIT 1
            """)
        ).scalar()

    # Each article should have at least 50 words
    # (French news articles are substantial)
    assert result >= 50, f"Article has only {result} words (expected >= 50)"
    print(f"✓ Minimum words per article validated: {result} words")


def test_word_facts_foreign_key_integrity(clean_test_db):
    """Test that all word_facts have valid article_id foreign keys."""
    print("\n=== E2E: Foreign Key Integrity ===")

    # Run pipeline
    subprocess.run(["make", "run-test-data"], capture_output=True, timeout=60)

    with get_session() as session:
        # Check for orphaned word_facts
        result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM word_facts wf
                LEFT JOIN raw_articles ra ON wf.article_id = ra.id
                WHERE ra.id IS NULL
            """)
        ).scalar()

    assert result == 0, f"Found {result} orphaned word_facts"
    print("✓ All word_facts have valid article_id")


def test_word_position_validation(clean_test_db):
    """Test that position_in_article is >= 0 for all words."""
    print("\n=== E2E: Word Position Validation ===")

    # Run pipeline
    subprocess.run(["make", "run-test-data"], capture_output=True, timeout=60)

    with get_session() as session:
        result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM word_facts
                WHERE position_in_article < 0
            """)
        ).scalar()

    assert result == 0, f"Found {result} words with negative position"
    print("✓ All word positions are valid (>= 0)")


def test_word_normalization(clean_test_db):
    """Test that words are normalized (lowercase, no empty strings)."""
    print("\n=== E2E: Word Normalization ===")

    # Run pipeline
    subprocess.run(["make", "run-test-data"], capture_output=True, timeout=60)

    with get_session() as session:
        # Check for empty words
        empty_count = session.execute(
            text("SELECT COUNT(*) FROM word_facts WHERE word = '' OR word IS NULL")
        ).scalar()

        # Check for uppercase words (should all be lowercase)
        uppercase_count = session.execute(
            text("SELECT COUNT(*) FROM word_facts WHERE word != LOWER(word)")
        ).scalar()

    assert empty_count == 0, f"Found {empty_count} empty words"
    assert uppercase_count == 0, f"Found {uppercase_count} non-lowercase words"
    print("✓ All words are normalized (lowercase, non-empty)")


def test_french_words_detected(clean_test_db):
    """Test that common French words are detected."""
    print("\n=== E2E: French Word Detection ===")

    # Run pipeline
    subprocess.run(["make", "run-test-data"], capture_output=True, timeout=60)

    # Common French articles/prepositions
    common_french_words = ["le", "la", "les", "un", "une", "de", "et", "à"]

    with get_session() as session:
        for word in common_french_words:
            count = session.execute(
                text("SELECT COUNT(*) FROM word_facts WHERE word = :word"),
                {"word": word},
            ).scalar()
            assert count > 0, f"Common French word '{word}' not found"

    print(f"✓ Common French words detected: {common_french_words}")


def test_star_schema_join(clean_test_db):
    """Test that star schema join works (word_facts → raw_articles)."""
    print("\n=== E2E: Star Schema Join ===")

    # Run pipeline
    subprocess.run(["make", "run-test-data"], capture_output=True, timeout=60)

    with get_session() as session:
        # Test join query
        result = session.execute(
            text("""
                SELECT ra.site, wf.word, COUNT(*) as frequency
                FROM word_facts wf
                JOIN raw_articles ra ON wf.article_id = ra.id
                WHERE wf.word = 'le'
                GROUP BY ra.site, wf.word
                ORDER BY frequency DESC
                LIMIT 1
            """)
        ).fetchone()

    assert result is not None, "Star schema join failed"
    assert result[0] is not None, "Site is NULL in join"
    assert result[1] == "le", "Word mismatch in join"
    assert result[2] > 0, "Frequency is 0"
    print(
        f"✓ Star schema join works: site={result[0]}, word={result[1]}, freq={result[2]}"
    )


def test_word_frequency_query(clean_test_db):
    """Test that we can query word frequencies (vocabulary learning use case)."""
    print("\n=== E2E: Word Frequency Query ===")

    # Run pipeline
    subprocess.run(["make", "run-test-data"], capture_output=True, timeout=60)

    with get_session() as session:
        # Get top 10 most frequent words
        results = session.execute(
            text("""
                SELECT word, COUNT(*) as frequency
                FROM word_facts
                GROUP BY word
                ORDER BY frequency DESC
                LIMIT 10
            """)
        ).fetchall()

    assert len(results) == 10, f"Expected 10 results, got {len(results)}"
    # Most frequent word should appear multiple times
    assert results[0][1] > 10, f"Top word only appears {results[0][1]} times"
    print(
        f"✓ Top 10 words query works. Most frequent: '{results[0][0]}' ({results[0][1]} times)"
    )


def test_article_word_count_placeholder(clean_test_db):
    """
    Placeholder: Validate reasonable word counts per article.

    TODO: Add specific assertions for expected word counts per fixture.
    This will be completed after other tests are working.
    """
    print("\n=== E2E: Article Word Count (Placeholder) ===")

    # Run pipeline
    subprocess.run(["make", "run-test-data"], capture_output=True, timeout=60)

    with get_session() as session:
        # Get word count per article
        results = session.execute(
            text("""
                SELECT ra.url, COUNT(wf.id) as word_count
                FROM raw_articles ra
                LEFT JOIN word_facts wf ON ra.id = wf.article_id
                GROUP BY ra.url, ra.id
                ORDER BY word_count DESC
            """)
        ).fetchall()

    # Basic validation: all articles should have words
    for url, count in results:
        assert count > 0, f"Article {url} has no words"

    print(f"✓ All {len(results)} articles have words extracted")
    print("⚠ TODO: Add specific word count assertions for each fixture")
    # TODO: Add assertions like:
    # assert results_for_slate_article_1 == expected_count_1
    # assert results_for_franceinfo_article_2 == expected_count_2
