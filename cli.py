#!/usr/bin/env python3

import click
import json
from datetime import datetime
from news_org_api_client import NewsOrgApiClient
from config import get_config, Config

# News categories available in News API
NEWS_CATEGORIES = [
    'business', 'entertainment', 'general', 'health', 
    'science', 'sports', 'technology'
]

def get_validated_config() -> Config:
    """Get and validate configuration."""
    config = get_config()
    if not config.validate():
        click.echo("❌ Configuration Error:")
        click.echo(config.get_error_message())
        raise click.Abort()
    return config

@click.group()
@click.version_option()
def cli():
    """Diego - News CLI tool powered by NewsAPI"""
    # Load version from config
    config = get_config()
    cli.version = config.app_version

@cli.command('config')
def show_config():
    """Show current configuration."""
    config = get_config()
    
    click.echo("📋 Current Configuration:")
    click.echo("=" * 30)
    click.echo(f"API Key: {'✅ Set' if config.news_api_key else '❌ Not set'}")
    click.echo(f"Default Country: {config.default_country}")
    click.echo(f"Default Language: {config.default_language}")
    click.echo(f"Default Page Size: {config.default_page_size}")
    click.echo(f"Max Page Size: {config.max_page_size}")
    click.echo(f"Default Format: {config.default_format}")
    click.echo(f"App Version: {config.app_version}")
    
    click.echo("\n🔧 Environment Variables:")
    click.echo("- NEWS_API_KEY (required)")
    click.echo("- NEWS_DEFAULT_COUNTRY (optional, default: us)")
    click.echo("- NEWS_DEFAULT_LANGUAGE (optional, default: en)")
    click.echo("- NEWS_DEFAULT_PAGE_SIZE (optional, default: 10)")
    click.echo("- NEWS_MAX_PAGE_SIZE (optional, default: 100)")
    click.echo("- NEWS_DEFAULT_FORMAT (optional, default: simple)")
    click.echo("- APP_VERSION (optional, default: 1.0.0)")
    
    if not config.validate():
        click.echo(f"\n❌ Configuration Issues:")
        click.echo(config.get_error_message())

@cli.command('list-topics')
def list_topics():
    """List available news topics/categories."""
    click.echo("Available news topics:")
    click.echo("-" * 25)
    for i, category in enumerate(NEWS_CATEGORIES, 1):
        click.echo(f"{i:2}. {category.capitalize()}")
    
    click.echo(f"\nTotal: {len(NEWS_CATEGORIES)} categories")
    click.echo("\nUse 'get-news --topic <category>' to get news for a specific topic")

@cli.command('get-news')
@click.option('--topic', '-t', help='News topic/category', 
              type=click.Choice(NEWS_CATEGORIES + ['all']))
@click.option('--query', '-q', help='Search query/keywords')
@click.option('--country', '-c', help='Country code (uses config default if not specified)')
@click.option('--limit', '-l', help='Number of articles (uses config default if not specified)', type=int)
@click.option('--format', '-f', 
              type=click.Choice(['simple', 'detailed', 'json']),
              help='Output format (uses config default if not specified)')
def get_news(topic, query, country, limit, format):
    """Get recent news articles by topic or search query."""
    config = get_validated_config()
    
    # Use config defaults if not specified
    country = country or config.default_country
    limit = limit or config.default_page_size
    format = format or config.default_format
    
    # Validate limit against config
    if limit > config.max_page_size:
        click.echo(f"❌ Limit cannot exceed {config.max_page_size}")
        return
    
    client = NewsOrgApiClient(config.news_api_key)
    
    try:
        if query:
            # Search for specific query
            response = client.search_articles(query=query, page_size=limit)
            click.echo(f"🔍 Search results for: '{query}'")
        elif topic and topic != 'all':
            # Get top headlines by category
            response = client.get_top_headlines(category=topic, country=country, page_size=limit)
            click.echo(f"📰 Top {topic.capitalize()} news:")
        else:
            # Get general top headlines
            response = client.get_top_headlines(country=country, page_size=limit)
            click.echo(f"📰 Top headlines:")
        
        if response['status'] != 'ok':
            click.echo(f"❌ Error: {response['message']}")
            return
        
        articles = response.get('articles', [])
        total_results = response.get('totalResults', 0)
        
        if not articles:
            click.echo("No articles found.")
            return
        
        click.echo(f"Found {total_results} articles (showing {len(articles)})")
        click.echo("=" * 60)
        
        if format == 'json':
            click.echo(json.dumps(articles, indent=2))
        else:
            for i, article in enumerate(articles, 1):
                if format == 'detailed':
                    _print_detailed_article(i, article)
                else:
                    _print_simple_article(i, article)
                
                if i < len(articles):
                    click.echo()
    
    except Exception as e:
        click.echo(f"❌ Error fetching news: {str(e)}")

