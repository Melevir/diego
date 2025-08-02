import pytest
from typing import Dict, Any

from diego.backends import NewsApiBackend


async def test__news_org_api_client_init__creates_underlying_client(mocked_newsapi_client, config) -> None:
    """Test NewsApiBackend initialization creates underlying client."""
    api_key = "test-api-key"
    NewsApiBackend(api_key)

    # Verify the underlying NewsApiClient was initialized with correct API key
    mocked_newsapi_client.assert_called_once_with(api_key=api_key)


async def test__get_top_headlines__success_with_query(
    news_client: NewsApiBackend, news_api_response: Dict[str, Any]
) -> None:
    """Test successful get_top_headlines call with query."""
    # Setup mock
    news_client._client.get_top_headlines.return_value = news_api_response

    # Call method
    result = news_client.get_top_headlines(query="bitcoin", country="us")

    # Verify call
    news_client._client.get_top_headlines.assert_called_once_with(
        q="bitcoin", country="us", category=None, sources=None, page_size=20
    )

    # Verify result
    assert result == news_api_response
    assert result["status"] == "ok"
    assert len(result["articles"]) == 2


async def test__get_top_headlines__with_sources_excludes_country(
    news_client: NewsApiBackend, news_api_response: Dict[str, Any]
) -> None:
    """Test that country is excluded when sources is provided (API requirement)."""
    news_client._client.get_top_headlines.return_value = news_api_response

    news_client.get_top_headlines(sources="bbc-news,cnn", country="us")

    # Verify country is set to None when sources is provided
    news_client._client.get_top_headlines.assert_called_once_with(
        q=None,
        country=None,  # Should be None when sources is provided
        category=None,
        sources="bbc-news,cnn",
        page_size=20,
    )


@pytest.mark.parametrize(
    ["query", "country", "category", "page_size"],
    [
        ("technology", "uk", "technology", 50),
        ("bitcoin", "us", None, 25),
        (None, "fr", "business", 10),
    ],
)
async def test__get_top_headlines__with_various_parameters(
    news_client: NewsApiBackend,
    news_api_response: Dict[str, Any],
    query: str,
    country: str,
    category: str,
    page_size: int,
) -> None:
    """Test get_top_headlines with various parameter combinations."""
    news_client._client.get_top_headlines.return_value = news_api_response

    news_client.get_top_headlines(query=query, country=country, category=category, page_size=page_size)

    news_client._client.get_top_headlines.assert_called_once_with(
        q=query, country=country, category=category, sources=None, page_size=page_size
    )


async def test__get_top_headlines__api_error_response(
    news_client: NewsApiBackend, news_api_error_response: Dict[str, Any]
) -> None:
    """Test get_top_headlines with API error response."""
    news_client._client.get_top_headlines.return_value = news_api_error_response

    result = news_client.get_top_headlines()

    assert result["status"] == "error"
    assert result["message"] == "Your API key is invalid or incorrect."
    assert result["code"] == "apiKeyInvalid"


async def test__get_top_headlines__handles_exception(news_client: NewsApiBackend) -> None:
    """Test get_top_headlines with exception handling."""
    # Setup mock to raise exception
    news_client._client.get_top_headlines.side_effect = Exception("Network error")

    result = news_client.get_top_headlines()

    assert result["status"] == "error"
    assert result["message"] == "Network error"
    assert result["code"] == "client_error"


async def test__search_articles__success_with_dates(
    news_client: NewsApiBackend, news_api_response: Dict[str, Any]
) -> None:
    """Test successful search_articles call with date filtering."""
    news_client._client.get_everything.return_value = news_api_response

    result = news_client.search_articles(query="artificial intelligence", from_date="2024-01-01", to_date="2024-01-31")

    news_client._client.get_everything.assert_called_once_with(
        q="artificial intelligence",
        from_param="2024-01-01",
        to="2024-01-31",
        language="en",
        sort_by="publishedAt",
        page_size=20,
    )

    assert result == news_api_response
    assert result["status"] == "ok"


@pytest.mark.parametrize(
    ["language", "sort_by", "page_size"],
    [
        ("fr", "popularity", 50),
        ("es", "relevancy", 25),
        ("de", "publishedAt", 10),
    ],
)
async def test__search_articles__with_various_options(
    news_client: NewsApiBackend, news_api_response: Dict[str, Any], language: str, sort_by: str, page_size: int
) -> None:
    """Test search_articles with various language and sorting options."""
    news_client._client.get_everything.return_value = news_api_response

    news_client.search_articles(query="bitcoin", language=language, sort_by=sort_by, page_size=page_size)

    news_client._client.get_everything.assert_called_once_with(
        q="bitcoin", from_param=None, to=None, language=language, sort_by=sort_by, page_size=page_size
    )


async def test__search_articles__minimal_required_parameter(
    news_client: NewsApiBackend, news_api_response: Dict[str, Any]
) -> None:
    """Test search_articles with only required parameter."""
    news_client._client.get_everything.return_value = news_api_response

    news_client.search_articles(query="test")

    news_client._client.get_everything.assert_called_once_with(
        q="test", from_param=None, to=None, language="en", sort_by="publishedAt", page_size=20
    )


