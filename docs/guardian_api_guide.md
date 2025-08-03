# Guardian API Integration Guide

## Overview

The Guardian API provides access to over 2 million articles from The Guardian newspaper, dating back to 1999. This guide covers how to use The Guardian API with Diego's GuardianApiClient wrapper.

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Available Endpoints](#available-endpoints)
4. [GuardianApiClient Usage](#guardinapiclient-usage)
5. [Parameter Mapping](#parameter-mapping)
6. [Response Format](#response-format)
7. [Rate Limits & Best Practices](#rate-limits--best-practices)
8. [Examples](#examples)

## API Overview

### Base Information
- **Base URL**: `https://content.guardianapis.com`
- **Format**: JSON
- **Coverage**: Articles from 1999 to present
- **Content**: News, opinion, sport, culture, lifestyle
- **Language**: English only

### Key Features
- Full-text search across all content
- Advanced filtering by date, section, tags
- Rich metadata including author, publication date, word count
- Access to article body text (when available)
- Historical article archive

## Authentication

### Getting an API Key
1. Visit [Guardian Open Platform](https://open-platform.theguardian.com/access/)
2. Register for a free developer account
3. Get your API key (e.g., `21535a59-66e7-4c61-af2c-133f02a39654`)

### Rate Limits
- **Free Tier**: 5,000 calls per day
- **Rate Limit**: 12 requests per second
- **Monitoring**: Check response headers for usage info

## Available Endpoints

### 1. Content Search (`/search`)
Search and retrieve articles with advanced filtering.

**Parameters:**
- `q` - Search query keywords
- `section` - Filter by section (e.g., technology, sport, business)
- `from-date` / `to-date` - Date range (YYYY-MM-DD)
- `order-by` - Sort order (newest, oldest, relevance)
- `page-size` - Results per page (max 200)
- `show-fields` - Additional fields (all, body, byline, etc.)

### 2. Sections (`/sections`)
Retrieve all available Guardian sections.

### 3. Tags (`/tags`)
Get all tags used to classify content.

### 4. Editions (`/editions`)
Access different regional editions (UK, US, AU).

## GuardianApiClient Usage

The `GuardianApiClient` provides the same interface as `NewsOrgApiClient` for seamless integration.

### Initialization
```python
from guardian_api_client import GuardianApiClient

client = GuardianApiClient(api_key='your-guardian-api-key')
```

### Methods

#### get_top_headlines()
Get recent top news articles.

```python
headlines = client.get_top_headlines(
    query="artificial intelligence",
    country="us",  # Maps to Guardian editions
    category="technology",  # Maps to Guardian sections
    page_size=20
)
```

#### search_articles()
Search through all Guardian articles.

```python
articles = client.search_articles(
    query="climate change",
    from_date="2025-01-01",
    to_date="2025-08-01",
    sort_by="publishedAt",
    page_size=50
)
```

#### get_sources()
Get available Guardian sections as "sources".

```python
sources = client.get_sources(
    category="technology",
    country="us"
)
```

## Parameter Mapping

### NewsAPI → Guardian API

| NewsAPI Parameter | Guardian Parameter | Notes |
|-------------------|-------------------|--------|
| `query` | `q` | Direct mapping |
| `country` | `edition` | us→US, uk→UK, au→AU |
| `category` | `section` | business→business, tech→technology |
| `sources` | Not supported | Guardian only has Guardian content |
| `from_date` | `from-date` | Same YYYY-MM-DD format |
| `to_date` | `to-date` | Same YYYY-MM-DD format |
| `language` | Not supported | Guardian is English only |
| `sort_by` | `order-by` | publishedAt→newest, relevancy→relevance |
| `page_size` | `page-size` | Max 200 for Guardian vs 100 for NewsAPI |

### Category Mapping

| NewsAPI Category | Guardian Section |
|------------------|------------------|
| `business` | `business` |
| `technology` | `technology` |
| `science` | `science` |
| `sports` | `sport` |
| `health` | `lifeandstyle` |
| `entertainment` | `culture` |
| `general` | `news` |

## Response Format

### Guardian Raw Response
```json
{
  "response": {
    "status": "ok",
    "total": 1000,
    "results": [
      {
        "id": "technology/2025/aug/02/ai-breakthrough",
        "webTitle": "AI breakthrough changes everything",
        "webUrl": "https://www.theguardian.com/technology/2025/aug/02/ai-breakthrough",
        "webPublicationDate": "2025-08-02T10:30:00Z",
        "fields": {
          "byline": "Tech Reporter",
          "standfirst": "Brief description...",
          "body": "Full article content..."
        }
      }
    ]
  }
}
```

### Normalized NewsAPI Format
```json
{
  "status": "ok",
  "totalResults": 1000,
  "articles": [
    {
      "title": "AI breakthrough changes everything",
      "description": "Brief description...",
      "url": "https://www.theguardian.com/technology/2025/aug/02/ai-breakthrough",
      "source": {"name": "The Guardian"},
      "author": "Tech Reporter",
      "publishedAt": "2025-08-02T10:30:00Z",
      "content": "Full article content..."
    }
  ]
}
```

## Rate Limits & Best Practices

### Managing Rate Limits
- **Check Headers**: Monitor `X-RateLimit-Remaining`
- **Implement Backoff**: Use exponential backoff for rate limit errors
- **Cache Responses**: Store frequently accessed data locally
- **Batch Requests**: Minimize API calls where possible

### Best Practices
1. **Use Specific Queries**: More specific searches return better results
2. **Filter by Date**: Limit searches to relevant time periods
3. **Request Only Needed Fields**: Use `show-fields` parameter efficiently
4. **Handle Pagination**: Guardian supports up to 200 results per page
5. **Error Handling**: Always check response status and handle errors gracefully

## Examples

### Basic News Search
```python
client = GuardianApiClient('your-api-key')

# Get latest technology news
tech_news = client.get_top_headlines(
    category="technology",
    page_size=10
)

for article in tech_news['articles']:
    print(f"{article['title']} - {article['publishedAt']}")
```

### Advanced Article Search
```python
# Search for climate articles in the last month
climate_articles = client.search_articles(
    query="climate change policy",
    from_date="2025-07-01",
    to_date="2025-08-01",
    sort_by="relevancy",
    page_size=25
)

print(f"Found {climate_articles['totalResults']} articles")
```

### Working with Sources/Sections
```python
# Get all available Guardian sections
sections = client.get_sources()

for source in sections['sources']:
    print(f"{source['name']}: {source['description']}")
```

### Error Handling
```python
try:
    articles = client.search_articles(query="breaking news")
    
    if articles['status'] == 'ok':
        print(f"Success: {len(articles['articles'])} articles found")
    else:
        print(f"API Error: {articles['message']}")
        
except Exception as e:
    print(f"Client Error: {str(e)}")
```

## Comparison with NewsAPI

### Advantages
- **Historical Archive**: Access to 25+ years of Guardian content
- **High-Quality Content**: Professional journalism and editorial standards
- **Rich Metadata**: Detailed article information and full-text search
- **Free Tier**: Generous 5,000 daily requests
- **No Credit Card**: Free registration without payment info

### Limitations
- **Single Source**: Only Guardian content (vs NewsAPI's multiple sources)
- **English Only**: No multi-language support
- **UK/US Focus**: Limited international coverage compared to NewsAPI
- **Fewer Categories**: Limited section variety compared to NewsAPI sources

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Check your API key is correct
- Ensure API key is included in all requests

**429 Rate Limit Exceeded**
- Implement request throttling
- Add delays between requests
- Use exponential backoff

**404 Not Found**
- Verify endpoint URLs are correct
- Check article IDs are valid

**Empty Results**
- Try broader search terms
- Adjust date ranges
- Remove overly restrictive filters

### Support Resources
- [Guardian API Documentation](https://open-platform.theguardian.com/documentation/)
- [Guardian API Forum](https://groups.google.com/g/guardian-api-talk)
- [API Status Page](https://open-platform.theguardian.com/status/)

---

**Last Updated**: August 2025  
**API Version**: v1  
**Client Version**: 1.0.0