#!/usr/bin/env python3
"""
Independent word counter for test fixtures.

Uses trafilatura to extract text and count French words,
providing ground truth for validating WordExtractor service.
"""

import re
from pathlib import Path

import trafilatura


def count_words_in_file(filepath: Path) -> dict:
    """Extract and count French words from a single file."""
    # Read file content
    html_content = filepath.read_text(encoding='utf-8')

    # Extract text using trafilatura
    extracted_text = trafilatura.extract(html_content)

    if not extracted_text:
        return {
            'file': filepath.name,
            'site': filepath.parent.name,
            'word_count': 0,
            'extraction_failed': True
        }

    # French word pattern (same as WordExtractor)
    french_word_pattern = re.compile(
        r"\b[a-zA-ZàâäçéèêëïîôöùûüÿñæœÀÂÄÇÉÈÊËÏÎÔÖÙÛÜŸÑÆŒ''-]+\b"
    )

    # Extract and normalize words (lowercase)
    words = french_word_pattern.findall(extracted_text.lower())

    return {
        'file': filepath.name,
        'site': filepath.parent.name,
        'word_count': len(words),
        'extraction_failed': False,
        'sample_words': words[:10]  # First 10 words for debugging
    }


def main():
    """Process all test fixture files and report word counts."""
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "test_html"

    if not fixtures_dir.exists():
        print(f"Error: Fixtures directory not found: {fixtures_dir}")
        return

    # Find all HTML and PHP files
    files = sorted(fixtures_dir.rglob("*.html")) + sorted(fixtures_dir.rglob("*.php"))

    if not files:
        print(f"No HTML/PHP files found in {fixtures_dir}")
        return

    print(f"Processing {len(files)} fixture files...\n")

    total_words = 0
    site_counts = {}
    results = []

    for filepath in files:
        result = count_words_in_file(filepath)
        results.append(result)

        # Aggregate by site
        site = result['site']
        if site not in site_counts:
            site_counts[site] = {'files': 0, 'words': 0}

        site_counts[site]['files'] += 1
        site_counts[site]['words'] += result['word_count']
        total_words += result['word_count']

    # Print detailed results
    print("=" * 60)
    print("WORD COUNTS BY FILE")
    print("=" * 60)

    for result in results:
        status = "FAILED" if result['extraction_failed'] else "OK"
        print(f"\n{result['site']}/{result['file']}: {result['word_count']} words [{status}]")
        if not result['extraction_failed'] and result['sample_words']:
            print(f"  Sample: {', '.join(result['sample_words'][:5])}...")

    # Print summary by site
    print("\n" + "=" * 60)
    print("SUMMARY BY SITE")
    print("=" * 60)

    for site in sorted(site_counts.keys()):
        counts = site_counts[site]
        avg_words = counts['words'] / counts['files'] if counts['files'] > 0 else 0
        print(f"\n{site}:")
        print(f"  Files: {counts['files']}")
        print(f"  Total words: {counts['words']}")
        print(f"  Avg words/file: {avg_words:.1f}")

    # Print overall summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    print(f"\nTotal files processed: {len(files)}")
    print(f"Total words extracted: {total_words}")
    print(f"Average words per file: {total_words / len(files):.1f}")

    # Suggested test assertions
    print("\n" + "=" * 60)
    print("SUGGESTED TEST ASSERTIONS")
    print("=" * 60)
    print(f"""
# Based on static fixture analysis:
EXPECTED_TOTAL_WORDS = {total_words}
EXPECTED_FILES = {len(files)}
EXPECTED_SITES = {len(site_counts)}

# Per-site expectations:
EXPECTED_SITE_WORDS = {{
{chr(10).join(f'    "{site}": {counts["words"]},' for site, counts in sorted(site_counts.items()))}
}}
""")


if __name__ == "__main__":
    main()