async def test__search_articles__handles_exception(news_client: NewsApiBackend) -> None:
    """Test search_articles exception handling."""
    news_client._client.get_everything.side_effect = ValueError("Invalid query")

    result = news_client.search_articles(query="test")

    assert result["status"] == "error"
    assert result["message"] == "Invalid query"
    assert result["code"] == "client_error"


async def test__get_sources__success_with_filters(
    news_client: NewsApiBackend, sources_response: Dict[str, Any]
) -> None:
    """Test successful get_sources call with category and country filters."""
    news_client._client.get_sources.return_value = sources_response

    result = news_client.get_sources(category="technology", country="us")

    news_client._client.get_sources.assert_called_once_with(category="technology", country="us", language="en")

    assert result == sources_response
    assert result["status"] == "ok"
    assert len(result["sources"]) == 1


async def test__get_sources__with_default_parameters(
    news_client: NewsApiBackend, sources_response: Dict[str, Any]
) -> None:
    """Test get_sources with default parameters."""
    news_client._client.get_sources.return_value = sources_response

    news_client.get_sources()

    news_client._client.get_sources.assert_called_once_with(category=None, country=None, language="en")


async def test__get_sources__handles_exception(news_client: NewsApiBackend) -> None:
    """Test get_sources exception handling."""
    news_client._client.get_sources.side_effect = ConnectionError("Connection failed")

    result = news_client.get_sources()

    assert result["status"] == "error"
    assert result["message"] == "Connection failed"
    assert result["code"] == "client_error"


async def test__standardize_response__with_success_status(news_client: NewsApiBackend) -> None:
    """Test _standardize_response with successful response."""
    response = {"status": "ok", "articles": [{"title": "test"}], "totalResults": 1}
    result = news_client._standardize_response(response)

    assert result == response


async def test__standardize_response__with_api_error_status(news_client: NewsApiBackend) -> None:
    """Test _standardize_response with API error response."""
    response = {"status": "error", "message": "API error", "code": "apiKeyInvalid"}
    result = news_client._standardize_response(response)

    assert result == {
        "status": "error",
        "message": "API error", 
        "code": "apiKeyInvalid"
    }


async def test__standardize_response__with_unknown_status(news_client: NewsApiBackend) -> None:
    """Test _standardize_response with unknown status format."""
    response = {"status": "unknown"}
    result = news_client._standardize_response(response)

    assert result["status"] == "error"
    assert result["message"] == "Unknown API error"
    assert result["code"] == "unknown"


async def test__handle_error__formats_exception_message(news_client: NewsApiBackend) -> None:
    """Test _handle_error method formats exception message correctly."""
    error = ValueError("Test error message")
    result = news_client._handle_error(error)

    assert result["status"] == "error"
    assert result["message"] == "Test error message"
    assert result["code"] == "client_error"


@pytest.mark.parametrize(
    ["method_name", "args", "expected_client_method"],
    [
        ("get_top_headlines", {"query": "test"}, "get_top_headlines"),
        ("search_articles", {"query": "test"}, "get_everything"),
        ("get_sources", {}, "get_sources"),
    ],
)
async def test__wrapper_methods__call_correct_underlying_methods(
    mocked_newsapi_client, method_name: str, args: Dict[str, Any], expected_client_method: str
) -> None:
    """Test that wrapper methods call correct underlying client methods."""
    # Setup
    client = NewsApiBackend("test-key")
    method = getattr(client, method_name)
    mock_response = {"status": "ok", "data": "test"}
    getattr(client._client, expected_client_method).return_value = mock_response

    # Call method
    result = method(**args)

    # Verify correct underlying method was called
    getattr(client._client, expected_client_method).assert_called_once()
    assert result == mock_response


@pytest.mark.parametrize(
    ["page_size", "should_raise"],
    [
        (1, False),  # Valid: minimum
        (50, False),  # Valid: middle range
        (100, False),  # Valid: maximum
        (0, True),  # Invalid: too small
        (-1, True),  # Invalid: negative
        (101, True),  # Invalid: too large
        ("50", True),  # Invalid: string
        (None, True),  # Invalid: None
        (50.5, True),  # Invalid: float
    ],
)
async def test__validate_page_size__with_various_inputs(
    news_client: NewsApiBackend, page_size: Any, should_raise: bool
) -> None:
    """Test page_size validation with various input types and values."""
    if should_raise:
        with pytest.raises(ValueError, match="page_size must be an integer between 1 and 100"):
            news_client._validate_page_size(page_size)
    else:
        # Should not raise
        news_client._validate_page_size(page_size)


async def test__get_top_headlines__validates_page_size(news_client: NewsApiBackend) -> None:
    """Test that get_top_headlines validates page_size parameter."""
    result = news_client.get_top_headlines(page_size=0)

    assert result["status"] == "error"
    assert "page_size must be an integer between 1 and 100" in result["message"]
    assert result["code"] == "client_error"


async def test__search_articles__validates_page_size(news_client: NewsApiBackend) -> None:
    """Test that search_articles validates page_size parameter."""
    result = news_client.search_articles(query="test", page_size=101)

    assert result["status"] == "error"
    assert "page_size must be an integer between 1 and 100" in result["message"]
    assert result["code"] == "client_error"
