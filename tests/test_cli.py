import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from typing import Dict, Any

from diego.cli import cli, NEWS_CATEGORIES


@pytest.fixture
def cli_runner() -> CliRunner:
    """Click CLI runner for testing."""
    return CliRunner()


async def test__cli_help__displays_all_commands(cli_runner: CliRunner) -> None:
    """Test CLI help command shows all available commands."""
    result = cli_runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Diego - News CLI tool" in result.output
    assert "config" in result.output
    assert "list-topics" in result.output
    assert "get-news" in result.output
    assert "sources" in result.output


@patch("diego.cli.get_config")
async def test__config_command__shows_valid_configuration(mock_get_config, cli_runner: CliRunner) -> None:
    """Test config command displays valid configuration."""
    # Setup mock config
    mock_config = Mock()
    mock_config.news_api_key = "test-key"
    mock_config.default_country = "us"
    mock_config.default_language = "en"
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_config.default_format = "simple"
    mock_config.app_version = "1.0.0"
    mock_config.validate.return_value = True
    mock_get_config.return_value = mock_config

    result = cli_runner.invoke(cli, ["config"])

    assert result.exit_code == 0
    assert "📋 Current Configuration:" in result.output
    assert "API Key: ✅ Set" in result.output
    assert "Default Country: us" in result.output
    assert "Default Language: en" in result.output


@patch("diego.cli.get_config")
async def test__config_command__shows_invalid_configuration_errors(mock_get_config, cli_runner: CliRunner) -> None:
    """Test config command displays validation errors for invalid config."""
    mock_config = Mock()
    mock_config.news_api_key = None
    mock_config.default_country = "us"
    mock_config.default_language = "en"
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_config.default_format = "simple"
    mock_config.app_version = "1.0.0"
    mock_config.validate.return_value = False
    mock_config.get_error_message.return_value = "API key not set"
    mock_get_config.return_value = mock_config

    result = cli_runner.invoke(cli, ["config"])

    assert result.exit_code == 0
    assert "API Key: ❌ Not set" in result.output
    assert "❌ Configuration Issues:" in result.output
    assert "API key not set" in result.output


async def test__list_topics_command__displays_all_categories(cli_runner: CliRunner) -> None:
    """Test list-topics command shows all news categories."""
    result = cli_runner.invoke(cli, ["list-topics"])

    assert result.exit_code == 0
    assert "Available news topics:" in result.output

    # Check all categories are listed
    for category in NEWS_CATEGORIES:
        assert category.capitalize() in result.output

    assert f"Total: {len(NEWS_CATEGORIES)} categories" in result.output
    assert "get-news --topic <category>" in result.output


@patch("diego.cli.get_validated_config")
@patch("diego.cli.NewsApiBackend")
async def test__get_news_command__success_with_topic(
    mock_client_class, mock_get_config, news_api_response: Dict[str, Any], cli_runner: CliRunner
) -> None:
    """Test successful get-news command with topic filter."""
    # Setup mocks
    mock_config = Mock()
    mock_config.news_api_key = "test-key"
    mock_config.guardian_api_key = None
    mock_config.default_country = "us"
    mock_config.default_page_size = 10
    mock_config.default_format = "simple"
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config

    mock_client = Mock()
    mock_client.get_top_headlines.return_value = news_api_response
    mock_client_class.return_value = mock_client

    result = cli_runner.invoke(cli, ["get-news", "--topic", "technology", "--source", "newsapi"])

    assert result.exit_code == 0
    assert "📰 Top Technology news:" in result.output
    assert "Found 2 articles" in result.output
    assert "Test Article 1" in result.output
    assert "Test Article 2" in result.output

    # Verify client was called correctly
    mock_client.get_top_headlines.assert_called_once_with(category="technology", country="us", page_size=10)


