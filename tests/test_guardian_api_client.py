import pytest
from unittest.mock import Mock, patch
import requests

from diego.backends import GuardianBackend


@pytest.fixture
def guardian_client():
    return GuardianBackend("test-api-key")


@pytest.fixture
def mock_guardian_response():
    return {
        "response": {
            "status": "ok",
            "total": 1000,
            "startIndex": 1,
            "pageSize": 20,
            "currentPage": 1,
            "pages": 50,
            "orderBy": "newest",
            "results": [
                {
                    "id": "technology/2025/aug/02/ai-breakthrough",
                    "type": "article",
                    "sectionId": "technology",
                    "sectionName": "Technology",
                    "webPublicationDate": "2025-08-02T10:30:00Z",
                    "webTitle": "AI breakthrough changes everything",
                    "webUrl": "https://www.theguardian.com/technology/2025/aug/02/ai-breakthrough",
                    "apiUrl": "https://content.guardianapis.com/technology/2025/aug/02/ai-breakthrough",
                    "fields": {
                        "headline": "AI breakthrough changes everything",
                        "standfirst": "Revolutionary AI development promises to transform technology landscape",
                        "byline": "Tech Reporter",
                        "body": "<p>This is the full article content with HTML tags...</p>",
                        "wordcount": "500",
                        "firstPublicationDate": "2025-08-02T10:30:00Z",
                    },
                },
                {
                    "id": "business/2025/aug/02/market-update",
                    "type": "article",
                    "sectionId": "business",
                    "sectionName": "Business",
                    "webPublicationDate": "2025-08-02T09:15:00Z",
                    "webTitle": "Markets surge on positive news",
                    "webUrl": "https://www.theguardian.com/business/2025/aug/02/market-update",
                    "apiUrl": "https://content.guardianapis.com/business/2025/aug/02/market-update",
                    "fields": {
                        "headline": "Markets surge on positive news",
                        "standfirst": "Stock markets rise following encouraging economic indicators",
                        "byline": "Business Correspondent",
                        "body": "<p>Markets showed strong performance today...</p>",
                        "wordcount": "350",
                    },
                },
            ],
        }
    }


@pytest.fixture
def mock_sections_response():
    return {
        "response": {
            "status": "ok",
            "total": 5,
            "results": [
                {
                    "id": "technology",
                    "webTitle": "Technology",
                    "webUrl": "https://www.theguardian.com/technology",
                    "apiUrl": "https://content.guardianapis.com/technology",
                },
                {
                    "id": "business",
                    "webTitle": "Business",
                    "webUrl": "https://www.theguardian.com/business",
                    "apiUrl": "https://content.guardianapis.com/business",
                },
                {
                    "id": "sport",
                    "webTitle": "Sport",
                    "webUrl": "https://www.theguardian.com/sport",
                    "apiUrl": "https://content.guardianapis.com/sport",
                },
            ],
        }
    }


@pytest.fixture
def mock_error_response():
    return {"response": {"status": "error", "message": "Invalid API key", "code": "invalid-api-key"}}


class TestGuardianBackendInit:
    def test_init_creates_client_with_api_key(self):
        """Test that GuardianBackend initializes with API key."""
        api_key = "test-key-123"
        client = GuardianBackend(api_key)

        assert client.api_key == api_key
        assert client.base_url == "https://content.guardianapis.com"
        assert client._sections_cache is None


class TestGetTopHeadlines:
    @patch("diego.backends.guardian_client.requests.get")
    def test_get_top_headlines_success(self, mock_get, guardian_client, mock_guardian_response):
        """Test successful get_top_headlines call."""
        mock_get.return_value.json.return_value = mock_guardian_response
        mock_get.return_value.raise_for_status.return_value = None

        result = guardian_client.get_top_headlines(query="technology", country="us")

        assert result["status"] == "ok"
        assert result["totalResults"] == 1000
        assert len(result["articles"]) == 2

        # Check first article format
        article = result["articles"][0]
        assert article["title"] == "AI breakthrough changes everything"
        assert article["source"]["name"] == "The Guardian"
        assert article["author"] == "Tech Reporter"
        assert "Revolutionary AI development" in article["description"]

    @patch("diego.backends.guardian_client.requests.get")
    def test_get_top_headlines_with_category_mapping(self, mock_get, guardian_client, mock_guardian_response):
        """Test that category parameter is mapped to Guardian sections."""
        mock_get.return_value.json.return_value = mock_guardian_response
        mock_get.return_value.raise_for_status.return_value = None

        guardian_client.get_top_headlines(category="technology", page_size=10)

        # Verify the API was called with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        params = call_args[1]["params"]

        assert params["section"] == "technology"
        assert params["page-size"] == 10
        assert params["order-by"] == "newest"

    @patch("diego.backends.guardian_client.requests.get")
    def test_get_top_headlines_with_country_mapping(self, mock_get, guardian_client, mock_guardian_response):
        """Test that country parameter is mapped to Guardian editions."""
        mock_get.return_value.json.return_value = mock_guardian_response
        mock_get.return_value.raise_for_status.return_value = None

        guardian_client.get_top_headlines(country="uk")

        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert params["edition"] == "uk"

    def test_get_top_headlines_validates_page_size(self, guardian_client):
        """Test that get_top_headlines validates page_size parameter."""
        # Test invalid page sizes
        result = guardian_client.get_top_headlines(page_size=0)
        assert result["status"] == "error"
        assert "page_size must be an integer between 1 and 200" in result["message"]

        result = guardian_client.get_top_headlines(page_size=250)
        assert result["status"] == "error"
        assert "page_size must be an integer between 1 and 200" in result["message"]

    @patch("diego.backends.guardian_client.requests.get")
    def test_get_top_headlines_handles_api_error(self, mock_get, guardian_client, mock_error_response):
        """Test handling of Guardian API errors."""
        mock_get.return_value.json.return_value = mock_error_response
        mock_get.return_value.raise_for_status.return_value = None

        result = guardian_client.get_top_headlines()

        assert result["status"] == "error"
        assert "Invalid API key" in result["message"]


