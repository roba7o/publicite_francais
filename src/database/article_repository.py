"""
Article repository for database operations.

Separates database concerns from business logic by providing
a clean interface for article-related database operations.
"""

from typing import Optional
from sqlalchemy import text

from config.settings import get_schema_name
from database import get_database_manager
from utils.structured_logger import get_structured_logger

logger = get_structured_logger(__name__)


class ArticleRepository:
    """Repository for article database operations."""
    
    def __init__(self):
        self.db = get_database_manager()
        self.schema_name = get_schema_name("news_data")
    
    def get_source_id(self, source_name: str) -> Optional[str]:
        """Get source ID from database by name."""
        try:
            with self.db.get_session() as session:
                result = session.execute(
                    text(f"""
                    SELECT id FROM {self.schema_name}.news_sources
                    WHERE name = :name
                """),
                    {"name": source_name},
                )
                
                row = result.fetchone()
                return str(row[0]) if row else None
                
        except Exception as e:
            logger.error(
                "Failed to get source ID",
                extra_data={"source_name": source_name, "error": str(e)}
            )
            return None