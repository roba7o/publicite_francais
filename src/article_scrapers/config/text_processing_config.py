SITE_CONFIGS = {
    'slate.fr': {
        'additional_stopwords': {'slate', 'article', 'lire', 'aussi', 'voir', 'copyright'},
        'min_word_frequency': 2,
        'min_word_length': 4,
        'max_word_length': 30
    },
    'franceinfo.fr': {
        'additional_stopwords': {'franceinfo', 'article', 'abonnés', 'premium'},
        'min_word_frequency': 1,
        'min_word_length': 3,
        'max_word_length': 25
    },
    'default': {
        'additional_stopwords': set(),
        'min_word_frequency': 2,
        'min_word_length': 3,
        'max_word_length': 50
    }
}