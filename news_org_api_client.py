from typing import Optional, Dict, Any
from newsapi import NewsApiClient


class NewsOrgApiClient:
    """
    Simplified wrapper for newsapi-python library.

    Provides easy-to-use methods for the most common News API operations
    with sensible defaults and simplified signatures.
    """

    def __init__(self, api_key: str):
        """
        Initialize the News API client.

        Args:
            api_key: Your News API key from newsapi.org
        """
        self._client = NewsApiClient(api_key=api_key)

    def _validate_page_size(self, page_size: int) -> None:
        """Validate page_size parameter."""
        if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
            raise ValueError("page_size must be an integer between 1 and 100")

    def get_top_headlines(
        self,
        query: Optional[str] = None,
        country: str = "us",
        category: Optional[str] = None,
        sources: Optional[str] = None,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Get current breaking news and top stories.

        Args:
            query: Keywords or phrases to search for in headlines
            country: 2-letter ISO country code (default: 'us')
            category: News category (business, entertainment, general, health, science, sports, technology)
            sources: Comma-separated news source IDs (e.g., 'bbc-news,cnn')
            page_size: Number of articles to return (max 100, default: 20)

        Returns:
            Dictionary containing articles and metadata

        Example:
            >>> client = NewsOrgApiClient('your-api-key')
            >>> headlines = client.get_top_headlines(query='bitcoin', country='us')
            >>> print(f"Found {headlines['totalResults']} articles")
        """
        try:
            self._validate_page_size(page_size)
            response = self._client.get_top_headlines(
                q=query,
                country=country if not sources else None,  # country and sources are mutually exclusive
                category=category,
                sources=sources,
                page_size=page_size,
            )
            return self._handle_response(response)
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
        """
        Search through all articles with keywords or phrases.

        Args:
            query: Keywords or phrases to search for (required)
            from_date: Search from this date (YYYY-MM-DD format)
            to_date: Search to this date (YYYY-MM-DD format)
            language: 2-letter language code (default: 'en')
            sort_by: Sort order ('relevancy', 'popularity', 'publishedAt')
            page_size: Number of articles to return (max 100, default: 20)

        Returns:
            Dictionary containing articles and metadata

        Example:
            >>> client = NewsOrgApiClient('your-api-key')
            >>> articles = client.search_articles('artificial intelligence', from_date='2024-01-01')
            >>> for article in articles['articles']:
            ...     print(article['title'])
        """
        try:
            self._validate_page_size(page_size)
            response = self._client.get_everything(
                q=query, from_param=from_date, to=to_date, language=language, sort_by=sort_by, page_size=page_size
            )
            return self._handle_response(response)
        except Exception as e:
            return self._handle_error(e)

    def get_sources(
        self, category: Optional[str] = None, country: Optional[str] = None, language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get list of available news sources.

        Args:
            category: Filter by category (business, entertainment, general, health, science, sports, technology)
            country: Filter by 2-letter ISO country code
            language: Filter by 2-letter language code (default: 'en')

        Returns:
            Dictionary containing sources and metadata

        Example:
            >>> client = NewsOrgApiClient('your-api-key')
            >>> sources = client.get_sources(category='technology')
            >>> for source in sources['sources']:
            ...     print(f"{source['name']}: {source['description']}")
        """
        try:
            response = self._client.get_sources(category=category, country=country, language=language)
            return self._handle_response(response)
        except Exception as e:
            return self._handle_error(e)

    def _handle_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful API responses."""
        if response.get("status") == "ok":
            return response
        else:
            return {
                "status": "error",
                "message": response.get("message", "Unknown API error"),
                "code": response.get("code", "unknown"),
            }

    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle API errors and exceptions."""
        return {"status": "error", "message": str(error), "code": "client_error"}