@patch("diego.cli.get_validated_config")
@patch("diego.cli.get_news_client")
async def test__get_news_command__success_with_query_search(
    mock_client_class, mock_get_config, news_api_response: Dict[str, Any], cli_runner: CliRunner
) -> None:
    """Test get-news command with search query instead of topic."""
    mock_config = Mock()
    mock_config.news_api_key = "test-key"
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config

    mock_client = Mock()
    mock_client.search_articles.return_value = news_api_response
    mock_client_class.return_value = mock_client

    result = cli_runner.invoke(cli, ["get-news", "--query", "bitcoin"])

    assert result.exit_code == 0
    assert "🔍 Search results for: 'bitcoin'" in result.output

    mock_client.search_articles.assert_called_once_with(query="bitcoin", page_size=10)


@pytest.mark.parametrize(
    ["topic", "country", "limit", "format_type"],
    [
        ("business", "uk", 25, "detailed"),
        ("sports", "fr", 15, "json"),
        ("health", "us", 5, "simple"),
    ],
)
@patch("diego.cli.get_validated_config")
@patch("diego.cli.get_news_client")
async def test__get_news_command__with_custom_options(
    mock_client_class,
    mock_get_config,
    news_api_response: Dict[str, Any],
    cli_runner: CliRunner,
    topic: str,
    country: str,
    limit: int,
    format_type: str,
) -> None:
    """Test get-news command with various custom options."""
    mock_config = Mock()
    mock_config.news_api_key = "test-key"
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config

    mock_client = Mock()
    mock_client.get_top_headlines.return_value = news_api_response
    mock_client_class.return_value = mock_client

    result = cli_runner.invoke(
        cli, ["get-news", "--topic", topic, "--country", country, "--limit", str(limit), "--format", format_type]
    )

    assert result.exit_code == 0
    mock_client.get_top_headlines.assert_called_once_with(category=topic, country=country, page_size=limit)


@patch("diego.cli.get_validated_config")
async def test__get_news_command__limit_exceeds_maximum(mock_get_config, cli_runner: CliRunner) -> None:
    """Test get-news command rejects limit exceeding maximum page size."""
    mock_config = Mock()
    mock_config.max_page_size = 50
    mock_get_config.return_value = mock_config

    result = cli_runner.invoke(cli, ["get-news", "--limit", "100"])

    assert result.exit_code == 0
    assert "❌ Limit cannot exceed 50" in result.output


@patch("diego.cli.get_validated_config")
@patch("diego.cli.get_news_client")
async def test__get_news_command__handles_api_error(
    mock_client_class, mock_get_config, news_api_error_response: Dict[str, Any], cli_runner: CliRunner
) -> None:
    """Test get-news command handles API error gracefully."""
    mock_config = Mock()
    mock_config.news_api_key = "test-key"
    mock_config.default_country = "us"
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config

    mock_client = Mock()
    mock_client.get_top_headlines.return_value = news_api_error_response
    mock_client_class.return_value = mock_client

    result = cli_runner.invoke(cli, ["get-news"])

    assert result.exit_code == 0
    assert "❌ Error: Your API key is invalid or incorrect." in result.output


@patch("diego.cli.get_validated_config")
@patch("diego.cli.get_news_client")
async def test__get_news_command__handles_no_articles_found(
    mock_client_class, mock_get_config, cli_runner: CliRunner
) -> None:
    """Test get-news command when no articles are found."""
    mock_config = Mock()
    mock_config.news_api_key = "test-key"
    mock_config.default_country = "us"
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config

    mock_client = Mock()
    mock_client.get_top_headlines.return_value = {"status": "ok", "totalResults": 0, "articles": []}
    mock_client_class.return_value = mock_client

    result = cli_runner.invoke(cli, ["get-news"])

    assert result.exit_code == 0
    assert "No articles found." in result.output


@patch("diego.cli.get_validated_config")
@patch("diego.cli.get_news_client")
async def test__sources_command__success_with_no_filters(
    mock_client_class, mock_get_config, sources_response: Dict[str, Any], cli_runner: CliRunner
) -> None:
    """Test sources command without any filters."""
    mock_config = Mock()
    mock_config.news_api_key = "test-key"
    mock_config.default_format = "simple"
    mock_get_config.return_value = mock_config

    mock_client = Mock()
    mock_client.get_sources.return_value = sources_response
    mock_client_class.return_value = mock_client

    result = cli_runner.invoke(cli, ["sources"])

    assert result.exit_code == 0
    assert "📺 Available news sources:" in result.output
    assert "Test Source (Technology, US)" in result.output

    mock_client.get_sources.assert_called_once_with(category=None, country=None)


