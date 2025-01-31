"""

imports all the parsers

returns csv with all the words and their frequencies and metadata such as 
source, date, etc

keeping it simple at start, no need for relational db


"""

from parsers.slate_fr_parser import SlateFrArticleParser
# from scrapers.slate_fr_scraper import SlateFrScraper



def main():

    slate_parser = SlateFrArticleParser()
    # slate_scraper = SlateFrScraper()    #Eventually get this to grap all releveant urls

    # TODO Grabbing slate urls
    # slate_urls = slate_scraper.get_article_urls()

    test_slate_url = "https://www.slate.fr/monde/regle-baillon-mondial-trump-entraver-acces-avortement-mexico-city-policy-anti-ivg-dangers-mort-femmes-deces-grossesse"

    # TODO change for live version

    live = False

    if live:
        soup = slate_parser.get_soup_from_url(test_slate_url)
    else:
        soup = slate_parser.get_soup_from_localfile("test_slate_article.html")

    result = slate_parser.parse_article_content(soup)

    if result:
        print(f"Successfully parsed article")
        print(f"number of paragraphs: {result['num_paragraphs']}")
        print("\nFirst 500 characters of content:")
        print(result['full_text'][:500])
    else:
        print("Failed to parse article")


if __name__ == '__main__':
    main()




