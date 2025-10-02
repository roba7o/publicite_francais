-- Migration 004: Add simple stop words reference table
-- Clean SQL - executed via Python migration runner
-- Creates a clean reference table for French stop words lookup

-- Create stop words table
CREATE TABLE IF NOT EXISTS stop_words (
    word TEXT PRIMARY KEY,
    language VARCHAR(10) DEFAULT 'fr',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Populate with French stop words (from dbt/resources/french-stop-words.txt)
INSERT INTO stop_words (word, language) VALUES
('a', 'fr'), ('an', 'fr'), ('and', 'fr'), ('are', 'fr'), ('as', 'fr'), ('at', 'fr'),
('be', 'fr'), ('but', 'fr'), ('by', 'fr'), ('for', 'fr'), ('if', 'fr'), ('in', 'fr'),
('into', 'fr'), ('is', 'fr'), ('it', 'fr'), ('no', 'fr'), ('not', 'fr'), ('of', 'fr'),
('on', 'fr'), ('or', 'fr'), ('s', 'fr'), ('such', 'fr'), ('t', 'fr'), ('that', 'fr'),
('the', 'fr'), ('their', 'fr'), ('then', 'fr'), ('there', 'fr'), ('these', 'fr'),
('they', 'fr'), ('this', 'fr'), ('to', 'fr'), ('was', 'fr'), ('will', 'fr'), ('with', 'fr'),
('au', 'fr'), ('aux', 'fr'), ('avec', 'fr'), ('ce', 'fr'), ('ces', 'fr'), ('dans', 'fr'),
('de', 'fr'), ('des', 'fr'), ('du', 'fr'), ('elle', 'fr'), ('en', 'fr'), ('et', 'fr'),
('eux', 'fr'), ('il', 'fr'), ('je', 'fr'), ('la', 'fr'), ('le', 'fr'), ('leur', 'fr'),
('lui', 'fr'), ('ma', 'fr'), ('mais', 'fr'), ('me', 'fr'), ('même', 'fr'), ('mes', 'fr'),
('moi', 'fr'), ('mon', 'fr'), ('ne', 'fr'), ('nos', 'fr'), ('notre', 'fr'), ('nous', 'fr'),
('on', 'fr'), ('ou', 'fr'), ('par', 'fr'), ('pas', 'fr'), ('pour', 'fr'), ('qu', 'fr'),
('que', 'fr'), ('qui', 'fr'), ('sa', 'fr'), ('se', 'fr'), ('ses', 'fr'), ('son', 'fr'),
('sur', 'fr'), ('ta', 'fr'), ('te', 'fr'), ('tes', 'fr'), ('toi', 'fr'), ('ton', 'fr'),
('tu', 'fr'), ('un', 'fr'), ('une', 'fr'), ('vos', 'fr'), ('votre', 'fr'), ('vous', 'fr'),
('c', 'fr'), ('d', 'fr'), ('j', 'fr'), ('l', 'fr'), ('à', 'fr'), ('m', 'fr'),
('n', 'fr'), ('y', 'fr'), ('été', 'fr'), ('étée', 'fr'), ('étées', 'fr'), ('étés', 'fr'),
('étant', 'fr'), ('suis', 'fr'), ('es', 'fr'), ('est', 'fr'), ('sommes', 'fr'),
('êtes', 'fr'), ('sont', 'fr'), ('serai', 'fr'), ('seras', 'fr'), ('sera', 'fr'),
('serons', 'fr'), ('serez', 'fr'), ('seront', 'fr'), ('serais', 'fr'), ('serait', 'fr'),
('serions', 'fr'), ('seriez', 'fr'), ('seraient', 'fr'), ('étais', 'fr'), ('était', 'fr'),
('étions', 'fr'), ('étiez', 'fr'), ('étaient', 'fr'), ('fus', 'fr'), ('fut', 'fr'),
('fûmes', 'fr'), ('fûtes', 'fr'), ('furent', 'fr'), ('sois', 'fr'), ('soit', 'fr'),
('soyons', 'fr'), ('soyez', 'fr'), ('soient', 'fr'), ('fusse', 'fr'), ('fusses', 'fr'),
('fût', 'fr'), ('fussions', 'fr'), ('fussiez', 'fr'), ('fussent', 'fr'), ('ayant', 'fr'),
('eu', 'fr'), ('eue', 'fr'), ('eues', 'fr'), ('eus', 'fr'), ('ai', 'fr'), ('as', 'fr'),
('avons', 'fr'), ('avez', 'fr'), ('ont', 'fr'), ('aurai', 'fr'), ('auras', 'fr'),
('aura', 'fr'), ('aurons', 'fr'), ('aurez', 'fr'), ('auront', 'fr'), ('aurais', 'fr'),
('aurait', 'fr'), ('aurions', 'fr'), ('auriez', 'fr'), ('auraient', 'fr'), ('avais', 'fr'),
('avait', 'fr'), ('avions', 'fr'), ('aviez', 'fr'), ('avaient', 'fr'), ('eut', 'fr'),
('eûmes', 'fr'), ('eûtes', 'fr'), ('eurent', 'fr'), ('aie', 'fr'), ('aies', 'fr'),
('ait', 'fr'), ('ayons', 'fr'), ('ayez', 'fr'), ('aient', 'fr'), ('eusse', 'fr'),
('eusses', 'fr'), ('eût', 'fr'), ('eussions', 'fr'), ('eussiez', 'fr'), ('eussent', 'fr'),
('ceci', 'fr'), ('celà', 'fr'), ('cet', 'fr'), ('cette', 'fr'), ('ici', 'fr'), ('ils', 'fr'),
('les', 'fr'), ('leurs', 'fr'), ('quel', 'fr'), ('quels', 'fr'), ('quelle', 'fr'),
('quelles', 'fr'), ('sans', 'fr'), ('soi', 'fr')
ON CONFLICT (word) DO NOTHING;

-- Create index for fast word lookup
CREATE INDEX IF NOT EXISTS idx_stop_words_word ON stop_words(word);