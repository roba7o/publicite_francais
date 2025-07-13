"""
Mock parser implementations for testing.

These mock parsers simulate real parser behavior without processing
actual HTML, allowing for controlled testing scenarios.
"""

from typing import Dict, Any, Optional, List, Tuple
from unittest.mock import Mock
from bs4 import BeautifulSoup


class MockParser:
    """Mock article parser for testing."""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = Mock()
        self.delay = 0.1
        
    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Return mock article data."""
        return {
            'title': 'Mock Article Title',
            'full_text': 'Ceci est un article de test français avec du contenu pour analyse.',
            'article_date': '2025-07-13',
            'date_scraped': '2025-07-13 17:00:00'
        }
        
    def get_soup_from_url(self, url: str) -> Optional[BeautifulSoup]:
        """Return mock BeautifulSoup object."""
        html = "<html><body><h1>Test</h1><p>Mock content</p></body></html>"
        return BeautifulSoup(html, 'html.parser')
        
    def get_test_sources_from_directory(self, source_name: str) -> List[Tuple[Optional[BeautifulSoup], str]]:
        """Return mock test sources."""
        html = "<html><body><h1>Test Article</h1><p>Test content here</p></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        return [(soup, "https://test.example.com/mock-article")]
        
    def to_csv(self, parsed_data: Dict[str, Any], url: str) -> None:
        """Mock CSV writing."""
        pass


class MockFailingParser:
    """Mock parser that simulates parsing failures."""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = Mock()
        self.delay = 0.1
        
    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Simulate parsing failure."""
        return None
        
    def get_soup_from_url(self, url: str) -> Optional[BeautifulSoup]:
        """Simulate URL fetch failure."""
        return None
        
    def get_test_sources_from_directory(self, source_name: str) -> List[Tuple[Optional[BeautifulSoup], str]]:
        """Return empty sources."""
        return []
        
    def to_csv(self, parsed_data: Dict[str, Any], url: str) -> None:
        """Mock CSV writing."""
        pass


class MockParserWithRichContent:
    """Mock parser that returns rich content for text processing tests."""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = Mock()
        self.delay = 0.1
        
    def parse_article(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Return mock article with rich French content."""
        return {
            'title': 'Article Français Complexe avec Analyses Détaillées',
            'full_text': """
            Le gouvernement français annonce des réformes importantes pour l'économie nationale.
            Ces changements concernent principalement la sécurité sociale et les politiques publiques.
            Les citoyens français attendent ces modifications avec un intérêt particulier.
            Cette nouvelle politique devrait considérablement améliorer la situation économique du pays.
            
            Les experts économiques analysent ces décisions gouvernementales avec attention.
            Plusieurs ministres ont confirmé l'importance de ces transformations structurelles.
            L'opposition politique critique certains aspects de cette réforme ambitieuse.
            Les syndicats français organisent des manifestations pour exprimer leurs préoccupations.
            
            La population française découvre progressivement les détails de cette politique.
            Les médias nationaux couvrent extensivement ces développements politiques majeurs.
            Cette situation politique complexe nécessite une analyse approfondie des enjeux.
            """,
            'article_date': '2025-07-13',
            'date_scraped': '2025-07-13 17:00:00'
        }
        
    def get_soup_from_url(self, url: str) -> Optional[BeautifulSoup]:
        """Return mock BeautifulSoup with rich content."""
        html = """
        <html>
        <body>
            <h1>Article Français Complexe</h1>
            <div class="content">
                <p>Le gouvernement français annonce des réformes importantes...</p>
                <p>Ces changements concernent principalement la sécurité sociale...</p>
            </div>
        </body>
        </html>
        """
        return BeautifulSoup(html, 'html.parser')
        
    def get_test_sources_from_directory(self, source_name: str) -> List[Tuple[Optional[BeautifulSoup], str]]:
        """Return mock test sources with rich content."""
        soup = self.get_soup_from_url("mock://url")
        return [(soup, "https://test.example.com/rich-article")]
        
    def to_csv(self, parsed_data: Dict[str, Any], url: str) -> None:
        """Mock CSV writing."""
        pass