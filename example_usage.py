"""
Example usage of NewsOrgApiClient wrapper.

Before running:
1. Install newsapi-python: pip install newsapi-python
2. Get your API key from https://newsapi.org/
3. Replace 'YOUR_API_KEY' with your actual API key
"""

from news_org_api_client import NewsOrgApiClient


def main():
    # Initialize client with your API key
    client = NewsOrgApiClient('YOUR_API_KEY')
    
    # Example 1: Get top headlines
    print("=== TOP HEADLINES ===")
    headlines = client.get_top_headlines(query='bitcoin', country='us')
    
    if headlines['status'] == 'ok':
        print(f"Found {headlines['totalResults']} articles")
        for article in headlines['articles'][:3]:  # Show first 3
            print(f"- {article['title']}")
            print(f"  Source: {article['source']['name']}")
            print()
    else:
        print(f"Error: {headlines['message']}")
    
    # Example 2: Search articles
    print("=== SEARCH ARTICLES ===")
    articles = client.search_articles(
        query='artificial intelligence',
        from_date='2024-01-01',
        sort_by='popularity'
    )
    
    if articles['status'] == 'ok':
        print(f"Found {articles['totalResults']} articles about AI")
        for article in articles['articles'][:3]:  # Show first 3
            print(f"- {article['title']}")
            print(f"  Published: {article['publishedAt']}")
            print()
    else:
        print(f"Error: {articles['message']}")
    
    # Example 3: Get news sources
    print("=== NEWS SOURCES ===")
    sources = client.get_sources(category='technology')
    
    if sources['status'] == 'ok':
        print(f"Found {len(sources['sources'])} technology sources")
        for source in sources['sources'][:5]:  # Show first 5
            print(f"- {source['name']}: {source['description']}")
        print()
    else:
        print(f"Error: {sources['message']}")


if __name__ == '__main__':
    main()