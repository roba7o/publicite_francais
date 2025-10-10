"""
E2E Test: Complete Word Extraction Pipeline

Single comprehensive test that runs the full pipeline once and validates:
- Articles are stored
- Words are extracted
- Data integrity is maintained
"""

import subprocess

import pytest
from sqlalchemy import text

from database.database import get_session


# Expected word counts per article (from static fixtures)
# Each tuple: (url_pattern, expected_count, tolerance_pct)
EXPECTED_WORD_COUNTS = [
    ("creation-d-un-etat-de-nouvelle-caledonie", 1014, 5),
    ("elisabeth-borne-recadre-son-ministre", 428, 5),
    ("infographie-de-32-milliards-en-2017", 486, 5),
    ("nouvelle-caledonie-une-majorite-de-la-classe", 572, 5),
    ("canada-quelque-chose-mysterieux-tue-grands-requins", 539, 5),
    ("civilisation-alien-vacarme-radar-aeroport", 529, 5),
    ("europe-dissuasion-nuclaire-russie-angleterre", 518, 5),
    ("regle-baillon-mondial-trump-entraver-acces", 496, 5),
    ("comment-investir-son-argent-avec-un-cashback", 839, 5),
    ("les-astuces-pour-eviter-les-arnaques-en-ligne", 217, 5),
    ("pas-d-armement-offensif-francois-bayrou", 231, 5),
    ("vous-voulez-savoir-si-quelqu-un-vous-ment", 471, 5),
    ("fendez-jusqua-100-buches-par-heure", 478, 5),
    ("icone-de-la-tendance-cette-paire-de-nike", 434, 5),
    ("intemperies-dans-le-lot-des-fils-electriques", 211, 5),
    ("tyrolienne-au-dessus-du-lot-2-km-de-cordes", 619, 5),
]


def within_tolerance(actual: int, expected: int, tolerance_pct: float) -> bool:
    """Check if actual value is within tolerance percentage of expected."""
    tolerance = expected * (tolerance_pct / 100.0)
    return expected - tolerance <= actual <= expected + tolerance


def test_complete_word_extraction_pipeline(clean_test_db):
    """
    Test complete pipeline: HTML fixtures → dim_articles + word_facts.

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
            text("SELECT COUNT(*) FROM dim_articles")
        ).scalar()
        assert article_count >= 16, f"Expected >= 16 articles, got {article_count}"
        print(f"✓ Articles stored: {article_count}")

        # 2. Verify total words extracted
        total_word_count = session.execute(
            text("SELECT COUNT(*) FROM word_facts")
        ).scalar()
        assert total_word_count is not None
        expected_total = 8082
        assert within_tolerance(total_word_count, expected_total, 5), (
            f"Expected ~{expected_total} words (±5%), got {total_word_count}"
        )
        print(
            f"✓ Total words extracted: {total_word_count} (expected: {expected_total} ±5%)"
        )

        # 3. Verify word count per article
        failed_assertions = []
        for url_pattern, expected_count, tolerance_pct in EXPECTED_WORD_COUNTS:
            result = session.execute(
                text("""
                    SELECT da.url, COUNT(wf.id) as word_count
                    FROM dim_articles da
                    LEFT JOIN word_facts wf ON wf.article_id = da.id
                    WHERE da.url LIKE :pattern
                    GROUP BY da.url
                """),
                {"pattern": f"%{url_pattern}%"},
            ).fetchone()

            if result is None:
                failed_assertions.append(f"Article not found: {url_pattern}")
                continue

            url, actual_count = result

            if not within_tolerance(actual_count, expected_count, tolerance_pct):
                tolerance = expected_count * (tolerance_pct / 100.0)
                min_count = int(expected_count - tolerance)
                max_count = int(expected_count + tolerance)
                failed_assertions.append(
                    f"{url_pattern}: {actual_count} not in range [{min_count}, {max_count}]"
                )

        if failed_assertions:
            pytest.fail("\n".join(["Word count mismatches:"] + failed_assertions))

        print(
            f"✓ All {len(EXPECTED_WORD_COUNTS)} articles have correct word counts (±5%)"
        )

        # 4. Verify French words present (no filtering)
        french_words = ["le", "la", "de", "et"]
        for word in french_words:
            count = session.execute(
                text("SELECT COUNT(*) FROM word_facts WHERE word = :word"),
                {"word": word},
            ).scalar()
            assert count > 0, f"Common French word '{word}' not found"
        print(f"✓ French words detected: {french_words}")

        # 5. Verify foreign key integrity
        orphaned = session.execute(
            text("""
                SELECT COUNT(*)
                FROM word_facts wf
                LEFT JOIN dim_articles da ON wf.article_id = da.id
                WHERE da.id IS NULL
            """)
        ).scalar()
        assert orphaned == 0, f"Found {orphaned} orphaned word_facts"
        print("✓ Foreign key integrity verified")

        # 6. Verify star schema join works
        result = session.execute(
            text("""
                SELECT da.site, wf.word, COUNT(*) as frequency
                FROM word_facts wf
                JOIN dim_articles da ON wf.article_id = da.id
                WHERE wf.word = 'le'
                GROUP BY da.site, wf.word
                ORDER BY frequency DESC
                LIMIT 1
            """)
        ).fetchone()
        assert result is not None, "Star schema join failed"
        print(
            f"✓ Star schema join works: {result[0]} has '{result[1]}' {result[2]} times"
        )

    print("✓ Complete E2E pipeline test passed")
