"""
Initial web scraper, will reformat this and create python 
package but initially just want to get the scraping script working for the following
News sites:

Le monde
France24
Figaro
francetvinfo
Libération
"""



from bs4 import BeautifulSoup
import requests
import pandas as pd
import os

import logging
from logging_config import setup_logging

# Initialize logging
setup_logging()

#starting with slate.fr

slatefr_url = "https://www.slate.fr/"

def scrape_webpage_data(url):
    """
    Scrapes data based on url. plan to fee
    """

    logging.info(f"URL to scrape: {url}")

    # Catching request errors, could include sessions attempts but might be overkill
    try:
        response = requests.get(url, timeout=1)
        response.raise_for_status()
    except requests.



if __name__ == "__main__":
    scrape_webpage_data(figaro_url)







