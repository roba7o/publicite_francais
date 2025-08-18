"""
Unified configurable mock parser for testing.

Single class that can simulate different parser behaviors through configuration,
replacing the multiple separate mock parser classes.
"""

from unittest.mock import Mock

from bs4 import BeautifulSoup

from models import ArticleData


class ConfigurableMockParser:
    """
    Single configurable mock parser that can simulate various scenarios.

    Behaviors:
    - success: Normal successful parsing
    - failure: Parsing failures (returns None/False)
    - rich_content: Rich French content for text processing tests
    - empty: No content/sources returned
    """

    def __init__(
        self,
        source_id: str = "mock-source-id",
        behavior: str = "success",
        debug: bool = False,
    ):
        """
        Initialize configurable mock parser.

        Args:
            source_id: Source ID for the parser
            behavior: Behavior mode ('success', 'failure', 'rich_content', 'empty')
            debug: Debug mode flag
        """
        self.source_id = source_id
        self.behavior = behavior
        self.debug = debug
        self.logger = Mock()
        self.delay = 0.1

        # Content configurations for different behaviors
        self.content_configs = {
            "success": {
                "title": "Mock Article Title",
                "full_text": "Ceci est un article de test français avec du contenu pour analyse.",
                "article_date": "2025-07-13",
                "date_scraped": "2025-07-13",
            },
            "rich_content": {
                "title": "Article Français Complexe avec Analyses Détaillées",
                "full_text": """
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
                "article_date": "2025-07-13",
                "date_scraped": "2025-07-13",
            },
        }

    def parse_article(self, soup: BeautifulSoup) -> ArticleData | None:
        """Parse article based on behavior configuration."""
        if self.behavior in ["failure", "empty"]:
            return None

        config = self.content_configs.get(
            self.behavior, self.content_configs["success"]
        )
        return ArticleData(**config)

    def get_soup_from_url(self, url: str) -> BeautifulSoup | None:
        """Get soup based on behavior configuration."""
        if self.behavior == "failure":
            return None

        if self.behavior == "rich_content":
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
        else:
            html = "<html><body><h1>Test</h1><p>Mock content</p></body></html>"

        return BeautifulSoup(html, "html.parser")

    def get_test_sources_from_directory(
        self, source_name: str
    ) -> list[tuple[BeautifulSoup | None, str]]:
        """Get test sources based on behavior configuration."""
        if self.behavior in ["failure", "empty"]:
            return []

        soup = self.get_soup_from_url("mock://url")
        return [(soup, f"https://test.example.com/{self.behavior}-article")]

    def to_database(self, article_data: ArticleData, url: str) -> bool:
        """Mock database operation based on behavior configuration."""
        if self.behavior == "failure":
            return False
        return True


# Factory functions for creating pre-configured parsers
def create_mock_parser(
    source_id: str = "mock-source-id", debug: bool = False
) -> ConfigurableMockParser:
    """Create standard success mock parser."""
    return ConfigurableMockParser(source_id, behavior="success", debug=debug)


def create_failing_mock_parser(
    source_id: str = "mock-failing-id", debug: bool = False
) -> ConfigurableMockParser:
    """Create failing mock parser."""
    return ConfigurableMockParser(source_id, behavior="failure", debug=debug)


def create_rich_content_mock_parser(
    source_id: str = "mock-rich-id", debug: bool = False
) -> ConfigurableMockParser:
    """Create mock parser with rich French content."""
    return ConfigurableMockParser(source_id, behavior="rich_content", debug=debug)


def create_empty_mock_parser(
    source_id: str = "mock-empty-id", debug: bool = False
) -> ConfigurableMockParser:
    """Create mock parser that returns empty results."""
    return ConfigurableMockParser(source_id, behavior="empty", debug=debug)


# Backward compatibility aliases
MockDatabaseParser = create_mock_parser


def MockParser(debug=False):
    return create_mock_parser("mock-source-id", debug)


MockFailingParser = create_failing_mock_parser
MockParserWithRichContent = create_rich_content_mock_parser