@patch("diego.cli.get_validated_config")
@patch("diego.cli.get_news_client")
async def test__sources_command__success_with_filters(
    mock_client_class, mock_get_config, sources_response: Dict[str, Any], cli_runner: CliRunner
) -> None:
    """Test sources command with topic and country filters."""
    mock_config = Mock()
    mock_config.news_api_key = "test-key"
    mock_config.default_format = "simple"
    mock_get_config.return_value = mock_config

    mock_client = Mock()
    mock_client.get_sources.return_value = sources_response
    mock_client_class.return_value = mock_client

    result = cli_runner.invoke(cli, ["sources", "--topic", "technology", "--country", "us", "--format", "detailed"])

    assert result.exit_code == 0
    assert "📺 Available news sources (topic: technology, country: us):" in result.output

    mock_client.get_sources.assert_called_once_with(category="technology", country="us")


@patch("diego.cli.get_config")
async def test__get_validated_config_failure__aborts_command(mock_get_config, cli_runner: CliRunner) -> None:
    """Test command aborts when config validation fails."""
    mock_config = Mock()
    mock_config.validate.return_value = False
    mock_config.get_error_message.return_value = "Config error"
    # Add necessary attributes to avoid comparison errors
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config

    result = cli_runner.invoke(cli, ["get-news"])

    assert result.exit_code == 1  # click.Abort() causes exit code 1
    assert "❌ Configuration Error:" in result.output
    assert "Config error" in result.output


@patch("diego.cli.get_validated_config")
@patch("diego.cli.get_news_client")
async def test__get_news_command__json_format_output(
    mock_client_class, mock_get_config, news_api_response: Dict[str, Any], cli_runner: CliRunner
) -> None:
    """Test get-news command with JSON format output."""
    mock_config = Mock()
    mock_config.news_api_key = "test-key"
    mock_config.default_country = "us"
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config

    mock_client = Mock()
    mock_client.get_top_headlines.return_value = news_api_response
    mock_client_class.return_value = mock_client

    result = cli_runner.invoke(cli, ["get-news", "--format", "json"])

    assert result.exit_code == 0
    # Should contain JSON formatted output
    assert '"title": "Test Article 1"' in result.output
    assert '"source":' in result.output


@patch("diego.cli.get_validated_config")
@patch("diego.cli.get_news_client")
async def test__get_news_command__detailed_format_output(
    mock_client_class, mock_get_config, news_api_response: Dict[str, Any], cli_runner: CliRunner
) -> None:
    """Test get-news command with detailed format output."""
    mock_config = Mock()
    mock_config.news_api_key = "test-key"
    mock_config.default_country = "us"
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config

    mock_client = Mock()
    mock_client.get_top_headlines.return_value = news_api_response
    mock_client_class.return_value = mock_client

    result = cli_runner.invoke(cli, ["get-news", "--format", "detailed"])

    assert result.exit_code == 0
    # Should contain detailed information
    assert "Source: Test Source" in result.output
    assert "Author: Test Author" in result.output
    assert "Description: Test description 1" in result.output
    assert "URL: https://example.com/1" in result.output


# Summary command tests


@patch("diego.cli.get_config")
@patch("diego.cli.get_claude_client")
async def test__summary_command__help_displays_correctly(
    mock_get_claude_client, mock_get_config, cli_runner: CliRunner
) -> None:
    """Test summary command help is displayed correctly."""
    result = cli_runner.invoke(cli, ["summary", "--help"])

    assert result.exit_code == 0
    assert "Summarize an article using Claude AI" in result.output
    assert "--url" in result.output
    assert "--file" in result.output


