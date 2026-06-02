"""
DocMind AI - Main Package
Intelligent Document Change Intelligence Platform
"""

__version__ = "1.0.0"
__author__ = "DocMind AI Team"
__description__ = "Enterprise-grade document comparison and analysis platform"

from .config import config, Config, get_database_url, get_storage_path, is_production

__all__ = [
    "config",
    "Config",
    "get_database_url",
    "get_storage_path",
    "is_production"
]