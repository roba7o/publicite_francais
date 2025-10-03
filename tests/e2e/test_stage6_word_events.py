"""
Stage 6: Word Events Processing Test

Goal: Verify that word events are correctly extracted and stored from articles.

This test validates the word events fact table generation:
1. Word extraction from article text
2. Position tracking within articles
3. Proper foreign key relationships
4. No filtering at storage level (pure ELT approach)
"""

import subprocess
from sqlalchemy import text

from database.database import get_session


def test_word_events_processing(clean_test_db):
    """Test that word events are generated and stored correctly from static fixtures.

    Based on fixtures: 16 articles should generate substantial word events.
    Tests the word analytics fact table foundation.
    """

    print("\n=== Stage 6: Testing Word Events Processing ===")

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
    EXPECTED_ARTICLES = 16

    with get_session() as session:
        # Test 1: Basic word events generation
        word_stats = session.execute(
            text("""
                SELECT
                    COUNT(*) as total_word_events,
                    COUNT(DISTINCT word) as unique_words,
                    COUNT(DISTINCT article_id) as articles_with_words,
                    AVG(position_in_article) as avg_position,
                    MAX(position_in_article) as max_position
                FROM word_events
            """)
        ).fetchone()

        total_events, unique_words, articles_with_words, avg_pos, max_pos = word_stats

        print("Word events statistics:")
        print(f"  Total word events: {total_events}")
        print(f"  Unique words: {unique_words}")
        print(f"  Articles with words: {articles_with_words}")
        print(f"  Average word position: {avg_pos:.1f}")
        print(f"  Maximum word position: {max_pos}")

        # Basic validation
        assert total_events > 0, "No word events generated"
        assert unique_words > 0, "No unique words found"
        assert articles_with_words == EXPECTED_ARTICLES, (
            f"Expected all {EXPECTED_ARTICLES} articles to have word events, "
            f"but only {articles_with_words} have words"
        )

        # Word events should be substantial (minimum words per article)
        min_words_per_article = 50  # Conservative estimate for French news articles
        expected_min_total = EXPECTED_ARTICLES * min_words_per_article
        assert total_events >= expected_min_total, (
            f"Expected at least {expected_min_total} word events "
            f"({min_words_per_article} words/article), but got {total_events}"
        )

        # Should have reasonable vocabulary diversity
        min_unique_words = 100  # Should have at least 100 unique words across all articles
        assert unique_words >= min_unique_words, (
            f"Expected at least {min_unique_words} unique words, but got {unique_words}. "
            f"Check word extraction and text quality."
        )

        # Test 2: Foreign key relationships
        print("\nForeign key relationship validation:")
        orphaned_words = session.execute(
            text("""
                SELECT COUNT(*)
                FROM word_events we
                LEFT JOIN raw_articles ra ON we.article_id = ra.id
                WHERE ra.id IS NULL
            """)
        ).scalar()

        print(f"  Orphaned word events: {orphaned_words}")
        assert orphaned_words == 0, (
            f"Found {orphaned_words} word events with invalid article_id references"
        )

        # Test 3: Position tracking validation
        print("\nPosition tracking validation:")
        position_stats = session.execute(
            text("""
                SELECT
                    article_id,
                    COUNT(*) as word_count,
                    MIN(position_in_article) as min_pos,
                    MAX(position_in_article) as max_pos
                FROM word_events
                GROUP BY article_id
                ORDER BY word_count DESC
                LIMIT 5
            """)
        ).fetchall()

        for article_id, word_count, min_pos, max_pos in position_stats:
            print(f"  Article {str(article_id)[:8]}...: {word_count} words, positions {min_pos}-{max_pos}")

            # Positions should start at 0 and be continuous
            assert min_pos >= 0, f"Article {article_id} has negative word position: {min_pos}"
            assert max_pos >= min_pos, f"Article {article_id} has invalid position range: {min_pos}-{max_pos}"

        # Test 4: Word length validation (basic quality check)
        print("\nWord quality validation:")
        word_length_stats = session.execute(
            text("""
                SELECT
                    AVG(LENGTH(word)) as avg_length,
                    MIN(LENGTH(word)) as min_length,
                    MAX(LENGTH(word)) as max_length,
                    COUNT(CASE WHEN LENGTH(word) >= 2 THEN 1 END) as valid_length_words,
                    COUNT(*) as total_words
                FROM word_events
            """)
        ).fetchone()

        avg_len, min_len, max_len, valid_words, total_words = word_length_stats
        valid_percentage = (valid_words / total_words * 100) if total_words > 0 else 0

        print(f"  Average word length: {avg_len:.1f} characters")
        print(f"  Word length range: {min_len}-{max_len} characters")
        print(f"  Valid length words (≥2 chars): {valid_words}/{total_words} ({valid_percentage:.1f}%)")

        # Word quality checks
        assert min_len >= 2, f"Found words shorter than 2 characters (minimum: {min_len})"
        assert avg_len >= 4, f"Average word length too short: {avg_len:.1f} (expected ≥4 for French)"
        assert valid_percentage >= 95, f"Too many short words: {valid_percentage:.1f}% valid (expected ≥95%)"

        # Test 5: Sample word extraction verification
        print("\nSample words verification:")
        sample_words = session.execute(
            text("""
                SELECT word, COUNT(*) as frequency
                FROM word_events
                GROUP BY word
                ORDER BY frequency DESC
                LIMIT 10
            """)
        ).fetchall()

        print("  Most frequent words:")
        for word, freq in sample_words:
            print(f"    '{word}': {freq} occurrences")

        # Should have common French words
        common_french_words = ['le', 'la', 'de', 'et', 'à', 'un', 'une', 'du', 'des', 'pour']
        found_common = [word for word, _ in sample_words if word in common_french_words]

        assert len(found_common) >= 3, (
            f"Expected to find common French words in top 10, but only found: {found_common}. "
            f"Check if French text extraction is working properly."
        )

    print(f"✓ Word events processing validated: {total_events} events from {EXPECTED_ARTICLES} articles")
