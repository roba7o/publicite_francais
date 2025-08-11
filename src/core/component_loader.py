"""
Simple factory function for creating components from class paths.

Replaces the complex two-layer factory system with a single, straightforward function.
"""

import importlib
from typing import Any


def create_component(class_path: str, *args, **kwargs) -> Any:
    """
    Create component instance from full class path.
    
    Args:
        class_path: Full module path like 'scrapers.slate_fr_scraper.SlateFrURLScraper'
        *args: Positional arguments to pass to component constructor
        **kwargs: Keyword arguments to pass to component constructor
        
    Returns:
        Component instance
        
    Raises:
        ImportError: If module or class cannot be imported
    """
    if '.' not in class_path:
        raise ImportError(f"Invalid class path: {class_path}. Expected format: 'module.class'")
    
    module_path, class_name = class_path.rsplit('.', 1)
    
    try:
        module = importlib.import_module(module_path)
        component_class = getattr(module, class_name)
        return component_class(*args, **kwargs)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Failed to import {class_path}: {e}")


def extract_class_name(full_path: str) -> str:
    """Extract class name from full module path for backward compatibility."""
    return full_path.split('.')[-1]