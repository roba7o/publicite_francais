from bs4 import BeautifulSoup
import requests, os, time
from article_scrapers.utils.csv_writer import DailyCSVWriter
from collections import Counter
from ..settings import DEBUG

class BaseParser:
    def __init__(self, debug=None, delay=1):
        # This user-agent header is used to mimic a browser visit
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        self.debug = debug if debug is not None else DEBUG
        self.delay = delay
        self.csv_writer = DailyCSVWriter(debug=True)

    def get_soup_from_url(self, url):
        """
        Get a BeautifulSoup object from a given URL.
        """
        if self.debug:
            print(f"Fetching URL: {url}...")  # Indicate the start of the request
        
        try:
            response = requests.get(url, headers=self.headers)
            time.sleep(self.delay)  # Be polite and wait 1 second between requests
            response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
            
            print(f"Successfully fetched URL: {url}")
            return BeautifulSoup(response.content, 'html.parser')
        
        except requests.exceptions.RequestException as e:
            if self.debug:
                print(f"Failed to fetch URL: {url} | Status Code: {response.status_code if 'response' in locals() else 'N/A'} | Error: {e}")
            return None  # Return None if the request fails

    
    def get_soup_from_localfile(self, file_name):
        """
        Get a BeautifulSoup object from a local html file -> can be used for testing purposes.
        """

        # Get the absolute path to the test file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get root dir
        test_file_path = os.path.join(base_dir, "test_data", file_name)
        
        with open(test_file_path, "r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), 'html.parser')

    def count_word_frequency(self, text):
        """
        Count the frequency of each word in the input text.

        Splits the input string by whitespace and uses a Counter to count the
        number of occurrences of each word. The counting is case-sensitive
        and does not remove punctuation.

        Parameters:
            text (str): The input string to analyze.

        Returns:
            collections.Counter: A dictionary-like object where keys are words
            and values are their respective frequencies in the text.
        """
        words = text.split()
        word_frequencies = Counter(words)
        return word_frequencies
    

    def to_csv(self, dict_content, url):
        try:
            word_freqs = self.count_word_frequency(dict_content["full_text"])
            self.csv_writer.write_article(
                parsed_data=dict_content,
                url=url,
                word_freqs=word_freqs
            )
            if self.debug:
                print(f"✅ Successfully wrote data to CSV for URL: {url}")
        except Exception as e:
            if self.debug:
                print(f"❌ Error writing to CSV for URL: {url} | Error: {e}")
