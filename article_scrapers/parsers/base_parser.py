from bs4 import BeautifulSoup
import requests, os, time

class BaseParser:
    def __init__(self, debug=False):
        # This user-agent header is used to mimic a browser visit
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        self.debug = debug
        

    def get_soup_from_url(self, url):
        """
        Get a BeautifulSoup object from a given url
        """
        response = requests.get(url, headers=self.headers)
        time.sleep(1)  # Be polite and wait 1 second between requests
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    
    def get_soup_from_localfile(self, file_name):
        """
        Get a BeautifulSoup object from a local html file
        """

        # Get the absolute path to the test file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get root dir
        test_file_path = os.path.join(base_dir, "test_data", file_name)
        
        with open(test_file_path, "r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), 'html.parser')