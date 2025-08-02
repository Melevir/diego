from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class Config:

    news_api_key: Optional[str] = None
    guardian_api_key: Optional[str] = None
    default_country: str = "us"
    default_language: str = "en"
    default_page_size: int = 10
    max_page_size: int = 100

    default_format: str = "simple"
    app_version: str = "1.0.0"

    @classmethod
    def from_env(cls) -> "Config":

        def safe_int(value: str, default: int) -> int:
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        return cls(
            news_api_key=os.getenv("NEWS_API_KEY"),
            guardian_api_key=os.getenv("GUARDIAN_API_KEY"),
            default_country=os.getenv("NEWS_DEFAULT_COUNTRY", "us"),
            default_language=os.getenv("NEWS_DEFAULT_LANGUAGE", "en"),
            default_page_size=safe_int(os.getenv("NEWS_DEFAULT_PAGE_SIZE", "10"), 10),
            max_page_size=safe_int(os.getenv("NEWS_MAX_PAGE_SIZE", "100"), 100),
            default_format=os.getenv("NEWS_DEFAULT_FORMAT", "simple"),
            app_version=os.getenv("APP_VERSION", "1.0.0"),
        )

    def validate(self, source: str = "newsapi") -> bool:
        if source == "newsapi" and not self.news_api_key:
            return False
        elif source == "guardian" and not self.guardian_api_key:
            return False
        elif source == "auto" and not (self.news_api_key or self.guardian_api_key):
            return False

        if self.default_page_size <= 0 or self.default_page_size > self.max_page_size:
            return False

        if self.default_format not in ["simple", "detailed", "json"]:
            return False

        if len(self.default_country) != 2:
            return False

        if len(self.default_language) != 2:
            return False

        return True

    def get_error_message(self, source: str = "newsapi") -> str:
        errors = []

        if source == "newsapi" and not self.news_api_key:
            errors.append("NEWS_API_KEY environment variable not set")
            errors.append("Get your API key from https://newsapi.org/")
            errors.append("Set it with: export NEWS_API_KEY='your-api-key-here'")
        elif source == "guardian" and not self.guardian_api_key:
            errors.append("GUARDIAN_API_KEY environment variable not set")
            errors.append("Get your API key from https://open-platform.theguardian.com/access/")
            errors.append("Set it with: export GUARDIAN_API_KEY='your-api-key-here'")
        elif source == "auto" and not (self.news_api_key or self.guardian_api_key):
            errors.append("Neither NEWS_API_KEY nor GUARDIAN_API_KEY environment variable is set")
            errors.append("Get NewsAPI key from https://newsapi.org/")
            errors.append("Get Guardian API key from https://open-platform.theguardian.com/access/")
            errors.append("Set at least one: export NEWS_API_KEY='key' or export GUARDIAN_API_KEY='key'")

        if self.default_page_size <= 0 or self.default_page_size > self.max_page_size:
            errors.append(f"NEWS_DEFAULT_PAGE_SIZE must be between 1 and {self.max_page_size}")

        if self.default_format not in ["simple", "detailed", "json"]:
            errors.append("NEWS_DEFAULT_FORMAT must be one of: simple, detailed, json")

        if len(self.default_country) != 2:
            errors.append("NEWS_DEFAULT_COUNTRY must be a 2-letter country code")

        if len(self.default_language) != 2:
            errors.append("NEWS_DEFAULT_LANGUAGE must be a 2-letter language code")

        return "\n".join(errors)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment variables."""
    global _config
    _config = Config.from_env()
    return _config