@patch("diego.cli.get_config")
@patch("diego.cli.get_claude_client")
@patch("diego.cli.extract_text_from_url")
@patch("diego.cli.summarize_with_claude")
async def test__summary_command__url_input_success(
    mock_summarize, mock_extract, mock_get_claude_client, mock_get_config, cli_runner: CliRunner
) -> None:
    """Test summary command with URL input."""
    # Setup mocks
    mock_config = Mock()
    mock_config.claude_api_key = "test-api-key"
    mock_config.validate.return_value = True
    mock_get_config.return_value = mock_config

    mock_claude_client = Mock()
    mock_get_claude_client.return_value = mock_claude_client

    mock_extract.return_value = "This is a test article with some content to summarize."
    mock_summarize.return_value = "First sentence. Second sentence. Third sentence."

    result = cli_runner.invoke(cli, ["summary", "--url", "https://example.com/article"])

    assert result.exit_code == 0
    assert "Fetching article from: https://example.com/article" in result.output
    assert "Article length:" in result.output
    assert "Generating summary with Claude AI..." in result.output
    assert "SUMMARY" in result.output
    assert "First sentence. Second sentence. Third sentence." in result.output

    mock_extract.assert_called_once_with("https://example.com/article")
    mock_summarize.assert_called_once()


@patch("diego.cli.get_config")
@patch("diego.cli.get_claude_client")
@patch("diego.cli.read_text_from_file")
@patch("diego.cli.summarize_with_claude")
async def test__summary_command__file_input_success(
    mock_summarize, mock_read_file, mock_get_claude_client, mock_get_config, cli_runner: CliRunner
) -> None:
    """Test summary command with file input."""
    # Setup mocks
    mock_config = Mock()
    mock_config.claude_api_key = "test-api-key"
    mock_config.validate.return_value = True
    mock_get_config.return_value = mock_config

    mock_claude_client = Mock()
    mock_get_claude_client.return_value = mock_claude_client

    mock_read_file.return_value = "File content to be summarized."
    mock_summarize.return_value = "Summary sentence one. Summary sentence two. Summary sentence three."

    result = cli_runner.invoke(cli, ["summary", "--file", "test.txt"])

    assert result.exit_code == 0
    assert "Reading article from: test.txt" in result.output
    assert "SUMMARY" in result.output
    assert "Summary sentence one. Summary sentence two. Summary sentence three." in result.output

    mock_read_file.assert_called_once_with("test.txt")


@patch("diego.cli.get_config")
async def test__summary_command__missing_claude_api_key(mock_get_config, cli_runner: CliRunner) -> None:
    """Test summary command fails when Claude API key is missing."""
    mock_config = Mock()
    mock_config.claude_api_key = None
    mock_config.validate.return_value = False
    mock_config.get_error_message.return_value = "CLAUDE_API_KEY environment variable not set"
    mock_get_config.return_value = mock_config

    result = cli_runner.invoke(cli, ["summary", "--url", "https://example.com/article"])

    assert result.exit_code == 1
    assert "Configuration Error" in result.output
    assert "CLAUDE_API_KEY environment variable not set" in result.output


@patch("diego.cli.get_config")
@patch("diego.cli.get_claude_client")
async def test__summary_command__multiple_input_sources_error(
    mock_get_claude_client, mock_get_config, cli_runner: CliRunner
) -> None:
    """Test summary command fails with multiple input sources."""
    mock_config = Mock()
    mock_config.claude_api_key = "test-api-key"
    mock_config.validate.return_value = True
    mock_get_config.return_value = mock_config

    result = cli_runner.invoke(cli, ["summary", "--url", "https://example.com/article", "--file", "test.txt"])

    assert result.exit_code == 1
    assert "Please specify only one input source" in result.output


@patch("diego.cli.get_config")
@patch("diego.cli.get_claude_client")
@patch("diego.cli.extract_text_from_url")
async def test__summary_command__url_fetch_error(
    mock_extract, mock_get_claude_client, mock_get_config, cli_runner: CliRunner
) -> None:
    """Test summary command handles URL fetch errors."""
    mock_config = Mock()
    mock_config.claude_api_key = "test-api-key"
    mock_config.validate.return_value = True
    mock_get_config.return_value = mock_config

    mock_extract.side_effect = Exception("Network error")

    result = cli_runner.invoke(cli, ["summary", "--url", "https://example.com/article"])

    assert result.exit_code == 0  # Click catches exceptions and prints error
    assert "Error" in result.output


