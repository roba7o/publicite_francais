{{ config(materialized='table') }}

-- All words extracted with classification flags (for analytics)
select distinct
    {{ dbt_utils.generate_surrogate_key(['word_clean']) }} as word_id,
    word_clean,
    length(word_clean) as word_length,
    frequency,
    
    -- Classification flags for filtering
    case when word_clean in (
        'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'au', 'aux',
        'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'ce', 'cette', 'ces',
        'à', 'dans', 'sur', 'avec', 'sans', 'pour', 'par', 'vers', 'chez', 'entre',
        'et', 'ou', 'mais', 'donc', 'car', 'ni', 'or',
        'est', 'sont', 'était', 'étaient', 'être', 'avoir', 'a', 'ont', 'avait',
        'comme', 'aussi', 'bien', 'très', 'plus', 'moins', 'tout', 'tous', 'toute', 'toutes',
        'peu', 'beaucoup', 'encore', 'déjà', 'maintenant', 'alors',
        'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf', 'dix',
        'aujourd''hui', 'hier', 'demain', 'semaine', 'mois', 'année', 'jour',
        'ici', 'là', 'où', 'quand', 'comment', 'pourquoi', 'si', 'non', 'oui',
        'que', 'qui', 'dont', 'leur', 'leurs', 'ses', 'son', 'sa', 'votre', 'nos', 'vos',
        'mes', 'mon', 'ma', 'ta', 'tes', 'ton'
    ) then true else false end as is_stopword,
    
    case when word_clean in (
        'tre', 'ses', 'comple', 'apre', 'franc', 'cision', 'sente', 'core', 'bre', 'tait',
        'ment', 'leurs', 'dont', 'quipe', 'dote', 'serait', 'avance', 'tecter', 'ramiro',
        'caisse', 'saide', 'rentes', 'ducatif', 'suspecte', 'tention', 'provisoire', 'soupc',
        'onne', 'empreinte', 'repe', 'peut-e', 'contro', 'ricain', 'fense', 'enne', 'aire',
        'ration', 'commenc', 'ait', 'imme', 'diat', 'pre', 'potentiellement', 'jusqu',
        'selon', 'pas', 'monde', 'fait', 'peuvent', 'leur', 'prix', 'offre', 'mode',
        'impose', 'euros', 'couverture', 'simple', 'peut', 'argent', 'premier', 'certains',
        'offrent', 'rendement', 'investissement', 'payer', 'cher', 'investir', 'suivez',
        'placements', 'cashback', 'travailler', 'messages', 'involontaires', 'd''avoir',
        'mis', 'examen', 'meurtre', 'personne', 'charge', 'd''une', 'mission', 'public',
        'place', 'lors', 'd''un', 'devant', 'face', 'pourrait', 'pays', 'reste'
    ) then true else false end as is_junk_word,
    
    case when length(word_clean) < 4 then true else false end as too_short,
    case when word_clean ~ '^[0-9]+$' then true else false end as is_numeric,
    case when (length(regexp_replace(word_clean, '[0-9]', '', 'g')) / length(word_clean)::float) < 0.7 then true else false end as mostly_numeric
    
from (
    select 
        lower(trim(word)) as word_clean,
        count(*) as frequency
    from (
        select 
            unnest(string_to_array(
                regexp_replace(
                    regexp_replace(sentence_text, '<[^>]*>', '', 'g'),
                    '[^\w\sàâäçéèêëïîôûùüÿñæœÀÂÄÇÉÈÊËÏÎÔÛÙÜŸÑÆŒ''-]', ' ', 'g'
                ),
                ' '
            )) as word
        from {{ ref('sentences') }}
    ) word_splits
    where length(trim(word)) >= 1
    group by lower(trim(word))
) words

where length(word_clean) > 0
order by frequency desc