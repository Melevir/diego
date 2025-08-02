import os
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from config import Config
from news_org_api_client import NewsOrgApiClient


@pytest.fixture
def valid_env_vars() -> Dict[str, str]:
    """Valid environment variables for testing."""
    return {
        'NEWS_API_KEY': 'test-api-key-12345',
        'NEWS_DEFAULT_COUNTRY': 'us',
        'NEWS_DEFAULT_LANGUAGE': 'en',
        'NEWS_DEFAULT_PAGE_SIZE': '10',
        'NEWS_MAX_PAGE_SIZE': '100',
        'NEWS_DEFAULT_FORMAT': 'simple',
        'APP_VERSION': '1.0.0'
    }


@pytest.fixture
def invalid_env_vars() -> Dict[str, str]:
    """Invalid environment variables for testing.""" 
    return {
        'NEWS_DEFAULT_COUNTRY': 'invalid',  # Should be 2 letters
        'NEWS_DEFAULT_LANGUAGE': 'invalid',  # Should be 2 letters
        'NEWS_DEFAULT_PAGE_SIZE': '0',  # Should be > 0
        'NEWS_DEFAULT_FORMAT': 'invalid'  # Should be simple/detailed/json
    }


@pytest.fixture
def config(valid_env_vars: Dict[str, str]) -> Config:
    """Valid config instance."""
    with patch.dict(os.environ, valid_env_vars, clear=True):
        return Config.from_env()


@pytest.fixture
def invalid_config(invalid_env_vars: Dict[str, str]) -> Config:
    """Invalid config instance."""
    with patch.dict(os.environ, invalid_env_vars, clear=True):
        return Config.from_env()


@pytest.fixture
def news_api_response() -> Dict[str, Any]:
    """Mock successful News API response."""
    return {
        'status': 'ok',
        'totalResults': 2,
        'articles': [
            {
                'title': 'Test Article 1',
                'description': 'Test description 1',
                'url': 'https://example.com/1',
                'publishedAt': '2024-01-01T12:00:00Z',
                'source': {'name': 'Test Source'},
                'author': 'Test Author'
            },
            {
                'title': 'Test Article 2',
                'description': 'Test description 2', 
                'url': 'https://example.com/2',
                'publishedAt': '2024-01-02T12:00:00Z',
                'source': {'name': 'Another Source'},
                'author': 'Another Author'
            }
        ]
    }


@pytest.fixture
def news_api_error_response() -> Dict[str, Any]:
    """Mock error News API response."""
    return {
        'status': 'error',
        'code': 'apiKeyInvalid',
        'message': 'Your API key is invalid or incorrect.'
    }


@pytest.fixture
def sources_response() -> Dict[str, Any]:
    """Mock successful sources API response."""
    return {
        'status': 'ok',
        'sources': [
            {
                'id': 'test-source',
                'name': 'Test Source',
                'description': 'A test news source',
                'category': 'technology',
                'country': 'us',
                'language': 'en',
                'url': 'https://testsource.com'
            }
        ]
    }


@pytest.fixture
def mocked_newsapi_client():
    """Mock NewsApiClient from newsapi-python library."""
    with patch('news_org_api_client.NewsApiClient') as mock:
        yield mock


@pytest.fixture
def news_client(config: Config, mocked_newsapi_client) -> NewsOrgApiClient:
    """NewsOrgApiClient instance with mocked dependencies."""
    return NewsOrgApiClient(config.news_api_key)