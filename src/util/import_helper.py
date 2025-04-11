"""
Import Helper Module for GraphRAG.

This module provides helper functions to import modules in a way that works
in both local development and Heroku deployment environments.
"""

import importlib
import sys
from typing import Any, Dict, List, Callable


def import_module(module_path: str) -> Any:
    """
    Import a module using either local or Heroku path format.
    
    Args:
        module_path: The module path to import (e.g., 'util.debug')
        
    Returns:
        The imported module
        
    Raises:
        ImportError: If the module cannot be imported in either format
    """
    try:
        # Try local import path first
        return importlib.import_module(module_path)
    except ModuleNotFoundError:
        # Fall back to Heroku import path
        try:
            return importlib.import_module(f"src.{module_path}")
        except ModuleNotFoundError:
            # Re-raise the original error with a more helpful message
            raise ImportError(
                f"Could not import '{module_path}' in either local or Heroku format. "
                f"Tried both '{module_path}' and 'src.{module_path}'."
            )


def import_from(module_path: str, name: str) -> Any:
    """
    Import a specific object from a module using either local or Heroku path format.
    
    Args:
        module_path: The module path to import from (e.g., 'util.debug')
        name: The name of the object to import (e.g., 'debug_print')
        
    Returns:
        The imported object
        
    Raises:
        ImportError: If the object cannot be imported in either format
    """
    try:
        # Try local import path first
        module = importlib.import_module(module_path)
        return getattr(module, name)
    except (ModuleNotFoundError, AttributeError):
        # Fall back to Heroku import path
        try:
            module = importlib.import_module(f"src.{module_path}")
            return getattr(module, name)
        except (ModuleNotFoundError, AttributeError):
            # Re-raise the original error with a more helpful message
            raise ImportError(
                f"Could not import '{name}' from '{module_path}' in either local or Heroku format. "
                f"Tried both '{module_path}' and 'src.{module_path}'."
            )


# Common imports used throughout the application
def get_debug_print() -> Callable:
    """Get the debug_print function from util.debug"""
    return import_from('util.debug', 'debug_print')


def get_llm_type() -> Any:
    """Get the LLMType enum from llm.providers.base"""
    return import_from('llm.providers.base', 'LLMType')


def get_config_functions() -> Dict[str, Callable]:
    """Get common configuration functions"""
    return {
        'get_api_key': import_from('util.config', 'get_api_key'),
        'load_environment_variables': import_from('util.config', 'load_environment_variables')
    }


def is_heroku_environment() -> bool:
    """
    Detect if the application is running in a Heroku environment.
    
    Returns:
        True if running on Heroku, False otherwise
    """
    return 'DYNO' in sys.modules or 'PORT' in sys.modules


def patch_imports() -> None:
    """
    Patch the import system to handle both local and Heroku imports.
    Call this at the start of your application to automatically handle imports.
    """
    # This is a placeholder for future implementation if needed
    pass
