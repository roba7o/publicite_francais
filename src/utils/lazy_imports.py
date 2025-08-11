"""
Lazy import utilities to reduce repeated import patterns.

Provides common lazy imports used throughout the application to avoid circular imports.
"""

import importlib
from functools import lru_cache
from typing import Any, Callable


@lru_cache(maxsize=None)
def lazy_import(module_name: str, attr_name: str = None) -> Any:
    """
    Lazily import a module or attribute with caching.
    
    Args:
        module_name: Name of the module to import
        attr_name: Optional attribute to get from the module
        
    Returns:
        The imported module or attribute
        
    Example:
        get_logger = lazy_import('utils.structured_logger', 'get_structured_logger')
        logger = get_logger(__name__)
    """
    module = importlib.import_module(module_name)
    return getattr(module, attr_name) if attr_name else module


def get_lazy_import(module_path: str) -> Callable:
    """
    Create a lazy import function for a specific module path.
    
    Args:
        module_path: Full module.attribute path like 'utils.structured_logger.get_structured_logger'
        
    Returns:
        Function that returns the imported object when called
        
    Example:
        get_logger = get_lazy_import('utils.structured_logger.get_structured_logger')
        logger = get_logger()(__name__)
    """
    if '.' not in module_path:
        raise ValueError(f"Invalid module path: {module_path}")
    
    module_name, attr_name = module_path.rsplit('.', 1)
    return lambda: lazy_import(module_name, attr_name)


# Pre-defined common lazy imports to reduce duplication
get_structured_logger = lambda: lazy_import('utils.structured_logger', 'get_structured_logger')
get_database_manager = lambda: lazy_import('database', 'get_database_manager')
get_article_repository = lambda: lazy_import('database', 'ArticleRepository')
get_simple_factory = lambda: lazy_import('core.component_loader', 'create_component')
get_shared_output = lambda: lazy_import('utils.shared_output', 'output')
get_debug_setting = lambda: lazy_import('config.settings', 'DEBUG')