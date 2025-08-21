"""
URL mapping configuration for test data.

This file maps test filenames to their original URLs for offline mode.

this could be fixed urls but we do not have control of the websites ability to change URLs.
This allows us to simulate real-world scenarios without needing live internet access.

"""

# Map of filename for path -> original URL for each test file
URL_MAPPING = {
    # Slate.fr test files
    (
        "regle-baillon-mondial-trump-entraver-acces-avortement-mexico-city-"
        "policy-anti-ivg-dangers-mort-femmes-deces-grossesse.html"
    ): (
        "https://www.slate.fr/monde/regle-baillon-mondial-trump-entraver-"
        "acces-avortement-mexico-city-policy-anti-ivg-dangers-mort-femmes-"
        "deces-grossesse"
    ),
    (
        "canada-quelque-chose-mysterieux-tue-grands-requins-blancs-cerveau-"
        "inflammation-maladie-autopsie-deces-mort-scientifiques.html"
    ): (
        "https://www.slate.fr/monde/canada-quelque-chose-mysterieux-tue-"
        "grands-requins-blancs-cerveau-inflammation-maladie-autopsie-deces-"
        "mort-scientifiques"
    ),
    (
        "europe-dissuasion-nuclaire-russie-angleterre-france-uranium-"
        "poutine-otan-arsenal.html"
    ): (
        "https://www.slate.fr/monde/europe-dissuasion-nuclaire-russie-"
        "angleterre-france-uranium-poutine-otan-arsenal"
    ),
    (
        "civilisation-alien-vacarme-radar-aeroport-signaux-espace-annees-"
        "lumieres-galaxie-technologie.html"
    ): (
        "https://www.slate.fr/sciences/civilisation-alien-vacarme-radar-"
        "aeroport-signaux-espace-annees-lumieres-galaxie-technologie"
    ),
    # La Dépêche test files
    (
        "intemperies-dans-le-lot-des-fils-electriques-sont-tombes-au-sol-"
        "une-route-est-coupee-12822614.php"
    ): (
        "https://www.ladepeche.fr/2025/07/12/intemperies-dans-le-lot-des-"
        "fils-electriques-sont-tombes-au-sol-une-route-est-coupee-12822614.php"
    ),
    (
        "tyrolienne-au-dessus-du-lot-2-km-de-cordes-tendues-pour-un-saut-"
        "vertigineux-en-toute-securite-12822434.php"
    ): (
        "https://www.ladepeche.fr/2025/07/13/tyrolienne-au-dessus-du-lot-"
        "2-km-de-cordes-tendues-pour-un-saut-vertigineux-en-toute-securite-"
        "12822434.php"
    ),
    (
        "icone-de-la-tendance-cette-paire-de-nike-air-jordan-frole-la-"
        "rupture-de-stock-12636138.php"
    ): (
        "https://www.ladepeche.fr/2025/04/16/icone-de-la-tendance-cette-"
        "paire-de-nike-air-jordan-frole-la-rupture-de-stock-12636138.php"
    ),
    (
        "fendez-jusqua-100-buches-par-heure-avec-ce-fendeur-de-bois-a-prix-"
        "casse-ce-vendredi-12447694.php"
    ): (
        "https://www.ladepeche.fr/2025/01/17/fendez-jusqua-100-buches-par-"
        "heure-avec-ce-fendeur-de-bois-a-prix-casse-ce-vendredi-12447694.php"
    ),
    # Le Monde test files
    (
        "au-mali-le-general-assimi-goita-promulgue-une-loi-lui-accordant-"
        "un-mandat-illimite-de-president_6620633_3212.html"
    ): (
        "https://www.lemonde.fr/afrique/article/2025/07/11/au-mali-le-"
        "general-assimi-goita-promulgue-une-loi-lui-accordant-un-mandat-"
        "illimite-de-president_6620633_3212.html"
    ),
    ("la-chine-et-l-indonesie-renforcent-leurs-liens-economiques_6182350_3210.html"): (
        "https://www.lemonde.fr/international/article/2025/07/13/la-chine-"
        "et-l-indonesie-renforcent-leurs-liens-economiques_6182350_3210.html"
    ),
    (
        "le-gouvernement-francais-annonce-des-reformes-pour-renforcer-la-"
        "securite-sociale_6182361_3224.html"
    ): (
        "https://www.lemonde.fr/societe/article/2025/07/14/le-gouvernement-"
        "francais-annonce-des-reformes-pour-renforcer-la-securite-sociale_"
        "6182361_3224.html"
    ),
    (
        "algerian-boxer-imane-khelif-taking-legal-action-over-gender-"
        "reports_6731869_4.html"
    ): (
        "https://www.lemonde.fr/en/international/article/2024/11/06/"
        "algerian-boxer-imane-khelif-taking-legal-action-over-gender-"
        "reports_6731869_4.html"
    ),
    # FranceInfo.fr test files
    (
        "creation-d-un-etat-de-nouvelle-caledonie-nationalite-corps-electoral-"
        "ce-que-contient-l-accord-historique-signe-entre-l-etat-et-les-forces-"
        "politiques-du-territoire_7372849.html"
    ): (
        "https://www.franceinfo.fr/politique/nouvelle-caledonie/creation-d-un-"
        "etat-de-nouvelle-caledonie-nationalite-corps-electoral-ce-que-contient-"
        "l-accord-historique-signe-entre-l-etat-et-les-forces-politiques-du-"
        "territoire_7372849.html"
    ),
    (
        "elisabeth-borne-recadre-son-ministre-de-l-enseignement-superieur-qui-"
        "avait-declare-que-la-notion-d-islamo-gauchisme-n-existait-pas_7375003.html"
    ): (
        "https://www.franceinfo.fr/politique/elisabeth-borne-recadre-son-"
        "ministre-de-l-enseignement-superieur-qui-avait-declare-que-la-notion-"
        "d-islamo-gauchisme-n-existait-pas_7375003.html"
    ),
    (
        "infographie-de-32-milliards-en-2017-a-plus-de-67-prevus-en-2030-"
        "comment-le-budget-de-la-defense-francaise-a-evolue-ces-dernieres-"
        "annees_7374634.html"
    ): (
        "https://www.franceinfo.fr/politique/defense/infographie-de-32-"
        "milliards-en-2017-a-plus-de-67-prevus-en-2030-comment-le-budget-de-"
        "la-defense-francaise-a-evolue-ces-dernieres-annees_7374634.html"
    ),
    (
        "nouvelle-caledonie-une-majorite-de-la-classe-politique-salue-l-accord-"
        "le-rn-exprime-de-vives-inquietudes_7374766.html"
    ): (
        "https://www.franceinfo.fr/politique/nouvelle-caledonie/nouvelle-"
        "caledonie-une-majorite-de-la-classe-politique-salue-l-accord-le-rn-"
        "exprime-de-vives-inquietudes_7374766.html"
    ),
    # TF1 Info test files
    "comment-investir-son-argent-avec-un-cashback-2377334.html": (
        "https://www.tf1info.fr/economie/comment-investir-son-argent-avec-"
        "un-cashback-2377334.html"
    ),
    "les-astuces-pour-eviter-les-arnaques-en-ligne-2377335.html": (
        "https://www.tf1info.fr/societe/les-astuces-pour-eviter-les-"
        "arnaques-en-ligne-2377335.html"
    ),
    (
        "vous-voulez-savoir-si-quelqu-un-vous-ment-voici-les-signes-qui-"
        "ne-trompent-pas-2377336.html"
    ): (
        "https://www.tf1info.fr/societe/vous-voulez-savoir-si-quelqu-un-"
        "vous-ment-voici-les-signes-qui-ne-trompent-pas-2377336.html"
    ),
    (
        "pas-d-armement-offensif-francois-bayrou-justifie-la-fermeture-"
        "des-stands-israeliens-au-salon-du-bourget-2377337.html"
    ): (
        "https://www.tf1info.fr/politique/pas-d-armement-offensif-francois-"
        "bayrou-justifie-la-fermeture-des-stands-israeliens-au-salon-du-"
        "bourget-2377337.html"
    ),
}
