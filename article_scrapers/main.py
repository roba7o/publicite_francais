"""

imports all the parsers

returns csv with all the words and their frequencies and metadata such as 
source, date, etc

keeping it simple at start, no need for relational db


"""

from parsers.slate_fr_parser import SlateFrArticleParser
from scrapers.slate_fr_scraper import SlateFrURLScraper
from utils.csv_writer import write_to_csv


def main():

    slate_parser = SlateFrArticleParser()
    slate_scraper = SlateFrURLScraper()  #Eventually get this to grap all releveant urls


    # Grabbing slate urls
    live_scraper = True # TODO change for live version
    if live_scraper:
        slate_urls = slate_scraper.get_article_urls()
    else:
        test_slate_urls = [
        "https://www.slate.fr/monde/regle-baillon-mondial-trump-entraver-acces-avortement-mexico-city-policy-anti-ivg-dangers-mort-femmes-deces-grossesse",
        "https://www.slate.fr/monde/canada-quelque-chose-mysterieux-tue-grands-requins-blancs-cerveau-inflammation-maladie-autopsie-deces-mort-scientifiques"
        ]

        test_local_files = [
            "test_slate_article.html",
            "test_slate_article2.html"
        ]

    

    

    live_parser = True # TODO change for live version

    if live_parser:
        soups_url_pairs = [(slate_parser.get_soup_from_url(url), url) for url in slate_urls]
    else:
        soups_url_pairs = [(slate_parser.get_soup_from_localfile(file), file) for file in test_local_files]

    for soup, url in soups_url_pairs:
        if soup:
            parsed_content = slate_parser.parse_article_content(soup)
            if parsed_content:
                slate_parser.to_csv(parsed_content, url)
            else:
                print("Error parsing article")
        else:
            print("Error fetching article")

if __name__ == '__main__':
    main()




