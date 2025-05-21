import pytest
from parsers.base_parser import BaseParser
from bs4 import BeautifulSoup
import os
from unittest.mock import patch, mock_open

@pytest.fixture
def base_parser():
    return BaseParser(debug=True)

def test_get_soup_from_localfile(base_parser):
    # Use your actual test file paths
    test_file = "regle-baillon-mondial-trump-entraver-acces-avortement-mexico-city-policy-anti-ivg-dangers-mort-femmes-deces-grossesse.html"
    soup = base_parser.get_soup_from_localfile(test_file)
    assert soup is not None
    # Add more specific assertions based on your test file content
    assert soup.find('article') is not None
    assert soup.find('h1') is not None
    assert soup.find('p') is not None
    assert soup.find('h2') is not None

def test_get_soup_from_url(base_parser):
    # Mock the requests.get method to simulate a successful response
    with patch('requests.get') as mock_get:
        mock_response = patch('requests.models.Response')
        mock_response.status_code = 200
        mock_response.content = b"<html><body><article></article></body></html>"
        mock_get.return_value = mock_response

        url = "http://example.com"
        soup = base_parser.get_soup_from_url(url)
        
        assert soup is not None
        assert soup.find('article') is not None
        assert soup.find('h1') is None


def test_get_soup_from_url_failure(base_parser):
    # Mock the requests.get method to simulate a failed response
    with patch('requests.get') as mock_get:
        mock_response = patch('requests.models.Response')
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        url = "http://example.com"
        soup = base_parser.get_soup_from_url(url)
        
        assert soup is None


def test_count_word_frequency(base_parser):
    text = "hello world hello"
    expected_frequency = {'hello': 2, 'world': 1}
    frequency = base_parser.count_word_frequency(text)
    
    assert frequency == expected_frequency

def test_to_csv(base_parser):
    # Mock the write_to_csv function
    with patch('article_scrapers.parsers.base_parser.write_to_csv') as mock_write_to_csv:
        dict_content = {
            "full_text": "hello world hello",
            "article_date": "2023-10-01",
            "date_scraped": "2023-10-02",
            "title": "Test Title"
        }
        url = "http://example.com"
        
        base_parser.to_csv(dict_content, url)
        
        mock_write_to_csv.assert_called_once()
        args, kwargs = mock_write_to_csv.call_args
        assert kwargs['data']['source'] == url
        assert kwargs['data']['article_date'] == dict_content['article_date']
        assert kwargs['data']['date_scraped'] == dict_content['date_scraped']
        assert kwargs['data']['title'] == dict_content['title']
        assert kwargs['data']['word_frequencies'] == {'hello': 2, 'world': 1}

def test_to_csv_failure(base_parser):
    # Mock the write_to_csv function to raise an exception
    with patch('article_scrapers.parsers.base_parser.write_to_csv') as mock_write_to_csv:
        mock_write_to_csv.side_effect = Exception("Write error")
        
        dict_content = {
            "full_text": "hello world hello",
            "article_date": "2023-10-01",
            "date_scraped": "2023-10-02",
            "title": "Test Title"
        }
        url = "http://example.com"
        
        base_parser.to_csv(dict_content, url)
        
        mock_write_to_csv.assert_called_once()
        args, kwargs = mock_write_to_csv.call_args
        assert kwargs['data']['source'] == url
        assert kwargs['data']['article_date'] == dict_content['article_date']
        assert kwargs['data']['date_scraped'] == dict_content['date_scraped']
        assert kwargs['data']['title'] == dict_content['title']
        assert kwargs['data']['word_frequencies'] == {'hello': 2, 'world': 1}


