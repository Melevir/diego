import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from typing import Dict, Any

from cli import cli, NEWS_CATEGORIES


@pytest.fixture
def cli_runner() -> CliRunner:
    """Click CLI runner for testing."""
    return CliRunner()


async def test__cli_help__displays_all_commands(cli_runner: CliRunner) -> None:
    """Test CLI help command shows all available commands."""
    result = cli_runner.invoke(cli, ['--help'])
    
    assert result.exit_code == 0
    assert 'Diego - News CLI tool powered by NewsAPI' in result.output
    assert 'config' in result.output
    assert 'list-topics' in result.output
    assert 'get-news' in result.output
    assert 'sources' in result.output


@patch('cli.get_config')
async def test__config_command__shows_valid_configuration(
    mock_get_config,
    cli_runner: CliRunner
) -> None:
    """Test config command displays valid configuration."""
    # Setup mock config
    mock_config = Mock()
    mock_config.news_api_key = 'test-key'
    mock_config.default_country = 'us'
    mock_config.default_language = 'en'
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_config.default_format = 'simple'
    mock_config.app_version = '1.0.0'
    mock_config.validate.return_value = True
    mock_get_config.return_value = mock_config
    
    result = cli_runner.invoke(cli, ['config'])
    
    assert result.exit_code == 0
    assert '📋 Current Configuration:' in result.output
    assert 'API Key: ✅ Set' in result.output
    assert 'Default Country: us' in result.output
    assert 'Default Language: en' in result.output


@patch('cli.get_config')
async def test__config_command__shows_invalid_configuration_errors(
    mock_get_config,
    cli_runner: CliRunner
) -> None:
    """Test config command displays validation errors for invalid config."""
    mock_config = Mock()
    mock_config.news_api_key = None
    mock_config.default_country = 'us'
    mock_config.default_language = 'en'
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_config.default_format = 'simple'
    mock_config.app_version = '1.0.0'
    mock_config.validate.return_value = False
    mock_config.get_error_message.return_value = 'API key not set'
    mock_get_config.return_value = mock_config
    
    result = cli_runner.invoke(cli, ['config'])
    
    assert result.exit_code == 0
    assert 'API Key: ❌ Not set' in result.output
    assert '❌ Configuration Issues:' in result.output
    assert 'API key not set' in result.output


async def test__list_topics_command__displays_all_categories(
    cli_runner: CliRunner
) -> None:
    """Test list-topics command shows all news categories."""
    result = cli_runner.invoke(cli, ['list-topics'])
    
    assert result.exit_code == 0
    assert 'Available news topics:' in result.output
    
    # Check all categories are listed
    for category in NEWS_CATEGORIES:
        assert category.capitalize() in result.output
    
    assert f'Total: {len(NEWS_CATEGORIES)} categories' in result.output
    assert 'get-news --topic <category>' in result.output


@patch('cli.get_validated_config')
@patch('cli.NewsOrgApiClient')
async def test__get_news_command__success_with_topic(
    mock_client_class,
    mock_get_config,
    news_api_response: Dict[str, Any],
    cli_runner: CliRunner
) -> None:
    """Test successful get-news command with topic filter."""
    # Setup mocks
    mock_config = Mock()
    mock_config.news_api_key = 'test-key'
    mock_config.default_country = 'us'
    mock_config.default_page_size = 10
    mock_config.default_format = 'simple'
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config
    
    mock_client = Mock()
    mock_client.get_top_headlines.return_value = news_api_response
    mock_client_class.return_value = mock_client
    
    result = cli_runner.invoke(cli, ['get-news', '--topic', 'technology'])
    
    assert result.exit_code == 0
    assert '📰 Top Technology news:' in result.output
    assert 'Found 2 articles' in result.output
    assert 'Test Article 1' in result.output
    assert 'Test Article 2' in result.output
    
    # Verify client was called correctly
    mock_client.get_top_headlines.assert_called_once_with(
        category='technology',
        country='us',
        page_size=10
    )


