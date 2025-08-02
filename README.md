# Diego - News CLI Tool 📰

[![CI Pipeline](https://github.com/Melevir/diego/actions/workflows/ci.yml/badge.svg)](https://github.com/Melevir/diego/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen)](https://github.com/Melevir/diego/actions)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A powerful command-line news aggregator powered by [NewsAPI](https://newsapi.org/), featuring a clean wrapper library and comprehensive CLI interface.

## ✨ Features

- 🔍 **Search articles** by keywords or phrases
- 📊 **Browse news by category** (business, tech, sports, etc.)
- 🌍 **Filter by country** and language
- 📺 **List news sources** with filtering options
- 🎨 **Multiple output formats** (simple, detailed, JSON)
- ⚙️ **Environment-based configuration**
- 🧪 **Comprehensive test suite** (89% coverage)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/melevir/diego.git
cd diego

# Install dependencies
pip install -r requirements-test.txt

# Set your NewsAPI key
export NEWS_API_KEY='your-api-key-from-newsapi.org'
```

### Usage

```bash
# List available news categories
python cli.py list-topics

# Get top technology news
python cli.py get-news --topic technology

# Search for specific topics
python cli.py get-news --query "artificial intelligence"

# Get detailed format with custom options
python cli.py get-news --topic business --country uk --limit 5 --format detailed

# List news sources
python cli.py sources --topic technology

# Check current configuration
python cli.py config
```

## 📋 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `list-topics` | Show available news categories | `python cli.py list-topics` |
| `get-news` | Get news by topic or search query | `python cli.py get-news --topic tech` |
| `sources` | List available news sources | `python cli.py sources --topic business` |
| `config` | Show current configuration | `python cli.py config` |

## ⚙️ Configuration

Configure Diego using environment variables:

```bash
# Required
export NEWS_API_KEY='your-newsapi-key'

# Optional (with defaults)
export NEWS_DEFAULT_COUNTRY='us'          # Default country
export NEWS_DEFAULT_LANGUAGE='en'         # Default language  
export NEWS_DEFAULT_PAGE_SIZE='10'        # Default article count
export NEWS_MAX_PAGE_SIZE='100'           # Maximum article count
export NEWS_DEFAULT_FORMAT='simple'       # Default output format
export APP_VERSION='1.0.0'                # App version
```

## 🏗️ Architecture

Diego consists of three main components:

### 1. NewsOrgApiClient (`news_org_api_client.py`)
Clean wrapper around the `newsapi-python` library with simplified signatures:
- `get_top_headlines()` - Get breaking news and top stories
- `search_articles()` - Search through all articles
- `get_sources()` - Get available news sources

### 2. Config Management (`config.py`)
Environment-based configuration with validation:
- Dataclass-based configuration
- Environment variable loading
- Validation with detailed error messages
- Global singleton pattern

### 3. CLI Interface (`cli.py`)
Feature-rich command-line interface built with Click:
- Multiple commands with intuitive options
- Multiple output formats (simple, detailed, JSON)
- Comprehensive error handling
- Configuration integration

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

**Test Coverage**: 89% (71 tests)
- `config.py`: 100% coverage
- `news_org_api_client.py`: 100% coverage  
- `cli.py`: 92% coverage

## 📁 Project Structure

```
diego/
├── cli.py                      # Main CLI application
├── config.py                   # Configuration management
├── news_org_api_client.py      # NewsAPI wrapper client
├── example_usage.py            # Usage examples
├── run_tests.py               # Test runner script
├── pyproject.toml             # Project configuration
├── requirements-test.txt       # Test dependencies
├── tests/                     # Test suite
│   ├── conftest.py           # Test fixtures
│   ├── test_cli.py           # CLI tests (17 tests)
│   ├── test_config.py        # Config tests (20 tests)
│   └── test_news_org_api_client.py  # Client tests (25 tests)
└── README.md                  # This file
```

## 🎯 Examples

### Basic Usage

```python
from news_org_api_client import NewsOrgApiClient

# Initialize client
client = NewsOrgApiClient('your-api-key')

# Get top headlines
headlines = client.get_top_headlines(category='technology', country='us')

# Search articles
articles = client.search_articles(
    query='machine learning',
    from_date='2024-01-01',
    sort_by='popularity'
)

# Get sources
sources = client.get_sources(category='business', country='us')
```

### CLI Examples

```bash
# Technology news from UK in detailed format
python cli.py get-news --topic technology --country uk --format detailed

# Search with date filtering (API client method)
python cli.py get-news --query "climate change" --limit 15

# Business news sources from US
python cli.py sources --topic business --country us

# JSON output for programmatic use
python cli.py get-news --topic science --format json
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
