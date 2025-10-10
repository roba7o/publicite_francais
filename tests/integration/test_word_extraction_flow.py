"""
Integration test for word extraction flow.

Tests the complete flow: RawArticle → WordExtractor → WordFacts → Database
This is faster than E2E tests and provides quick feedback on word extraction logic.
"""

from sqlalchemy import text

from database.database import store_article, store_word_facts_batch, get_session
from database.models import RawArticle
from services.word_extractor import WordExtractor


def test_word_extraction_and_storage_flow(clean_test_db):
    """Test complete flow: RawArticle → WordExtractor → WordFacts → Database."""
    # 1. Create sample article with French content
    article = RawArticle(
        url="https://test.fr/article",
        raw_html="<html><body><p>Le chat mange une pomme rouge.</p></body></html>",
        site="test.fr",
    )

    # 2. Store article in database
    result = store_article(article)
    assert result, "Failed to store article"

    # 3. Extract words using WordExtractor
    extractor = WordExtractor()
    word_facts = extractor.extract_words_from_article(article)

    # Verify words were extracted
    assert len(word_facts) > 0, "No words extracted"
    assert len(word_facts) == 6, f"Expected 6 words, got {len(word_facts)}"

    # Verify word content (lowercase, normalized)
    extracted_words = [wf.word for wf in word_facts]
    assert extracted_words == ["le", "chat", "mange", "une", "pomme", "rouge"]

    # Verify positions are sequential
    for i, wf in enumerate(word_facts):
        assert wf.position_in_article == i, f"Word {i} has wrong position"
        assert wf.article_id == article.id, f"Word {i} has wrong article_id"

    # 4. Store word facts in database
    stored, failed = store_word_facts_batch(word_facts)
    assert stored == len(word_facts), f"Expected {len(word_facts)} stored, got {stored}"
    assert failed == 0, f"Expected 0 failed, got {failed}"

    # 5. Verify in database using SQL queries
    with get_session() as session:
        # Check word count for this article
        count = session.execute(
            text("SELECT COUNT(*) FROM word_facts WHERE article_id = :id"),
            {"id": article.id},
        ).scalar()
        assert count == 6, f"Expected 6 words in database, got {count}"

        # Verify specific words exist
        for expected_word in ["le", "chat", "pomme"]:
            word_count = session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM word_facts
                    WHERE article_id = :id AND word = :word
                """
                ),
                {"id": article.id, "word": expected_word},
            ).scalar()
            assert word_count == 1, f"Word '{expected_word}' not found in database"

        # Verify star schema join works
        result = session.execute(
            text(
                """
                SELECT da.url, wf.word, wf.position_in_article
                FROM word_facts wf
                JOIN dim_articles da ON wf.article_id = da.id
                WHERE da.id = :id
                ORDER BY wf.position_in_article
            """
            ),
            {"id": article.id},
        ).fetchall()

        assert len(result) == 6, "Star schema join returned wrong count"
        assert result[0][1] == "le", "First word should be 'le'"
        assert result[5][1] == "rouge", "Last word should be 'rouge'"


def test_word_extraction_with_complex_html(clean_test_db):
    """Test word extraction handles complex HTML with multiple paragraphs."""
    # Article with multiple paragraphs and mixed content
    article = RawArticle(
        url="https://test.fr/complex",
        raw_html="""
        <html>
            <body>
                <h1>Titre de l'article</h1>
                <p>Premier paragraphe avec des mots.</p>
                <div>
                    <p>Deuxième paragraphe.</p>
                </div>
            </body>
        </html>
        """,
        site="test.fr",
    )

    # Store article
    assert store_article(article)

    # Extract words
    extractor = WordExtractor()
    word_facts = extractor.extract_words_from_article(article)

    # Should extract words from all text content
    assert len(word_facts) >= 10, "Should extract words from entire HTML"

    # Store and verify
    stored, failed = store_word_facts_batch(word_facts)
    assert stored == len(word_facts)
    assert failed == 0

    with get_session() as session:
        # Verify all words are linked to correct article
        orphaned = session.execute(
            text(
                """
                SELECT COUNT(*) FROM word_facts
                WHERE article_id = :id AND scraped_at IS NULL
            """
            ),
            {"id": article.id},
        ).scalar()
        assert orphaned == 0, "All word_facts should have scraped_at timestamp"


def test_word_extraction_empty_content(clean_test_db):
    """Test word extraction handles HTML with no extractable text."""
    # Article with only images/scripts, no readable text
    article = RawArticle(
        url="https://test.fr/empty",
        raw_html="<html><body><img src='test.jpg'/><script>alert('test');</script></body></html>",
        site="test.fr",
    )

    # Store article
    assert store_article(article)

    # Extract words - should return empty list
    extractor = WordExtractor()
    word_facts = extractor.extract_words_from_article(article)

    assert len(word_facts) == 0, "Should extract 0 words from content-less HTML"

    # Store should succeed even with empty list
    stored, failed = store_word_facts_batch(word_facts)
    assert stored == 0
    assert failed == 0


def test_word_extraction_preserves_french_characters(clean_test_db):
    """Test that French accented characters are preserved in word extraction."""
    article = RawArticle(
        url="https://test.fr/accents",
        raw_html="<html><body><p>Un élève français étudie avec passion.</p></body></html>",
        site="test.fr",
    )

    # Store article
    assert store_article(article)

    # Extract words
    extractor = WordExtractor()
    word_facts = extractor.extract_words_from_article(article)

    # Verify accented words are preserved (lowercase)
    extracted_words = [wf.word for wf in word_facts]
    assert "élève" in extracted_words, "Should preserve 'élève' with accent"
    assert "français" in extracted_words, "Should preserve 'français' with ç"
    assert "étudie" in extracted_words, "Should preserve 'étudie' with accent"

    # Store and verify
    stored, failed = store_word_facts_batch(word_facts)
    assert stored == len(word_facts)
    assert failed == 0

    # Verify in database
    with get_session() as session:
        for word in ["élève", "français", "étudie"]:
            count = session.execute(
                text("SELECT COUNT(*) FROM word_facts WHERE word = :word"),
                {"word": word},
            ).scalar()
            assert count > 0, f"Accented word '{word}' should be in database"