@patch('cli.get_validated_config')
@patch('cli.NewsOrgApiClient')
async def test__get_news_command__success_with_query_search(
    mock_client_class,
    mock_get_config,
    news_api_response: Dict[str, Any],
    cli_runner: CliRunner
) -> None:
    """Test get-news command with search query instead of topic."""
    mock_config = Mock()
    mock_config.news_api_key = 'test-key'
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config
    
    mock_client = Mock()
    mock_client.search_articles.return_value = news_api_response
    mock_client_class.return_value = mock_client
    
    result = cli_runner.invoke(cli, ['get-news', '--query', 'bitcoin'])
    
    assert result.exit_code == 0
    assert '🔍 Search results for: \'bitcoin\'' in result.output
    
    mock_client.search_articles.assert_called_once_with(
        query='bitcoin',
        page_size=10
    )


@pytest.mark.parametrize(
    ["topic", "country", "limit", "format_type"],
    [
        ("business", "uk", 25, "detailed"),
        ("sports", "fr", 15, "json"),
        ("health", "us", 5, "simple"),
    ],
)
@patch('cli.get_validated_config')
@patch('cli.NewsOrgApiClient')
async def test__get_news_command__with_custom_options(
    mock_client_class,
    mock_get_config,
    news_api_response: Dict[str, Any],
    cli_runner: CliRunner,
    topic: str,
    country: str,
    limit: int,
    format_type: str
) -> None:
    """Test get-news command with various custom options."""
    mock_config = Mock()
    mock_config.news_api_key = 'test-key'
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config
    
    mock_client = Mock()
    mock_client.get_top_headlines.return_value = news_api_response
    mock_client_class.return_value = mock_client
    
    result = cli_runner.invoke(cli, [
        'get-news', 
        '--topic', topic,
        '--country', country, 
        '--limit', str(limit),
        '--format', format_type
    ])
    
    assert result.exit_code == 0
    mock_client.get_top_headlines.assert_called_once_with(
        category=topic,
        country=country,
        page_size=limit
    )


@patch('cli.get_validated_config')
async def test__get_news_command__limit_exceeds_maximum(
    mock_get_config,
    cli_runner: CliRunner
) -> None:
    """Test get-news command rejects limit exceeding maximum page size."""
    mock_config = Mock()
    mock_config.max_page_size = 50
    mock_get_config.return_value = mock_config
    
    result = cli_runner.invoke(cli, ['get-news', '--limit', '100'])
    
    assert result.exit_code == 0
    assert '❌ Limit cannot exceed 50' in result.output


@patch('cli.get_validated_config')
@patch('cli.NewsOrgApiClient')
async def test__get_news_command__handles_api_error(
    mock_client_class,
    mock_get_config,
    news_api_error_response: Dict[str, Any],
    cli_runner: CliRunner
) -> None:
    """Test get-news command handles API error gracefully."""
    mock_config = Mock()
    mock_config.news_api_key = 'test-key'
    mock_config.default_country = 'us'
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config
    
    mock_client = Mock()
    mock_client.get_top_headlines.return_value = news_api_error_response
    mock_client_class.return_value = mock_client
    
    result = cli_runner.invoke(cli, ['get-news'])
    
    assert result.exit_code == 0
    assert '❌ Error: Your API key is invalid or incorrect.' in result.output


@patch('cli.get_validated_config')
@patch('cli.NewsOrgApiClient')
async def test__get_news_command__handles_no_articles_found(
    mock_client_class,
    mock_get_config,
    cli_runner: CliRunner
) -> None:
    """Test get-news command when no articles are found."""
    mock_config = Mock()
    mock_config.news_api_key = 'test-key'
    mock_config.default_country = 'us'
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config
    
    mock_client = Mock()
    mock_client.get_top_headlines.return_value = {
        'status': 'ok',
        'totalResults': 0,
        'articles': []
    }
    mock_client_class.return_value = mock_client
    
    result = cli_runner.invoke(cli, ['get-news'])
    
    assert result.exit_code == 0
    assert 'No articles found.' in result.output


