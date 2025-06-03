"""

imports all the parsers

returns csv with all the words and their frequencies and metadata such as 
source, date, etc

keeping it simple at start, will add more features later

saves to csv for local storage, but streams to postgresql for long term


"""

import os
from datetime import datetime

from article_scrapers.parsers.slate_fr_parser import SlateFrArticleParser
from article_scrapers.scrapers.slate_fr_scraper import SlateFrURLScraper
from article_scrapers.utils.postgres_conn import connect_to_db, load_slate_csv_to_db



def main():
    print("🚀 Starting the scraping and parsing process...")

    # Initialize the Slate.fr parser and scraper
    slate_scraper = SlateFrURLScraper()
    slate_parser = SlateFrArticleParser()

    live_parser = True  # TODO change for live version
    if live_parser:
        # Grabbing files from slate homepage (creates new connection everytime)
        print("🔍 Fetching article URLs...")
        slate_urls = slate_scraper.get_article_urls()
        print(f"✅ Found {len(slate_urls)} URLs")
        print("🛠 Parsing live URLs...")
        soups_url_pairs = [(slate_parser.get_soup_from_url(url), url) for url in slate_urls]

    # else:
        
    #     print("🛠 Parsing local test files...")
    #      # Test files for local testing (hard coded HTML files)
    #     test_local_files = [
    #         "canada-quelque-chose-mysterieux-tue-grands-requins-blancs-cerveau-inflammation-maladie-autopsie-deces-mort-scientifiques.html",
    #         "regle-baillon-mondial-trump-entraver-acces-avortement-mexico-city-policy-anti-ivg-dangers-mort-femmes-deces-grossesse.html"
    #     ]
    #     soups_url_pairs = [(slate_parser.get_soup_from_localfile(file), file) for file in test_local_files]

    if not soups_url_pairs:
        print("⚠️ No articles to process.")
        return
    
    # Prepare output directory
    os.makedirs("output", exist_ok=True)
    today_str = datetime.today().strftime('%Y-%m-%d')
    output_csv_path = os.path.join("output", f"{today_str}.csv")
    
    # Process the parsed content (count for number of articles processed)
    processed_count = 0
    for soup, url in soups_url_pairs:
        if soup:
            print(f"📄 Processing article: {url}")
            parsed_content = slate_parser.parse_article_content(soup)
            if parsed_content:
                slate_parser.to_csv(parsed_content, url, output_csv_path)
                processed_count += 1
            else:
                print(f"❌ Failed parsing article: {url}")
        else:
            print(f"❌ Failed fetching article: {url}")

    if processed_count == 0:
        print("⚠️ No articles processed successfully; skipping DB upload.")
        return

    print(f"✅ Processed {processed_count} articles; starting DB upload...")

if __name__ == '__main__':
    main()