def _print_simple_article(index, article):
    """Print article in simple format."""
    title = article.get('title', 'No title')
    source = article.get('source', {}).get('name', 'Unknown source')
    published = article.get('publishedAt', '')
    
    if published:
        try:
            dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
            published = dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            published = 'Invalid date'
    
    click.echo(f"{index:2}. {title}")
    click.echo(f"    Source: {source} | {published}")

def _print_detailed_article(index, article):
    """Print article in detailed format."""
    title = article.get('title', 'No title')
    source = article.get('source', {}).get('name', 'Unknown source')
    author = article.get('author', 'Unknown author')
    published = article.get('publishedAt', '')
    description = article.get('description', 'No description')
    url = article.get('url', '')
    
    if published:
        try:
            dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
            published = dt.strftime('%Y-%m-%d %H:%M UTC')
        except (ValueError, TypeError):
            published = 'Invalid date'
    
    click.echo(f"{index:2}. {title}")
    click.echo(f"    Source: {source}")
    click.echo(f"    Author: {author}")
    click.echo(f"    Published: {published}")
    click.echo(f"    Description: {description}")
    if url:
        click.echo(f"    URL: {url}")

@cli.command('sources')
@click.option('--topic', '-t', help='Filter by topic/category', 
              type=click.Choice(NEWS_CATEGORIES))
@click.option('--country', '-c', help='Filter by country code')
@click.option('--format', '-f', 
              type=click.Choice(['simple', 'detailed', 'json']),
              help='Output format (uses config default if not specified)')
def sources(topic, country, format):
    """List available news sources."""
    config = get_validated_config()
    
    # Use config default if not specified
    format = format or config.default_format
    
    client = NewsOrgApiClient(config.news_api_key)
    
    try:
        response = client.get_sources(category=topic, country=country)
        
        if response['status'] != 'ok':
            click.echo(f"❌ Error: {response['message']}")
            return
        
        sources_list = response.get('sources', [])
        
        if not sources_list:
            click.echo("No sources found.")
            return
        
        filter_info = []
        if topic:
            filter_info.append(f"topic: {topic}")
        if country:
            filter_info.append(f"country: {country}")
        
        filter_str = f" ({', '.join(filter_info)})" if filter_info else ""
        click.echo(f"📺 Available news sources{filter_str}:")
        click.echo("=" * 50)
        
        if format == 'json':
            click.echo(json.dumps(sources_list, indent=2))
        else:
            for i, source in enumerate(sources_list, 1):
                if format == 'detailed':
                    _print_detailed_source(i, source)
                else:
                    _print_simple_source(i, source)
                
                if i < len(sources_list):
                    click.echo()
    
    except Exception as e:
        click.echo(f"❌ Error fetching sources: {str(e)}")

def _print_simple_source(index, source):
    """Print source in simple format."""
    name = source.get('name', 'Unknown')
    category = source.get('category', 'general')
    country = source.get('country', 'unknown')
    
    click.echo(f"{index:2}. {name} ({category.capitalize()}, {country.upper()})")

def _print_detailed_source(index, source):
    """Print source in detailed format."""
    name = source.get('name', 'Unknown')
    description = source.get('description', 'No description')
    category = source.get('category', 'general')
    country = source.get('country', 'unknown')
    language = source.get('language', 'unknown')
    url = source.get('url', '')
    
    click.echo(f"{index:2}. {name}")
    click.echo(f"    Description: {description}")
    click.echo(f"    Category: {category.capitalize()}")
    click.echo(f"    Country: {country.upper()}")
    click.echo(f"    Language: {language.upper()}")
    if url:
        click.echo(f"    URL: {url}")

if __name__ == '__main__':
    cli()