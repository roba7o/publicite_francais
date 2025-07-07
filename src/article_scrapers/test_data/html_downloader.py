import os
import requests

def download_html(url, save_path, headers=None, overwrite=False):
    """
    Downloads an HTML page and saves it to a local file.

    Args:
        url (str): The URL of the HTML page to download.
        save_path (str): The local path to save the HTML file.
        headers (dict, optional): Optional headers for the HTTP request. Defaults to None.
        overwrite (bool, optional): If True, overwrites the file if it exists. Defaults to False.

    Returns:
        bool: True if the file was successfully downloaded and saved, False otherwise.
    """
    # Check if file exists and handle overwrite logic
    if not overwrite and os.path.exists(save_path):
        print(f"File already exists at: {save_path}")
        return False

    try:
        # Fetch the HTML content
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        
        # Write the content to the file
        with open(save_path, 'w', encoding='utf-8') as file:
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
    # Define the URL and save path

    test_slate_urls = [
        "https://www.slate.fr/monde/regle-baillon-mondial-trump-entraver-acces-avortement-mexico-city-policy-anti-ivg-dangers-mort-femmes-deces-grossesse",
        "https://www.slate.fr/monde/canada-quelque-chose-mysterieux-tue-grands-requins-blancs-cerveau-inflammation-maladie-autopsie-deces-mort-scientifiques"
        ]
    
    for url in test_slate_urls:
        save_path = f"./article_scrapers/test_data/{url.split('/')[-1]}.html"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        success = download_html(url, save_path, headers=headers, overwrite=True)
        if success:
            print("HTML download complete.")
        else:
            print("Failed to download HTML.")
    