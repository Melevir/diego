import os
import pytest
from unittest.mock import patch
from typing import Dict, Any

from diego.config import Config, get_config, reload_config


@pytest.mark.parametrize(
    ["raw_country", "clean_country"],
    [
        ("us", "us"),
        ("US", "US"),
        ("uk", "uk"),
        ("fr", "fr"),
    ],
)
async def test__config_from_env__with_valid_data(
    valid_env_vars: Dict[str, str], raw_country: str, clean_country: str
) -> None:
    env_vars = valid_env_vars.copy()
    env_vars["NEWS_DEFAULT_COUNTRY"] = raw_country

    with patch.dict(os.environ, env_vars, clear=True):
        config = Config.from_env()

        assert config.news_api_key == "test-api-key-12345"
        assert config.default_country == clean_country
        assert config.default_language == "en"
        assert config.default_page_size == 10
        assert config.max_page_size == 100
        assert config.default_format == "simple"
        assert config.app_version == "1.0.0"


async def test__config_from_env__with_missing_vars_uses_defaults() -> None:
    env = {"NEWS_API_KEY": "test-key"}

    with patch.dict(os.environ, env, clear=True):
        config = Config.from_env()

        assert config.news_api_key == "test-key"
        assert config.default_country == "us"  # default
        assert config.default_language == "en"  # default
        assert config.default_page_size == 10  # default
        assert config.max_page_size == 100  # default
        assert config.default_format == "simple"  # default
        assert config.app_version == "1.0.0"  # default


@pytest.mark.parametrize(
    ["env_var", "env_value", "expected_value"],
    [
        ("NEWS_DEFAULT_COUNTRY", "uk", "uk"),
        ("NEWS_DEFAULT_LANGUAGE", "fr", "fr"),
        ("NEWS_DEFAULT_PAGE_SIZE", "25", 25),
        ("NEWS_MAX_PAGE_SIZE", "50", 50),
        ("NEWS_DEFAULT_FORMAT", "detailed", "detailed"),
        ("APP_VERSION", "2.0.0", "2.0.0"),
    ],
)
async def test__config_from_env__with_custom_values(
    valid_env_vars: Dict[str, str], env_var: str, env_value: str, expected_value: Any
) -> None:
    env_vars = valid_env_vars.copy()
    env_vars[env_var] = env_value

    with patch.dict(os.environ, env_vars, clear=True):
        config = Config.from_env()
        field_name = env_var.lower().replace("news_", "").replace("app_", "app_")
        actual_value = getattr(config, field_name)
        assert actual_value == expected_value


async def test__config_validate__valid_config_passes(config: Config) -> None:
    assert config.validate() is True


@pytest.mark.parametrize(
    ["field_name", "field_value"],
    [
        ("news_api_key", None),
        ("news_api_key", ""),
        ("default_page_size", 0),
        ("default_page_size", -1),
        ("default_page_size", 101),  # exceeds max_page_size
        ("default_format", "invalid"),
        ("default_country", "invalid"),  # not 2 letters
        ("default_country", "u"),  # not 2 letters
        ("default_language", "invalid"),  # not 2 letters
        ("default_language", "e"),  # not 2 letters
    ],
)
async def test__config_validate__invalid_values_fail(config: Config, field_name: str, field_value: Any) -> None:
    setattr(config, field_name, field_value)
    assert config.validate() is False


async def test__config_get_error_message__missing_api_key() -> None:
    config = Config(news_api_key=None)
    error_msg = config.get_error_message()

    assert "NEWS_API_KEY environment variable not set" in error_msg
    assert "https://newsapi.org/" in error_msg
    assert "export NEWS_API_KEY=" in error_msg


async def test__config_get_error_message__invalid_page_size(config: Config) -> None:
    config.default_page_size = 0
    error_msg = config.get_error_message()

    assert "NEWS_DEFAULT_PAGE_SIZE must be between 1 and 100" in error_msg


async def test__config_get_error_message__invalid_format(config: Config) -> None:
    config.default_format = "invalid"
    error_msg = config.get_error_message()

    assert "NEWS_DEFAULT_FORMAT must be one of: simple, detailed, json" in error_msg


async def test__config_get_error_message__invalid_country(config: Config) -> None:
    config.default_country = "invalid"
    error_msg = config.get_error_message()

    assert "NEWS_DEFAULT_COUNTRY must be a 2-letter country code" in error_msg


async def test__config_get_error_message__invalid_language(config: Config) -> None:
    config.default_language = "invalid"
    error_msg = config.get_error_message()

    assert "NEWS_DEFAULT_LANGUAGE must be a 2-letter language code" in error_msg


async def test__config_get_error_message__multiple_errors() -> None:
    config = Config(news_api_key=None, default_page_size=0, default_format="invalid")
    error_msg = config.get_error_message()

    # Should contain all error messages
    assert "NEWS_API_KEY environment variable not set" in error_msg
    assert "NEWS_DEFAULT_PAGE_SIZE must be between 1 and 100" in error_msg
    assert "NEWS_DEFAULT_FORMAT must be one of: simple, detailed, json" in error_msg


async def test__get_config__returns_singleton(valid_env_vars: Dict[str, str]) -> None:
    """Test that get_config returns same instance on multiple calls."""
    with patch.dict(os.environ, valid_env_vars, clear=True):
        # Clear any existing global config
        import diego.config

        diego.config._config = None

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2  # Same instance
        assert config1.news_api_key == "test-api-key-12345"


async def test__reload_config__creates_new_instance(valid_env_vars: Dict[str, str]) -> None:
    """Test that reload_config creates new instance with updated env."""
    # Clear any existing global config
    import diego.config

    diego.config._config = None

    # First load with original env
    with patch.dict(os.environ, valid_env_vars, clear=True):
        config1 = get_config()
        assert config1.default_country == "us"

    # Update env and reload
    updated_env = valid_env_vars.copy()
    updated_env["NEWS_DEFAULT_COUNTRY"] = "uk"

    with patch.dict(os.environ, updated_env, clear=True):
        config2 = reload_config()

        assert config2 is not config1  # Different instance
        assert config2.default_country == "uk"  # Updated value

        # Subsequent get_config should return the reloaded config
        config3 = get_config()
        assert config3 is config2


@pytest.mark.parametrize(
    ["env_value", "expected_value"],
    [
        ("10", 10),  # Valid integer string
        ("invalid", 10),  # Invalid string uses default
        ("", 10),  # Empty string uses default
        ("50.5", 10),  # Float string uses default
        ("abc123", 10),  # Mixed string uses default
    ],
)
async def test__config_from_env__safe_int_conversion(env_value: str, expected_value: int) -> None:
    """Test that safe_int conversion handles invalid values gracefully."""
    env_vars = {"NEWS_API_KEY": "test-key", "NEWS_DEFAULT_PAGE_SIZE": env_value}

    with patch.dict(os.environ, env_vars, clear=True):
        config = Config.from_env()
        assert config.default_page_size == expected_value


async def test__config_from_env__safe_int_both_size_vars() -> None:
    """Test safe_int conversion for both page size environment variables."""
    env_vars = {"NEWS_API_KEY": "test-key", "NEWS_DEFAULT_PAGE_SIZE": "invalid1", "NEWS_MAX_PAGE_SIZE": "invalid2"}

    with patch.dict(os.environ, env_vars, clear=True):
        config = Config.from_env()

        # Should use defaults when conversion fails
        assert config.default_page_size == 10  # default
        assert config.max_page_size == 100  # default
