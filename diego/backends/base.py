from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseBackend(ABC):
    """Abstract base class for news backend implementations."""

    @abstractmethod
    def __init__(self, api_key: str):
        pass

    @abstractmethod
    def get_top_headlines(
        self,
        query: Optional[str] = None,
        country: str = "us",
        category: Optional[str] = None,
        sources: Optional[str] = None,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Get current breaking news and top stories."""
        pass

    @abstractmethod
    def search_articles(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Search through all articles with keywords or phrases."""
        pass

    @abstractmethod
    def get_sources(
        self, 
        category: Optional[str] = None, 
        country: Optional[str] = None, 
        language: str = "en"
    ) -> Dict[str, Any]:
        """Get list of available news sources."""
        pass

    def _validate_page_size(self, page_size: int, max_size: int = 100) -> None:
        if not isinstance(page_size, int) or page_size < 1 or page_size > max_size:
            raise ValueError(f"page_size must be an integer between 1 and {max_size}")

    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        return {
            "status": "error", 
            "message": str(error), 
            "code": "client_error"
        }

    def _standardize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        if response.get("status") == "ok":
            if "totalResults" not in response:
                response["totalResults"] = len(response.get("articles", []))
            if "articles" not in response:
                response["articles"] = []
            return response
        else:
            return {
                "status": "error",
                "message": response.get("message", "Unknown API error"),
                "code": response.get("code", "unknown"),
            }