#!/usr/bin/env python3
"""
Compare word counts between trafilatura extraction and database storage.
"""

import re
from pathlib import Path

import trafilatura
from sqlalchemy import text

# Import database functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.database import get_session, initialize_database


def get_trafilatura_count(filepath: Path) -> int:
    """Extract and count French words from a file using trafilatura."""
    html_content = filepath.read_text(encoding='utf-8')
    extracted_text = trafilatura.extract(html_content)

    if not extracted_text:
        return 0

    french_word_pattern = re.compile(
        r"\b[a-zA-ZàâäçéèêëïîôöùûüÿñæœÀÂÄÇÉÈÊËÏÎÔÖÙÛÜŸÑÆŒ''-]+\b"
    )
    words = french_word_pattern.findall(extracted_text.lower())
    return len(words)


def get_database_count_by_filename(filename: str) -> int:
    """Get word count from database by matching filename pattern in URL."""
    with get_session() as session:
        # Strip extension and match partial URL
        pattern = filename.replace('.html', '').replace('.php', '')

        query = text("""
            SELECT COUNT(*)
            FROM word_facts wf
            JOIN raw_articles ra ON wf.article_id = ra.id
            WHERE ra.url LIKE :pattern
        """)
        result = session.execute(query, {"pattern": f"%{pattern}%"}).scalar()
        return result or 0


def main():
    """Compare word counts between trafilatura and database."""
    # Initialize database
    initialize_database()

    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "test_html"

    files = sorted(fixtures_dir.rglob("*.html")) + sorted(fixtures_dir.rglob("*.php"))

    print("\n" + "╔" + "═" * 98 + "╗")
    print("║" + " " * 30 + "WORD COUNT COMPARISON" + " " * 47 + "║")
    print("╠" + "═" * 98 + "╣")
    print("║ Site/File" + " " * 50 + "│ Trafilatura │ Database │ Diff  ║")
    print("╠" + "═" * 98 + "╣")

    total_trafilatura = 0
    total_database = 0

    for filepath in files:
        trafilatura_count = get_trafilatura_count(filepath)
        database_count = get_database_count_by_filename(filepath.name)

        diff = database_count - trafilatura_count
        diff_str = f"+{diff}" if diff > 0 else str(diff)

        # Format filename with site
        display_name = f"{filepath.parent.name}/{filepath.name}"

        # Truncate if too long
        if len(display_name) > 58:
            display_name = display_name[:55] + "..."

        print(f"║ {display_name:<59} │ {trafilatura_count:>12} │ {database_count:>8} │ {diff_str:>5} ║")

        total_trafilatura += trafilatura_count
        total_database += database_count

    total_diff = total_database - total_trafilatura
    total_diff_str = f"+{total_diff}" if total_diff > 0 else str(total_diff)

    print("╠" + "═" * 98 + "╣")
    print(f"║ {'TOTAL':<59} │ {total_trafilatura:>12} │ {total_database:>8} │ {total_diff_str:>5} ║")
    print("╚" + "═" * 98 + "╝")

    # Summary
    if total_diff == 0:
        print("\n✓ Perfect match! Trafilatura and database counts are identical.")
    else:
        pct_diff = (total_diff / total_trafilatura * 100) if total_trafilatura > 0 else 0
        print(f"\n⚠ Difference: {total_diff_str} words ({pct_diff:+.2f}%)")


if __name__ == "__main__":
    main()
