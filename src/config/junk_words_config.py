"""
Configuration for junk word patterns in French text processing.

This module contains patterns and words that should be filtered out during
French text analysis. These include truncated words, common fragments,
overly generic terms, and parsing artifacts that aren't useful for
vocabulary learning or analysis.

Categories:
- TRUNCATED_WORDS: Incomplete words commonly found in scraped content
- GENERIC_WORDS: Overly common words with little learning value
- PARSING_ARTIFACTS: Words resulting from HTML parsing errors
- NUMERIC_PATTERNS: Number-heavy or date-related fragments
"""

# Truncated or incomplete words commonly found in scraped French content
TRUNCATED_WORDS = {
    "tre",
    "ses",
    "comple",
    "apre",
    "franc",
    "cision",
    "sente",
    "core",
    "bre",
    "tait",
    "ment",
    "leurs",
    "dont",
    "quipe",
    "dote",
    "serait",
    "avance",
    "tecter",
    "ramiro",
    "caisse",
    "saide",
    "rentes",
    "ducatif",
    "suspecte",
    "tention",
    "provisoire",
    "soupc",
    "onne",
    "empreinte",
    "repe",
    "peut-e",
    "contro",
    "ricain",
    "fense",
    "enne",
    "aire",
    "ration",
    "commenc",
    "ait",
    "imme",
    "diat",
    "pre",
    "potentiellement",
    "jusqu",
}

# Generic French words that are too common for vocabulary learning
GENERIC_WORDS = {
    "selon",
    "qui",
    "que",
    "pas",
    "monde",
    "fait",
    "peuvent",
    "leur",
    "prix",
    "offre",
    "mode",
    "impose",
    "euros",
    "dont",
    "couverture",
    "simple",
    "peut",
    "ses",
    "sente",
    "ment",
    "leurs",
    "votre",
    "argent",
    "premier",
    "certains",
    "offrent",
    "rendement",
    "investissement",
    "payer",
    "cher",
    "investir",
    "suivez",
    "placements",
    "cashback",
    "travailler",
}

# Words that commonly result from HTML parsing artifacts
PARSING_ARTIFACTS = {
    "messages",
    "involontaires",
    "d'avoir",
    "mis",
    "examen",
    "meurtre",
    "personne",
    "charge",
    "d'une",
    "mission",
    "public",
    "place",
    "lors",
    "d'un",
    "devant",
    "oise-dolto",
    "nucle",
    "aires",
    "bombe",
    "europe",
    "continent",
    "l'europe",
    "l'arsenal",
    "face",
    "pourrait",
    "pays",
    "l'uranium",
    "missiles",
    "londres",
    "l'allemagne",
    "politique",
    "france",
    "royaume-uni",
    "renforcement",
    "reste",
}

# Location and proper noun fragments
LOCATION_FRAGMENTS = {
    "france",
    "europe",
    "londres",
    "royaume-uni",
    "l'allemagne",
    "continent",
    "l'europe",
    "nucle",
    "aires",
    "politique",
}

# Financial and investment-related generic terms
FINANCIAL_TERMS = {
    "euros",
    "prix",
    "argent",
    "investissement",
    "placements",
    "rendement",
    "cashback",
    "payer",
    "cher",
    "investir",
    "offre",
    "offrent",
}

# Verb forms that are too common
COMMON_VERB_FORMS = {
    "tait",
    "serait",
    "peuvent",
    "offrent",
    "commenc",
    "ait",
    "dote",
    "pourrait",
    "travailler",
}

# Adjectives and adverbs that are overly generic
GENERIC_DESCRIPTORS = {
    "simple",
    "comple",
    "certains",
    "potentiellement",
    "imme",
    "diat",
    "premier",
    "reste",
}

# All junk patterns combined for easy access
ALL_JUNK_PATTERNS = (
    TRUNCATED_WORDS
    | GENERIC_WORDS
    | PARSING_ARTIFACTS
    | LOCATION_FRAGMENTS
    | FINANCIAL_TERMS
    | COMMON_VERB_FORMS
    | GENERIC_DESCRIPTORS
)


def get_junk_patterns() -> set:
    """
    Get the complete set of junk word patterns.

    Returns:
        Set of all junk word patterns to be filtered out
    """
    return ALL_JUNK_PATTERNS


def get_category_patterns(category: str) -> set:
    """
    Get junk patterns for a specific category.

    Args:
        category: One of 'truncated', 'generic', 'artifacts', 'locations',
                 'financial', 'verbs', 'descriptors'

    Returns:
        Set of patterns for the specified category

    Raises:
        KeyError: If category is not recognized
    """
    categories = {
        "truncated": TRUNCATED_WORDS,
        "generic": GENERIC_WORDS,
        "artifacts": PARSING_ARTIFACTS,
        "locations": LOCATION_FRAGMENTS,
        "financial": FINANCIAL_TERMS,
        "verbs": COMMON_VERB_FORMS,
        "descriptors": GENERIC_DESCRIPTORS,
    }

    if category not in categories:
        raise KeyError(
            f"Unknown category: {category}. Available: {list(categories.keys())}"
        )

    return categories[category]


def is_junk_word(word: str) -> bool:
    """
    Check if a word should be considered junk and filtered out.

    Args:
        word: Word to check

    Returns:
        True if the word is in the junk patterns, False otherwise
    """
    return word.lower().strip() in ALL_JUNK_PATTERNS
