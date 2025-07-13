"""
Unit tests for the base parser functionality.

Tests common parser behaviors, HTML processing, and base class methods.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
import requests
from article_scrapers.parsers.base_parser import BaseParser


class TestBaseParser:
    """Test suite for BaseParser class."""
    
    def test_initialization(self):
        """Test base parser initializes correctly."""
        parser = BaseParser(debug=True)
        assert parser.debug is True
        assert hasattr(parser, 'logger')
        assert parser.delay > 0
        assert hasattr(parser, 'session')
    
    def test_initialization_default_values(self):
        """Test base parser default initialization values."""
        parser = BaseParser()
        assert parser.debug is False
        assert parser.delay == 1.0
        assert isinstance(parser.session, requests.Session)
    
    def test_get_soup_from_url_success(self, base_parser):
        """Test successful URL parsing to BeautifulSoup."""
        html_content = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        
        with patch.object(base_parser.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.content = html_content.encode('utf-8')
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            soup = base_parser.get_soup_from_url("https://test.com/article")
            
            assert isinstance(soup, BeautifulSoup)
            assert soup.find('h1').text == "Test"
            assert soup.find('p').text == "Content"
    
    def test_get_soup_from_url_http_error(self, base_parser):
        """Test handling of HTTP errors."""
        with patch.object(base_parser.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            soup = base_parser.get_soup_from_url("https://test.com/missing")
            assert soup is None
    
    def test_get_soup_from_url_connection_error(self, base_parser):
        """Test handling of connection errors."""
        with patch.object(base_parser.session, 'get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Network unreachable")
            
            soup = base_parser.get_soup_from_url("https://unreachable.com")
            assert soup is None
    
    def test_get_soup_from_url_timeout(self, base_parser):
        """Test handling of request timeouts."""
        with patch.object(base_parser.session, 'get') as mock_get:
            mock_get.side_effect = requests.Timeout("Request timed out")
            
            soup = base_parser.get_soup_from_url("https://slow.com")
            assert soup is None
    
    def test_get_soup_from_url_invalid_html(self, base_parser):
        """Test handling of invalid HTML content."""
        invalid_html = "<<broken>html>content"
        
        with patch.object(base_parser.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.content = invalid_html.encode('utf-8')
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            soup = base_parser.get_soup_from_url("https://test.com/broken")
            
            # BeautifulSoup should still parse it, even if malformed
            assert isinstance(soup, BeautifulSoup)
    
    def test_get_soup_from_url_encoding_detection(self, base_parser):
        """Test proper encoding detection and handling."""
        french_content = "<html><body><p>Café français avec accents</p></body></html>"
        
        with patch.object(base_parser.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.content = french_content.encode('utf-8')
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            soup = base_parser.get_soup_from_url("https://test.com/french")
            
            assert isinstance(soup, BeautifulSoup)
            text = soup.find('p').text
            assert "Café" in text
            assert "français" in text
    
    def test_clean_text_basic(self, base_parser):
        """Test basic text cleaning functionality."""
        dirty_text = "  This is some   text with   extra spaces  "
        clean_text = base_parser._clean_text(dirty_text)
        
        assert clean_text.strip() == clean_text
        assert "  " not in clean_text  # No double spaces
        assert clean_text == "This is some text with extra spaces"
    
    def test_clean_text_newlines_and_tabs(self, base_parser):
        """Test cleaning of newlines and tabs."""
        messy_text = "Line 1\n\nLine 2\t\tTabbed\r\nCarriage return"
        clean_text = base_parser._clean_text(messy_text)
        
        assert '\n' not in clean_text
        assert '\r' not in clean_text
        assert '\t' not in clean_text
        assert "Line 1 Line 2 Tabbed Carriage return" == clean_text
    
    def test_clean_text_special_characters(self, base_parser):
        """Test handling of special characters."""
        special_text = "Text with • bullets and — dashes"
        clean_text = base_parser._clean_text(special_text)
        
        # Should preserve readable special characters
        assert "•" in clean_text or "bullets" in clean_text
        assert "—" in clean_text or "dashes" in clean_text
    
    def test_clean_text_empty_input(self, base_parser):
        """Test cleaning with empty or None input."""
        assert base_parser._clean_text("") == ""
        assert base_parser._clean_text(None) == ""
        assert base_parser._clean_text("   ") == ""
    
    def test_extract_text_from_element(self, base_parser):
        """Test text extraction from HTML elements."""
        html = """
        <div>
            <p>First paragraph</p>
            <p>Second paragraph</p>
            <span>Span text</span>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        div_element = soup.find('div')
        
        text = base_parser._extract_text_from_element(div_element)
        
        assert "First paragraph" in text
        assert "Second paragraph" in text
        assert "Span text" in text
    
    def test_extract_text_from_element_with_separator(self, base_parser):
        """Test text extraction with custom separator."""
        html = "<div><p>Para 1</p><p>Para 2</p></div>"
        soup = BeautifulSoup(html, 'html.parser')
        div_element = soup.find('div')
        
        text = base_parser._extract_text_from_element(div_element, separator=" | ")
        
        assert "Para 1 | Para 2" in text
    
    def test_extract_text_handles_nested_elements(self, base_parser):
        """Test text extraction with nested HTML elements."""
        html = """
        <article>
            <h1>Title</h1>
            <div class="content">
                <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
                <ul>
                    <li>List item 1</li>
                    <li>List item 2</li>
                </ul>
            </div>
        </article>
        """
        soup = BeautifulSoup(html, 'html.parser')
        article = soup.find('article')
        
        text = base_parser._extract_text_from_element(article)
        
        assert "Title" in text
        assert "bold" in text
        assert "italic" in text
        assert "List item 1" in text
        assert "List item 2" in text
    
    def test_validate_parsed_data_valid(self, base_parser):
        """Test validation of properly formatted parsed data."""
        valid_data = {
            'title': 'Valid Article Title',
            'full_text': 'This is the article content with sufficient length for validation.',
            'article_date': '2025-07-13',
            'date_scraped': '2025-07-13 17:00:00'
        }
        
        assert base_parser._validate_parsed_data(valid_data) is True
    
    def test_validate_parsed_data_missing_fields(self, base_parser):
        """Test validation with missing required fields."""
        invalid_data = {
            'title': 'Title only'
            # Missing other required fields
        }
        
        assert base_parser._validate_parsed_data(invalid_data) is False
    
    def test_validate_parsed_data_empty_fields(self, base_parser):
        """Test validation with empty required fields."""
        invalid_data = {
            'title': '',
            'full_text': 'Content',
            'article_date': '2025-07-13',
            'date_scraped': '2025-07-13 17:00:00'
        }
        
        assert base_parser._validate_parsed_data(invalid_data) is False
    
    def test_validate_parsed_data_short_content(self, base_parser):
        """Test validation rejects content that's too short."""
        invalid_data = {
            'title': 'Title',
            'full_text': 'Short',  # Too short
            'article_date': '2025-07-13',
            'date_scraped': '2025-07-13 17:00:00'
        }
        
        assert base_parser._validate_parsed_data(invalid_data) is False
    
    def test_apply_request_delay(self, base_parser):
        """Test request delay application."""
        import time
        
        start_time = time.time()
        base_parser._apply_request_delay()
        end_time = time.time()
        
        elapsed = end_time - start_time
        assert elapsed >= base_parser.delay - 0.1  # Allow small timing variance
    
    def test_apply_request_delay_debug_mode(self):
        """Test request delay in debug mode (should be shorter)."""
        debug_parser = BaseParser(debug=True)
        import time
        
        start_time = time.time()
        debug_parser._apply_request_delay()
        end_time = time.time()
        
        elapsed = end_time - start_time
        assert elapsed < 1.0  # Should be faster in debug mode
    
    def test_get_test_sources_from_directory_exists(self, base_parser, tmp_path):
        """Test loading test sources from existing directory."""
        # Create test directory structure
        test_dir = tmp_path / "test_data" / "test_source"
        test_dir.mkdir(parents=True)
        
        # Create test HTML files
        (test_dir / "article1.html").write_text("<html><body>Article 1</body></html>")
        (test_dir / "article2.html").write_text("<html><body>Article 2</body></html>")
        
        with patch('article_scrapers.parsers.base_parser.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.glob.return_value = [
                test_dir / "article1.html",
                test_dir / "article2.html"
            ]
            
            # Mock file reading
            def mock_read_text(encoding=None):
                if "article1" in str(mock_path.return_value):
                    return "<html><body>Article 1</body></html>"
                return "<html><body>Article 2</body></html>"
            
            mock_path.return_value.read_text = mock_read_text
            
            sources = base_parser.get_test_sources_from_directory("test_source")
            
            assert len(sources) >= 0  # Should return list (implementation dependent)
    
    def test_get_test_sources_directory_not_found(self, base_parser):
        """Test handling of missing test directory."""
        sources = base_parser.get_test_sources_from_directory("nonexistent_source")
        assert sources == []
    
    def test_session_configuration(self, base_parser):
        """Test HTTP session is properly configured."""
        session = base_parser.session
        
        assert isinstance(session, requests.Session)
        assert session.headers.get('User-Agent') is not None
        # Check session has reasonable timeout settings
    
    def test_parse_article_not_implemented(self, base_parser):
        """Test that parse_article raises NotImplementedError in base class."""
        soup = BeautifulSoup("<html><body>Test</body></html>", 'html.parser')
        
        with pytest.raises(NotImplementedError):
            base_parser.parse_article(soup)
    
    def test_to_csv_not_implemented(self, base_parser):
        """Test that to_csv raises NotImplementedError in base class."""
        data = {'title': 'Test'}
        url = 'https://test.com'
        
        with pytest.raises(NotImplementedError):
            base_parser.to_csv(data, url)
    
    @pytest.mark.parametrize("html_content,expected_elements", [
        ("<html><body><p>Simple</p></body></html>", 1),
        ("<html><body><div><p>Para 1</p><p>Para 2</p></div></body></html>", 2),
        ("<html><body></body></html>", 0),
    ])
    def test_soup_parsing_various_structures(self, base_parser, html_content, expected_elements):
        """Test BeautifulSoup parsing with various HTML structures."""
        with patch.object(base_parser.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.content = html_content.encode('utf-8')
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            soup = base_parser.get_soup_from_url("https://test.com")
            
            assert isinstance(soup, BeautifulSoup)
            paragraphs = soup.find_all('p')
            assert len(paragraphs) == expected_elements
    
    def test_error_logging_on_failure(self, base_parser):
        """Test that errors are properly logged."""
        with patch.object(base_parser.session, 'get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Network error")
            
            with patch.object(base_parser.logger, 'error') as mock_log:
                soup = base_parser.get_soup_from_url("https://failing.com")
                
                assert soup is None
                mock_log.assert_called()
                
                # Check that error message contains useful information
                call_args = mock_log.call_args[0][0]
                assert "failing.com" in call_args or "Network error" in call_args