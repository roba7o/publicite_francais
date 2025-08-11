"""
Class registry to replace string-based class loading.

Provides a centralized, type-safe registry for scraper and parser classes.
Replaces fragile string-based dynamic imports with pre-registered classes.
"""

from typing import Dict, Type, Any, Optional

from utils.structured_logger import get_structured_logger

logger = get_structured_logger(__name__)


class ClassRegistry:
    """Central registry for scraper and parser classes."""
    
    def __init__(self):
        self._scrapers: Dict[str, Type] = {}
        self._parsers: Dict[str, Type] = {}
        self._register_default_classes()
    
    def _register_default_classes(self):
        """Register all known scraper and parser classes."""
        try:
            # Import and register scrapers
            from scrapers.slate_fr_scraper import SlateFrURLScraper
            from scrapers.france_info_scraper import FranceInfoURLScraper
            from scrapers.tf1_info_scraper import TF1InfoURLScraper
            from scrapers.ladepeche_fr_scraper import LadepecheFrURLScraper
            
            self._scrapers.update({
                'SlateFrURLScraper': SlateFrURLScraper,
                'FranceInfoURLScraper': FranceInfoURLScraper,
                'TF1InfoURLScraper': TF1InfoURLScraper,
                'LadepecheFrURLScraper': LadepecheFrURLScraper,
            })
            
            # Import and register database parsers
            from parsers.database_slate_fr_parser import DatabaseSlateFrParser
            from parsers.database_france_info_parser import DatabaseFranceInfoParser
            from parsers.database_tf1_info_parser import DatabaseTF1InfoParser
            from parsers.database_ladepeche_fr_parser import DatabaseLadepecheFrParser
            
            self._parsers.update({
                'DatabaseSlateFrParser': DatabaseSlateFrParser,
                'DatabaseFranceInfoParser': DatabaseFranceInfoParser,
                'DatabaseTF1InfoParser': DatabaseTF1InfoParser,
                'DatabaseLadepecheFrParser': DatabaseLadepecheFrParser,
            })
            
            # Register test/mock classes (for testing environment)
            self._register_test_classes()
            
            logger.info(
                "Class registry initialized",
                extra_data={
                    "scrapers_registered": len(self._scrapers),
                    "parsers_registered": len(self._parsers)
                }
            )
            
        except ImportError as e:
            logger.error(
                "Failed to register some classes",
                extra_data={"error": str(e)},
                exc_info=True
            )
    
    def _register_test_classes(self):
        """Register test/mock classes for testing environment."""
        try:
            # Only import test classes if they're available (in test environment)
            from tests.fixtures.mock_scraper import MockScraper, MockFailingScraper, MockSlowScraper, MockEmptyScraper
            from tests.fixtures.mock_parser import MockDatabaseParser, MockParser, MockFailingParser, MockParserWithRichContent
            
            # Register mock scrapers
            self._scrapers.update({
                'MockScraper': MockScraper,
                'MockFailingScraper': MockFailingScraper, 
                'MockSlowScraper': MockSlowScraper,
                'MockEmptyScraper': MockEmptyScraper,
            })
            
            # Register mock parsers
            self._parsers.update({
                'MockDatabaseParser': MockDatabaseParser,
                'MockParser': MockParser,
                'MockFailingParser': MockFailingParser,
                'MockParserWithRichContent': MockParserWithRichContent,
            })
            
        except ImportError:
            # Test classes not available (not in test environment)
            pass
    
    def get_scraper_class(self, class_name: str) -> Optional[Type]:
        """Get scraper class by name (class name only, not full path)."""
        if class_name in self._scrapers:
            return self._scrapers[class_name]
        
        logger.error(
            "Scraper class not found in registry",
            extra_data={
                "requested_class": class_name,
                "available_classes": list(self._scrapers.keys())
            }
        )
        return None
    
    def get_parser_class(self, class_name: str) -> Optional[Type]:
        """Get parser class by name (class name only, not full path)."""
        if class_name in self._parsers:
            return self._parsers[class_name]
        
        logger.error(
            "Parser class not found in registry",
            extra_data={
                "requested_class": class_name,
                "available_classes": list(self._parsers.keys())
            }
        )
        return None
    
    def register_scraper(self, name: str, class_type: Type):
        """Register a new scraper class."""
        self._scrapers[name] = class_type
        logger.info(f"Registered scraper: {name}")
    
    def register_parser(self, name: str, class_type: Type):
        """Register a new parser class."""
        self._parsers[name] = class_type
        logger.info(f"Registered parser: {name}")


# Global registry instance
_registry = ClassRegistry()


def get_scraper_class(class_name: str) -> Optional[Type]:
    """Get scraper class from global registry."""
    return _registry.get_scraper_class(class_name)


def get_parser_class(class_name: str) -> Optional[Type]:
    """Get parser class from global registry."""
    return _registry.get_parser_class(class_name)


def extract_class_name(full_path: str) -> str:
    """Extract class name from full module path for backward compatibility."""
    return full_path.split('.')[-1]