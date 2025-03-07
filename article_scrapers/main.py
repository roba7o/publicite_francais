"""

imports all the parsers

returns csv with all the words and their frequencies and metadata such as 
source, date, etc

keeping it simple at start, will add more features later

saves to csv for local storage, but streams to postgresql for long term


"""

import os
import shutil
import psycopg2

from parsers.slate_fr_parser import SlateFrArticleParser
from scrapers.slate_fr_scraper import SlateFrURLScraper
from utils.csv_writer import write_to_csv

import psycopg2

# Database Connection Details
DB_CONFIG = {
    "dbname": "scraped_data",
    "user": "postgres",
    "password": "francais",
    "host": "localhost",
    "port": "5432",
}


def connect_to_db():
    """Establishes a connection to PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None
    
def bulk_insert_csv_to_db(csv_file, conn):
    """Loads CSV data into PostgreSQL using COPY and then deletes the file."""
    temp_file = csv_file.replace(".csv", "_backup.csv")  # Rename for debugging

    try:
        cur = conn.cursor()
        with open(csv_file, "r", encoding="utf-8") as f:
            next(f)  # Skip header row if CSV has one
            cur.copy_expert(
                "COPY articles (word, frequency, date, title, url) FROM STDIN WITH CSV",
                f
            )
        conn.commit()
        print("✅ Data successfully inserted into PostgreSQL")

        # Rename for debugging, then delete
        shutil.move(csv_file, temp_file)
        os.remove(temp_file)
        print(f"🗑️ Deleted CSV: {temp_file}")

    except Exception as e:
        print(f"❌ Error loading CSV into PostgreSQL: {e}")
        conn.rollback()
    finally:
        cur.close()




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




