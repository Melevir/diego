from typing import Optional, Dict, Any
import requests

from .base import BaseBackend


class GuardianBackend(BaseBackend):
    """Guardian API backend implementation."""

    CATEGORY_MAPPING = {
        "business": "business",
        "technology": "technology",
        "science": "science",
        "sports": "sport",
        "health": "lifeandstyle",
        "entertainment": "culture",
        "general": "news",
    }

    EDITION_MAPPING = {"us": "us", "uk": "uk", "au": "au"}

    SORT_MAPPING = {"publishedAt": "newest", "relevancy": "relevance", "popularity": "newest"}

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://content.guardianapis.com"
        self._sections_cache = None

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params["api-key"] = self.api_key

        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                return self._handle_error(Exception("Invalid API key"))
            elif response.status_code == 429:
                return self._handle_error(Exception("Rate limit exceeded. Please wait and try again."))
            else:
                return self._handle_error(Exception(f"HTTP {response.status_code}: {str(e)}"))

        except requests.exceptions.RequestException as e:
            return self._handle_error(Exception(f"Network error: {str(e)}"))

        except Exception as e:
            return self._handle_error(e)

    def get_top_headlines(
        self,
        query: Optional[str] = None,
        country: str = "us",
        category: Optional[str] = None,
        sources: Optional[str] = None,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        try:
            self._validate_page_size(page_size, max_size=200)

            params = {"page-size": page_size, "order-by": "newest", "show-fields": "all"}

            if query:
                params["q"] = query

            if category and category in self.CATEGORY_MAPPING:
                params["section"] = self.CATEGORY_MAPPING[category]
            if country in self.EDITION_MAPPING:
                params["edition"] = self.EDITION_MAPPING[country]

                if sources:
                    pass

            response = self._make_request("/search", params)

            if response.get("status") == "error":
                return response

            return self._normalize_response(response)

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
            self._validate_page_size(page_size, max_size=200)

            params = {"q": query, "page-size": page_size, "show-fields": "all"}

            if from_date:
                params["from-date"] = from_date
            if to_date:
                params["to-date"] = to_date

            if sort_by in self.SORT_MAPPING:
                params["order-by"] = self.SORT_MAPPING[sort_by]
            else:
                params["order-by"] = "newest"

            response = self._make_request("/search", params)

            if response.get("status") == "error":
                return response

            return self._normalize_response(response)

        except Exception as e:
            return self._handle_error(e)

    def get_sources(
        self, category: Optional[str] = None, country: Optional[str] = None, language: str = "en"
    ) -> Dict[str, Any]:
        try:
            if self._sections_cache is None:
                response = self._make_request("/sections", {})
                if response.get("status") == "error":
                    return response
                self._sections_cache = response
            else:
                response = self._sections_cache

            if "response" not in response or "results" not in response["response"]:
                return self._handle_error(Exception("Invalid sections response from Guardian API"))

            sections = response["response"]["results"]
            sources = []

            for section in sections:
                if category:
                    guardian_section = self.CATEGORY_MAPPING.get(category)
                    if guardian_section and section["id"] != guardian_section:
                        continue

                source = {
                    "id": f"guardian-{section['id']}",
                    "name": f"The Guardian - {section['webTitle']}",
                    "description": f"The Guardian's {section['webTitle']} section",
                    "url": section["webUrl"],
                    "category": self._map_section_to_category(section["id"]),
                    "language": "en",
                    "country": country if country in self.EDITION_MAPPING else "us",
                }
                sources.append(source)

            return {"status": "ok", "sources": sources}

        except Exception as e:
            return self._handle_error(e)

    def _map_section_to_category(self, section_id: str) -> str:
        reverse_mapping = {v: k for k, v in self.CATEGORY_MAPPING.items()}
        return reverse_mapping.get(section_id, "general")

    def _normalize_response(self, guardian_response: Dict[str, Any]) -> Dict[str, Any]:
        if "response" not in guardian_response:
            return self._handle_error(Exception("Invalid Guardian API response format"))

        guardian_data = guardian_response["response"]

        if guardian_data.get("status") != "ok":
            return {
                "status": "error",
                "message": guardian_data.get("message", "Guardian API error"),
                "code": "guardian_api_error",
            }

        articles = []

        for item in guardian_data.get("results", []):
            article = {
                "title": item.get("webTitle", "No title"),
                "description": self._extract_description(item),
                "url": item.get("webUrl", ""),
                "source": {"id": "the-guardian", "name": "The Guardian"},
                "author": self._extract_author(item),
                "publishedAt": item.get("webPublicationDate", ""),
                "content": self._extract_content(item),
            }
            articles.append(article)

        return {"status": "ok", "totalResults": guardian_data.get("total", 0), "articles": articles}

    def _extract_description(self, item: Dict[str, Any]) -> str:
        fields = item.get("fields", {})

        if fields.get("standfirst"):
            import re

            return re.sub(r"<[^>]+>", "", fields["standfirst"]).strip()
        elif fields.get("trailText"):
            return fields["trailText"].strip()
        elif fields.get("body"):
            import re

            clean_body = re.sub(r"<[^>]+>", "", fields["body"])
            return clean_body[:200].strip() + ("..." if len(clean_body) > 200 else "")

        return "No description available"

    def _extract_author(self, item: Dict[str, Any]) -> str:
        fields = item.get("fields", {})
        byline = fields.get("byline", "")

        if byline:
            byline = byline.replace("By ", "").strip()
            return byline if byline else "The Guardian"

        return "The Guardian"

    def _extract_content(self, item: Dict[str, Any]) -> str:
        fields = item.get("fields", {})

        if fields.get("body"):
            import re

            clean_content = re.sub(r"<[^>]+>", "", fields["body"])
            return clean_content[:500].strip() + ("..." if len(clean_content) > 500 else "")

        return self._extract_description(item)
