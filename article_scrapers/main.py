"""

imports all the parsers

returns csv with all the words and their frequencies and metadata such as 
source, date, etc

keeping it simple at start, will add more features later

saves to csv for local storage, but streams to postgresql for long term


"""

import os
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
    """
    Establishes a connection to the PostgreSQL database.

    Returns:
        psycopg2.extensions.connection: A connection object if successful, otherwise None.
    """
    try:
        print("🔗 Attempting to connect to PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Successfully connected to PostgreSQL.")
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None


def main():
    print("🚀 Starting the scraping and parsing process...")

    # Initialize the Slate.fr parser and scraper
    slate_parser = SlateFrArticleParser()
    slate_scraper = SlateFrURLScraper()


    live_parser = True  # TODO change for live version
    if live_parser:
        # Grabbing files from slate homepage (creates new connection everytime)
        print("🔍 Fetching article URLs...")
        slate_urls = slate_scraper.get_article_urls()
        print(f"✅ Found {len(slate_urls)} URLs")

        print("🛠 Parsing live URLs...")
        soups_url_pairs = [(slate_parser.get_soup_from_url(url), url) for url in slate_urls]

    else:
        print("🛠 Parsing local test files...")
         # Test files for local testing (hard coded HTML files)
        test_local_files = [
            "test_slate_article.html",
            "test_slate_article2.html"
        ]
        soups_url_pairs = [(slate_parser.get_soup_from_localfile(file), file) for file in test_local_files]

    for soup, url in soups_url_pairs:
        if soup:
            print(f"📄 Successfully fetched article from {url}")
            parsed_content = slate_parser.parse_article_content(soup)
            if parsed_content:
                slate_parser.to_csv(parsed_content, url)
            else:
                print("❌ Error parsing article")
        else:
            print("❌ Error fetching article")


if __name__ == '__main__':
    main()





