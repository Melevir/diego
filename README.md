# Diego - News CLI Tool 📰

[![CI Pipeline](https://github.com/Melevir/diego/actions/workflows/ci.yml/badge.svg)](https://github.com/Melevir/diego/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)](https://github.com/Melevir/diego/actions)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A powerful command-line news aggregator supporting multiple news sources including [NewsAPI](https://newsapi.org/) and [The Guardian](https://www.theguardian.com), featuring clean wrapper libraries and a comprehensive CLI interface.

## ✨ Features

- 🔄 **Multiple News Sources**: NewsAPI and Guardian API support with auto-fallback
- 🔍 **Search articles** by keywords or phrases across all sources
- 📊 **Browse news by category** (business, tech, sports, etc.)
- 🌍 **Filter by country** and language
- 📺 **List news sources** with filtering options
- 🎨 **Multiple output formats** (simple, detailed, JSON)
- 🤖 **AI-Powered Summarization**: Generate 3-sentence summaries using Claude AI
- ⚙️ **Environment-based configuration**
- 🧪 **Comprehensive test suite** (82% coverage)
- 🛡️ **Robust error handling** with graceful source switching

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/melevir/diego.git
cd diego

# Install dependencies
pip install -r requirements-test.txt

# Set your API keys
export NEWS_API_KEY='your-api-key-from-newsapi.org'        # For news fetching
export GUARDIAN_API_KEY='your-api-key-from-guardian'       # For news fetching  
export CLAUDE_API_KEY='your-api-key-from-anthropic'        # For article summarization
```

### Usage

```bash
# List available news categories
python diego_cli.py list-topics

# Get top technology news (auto-selects best available source)
python diego_cli.py get-news --topic technology

# Use specific news source
python diego_cli.py get-news --source guardian --topic technology
python diego_cli.py get-news --source newsapi --topic business

# Search for specific topics
python diego_cli.py get-news --query "artificial intelligence"

# Get detailed format with custom options
python diego_cli.py get-news --topic business --country uk --limit 5 --format detailed

# List news sources from different providers
python diego_cli.py sources --source guardian --topic technology
python diego_cli.py sources --source newsapi

# Check current configuration
python diego_cli.py config

# Summarize articles with Claude AI
python diego_cli.py summary --url "https://example.com/article"
python diego_cli.py summary --file "article.txt"
echo "Article text here" | python diego_cli.py summary
```

## 📋 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `list-topics` | Show available news categories | `python diego_cli.py list-topics` |
| `get-news` | Get news by topic or search query | `python diego_cli.py get-news --source guardian --topic tech` |
| `sources` | List available news sources | `python diego_cli.py sources --source newsapi --topic business` |
| `summary` | Summarize article using Claude AI (3 sentences) | `python diego_cli.py summary --url "https://example.com/article"` |
| `config` | Show current configuration | `python diego_cli.py config` |

### Source Options

All commands support a `--source` option to specify the news provider:

- `--source newsapi` - Use NewsAPI (80,000+ sources worldwide)
- `--source guardian` - Use The Guardian API (Guardian content only, historical archive back to 1999)
- `--source auto` - Auto-select best available source (default behavior)

## ⚙️ Configuration

Configure Diego using environment variables:

```bash
# API Keys
export NEWS_API_KEY='your-newsapi-key'        # Get from https://newsapi.org/
export GUARDIAN_API_KEY='your-guardian-key'   # Get from https://open-platform.theguardian.com/access/
export CLAUDE_API_KEY='your-claude-key'       # Get from https://console.anthropic.com/

# Optional (with defaults)
export NEWS_DEFAULT_COUNTRY='us'          # Default country
export NEWS_DEFAULT_LANGUAGE='en'         # Default language  
export NEWS_DEFAULT_PAGE_SIZE='10'        # Default article count
export NEWS_MAX_PAGE_SIZE='100'           # Maximum article count
export NEWS_DEFAULT_FORMAT='simple'       # Default output format
export APP_VERSION='1.0.0'                # App version
```

### API Key Setup

1. **NewsAPI**: Visit [newsapi.org](https://newsapi.org/) to get a free API key (1,000 requests/month)
2. **Guardian API**: Visit [Guardian Open Platform](https://open-platform.theguardian.com/access/) to get a free API key (5,000 requests/day)
3. **Claude AI**: Visit [Anthropic Console](https://console.anthropic.com/) to get an API key for article summarization

## 🏗️ Architecture

Diego consists of four main components:

### 1. Backend Architecture (`diego/backends/`)
Modular news API backend system with unified interface:
- `BaseBackend` - Abstract base class defining common interface
- `NewsApiBackend` - Clean wrapper around the `newsapi-python` library
- `GuardianBackend` - Guardian API client with NewsAPI-compatible interface
- Automatic source fallback when `--source auto` is used (tries NewsAPI first, falls back to Guardian)
- All backends provide: `get_top_headlines()`, `search_articles()`, `get_sources()`

### 2. NewsAPI Backend (`backends/newsapi_client.py`)
Wrapper around the `newsapi-python` library with simplified signatures:
- `get_top_headlines()` - Get breaking news and top stories
- `search_articles()` - Search through all articles  
- `get_sources()` - Get available news sources
- Supports 80,000+ sources worldwide

### 3. Guardian Backend (`backends/guardian_client.py`)
Clean wrapper around The Guardian's Open Platform API:
- `get_top_headlines()` - Get breaking news and top stories from Guardian
- `search_articles()` - Search through Guardian's archive (1999-present)
- `get_sources()` - Get Guardian sections as "sources"
- Full compatibility with NewsAPI interface for seamless source switching
- Intelligent parameter mapping and response normalization

### 4. Config Management (`config.py`)
Environment-based configuration with validation:
- Dataclass-based configuration supporting multiple API keys
- Environment variable loading with fallbacks
- Source-specific validation with detailed error messages
- Global singleton pattern

### 5. CLI Interface (`cli.py`)
Feature-rich command-line interface built with Click:
- Multiple commands with intuitive options
- Intelligent source selection with auto-fallback (`--source` option)
- Multiple output formats (simple, detailed, JSON)
- Comprehensive error handling with graceful source switching
- Configuration integration with multiple APIs

## 🧪 Testing

Diego features a comprehensive test suite following professional patterns:

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_config.py -v

# Use the test runner
python run_tests.py
```

**Test Coverage**: 85% (115 tests)
- `config.py`: 87% coverage
- `backends/newsapi_client.py`: 100% coverage
- `backends/guardian_client.py`: 86% coverage
- `cli.py`: 89% coverage

## 📁 Project Structure

```
diego/
├── diego/                      # Main package
│   ├── __init__.py            # Package initialization
│   ├── cli.py                 # Main CLI application
│   ├── config.py              # Configuration management
│   └── backends/              # News API backends
│       ├── __init__.py        # Backend exports
│       ├── base.py            # Abstract base backend class
│       ├── newsapi_client.py  # NewsAPI wrapper client
│       └── guardian_client.py # Guardian API wrapper client
├── diego_cli.py               # CLI entry point script
├── run_tests.py               # Test runner script
├── pyproject.toml             # Project configuration
├── requirements.txt           # Production dependencies
├── requirements-test.txt      # Test dependencies
├── docs/                      # Documentation
│   └── guardian_api_guide.md  # Guardian API usage guide
├── tests/                     # Test suite (115 tests)
│   ├── conftest.py           # Test fixtures
│   ├── test_cli.py           # CLI tests
│   ├── test_config.py        # Config tests
│   ├── test_news_org_api_client.py    # NewsAPI client tests
│   └── test_guardian_api_client.py    # Guardian client tests
└── README.md                  # This file
```

## 🎯 Examples

### Basic Usage

```python
from diego.backends import NewsApiBackend, GuardianBackend

# Initialize NewsAPI client
news_client = NewsApiBackend('your-newsapi-key')

# Initialize Guardian client
guardian_client = GuardianBackend('your-guardian-key')

# Get top headlines (both clients have identical interface)
headlines = news_client.get_top_headlines(category='technology', country='us')
guardian_headlines = guardian_client.get_top_headlines(category='technology', country='uk')

# Search articles
articles = news_client.search_articles(
    query='machine learning',
    page_size=25
)

# Get sources
sources = news_client.get_sources(category='business', country='us')
```

### CLI Examples

```bash
# Technology news from UK in detailed format
python diego_cli.py get-news --topic technology --country uk --format detailed

# Search with date filtering (API client method)
python diego_cli.py get-news --query "climate change" --limit 15

# Business news sources from US
python diego_cli.py sources --topic business --country us

# JSON output for programmatic use
python diego_cli.py get-news --topic science --format json

# Article summarization with Claude AI
python diego_cli.py summary --url "https://www.bbc.com/news/technology-12345"
python diego_cli.py summary --file "research_paper.txt"
echo "Long article text here..." | python diego_cli.py summary
```

## 📜 License

MIT License - feel free to use Diego in your projects!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)  
3. Run tests (`python -m pytest tests/`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 🔗 Links

- [NewsAPI Documentation](https://newsapi.org/docs)
- [newsapi-python Library](https://github.com/mattlisiv/newsapi-python)
- [Click Documentation](https://click.palletsprojects.com/)

---

**Get your free NewsAPI key**: https://newsapi.org/

Built with ❤️ using Python, Click, and NewsAPI
