from typing import Optional, Dict, Any
from newsapi import NewsApiClient as NewsApiLibClient

from .base import BaseBackend


class NewsApiBackend(BaseBackend):
    """NewsAPI.org backend implementation."""

    def __init__(self, api_key: str):
        self._client = NewsApiLibClient(api_key=api_key)

    def get_top_headlines(
        self,
        query: Optional[str] = None,
        country: str = "us",
        category: Optional[str] = None,
        sources: Optional[str] = None,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        try:
            self._validate_page_size(page_size, max_size=100)
            response = self._client.get_top_headlines(
                q=query,
                country=country if not sources else None,
                category=category,
                sources=sources,
                page_size=page_size,
            )
            return self._standardize_response(response)
        except Exception as e:
            return self._handle_error(e)

    def search_articles(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20,
    ) -> Dict[str, Any]:
        try:
            self._validate_page_size(page_size, max_size=100)
            response = self._client.get_everything(
                q=query, from_param=from_date, to=to_date, language=language, sort_by=sort_by, page_size=page_size
            )
            return self._standardize_response(response)
        except Exception as e:
            return self._handle_error(e)

    def get_sources(
        self, category: Optional[str] = None, country: Optional[str] = None, language: str = "en"
    ) -> Dict[str, Any]:
        try:
            response = self._client.get_sources(category=category, country=country, language=language)
            return self._standardize_response(response)
        except Exception as e:
            return self._handle_error(e)