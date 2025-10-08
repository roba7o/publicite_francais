"""
E2E Test: Complete Word Extraction Pipeline

Single comprehensive test that runs the full pipeline once and validates:
- Articles are stored
- Words are extracted  
- Data integrity is maintained
"""

import subprocess

from sqlalchemy import text

from database.database import get_session


def test_complete_word_extraction_pipeline(clean_test_db):
    """
    Test complete pipeline: HTML fixtures → raw_articles + word_facts.
    
    Runs pipeline once, then validates all critical aspects.
    """
    print("\n=== E2E: Complete Word Extraction Pipeline ===")

    # Run the pipeline once
    print("Running pipeline...")
    result = subprocess.run(
        ["make", "run-test-data"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"Pipeline failed: {result.returncode}"
    print("✓ Pipeline completed successfully")

    with get_session() as session:
        # 1. Verify articles stored
        article_count = session.execute(
            text("SELECT COUNT(*) FROM raw_articles")
        ).scalar()
        assert article_count >= 12, f"Expected >= 12 articles, got {article_count}"
        print(f"✓ Articles stored: {article_count}")

        # 2. Verify words extracted
        word_count = session.execute(
            text("SELECT COUNT(*) FROM word_facts")
        ).scalar()
        assert word_count > 0, "No words extracted"
        print(f"✓ Words extracted: {word_count}")

        # 3. Verify French words present (no filtering)
        french_words = ['le', 'la', 'de', 'et']
        for word in french_words:
            count = session.execute(
                text("SELECT COUNT(*) FROM word_facts WHERE word = :word"),
                {"word": word}
            ).scalar()
            assert count > 0, f"Common French word '{word}' not found"
        print(f"✓ French words detected: {french_words}")

        # 4. Verify foreign key integrity
        orphaned = session.execute(
            text("""
                SELECT COUNT(*)
                FROM word_facts wf
                LEFT JOIN raw_articles ra ON wf.article_id = ra.id
                WHERE ra.id IS NULL
            """)
        ).scalar()
        assert orphaned == 0, f"Found {orphaned} orphaned word_facts"
        print("✓ Foreign key integrity verified")

        # 5. Verify star schema join works
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
        print(f"✓ Star schema join works: {result[0]} has '{result[1]}' {result[2]} times")

    print("✓ Complete E2E pipeline test passed")
