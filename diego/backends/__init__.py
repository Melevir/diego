"""
News API Backends

This package contains the news API client implementations with a common interface.
"""

from .base import BaseBackend
from .newsapi_client import NewsApiBackend  
from .guardian_client import GuardianBackend

__all__ = ['BaseBackend', 'NewsApiBackend', 'GuardianBackend']