from bs4 import BeautifulSoup
import requests, os, time
from utils.csv_writer import write_to_csv

class BaseParser:
    def __init__(self, debug=False):
        # This user-agent header is used to mimic a browser visit
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        self.debug = debug
        

    def get_soup_from_url(self, url):
        """
        Get a BeautifulSoup object from a given URL.
        """
        print(f"Fetching URL: {url}...")  # Indicate the start of the request
        
        try:
            response = requests.get(url, headers=self.headers)
            time.sleep(1)  # Be polite and wait 1 second between requests
            response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
            
            print(f"Successfully fetched URL: {url}")
            return BeautifulSoup(response.content, 'html.parser')
        
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch URL: {url} | Error: {e}")
            return None  # Return None if the request fails

    
    def get_soup_from_localfile(self, file_name):
        """
        Get a BeautifulSoup object from a local html file
        """

        # Get the absolute path to the test file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get root dir
        test_file_path = os.path.join(base_dir, "test_data", file_name)
        
        with open(test_file_path, "r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), 'html.parser')

    def count_word_frequency(self, text):
        """Counts word frequencies from the article text"""
        from collections import Counter
        words = text.split()
        word_frequencies = Counter(words)
        return word_frequencies
    

    def to_csv(self, dict_content, url):
        write_to_csv({
            'word_frequencies': self.count_word_frequency(dict_content['full_text']),
            'source': url,
            'date': dict_content['date'],
            'title': dict_content['title']
        })
