"""
DocMind AI Configuration Module
"""

from .settings import config, Config, get_database_url, get_storage_path, is_production

__all__ = ["config", "Config", "get_database_url", "get_storage_path", "is_production"]