@patch('cli.get_validated_config')
@patch('cli.NewsOrgApiClient')
async def test__sources_command__success_with_no_filters(
    mock_client_class,
    mock_get_config,
    sources_response: Dict[str, Any],
    cli_runner: CliRunner
) -> None:
    """Test sources command without any filters."""
    mock_config = Mock()
    mock_config.news_api_key = 'test-key'
    mock_config.default_format = 'simple'
    mock_get_config.return_value = mock_config
    
    mock_client = Mock()
    mock_client.get_sources.return_value = sources_response
    mock_client_class.return_value = mock_client
    
    result = cli_runner.invoke(cli, ['sources'])
    
    assert result.exit_code == 0
    assert '📺 Available news sources:' in result.output
    assert 'Test Source (Technology, US)' in result.output
    
    mock_client.get_sources.assert_called_once_with(
        category=None,
        country=None
    )


@patch('cli.get_validated_config')
@patch('cli.NewsOrgApiClient')
async def test__sources_command__success_with_filters(
    mock_client_class,
    mock_get_config,
    sources_response: Dict[str, Any],
    cli_runner: CliRunner
) -> None:
    """Test sources command with topic and country filters."""
    mock_config = Mock()
    mock_config.news_api_key = 'test-key'
    mock_config.default_format = 'simple'
    mock_get_config.return_value = mock_config
    
    mock_client = Mock()
    mock_client.get_sources.return_value = sources_response
    mock_client_class.return_value = mock_client
    
    result = cli_runner.invoke(cli, [
        'sources', 
        '--topic', 'technology',
        '--country', 'us',
        '--format', 'detailed'
    ])
    
    assert result.exit_code == 0
    assert '📺 Available news sources (topic: technology, country: us):' in result.output
    
    mock_client.get_sources.assert_called_once_with(
        category='technology',
        country='us'
    )


@patch('cli.get_config')
async def test__get_validated_config_failure__aborts_command(
    mock_get_config,
    cli_runner: CliRunner
) -> None:
    """Test command aborts when config validation fails."""
    mock_config = Mock()
    mock_config.validate.return_value = False
    mock_config.get_error_message.return_value = 'Config error'
    # Add necessary attributes to avoid comparison errors
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config
    
    result = cli_runner.invoke(cli, ['get-news'])
    
    assert result.exit_code == 1  # click.Abort() causes exit code 1
    assert '❌ Configuration Error:' in result.output
    assert 'Config error' in result.output


@patch('cli.get_validated_config')
@patch('cli.NewsOrgApiClient')
async def test__get_news_command__json_format_output(
    mock_client_class,
    mock_get_config,
    news_api_response: Dict[str, Any],
    cli_runner: CliRunner
) -> None:
    """Test get-news command with JSON format output."""
    mock_config = Mock()
    mock_config.news_api_key = 'test-key'
    mock_config.default_country = 'us'
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config
    
    mock_client = Mock()
    mock_client.get_top_headlines.return_value = news_api_response
    mock_client_class.return_value = mock_client
    
    result = cli_runner.invoke(cli, ['get-news', '--format', 'json'])
    
    assert result.exit_code == 0
    # Should contain JSON formatted output
    assert '"title": "Test Article 1"' in result.output
    assert '"source":' in result.output


@patch('cli.get_validated_config')
@patch('cli.NewsOrgApiClient')
async def test__get_news_command__detailed_format_output(
    mock_client_class,
    mock_get_config,
    news_api_response: Dict[str, Any],
    cli_runner: CliRunner
) -> None:
    """Test get-news command with detailed format output."""
    mock_config = Mock()
    mock_config.news_api_key = 'test-key'
    mock_config.default_country = 'us'
    mock_config.default_page_size = 10
    mock_config.max_page_size = 100
    mock_get_config.return_value = mock_config
    
    mock_client = Mock()
    mock_client.get_top_headlines.return_value = news_api_response
    mock_client_class.return_value = mock_client
    
    result = cli_runner.invoke(cli, ['get-news', '--format', 'detailed'])
    
    assert result.exit_code == 0
    # Should contain detailed information
    assert 'Source: Test Source' in result.output
    assert 'Author: Test Author' in result.output
    assert 'Description: Test description 1' in result.output
    assert 'URL: https://example.com/1' in result.output