class TestSearchArticles:
    @patch("diego.backends.guardian_client.requests.get")
    def test_search_articles_success(self, mock_get, guardian_client, mock_guardian_response):
        """Test successful search_articles call."""
        mock_get.return_value.json.return_value = mock_guardian_response
        mock_get.return_value.raise_for_status.return_value = None

        result = guardian_client.search_articles(
            query="artificial intelligence", from_date="2025-01-01", to_date="2025-08-01"
        )

        assert result["status"] == "ok"
        assert result["totalResults"] == 1000
        assert len(result["articles"]) == 2

    @patch("diego.backends.guardian_client.requests.get")
    def test_search_articles_with_date_filters(self, mock_get, guardian_client, mock_guardian_response):
        """Test search_articles with date filtering."""
        mock_get.return_value.json.return_value = mock_guardian_response
        mock_get.return_value.raise_for_status.return_value = None

        guardian_client.search_articles(query="test", from_date="2025-01-01", to_date="2025-08-01")

        call_args = mock_get.call_args
        params = call_args[1]["params"]

        assert params["from-date"] == "2025-01-01"
        assert params["to-date"] == "2025-08-01"
        assert params["q"] == "test"

    @patch("diego.backends.guardian_client.requests.get")
    def test_search_articles_sort_mapping(self, mock_get, guardian_client, mock_guardian_response):
        """Test that sort_by parameter is mapped correctly."""
        mock_get.return_value.json.return_value = mock_guardian_response
        mock_get.return_value.raise_for_status.return_value = None

        # Test relevancy mapping
        guardian_client.search_articles(query="test", sort_by="relevancy")
        params = mock_get.call_args[1]["params"]
        assert params["order-by"] == "relevance"

        # Test publishedAt mapping
        mock_get.reset_mock()
        guardian_client.search_articles(query="test", sort_by="publishedAt")
        params = mock_get.call_args[1]["params"]
        assert params["order-by"] == "newest"

    def test_search_articles_validates_page_size(self, guardian_client):
        """Test that search_articles validates page_size parameter."""
        result = guardian_client.search_articles(query="test", page_size=300)
        assert result["status"] == "error"
        assert "page_size must be an integer between 1 and 200" in result["message"]


class TestGetSources:
    @patch("diego.backends.guardian_client.requests.get")
    def test_get_sources_success(self, mock_get, guardian_client, mock_sections_response):
        """Test successful get_sources call."""
        mock_get.return_value.json.return_value = mock_sections_response
        mock_get.return_value.raise_for_status.return_value = None

        result = guardian_client.get_sources()

        assert result["status"] == "ok"
        assert len(result["sources"]) == 3

        # Check source format
        source = result["sources"][0]
        assert "guardian-" in source["id"]
        assert "The Guardian -" in source["name"]
        assert source["language"] == "en"
        assert "url" in source

    @patch("diego.backends.guardian_client.requests.get")
    def test_get_sources_with_category_filter(self, mock_get, guardian_client, mock_sections_response):
        """Test get_sources with category filtering."""
        mock_get.return_value.json.return_value = mock_sections_response
        mock_get.return_value.raise_for_status.return_value = None

        result = guardian_client.get_sources(category="technology")

        # Should only return technology section
        assert result["status"] == "ok"
        assert len(result["sources"]) == 1
        assert "Technology" in result["sources"][0]["name"]

    @patch("diego.backends.guardian_client.requests.get")
    def test_get_sources_caches_sections(self, mock_get, guardian_client, mock_sections_response):
        """Test that get_sources caches sections response."""
        mock_get.return_value.json.return_value = mock_sections_response
        mock_get.return_value.raise_for_status.return_value = None

        # First call should make API request
        guardian_client.get_sources()
        assert mock_get.call_count == 1

        # Second call should use cache
        guardian_client.get_sources()
        assert mock_get.call_count == 1  # No additional API call