@patch("diego.cli.get_config")
@patch("diego.cli.get_claude_client")
@patch("diego.cli.read_text_from_file")
async def test__summary_command__file_not_found_error(
    mock_read_file, mock_get_claude_client, mock_get_config, cli_runner: CliRunner
) -> None:
    """Test summary command handles file not found errors."""
    mock_config = Mock()
    mock_config.claude_api_key = "test-api-key"
    mock_config.validate.return_value = True
    mock_get_config.return_value = mock_config

    mock_read_file.side_effect = Exception("File not found: nonexistent.txt")

    result = cli_runner.invoke(cli, ["summary", "--file", "nonexistent.txt"])

    assert result.exit_code == 0  # Click catches exceptions and prints error
    assert "Error" in result.output


@patch("diego.cli.get_config")
@patch("diego.cli.get_claude_client")
@patch("diego.cli.extract_text_from_url")
@patch("diego.cli.summarize_with_claude")
async def test__summary_command__empty_text_error(
    mock_summarize, mock_extract, mock_get_claude_client, mock_get_config, cli_runner: CliRunner
) -> None:
    """Test summary command handles empty text content."""
    mock_config = Mock()
    mock_config.claude_api_key = "test-api-key"
    mock_config.validate.return_value = True
    mock_get_config.return_value = mock_config

    mock_extract.return_value = ""  # Empty text

    result = cli_runner.invoke(cli, ["summary", "--url", "https://example.com/article"])

    assert result.exit_code == 0
    assert "No text content found to summarize" in result.output


@patch("diego.cli.get_config")
@patch("diego.cli.get_claude_client")
@patch("diego.cli.extract_text_from_url")
@patch("diego.cli.summarize_with_claude")
async def test__summary_command__claude_api_error(
    mock_summarize, mock_extract, mock_get_claude_client, mock_get_config, cli_runner: CliRunner
) -> None:
    """Test summary command handles Claude API errors."""
    mock_config = Mock()
    mock_config.claude_api_key = "test-api-key"
    mock_config.validate.return_value = True
    mock_get_config.return_value = mock_config

    mock_extract.return_value = "Test article content"
    mock_summarize.side_effect = Exception("Claude API error: Rate limit exceeded")

    result = cli_runner.invoke(cli, ["summary", "--url", "https://example.com/article"])

    assert result.exit_code == 0
    assert "Error" in result.output


# Test helper functions


@patch("requests.get")
async def test__extract_text_from_url__success(mock_get) -> None:
    """Test URL text extraction success."""
    from diego.cli import extract_text_from_url

    mock_response = Mock()
    mock_response.content = b"<html><body><article><p>Test article content</p></article></body></html>"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = extract_text_from_url("https://example.com/article")

    assert "Test article content" in result
    mock_get.assert_called_once()


async def test__read_text_from_file__success(tmp_path) -> None:
    """Test file text reading success."""
    from diego.cli import read_text_from_file

    # Create temporary file
    test_file = tmp_path / "test.txt"
    test_content = "This is test file content for summarization."
    test_file.write_text(test_content)

    result = read_text_from_file(str(test_file))

    assert result == test_content


@patch("diego.cli.Anthropic")
async def test__summarize_with_claude__success(mock_anthropic_class) -> None:
    """Test Claude summarization success."""
    from diego.cli import summarize_with_claude

    # Setup mock
    mock_client = Mock()
    mock_anthropic_class.return_value = mock_client

    mock_message = Mock()
    mock_message.content = [Mock()]
    mock_message.content[0].text = "First sentence. Second sentence. Third sentence."
    mock_client.messages.create.return_value = mock_message

    result = summarize_with_claude(mock_client, "Test article content")

    assert result == "First sentence. Second sentence. Third sentence."
    mock_client.messages.create.assert_called_once()
