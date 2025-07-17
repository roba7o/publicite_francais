import os
import requests


def download_html(url, save_path, headers=None, overwrite=False):
    """
    Downloads an HTML page and saves it to a local file.
    """
    if not overwrite and os.path.exists(save_path):
        print(f"File already exists at: {save_path}")
        return False

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"HTML downloaded and saved to: {save_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to download HTML from {url}. Error: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


if __name__ == "__main__":
    test_urls = {
        "slate_fr": [
            "https://www.slate.fr/monde/regle-baillon-mondial-trump-entraver-"
            "acces-avortement-mexico-city-policy-anti-ivg-dangers-mort-femmes-"
            "deces-grossesse",
            "https://www.slate.fr/monde/canada-quelque-chose-mysterieux-tue-"
            "grands-requins-blancs-cerveau-inflammation-maladie-autopsie-"
            "deces-mort-scientifiques",
            "https://www.slate.fr/monde/europe-dissuasion-nuclaire-russie-"
            "angleterre-france-uranium-poutine-otan-arsenal",
            "https://www.slate.fr/sciences/civilisation-alien-vacarme-radar-"
            "aeroport-signaux-espace-annees-lumieres-galaxie-technologie",
        ],
        "depeche_fr": [
            "https://www.ladepeche.fr/2025/07/12/intemperies-dans-le-lot-"
            "des-fils-electriques-sont-tombes-au-sol-une-route-est-coupee-"
            "12822614.php",
            "https://www.ladepeche.fr/2025/07/13/tyrolienne-au-dessus-du-lot-"
            "2-km-de-cordes-tendues-pour-un-saut-vertigineux-en-toute-"
            "securite-12822434.php",
            "https://www.ladepeche.fr/2025/04/16/icone-de-la-tendance-cette-"
            "paire-de-nike-air-jordan-frole-la-rupture-de-stock-12636138.php",
            "https://www.ladepeche.fr/2025/01/17/fendez-jusqua-100-buches-"
            "par-heure-avec-ce-fendeur-de-bois-a-prix-casse-ce-vendredi-"
            "12447694.php",
        ],
        "france_info": [
            "https://www.franceinfo.fr/france/nouvelle-caledonie-iles-loyaute/"
            "nouvelle-caledonie-une-majorite-de-la-classe-politique-salue-"
            "l-accord-le-rn-exprime-de-vives-inquietudes_7374766.html",
            "https://www.franceinfo.fr/societe/armee-securite-defense/"
            "infographie-de-32-milliards-en-2017-a-plus-de-67-prevus-en-2030-"
            "comment-le-budget-de-la-defense-francaise-a-evolue-ces-dernieres-"
            "annees_7374634.html",
            "https://www.franceinfo.fr/france/nouvelle-caledonie/"
            "creation-d-un-"
            "etat-de-nouvelle-caledonie-nationalite-corps-electoral-ce-que-"
            "contient-l-accord-historique-signe-entre-l-etat-et-les-forces-"
            "politiques-du-territoire_7372849.html",
            "https://www.franceinfo.fr/politique/elisabeth-borne-recadre-son-"
            "ministre-de-l-enseignement-superieur-qui-avait-declare-que-la-"
            "notion-d-islamo-gauchisme-n-existait-pas_7375003.html",
        ],
        "tf1_fr": [
            "https://www.tf1info.fr/economie/comment-investir-son-argent-"
            "avec-un-cashback-2377334.html",
            "https://www.tf1info.fr/societe/les-astuces-pour-eviter-les-"
            "arnaques-en-ligne-2377335.html",
            "https://www.tf1info.fr/societe/vous-voulez-savoir-si-quelqu-un-"
            "vous-ment-voici-les-signes-qui-ne-trompent-pas-2377336.html",
            "https://www.tf1info.fr/politique/pas-d-armement-offensif-"
            "francois-bayrou-justifie-la-fermeture-des-stands-israeliens-"
            "au-salon-du-bourget-2377337.html",
        ],
    }

    base_dir = "./src/article_scrapers/test_data/raw_url_soup"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        )
    }

    for site_key, urls in test_urls.items():
        site_dir = os.path.join(base_dir, site_key)
        os.makedirs(site_dir, exist_ok=True)
        for url in urls:
            filename = url.split("/")[-1]
            if not filename.endswith(".html") and not filename.endswith(".php"):
                filename += ".html"
            save_path = os.path.join(site_dir, filename)
            success = download_html(url, save_path, headers=headers, overwrite=True)
            if success:
                print(f"Downloaded: {url} -> {save_path}")
            else:
                print(f"Failed to download: {url}")