class TestResponseNormalization:
    def test_normalize_response_success(self, guardian_client, mock_guardian_response):
        """Test successful response normalization."""
        result = guardian_client._normalize_response(mock_guardian_response)

        assert result["status"] == "ok"
        assert result["totalResults"] == 1000
        assert len(result["articles"]) == 2

        article = result["articles"][0]
        assert article["title"] == "AI breakthrough changes everything"
        assert article["source"]["id"] == "the-guardian"
        assert article["author"] == "Tech Reporter"

    def test_extract_description_from_standfirst(self, guardian_client):
        """Test description extraction from standfirst field."""
        item = {"fields": {"standfirst": "<p>This is a <strong>test</strong> standfirst</p>"}}

        description = guardian_client._extract_description(item)
        assert description == "This is a test standfirst"

    def test_extract_author_from_byline(self, guardian_client):
        """Test author extraction from byline field."""
        item = {"fields": {"byline": "By John Smith"}}

        author = guardian_client._extract_author(item)
        assert author == "John Smith"

    def test_extract_content_from_body(self, guardian_client):
        """Test content extraction from body field."""
        long_body = "<p>" + "A" * 600 + "</p>"
        item = {"fields": {"body": long_body}}

        content = guardian_client._extract_content(item)
        assert len(content) <= 503  # 500 chars + "..."
        assert content.endswith("...")


class TestErrorHandling:
    @patch("diego.backends.guardian_client.requests.get")
    def test_handles_http_401_error(self, mock_get, guardian_client):
        """Test handling of 401 Unauthorized error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Error")
        mock_get.return_value = mock_response

        result = guardian_client.get_top_headlines()

        assert result["status"] == "error"
        assert "Invalid API key" in result["message"]

    @patch("diego.backends.guardian_client.requests.get")
    def test_handles_http_429_error(self, mock_get, guardian_client):
        """Test handling of 429 Rate Limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Error")
        mock_get.return_value = mock_response

        result = guardian_client.search_articles(query="test")

        assert result["status"] == "error"
        assert "Rate limit exceeded" in result["message"]

    @patch("diego.backends.guardian_client.requests.get")
    def test_handles_network_error(self, mock_get, guardian_client):
        """Test handling of network errors."""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

        result = guardian_client.get_sources()

        assert result["status"] == "error"
        assert "Network error" in result["message"]

    def test_handles_invalid_response_format(self, guardian_client):
        """Test handling of invalid Guardian API response format."""
        invalid_response = {"invalid": "format"}

        result = guardian_client._normalize_response(invalid_response)

        assert result["status"] == "error"
        assert "Invalid Guardian API response format" in result["message"]


class TestParameterMapping:
    def test_category_mapping(self, guardian_client):
        """Test NewsAPI category to Guardian section mapping."""
        assert guardian_client.CATEGORY_MAPPING["technology"] == "technology"
        assert guardian_client.CATEGORY_MAPPING["sports"] == "sport"
        assert guardian_client.CATEGORY_MAPPING["entertainment"] == "culture"

    def test_edition_mapping(self, guardian_client):
        """Test country to Guardian edition mapping."""
        assert guardian_client.EDITION_MAPPING["us"] == "us"
        assert guardian_client.EDITION_MAPPING["uk"] == "uk"
        assert guardian_client.EDITION_MAPPING["au"] == "au"

    def test_sort_mapping(self, guardian_client):
        """Test sort order mapping."""
        assert guardian_client.SORT_MAPPING["publishedAt"] == "newest"
        assert guardian_client.SORT_MAPPING["relevancy"] == "relevance"
        assert guardian_client.SORT_MAPPING["popularity"] == "newest"

    def test_map_section_to_category(self, guardian_client):
        """Test reverse mapping from Guardian section to NewsAPI category."""
        assert guardian_client._map_section_to_category("technology") == "technology"
        assert guardian_client._map_section_to_category("sport") == "sports"
        assert guardian_client._map_section_to_category("unknown") == "general"


class TestCompatibilityWithNewsOrgApiClient:
    """Test compatibility with NewsOrgApiClient interface."""

    def test_has_same_public_methods(self, guardian_client):
        """Test that GuardianBackend has same public methods as NewsApiBackend."""
        expected_methods = ["get_top_headlines", "search_articles", "get_sources"]

        for method_name in expected_methods:
            assert hasattr(guardian_client, method_name)
            assert callable(getattr(guardian_client, method_name))

    def test_method_signatures_compatible(self, guardian_client):
        """Test that method signatures are compatible with NewsOrgApiClient."""
        import inspect

        # Check get_top_headlines signature
        sig = inspect.signature(guardian_client.get_top_headlines)
        expected_params = ["query", "country", "category", "sources", "page_size"]
        actual_params = list(sig.parameters.keys())
        assert actual_params == expected_params

        # Check search_articles signature
        sig = inspect.signature(guardian_client.search_articles)
        expected_params = ["query", "from_date", "to_date", "language", "sort_by", "page_size"]
        actual_params = list(sig.parameters.keys())
        assert actual_params == expected_params

        # Check get_sources signature
        sig = inspect.signature(guardian_client.get_sources)
        expected_params = ["category", "country", "language"]
        actual_params = list(sig.parameters.keys())
        assert actual_params == expected_params
