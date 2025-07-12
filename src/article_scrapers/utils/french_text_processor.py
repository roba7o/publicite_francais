import re
import unicodedata
from collections import Counter
from typing import Dict, List, Set

class FrenchTextProcessor:
    """
    Enhanced text processor for French articles with proper cleaning,
    normalization, tokenization, and stopword filtering,
    specifically addressing contractions like 'l'eau' to filter 'l'' if needed.
    """

    def __init__(self):
        # A more comprehensive list of common French stopwords, including
        # articles and pronouns, both full and contracted forms.
        self.french_stopwords = {
            'a', 'ai', 'aie', 'aient', 'aies', 'ait', 'alors', 'an', 'ans', 'apres',
            'apres-midi', 'arret', 'au', 'aucun', 'aucune', 'aujourd', 'aujourd-hui',
            'aupres', 'aura', 'aurai', 'auraient', 'aurais', 'aurait', 'auras', 'aurez',
            'auriez', 'aurions', 'aurons', 'auront', 'aussi', 'autour', 'autre', 'autres',
            'aux', 'avaient', 'avais', 'avait', 'avant', 'avec', 'avez', 'aviez', 'avions',
            'avons', 'ayant', 'ayez', 'ayons', 'b', 'bah', 'bas', 'bon', 'bonne', 'c',
            'ca', 'car', 'ce', 'ceci', 'cela', 'celle', 'celles', 'celui', 'cent',
            'cependant', 'certain', 'certaine', 'certaines', 'certains', 'ces', 'cet',
            'cette', 'ceux', 'chaque', 'cher', 'chere', 'cheres', 'chers', 'chez',
            'chose', 'choses', 'ci', 'cinq', 'cinquantaine', 'cinquante', 'cinquantieme',
            'cités', 'd', 'dans', 'de', 'debout', 'dedans', 'dehors', 'deja', 'delà',
            'depuis', 'derriere', 'des', 'desormais', 'deux', 'devant', 'devers', 'devra',
            'devrait', 'did', 'differentes', 'differents', 'dire', 'divers', 'diverses',
            'dix', 'dizaine', 'donc', 'dont', 'douze', 'douzieme', 'droit', 'du', 'duquel',
            'e', 'elle', 'elles', 'en', 'encore', 'entre', 'envers', 'environ', 'est',
            'et', 'etaient', 'etais', 'etait', 'etant', 'etc', 'ete', 'etes', 'etiez',
            'etions', 'etre', 'eu', 'eue', 'eues', 'euh', 'eurent', 'eus', 'eusse',
            'eussent', 'eusses', 'eussiez', 'eussions', 'eut', 'eux', 'exactement', 'fais',
            'faisaient', 'faisait', 'faisant', 'fait', 'faites', 'faudra', 'faut',
            'faut-il', 'felicitation', 'fidele', 'fière', 'fières', 'fiers', 'fois',
            'font', 'force', 'g', 'gens', 'grace', 'grand', 'gros', 'guere', 'h', 'ha',
            'haut', 'hein', 'hem', 'hep', 'heureusement', 'heu', 'hier', 'hiers', 'ho',
            'hola', 'holà', 'hop', 'hormis', 'hors', 'huit', 'huitieme', 'hum', 'i', 'ici',
            'il', 'ils', 'j', 'ja', 'jamais', 'je', 'jusqu', 'jusque', 'k', 'l', 'la',
            'là', 'le', 'les', 'lesquelles', 'lesquels', 'leur', 'leurs', 'longtemps',
            'lors', 'lorsque', 'lui', 'm', 'ma', 'maintenant', 'mais', 'malgre', 'me',
            'meme', 'memes', 'merci', 'mes', 'mille', 'mince', 'moi', 'moins', 'mon',
            'mot', 'moyennant', 'n', 'ne', 'neuf', 'neuvieme', 'ni', 'nombreuses',
            'nombreux', 'non', 'nos', 'notre', 'nous', 'nouveau', 'nul', 'o', 'oh',
            'ohe', 'on', 'ont', 'onze', 'onzieme', 'ore', 'ou', 'où', 'outre', 'p', 'par',
            'parce', 'parmi', 'partant', 'pas', 'passé', 'pendant', 'peut', 'peuvent',
            'peu', 'peut-être', 'plus', 'plusieurs', 'plutot', 'point', 'pour', 'pourquoi',
            'premier', 'première', 'premièrement', 'pres', 'presque', 'preuve', 'probablement',
            'puisque', 'q', 'qu', 'quand', 'quant', 'quarante', 'quatrieme', 'que',
            'quel', 'quelle', 'quelles', 'quels', 'qui', 'quiconque', 'quinze', 'quoi',
            'quoique', 'r', 'rare', 'rarement', 's', 'sa', 'sans', 'se', 'selon', 'sens',
            'sept', 'septieme', 'sera', 'serai', 'seraient', 'serais', 'serait', 'seras',
            'serez', 'seriez', 'serions', 'serons', 'seront', 'ses', 'seul', 'seule',
            'seulement', 'si', 'sien', 'sienne', 'siennes', 'siens', 'sitôt', 'six',
            'sixieme', 'soi', 'soient', 'sois', 'soit', 'sommes', 'son', 'sont', 'sous',
            'souvent', 'specifique', 'specifiques', 'st', 'suis', 'suite', 'sur', 't', 'ta',
            'tandis', 'tant', 'tantôt', 'tard', 'te', 'tel', 'telle', 'telles', 'tels',
            'tenant', 'tend', 'tenir', 'termes', 'tes', 'toi', 'ton', 'tous', 'tout',
            'toute', 'toutes', 'treize', 'trente', 'tres', 'trois', 'troisieme', 'u', 'un',
            'une', 'unes', 'uns', 'v', 'va', 'vais', 'valeur', 'vas', 'vers', 'via',
            'vingt', 'voici', 'voila', 'voir', 'voire', 'vous', 'voulez', 'vous', 'votre',
            'vôtres', 'vos', 'x', 'y', 'z', 'zero'
        }
        # Convert to set for O(1) average time complexity for lookups
        self.french_stopwords = set(self.french_stopwords)

        # Common French contracted articles/pronouns to strip
        self.french_contractions_prefixes = {'l\'', 'd\'', 'qu\'', 'm\'', 't\'', 's\'', 'n\'', 'j\'', 'c\''}

        # Minimum word length to consider
        self.min_word_length = 3

        # Maximum word length (to filter out very long strings that might be URLs, etc.)
        self.max_word_length = 50

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize French text.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Normalize unicode characters to their closest ASCII equivalents where possible,
        # then re-compose to handle combined characters correctly.
        # This helps with characters like 'é' vs 'e' + accent mark.
        text = unicodedata.normalize('NFC', text)
        # Remove common French specific non-breaking spaces if present
        text = text.replace('\xa0', ' ') # non-breaking space

        # Convert to lowercase early for consistent processing
        text = text.lower()

        # Remove URLs
        text = re.sub(r'https?://[^\s]+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Remove numbers (optional - uncomment if you want to remove numbers)
        # text = re.sub(r'\d+', '', text)

        # Replace hyphens with spaces for multi-word expressions like "peut-être"
        # but be careful not to split hyphenated names if they are important
        text = text.replace('-', ' ')

        # Remove punctuation. Keep apostrophes for now, we'll handle them later.
        # This regex keeps letters, numbers (if not removed above), and apostrophes
        text = re.sub(r"[^\w\s']", '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def tokenize_french_text(self, text: str) -> List[str]:
        """
        Tokenize French text into words with proper handling of French punctuation
        and intelligent stripping of leading contractions (l', d', etc.).

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        if not text:
            return []

        cleaned_text = self.clean_text(text)

        # Split by spaces. This will initially keep "l'on", "l'eau" as single tokens.
        raw_tokens = cleaned_text.split()

        filtered_tokens = []
        for token in raw_tokens:
            processed_token = token

            # Check for French contractions and strip them
            # For example, "l'eau" -> "eau"
            for prefix in self.french_contractions_prefixes:
                if processed_token.startswith(prefix):
                    base_word = processed_token[len(prefix):]
                    # If the base word exists and is not a stopword, and the original is
                    # a stopword, then use the base word. Or if the base word is more meaningful.
                    # Here we prioritize keeping the base word if it's not empty.
                    if base_word and base_word not in self.french_stopwords:
                        processed_token = base_word
                    elif base_word in self.french_stopwords:
                        processed_token = "" # Mark for removal if base word is also a stopword
                    break # Only apply one prefix removal

            if not processed_token: # Remove if marked for removal (e.g., "l'on" where "on" is a stopword)
                continue

            # Apply length limits *after* contraction stripping
            if len(processed_token) < self.min_word_length or \
               len(processed_token) > self.max_word_length:
                continue

            # Check if the processed token itself is a stopword
            if processed_token in self.french_stopwords:
                continue

            # Final check to ensure it's not just an apostrophe or remaining punctuation
            if not re.match(r"^[a-zA-Zàâäéèêëïîôöùûüÿç]+$", processed_token):
                continue

            filtered_tokens.append(processed_token)

        return filtered_tokens

    def count_word_frequency(self, text: str) -> Dict[str, int]:
        """
        Count word frequencies in French text with proper cleaning.

        Args:
            text: Text to analyze

        Returns:
            Dictionary of word frequencies
        """
        tokens = self.tokenize_french_text(text)
        return dict(Counter(tokens))

    def get_top_words(self, text: str, n: int = 50) -> List[tuple]:
        """
        Get the top N most frequent words.

        Args:
            text: Text to analyze
            n: Number of top words to return

        Returns:
            List of (word, frequency) tuples
        """
        word_freq = self.count_word_frequency(text)
        return Counter(word_freq).most_common(n)

    def filter_by_frequency(self, word_freq: Dict[str, int], min_freq: int = 2) -> Dict[str, int]:
        """
        Filter words by minimum frequency.

        Args:
            word_freq: Dictionary of word frequencies
            min_freq: Minimum frequency threshold

        Returns:
            Filtered dictionary
        """
        return {word: freq for word, freq in word_freq.items() if freq >= min_freq}

    def expand_stopwords(self, additional_stopwords: Set[str]) -> None:
        """
        Add additional stopwords to the filter list.

        Args:
            additional_stopwords: Set of additional stopwords to add
        """
        self.french_stopwords.update(additional_stopwords)

    def set_word_length_limits(self, min_length: int = 3, max_length: int = 50) -> None:
        """
        Set minimum and maximum word length limits.

        Args:
            min_length: Minimum word length
            max_length: Maximum word length
        """
        self.min_word_length = min_length
        self.max_word_length = max_length