#!/usr/bin/env python3

import click
import json
import sys
import requests
from typing import Optional
from datetime import datetime
from .backends import NewsApiBackend, GuardianBackend
from .config import get_config, Config
from bs4 import BeautifulSoup
from anthropic import Anthropic
from .analytics import AnalyticsTracker

NEWS_CATEGORIES = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

# Global analytics tracker
_analytics_tracker = None


def get_analytics_tracker() -> AnalyticsTracker:
    """Get global analytics tracker instance."""
    global _analytics_tracker
    if _analytics_tracker is None:
        _analytics_tracker = AnalyticsTracker()
    return _analytics_tracker


def get_validated_config(source: str = "newsapi") -> Config:
    config = get_config()
    if not config.validate(source):
        click.echo("❌ Configuration Error:")
        click.echo(config.get_error_message(source))
        raise click.Abort()
    return config


def get_news_client(source: str, config: Config):
    if source == "newsapi":
        return NewsApiBackend(config.news_api_key)
    elif source == "guardian":
        return GuardianBackend(config.guardian_api_key)
    elif source == "auto":
        if config.news_api_key:
            return NewsApiBackend(config.news_api_key), "newsapi"
        elif config.guardian_api_key:
            return GuardianBackend(config.guardian_api_key), "guardian"

    raise click.ClickException(f"Unsupported source: {source}")


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Diego - News CLI tool"""
    pass


@cli.command("config")
def show_config():
    """Show current configuration including analytics settings."""
    tracker = get_analytics_tracker()
    tracker.start_session()

    config = get_config()

    click.echo("📋 Current Configuration:")
    click.echo("=" * 30)
    click.echo(f"NewsAPI Key: {'✅ Set' if config.news_api_key else '❌ Not set'}")
    click.echo(f"Guardian API Key: {'✅ Set' if config.guardian_api_key else '❌ Not set'}")
    click.echo(f"Claude API Key: {'✅ Set' if config.claude_api_key else '❌ Not set'}")
    click.echo(f"Default Country: {config.default_country}")
    click.echo(f"Default Language: {config.default_language}")
    click.echo(f"Default Page Size: {config.default_page_size}")
    click.echo(f"Max Page Size: {config.max_page_size}")
    click.echo(f"Default Format: {config.default_format}")
    click.echo(f"App Version: {config.app_version}")

    click.echo("\n📊 Analytics Settings:")
    click.echo(f"Analytics Enabled: {'✅ Yes' if config.analytics_enabled else '❌ No'}")
    click.echo(f"Data Retention: {config.analytics_retention_days} days")
    click.echo(f"Tracking Active: {'✅ Yes' if tracker.is_enabled() else '❌ No'}")

    click.echo("\n🔧 Environment Variables:")
    click.echo("- NEWS_API_KEY (optional)")
    click.echo("- GUARDIAN_API_KEY (optional)")
    click.echo("- CLAUDE_API_KEY (optional)")
    click.echo("- NEWS_DEFAULT_COUNTRY (optional, default: us)")
    click.echo("- NEWS_DEFAULT_LANGUAGE (optional, default: en)")
    click.echo("- NEWS_DEFAULT_PAGE_SIZE (optional, default: 10)")
    click.echo("- NEWS_MAX_PAGE_SIZE (optional, default: 100)")
    click.echo("- NEWS_DEFAULT_FORMAT (optional, default: simple)")
    click.echo("- APP_VERSION (optional, default: 1.0.0)")
    click.echo("- DIEGO_ANALYTICS_ENABLED (optional, default: true)")
    click.echo("- DIEGO_ANALYTICS_RETENTION_DAYS (optional, default: 365)")

    tracker.track_config_view()

    if not config.validate():
        click.echo("\n❌ Configuration Issues:")
        click.echo(config.get_error_message())


@cli.command("list-topics")
def list_topics():
    """List available news topics and categories."""
    tracker = get_analytics_tracker()
    tracker.start_session()

    click.echo("Available news topics:")
    click.echo("-" * 25)
    for i, category in enumerate(NEWS_CATEGORIES, 1):
        click.echo(f"{i:2}. {category.capitalize()}")

    click.echo(f"\nTotal: {len(NEWS_CATEGORIES)} categories")
    click.echo("\nUse 'get-news --topic <category>' to get news for a specific topic")

    tracker.track_topics_list()


@cli.command("get-news")
@click.option("--topic", "-t", help="News topic/category", type=click.Choice(NEWS_CATEGORIES + ["all"]))
@click.option("--query", "-q", help="Search query/keywords")
@click.option("--country", "-c", help="Country code (uses config default if not specified)")
@click.option("--limit", "-l", help="Number of articles (uses config default if not specified)", type=int)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["simple", "detailed", "json"]),
    help="Output format (uses config default if not specified)",
)
@click.option(
    "--source",
    "-s",
    type=click.Choice(["newsapi", "guardian", "auto"]),
    default="auto",
    help="News source to use (default: auto - try NewsAPI first, fallback to Guardian)",
)
def get_news(topic, query, country, limit, format, source):
    """Get news articles by topic or search query."""
    tracker = get_analytics_tracker()
    tracker.start_session()

    config = get_validated_config(source)

    country = country or config.default_country
    limit = limit or config.default_page_size
    format = format or config.default_format

    if source == "auto":
        client_result = get_news_client(source, config)
        if isinstance(client_result, tuple):
            client, actual_source = client_result
            click.echo(f"📡 Using {actual_source.upper()} (auto-detected)")
        else:
            client = client_result
            actual_source = source
    else:
        client = get_news_client(source, config)
        actual_source = source
        click.echo(f"📡 Using {actual_source.upper()}")

    max_limit = 200 if actual_source == "guardian" else config.max_page_size
    if limit > max_limit:
        click.echo(f"❌ Limit cannot exceed {max_limit} for {actual_source}")
        return

    try:
        if query:
            # Search for specific query
            response = client.search_articles(query=query, page_size=limit)
            click.echo(f"🔍 Search results for: '{query}'")
        elif topic and topic != "all":
            # Get top headlines by category
            response = client.get_top_headlines(category=topic, country=country, page_size=limit)
            click.echo(f"📰 Top {topic.capitalize()} news:")
        else:
            # Get general top headlines
            response = client.get_top_headlines(country=country, page_size=limit)
            click.echo("📰 Top headlines:")

        if response["status"] != "ok":
            click.echo(f"❌ Error: {response['message']}")
            return

        articles = response.get("articles", [])
        total_results = response.get("totalResults", 0)

        if not articles:
            click.echo("No articles found.")
            tracker.track_search(topic=topic, source=actual_source, keywords=query, country=country, result_count=0)
            return

        click.echo(f"Found {total_results} articles (showing {len(articles)})")
        click.echo("=" * 60)

        if format == "json":
            click.echo(json.dumps(articles, indent=2))
        else:
            for i, article in enumerate(articles, 1):
                if format == "detailed":
                    _print_detailed_article(i, article)
                else:
                    _print_simple_article(i, article)

                if i < len(articles):
                    click.echo()

        # Track successful search
        tracker.track_search(
            topic=topic, source=actual_source, keywords=query, country=country, result_count=len(articles)
        )

    except Exception as e:
        click.echo(f"❌ Error fetching news: {str(e)}")
        # Track failed search (source might not be available in exception context)
        tracker.track_search(topic=topic, source=source, keywords=query, country=country, result_count=0)


def _print_simple_article(index, article):
    title = article.get("title", "No title")
    source = article.get("source", {}).get("name", "Unknown source")
    published = article.get("publishedAt", "")

    if published:
        try:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            published = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            published = "Invalid date"

    click.echo(f"{index:2}. {title}")
    click.echo(f"    Source: {source} | {published}")


def _print_detailed_article(index, article):
    title = article.get("title", "No title")
    source = article.get("source", {}).get("name", "Unknown source")
    author = article.get("author", "Unknown author")
    published = article.get("publishedAt", "")
    description = article.get("description", "No description")
    url = article.get("url", "")

    if published:
        try:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            published = dt.strftime("%Y-%m-%d %H:%M UTC")
        except (ValueError, TypeError):
            published = "Invalid date"

    click.echo(f"{index:2}. {title}")
    click.echo(f"    Source: {source}")
    click.echo(f"    Author: {author}")
    click.echo(f"    Published: {published}")
    click.echo(f"    Description: {description}")
    if url:
        click.echo(f"    URL: {url}")


@cli.command("sources")
@click.option("--topic", "-t", help="Filter by topic/category", type=click.Choice(NEWS_CATEGORIES))
@click.option("--country", "-c", help="Filter by country code")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["simple", "detailed", "json"]),
    help="Output format (uses config default if not specified)",
)
@click.option(
    "--source",
    "-s",
    type=click.Choice(["newsapi", "guardian", "auto"]),
    default="auto",
    help="News source to use (default: auto - try NewsAPI first, fallback to Guardian)",
)
def sources(topic, country, format, source):
    """List available news sources with filtering options."""
    tracker = get_analytics_tracker()
    tracker.start_session()

    config = get_validated_config(source)

    format = format or config.default_format

    if source == "auto":
        client_result = get_news_client(source, config)
        if isinstance(client_result, tuple):
            client, actual_source = client_result
            click.echo(f"📡 Using {actual_source.upper()} (auto-detected)")
        else:
            client = client_result
            actual_source = source
    else:
        client = get_news_client(source, config)
        actual_source = source
        click.echo(f"📡 Using {actual_source.upper()}")

    try:
        response = client.get_sources(category=topic, country=country)

        if response["status"] != "ok":
            click.echo(f"❌ Error: {response['message']}")
            return

        sources_list = response.get("sources", [])

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

        if format == "json":
            click.echo(json.dumps(sources_list, indent=2))
        else:
            for i, source in enumerate(sources_list, 1):
                if format == "detailed":
                    _print_detailed_source(i, source)
                else:
                    _print_simple_source(i, source)

                if i < len(sources_list):
                    click.echo()

        # Track successful sources listing
        tracker.track_sources_list(source=actual_source, topic=topic, country=country, result_count=len(sources_list))

    except Exception as e:
        click.echo(f"❌ Error fetching sources: {str(e)}")
        # Track failed sources listing
        tracker.track_sources_list(source=source, topic=topic, country=country, result_count=0)


def _print_simple_source(index, source):
    name = source.get("name", "Unknown")
    category = source.get("category", "general")
    country = source.get("country", "unknown")

    click.echo(f"{index:2}. {name} ({category.capitalize()}, {country.upper()})")


def _print_detailed_source(index, source):
    name = source.get("name", "Unknown")
    description = source.get("description", "No description")
    category = source.get("category", "general")
    country = source.get("country", "unknown")
    language = source.get("language", "unknown")
    url = source.get("url", "")

    click.echo(f"{index:2}. {name}")
    click.echo(f"    Description: {description}")
    click.echo(f"    Category: {category.capitalize()}")
    click.echo(f"    Country: {country.upper()}")
    click.echo(f"    Language: {language.upper()}")
    if url:
        click.echo(f"    URL: {url}")


def get_claude_client(config: Config) -> Anthropic:
    """Initialize Claude client with API key."""
    if not config.claude_api_key:
        raise click.ClickException("Claude API key not configured. Set CLAUDE_API_KEY environment variable.")
    return Anthropic(api_key=config.claude_api_key)


def extract_text_from_url(url: str) -> str:
    """Extract text content from a web URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text from common article containers
        text_containers = soup.find_all(
            ["article", "main", "div"],
            class_=lambda x: x
            and any(word in x.lower() for word in ["content", "article", "body", "story", "text", "post"]),
        )

        if text_containers:
            text = " ".join([container.get_text() for container in text_containers])
        else:
            # Fallback to body text
            text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return text

    except requests.RequestException as e:
        raise click.ClickException(f"Error fetching URL: {str(e)}")
    except Exception as e:
        raise click.ClickException(f"Error extracting text from URL: {str(e)}")


def read_text_from_file(file_path: str) -> str:
    """Read text content from a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise click.ClickException(f"File not found: {file_path}")
    except Exception as e:
        raise click.ClickException(f"Error reading file: {str(e)}")


def read_text_from_stdin() -> str:
    """Read text content from stdin."""
    try:
        if sys.stdin.isatty():
            click.echo("Enter article text (press Ctrl+D when finished):")
        text = sys.stdin.read().strip()
        if not text:
            raise click.ClickException("No text provided")
        return text
    except KeyboardInterrupt:
        raise click.ClickException("Operation cancelled")
    except Exception as e:
        raise click.ClickException(f"Error reading from stdin: {str(e)}")


def summarize_with_claude(client: Anthropic, text: str) -> str:
    """Generate a 3-sentence summary using Claude."""
    try:
        # Truncate text if too long (Claude has token limits)
        max_chars = 100000  # Conservative limit
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            click.echo("⚠️  Text truncated due to length limits")

        prompt = f"""Please summarize the following article in exactly 3 sentences. The summary should be clear, concise, and capture the main points of the article.

Article text:
{text}

Summary (exactly 3 sentences):"""

        message = client.messages.create(
            model="claude-3-haiku-20240307", max_tokens=200, messages=[{"role": "user", "content": prompt}]
        )

        summary = message.content[0].text.strip()

        # Ensure we have exactly 3 sentences
        sentences = [s.strip() for s in summary.split(".") if s.strip()]
        if len(sentences) > 3:
            summary = ". ".join(sentences[:3]) + "."
        elif len(sentences) < 3:
            # If Claude returned fewer than 3 sentences, keep as is
            summary = ". ".join(sentences) + ("." if not summary.endswith(".") else "")

        return summary

    except Exception as e:
        raise click.ClickException(f"Error generating summary with Claude: {str(e)}")


@cli.command("summary")
@click.option("--url", "-u", help="URL of the article to summarize")
@click.option("--file", "-f", "file_path", help="Path to text file to summarize")
def summary(url: Optional[str], file_path: Optional[str]):
    """Summarize an article using Claude AI (exactly 3 sentences)."""
    tracker = get_analytics_tracker()
    tracker.start_session()

    config = get_validated_config("claude")

    # Determine input source
    input_sources = sum([bool(url), bool(file_path)])

    if input_sources > 1:
        raise click.ClickException("Please specify only one input source (--url, --file, or stdin)")

    try:
        # Get article text based on input method
        if url:
            click.echo(f"🔗 Fetching article from: {url}")
            text = extract_text_from_url(url)
        elif file_path:
            click.echo(f"📄 Reading article from: {file_path}")
            text = read_text_from_file(file_path)
        else:
            # Read from stdin
            text = read_text_from_stdin()

        if not text.strip():
            raise click.ClickException("No text content found to summarize")

        # Show text length info
        word_count = len(text.split())
        click.echo(f"📝 Article length: {word_count} words")

        # Generate summary using Claude
        click.echo("🤖 Generating summary with Claude AI...")
        claude_client = get_claude_client(config)
        summary_text = summarize_with_claude(claude_client, text)

        # Display the summary
        click.echo("\n" + "=" * 60)
        click.echo("📋 SUMMARY")
        click.echo("=" * 60)
        click.echo(summary_text)
        click.echo("=" * 60)

        # Track successful summary
        source_type = "url" if url else "file" if file_path else "stdin"
        duration = tracker.end_session()
        tracker.track_summary(source_type=source_type, duration=duration)

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        # Track failed summary
        source_type = "url" if url else "file" if file_path else "stdin"
        duration = tracker.end_session()
        tracker.track_summary(source_type=source_type, duration=duration)


@cli.command("analytics")
@click.option("--period", "-p", default=30, help="Analysis period in days")
@click.option("--show-bias-score", is_flag=True, help="Include bias analysis")
@click.option("--export-report", "-e", help="Export report to file")
def analytics_command(period: int, show_bias_score: bool, export_report: Optional[str]):
    """View news consumption analytics and insights."""
    from .analytics import InsightsGenerator, DataExporter

    tracker = get_analytics_tracker()
    tracker.start_session()

    try:
        # Generate insights report
        insights = InsightsGenerator()
        report = insights.generate_consumption_report(period)

        # Display key metrics
        key_metrics = report.get("key_metrics", {})
        click.echo(f"📊 Analytics Report ({period} days)")
        click.echo("=" * 50)
        click.echo(f"Total Activities: {key_metrics.get('total_activities', 0)}")
        click.echo(f"Daily Average: {key_metrics.get('daily_average', 0):.1f}")
        click.echo(f"Unique Sources: {key_metrics.get('unique_sources', 0)}")
        click.echo(f"Topics Explored: {key_metrics.get('unique_topics', 0)}")
        click.echo(f"Engagement Score: {key_metrics.get('engagement_score', 0):.2f}")

        # Show health score
        health_score = report.get("health_score", {})
        click.echo(f"\n🏥 Consumption Health: {health_score.get('interpretation', 'Unknown').title()}")
        click.echo(f"Overall Score: {health_score.get('overall_score', 0):.2f}/1.0")
        click.echo(f"{health_score.get('message', '')}")

        # Show bias analysis if requested
        if show_bias_score:
            source_analysis = report.get("source_analysis", {})
            click.echo("\n⚖️ Source Diversity Analysis:")
            click.echo(f"Diversity Score: {source_analysis.get('diversity_score', 0):.2f}")

            political_balance = source_analysis.get("political_balance", {})
            total_sources = sum(political_balance.values())
            if total_sources > 0:
                left_pct = (political_balance.get("left", 0) / total_sources) * 100
                center_pct = (political_balance.get("center", 0) / total_sources) * 100
                right_pct = (political_balance.get("right", 0) / total_sources) * 100
                click.echo(
                    f"Political Balance: Left {left_pct:.1f}% | Center {center_pct:.1f}% | Right {right_pct:.1f}%"
                )

            echo_chamber = source_analysis.get("echo_chamber_status", {})
            if echo_chamber.get("is_echo_chamber", False):
                click.echo(f"⚠️ Echo Chamber Detected: {echo_chamber.get('echo_chamber_type', 'Unknown')}")

        # Show key insights
        insights_list = report.get("insights", [])
        if insights_list:
            click.echo("\n💡 Key Insights:")
            for insight in insights_list[:3]:  # Show top 3 insights
                click.echo(f"• {insight.get('insight', '')}: {insight.get('detail', '')}")

        # Export report if requested
        if export_report:
            exporter = DataExporter()
            exported_file = exporter.export_insights_report(
                days=period,
                format_type="html" if export_report.endswith(".html") else "json",
                output_file=export_report,
            )
            click.echo(f"\n📄 Report exported to: {exported_file}")

        tracker.track_analytics_view(period, "basic" if not show_bias_score else "detailed")

    except Exception as e:
        click.echo(f"❌ Error generating analytics: {str(e)}")


@cli.command("recommend")
@click.option("--balance-political-spectrum", is_flag=True, help="Focus on political balance")
@click.option("--suggest-topics", is_flag=True, help="Suggest new topics to explore")
@click.option("--limit", "-l", default=5, help="Number of recommendations")
def recommend_command(balance_political_spectrum: bool, suggest_topics: bool, limit: int):
    """Get personalized recommendations for balanced news consumption."""
    from .analytics import NewsRecommender

    tracker = get_analytics_tracker()
    tracker.start_session()

    try:
        recommender = NewsRecommender()

        if suggest_topics:
            # Topic recommendations
            topic_recs = recommender.get_topic_recommendations(limit=limit)
            click.echo("🎯 Topic Recommendations:")
            click.echo("=" * 30)

            recommendations = topic_recs.get("recommendations", [])
            if recommendations:
                for rec in recommendations:
                    click.echo(f"• {rec['topic'].title()}: {rec['reason']}")
            else:
                click.echo("You're exploring topics well! Keep up the great coverage.")

            click.echo(f"\nTopic Coverage: {topic_recs.get('topic_coverage', '0/7')}")

        else:
            # Source recommendations
            source_recs = recommender.get_source_recommendations(limit=limit)
            click.echo("📰 Source Recommendations:")
            click.echo("=" * 30)

            recommendations = source_recs.get("recommendations", [])
            if recommendations:
                for rec in recommendations:
                    click.echo(f"• {rec['source'].title()}: {rec['reason']}")
            else:
                click.echo("Your source diversity looks good! Keep reading varied perspectives.")

            click.echo(f"\nCurrent Diversity Score: {source_recs.get('current_diversity_score', 0):.2f}")
            click.echo(f"Rationale: {source_recs.get('rationale', '')}")

            if source_recs.get("echo_chamber_risk", False):
                click.echo("\n⚠️ Echo chamber detected! Consider the recommendations above.")

        # Comprehensive recommendations
        if balance_political_spectrum:
            comprehensive = recommender.get_comprehensive_recommendations()
            click.echo("\n🎯 Priority Actions:")
            for action in comprehensive.get("priority_actions", []):
                click.echo(f"• {action}")

        rec_type = "sources" if not suggest_topics else "topics"
        tracker.track_recommendations_view(rec_type)

    except Exception as e:
        click.echo(f"❌ Error generating recommendations: {str(e)}")


@cli.command("export")
@click.option(
    "--format", "-f", "format_type", default="csv", type=click.Choice(["csv", "json", "html"]), help="Export format"
)
@click.option("--period", "-p", default=30, help="Period in days to export")
@click.option("--include-sensitive", is_flag=True, help="Include detailed consumption data")
@click.option("--output", "-o", help="Output file path")
def export_command(format_type: str, period: int, include_sensitive: bool, output: Optional[str]):
    """Export analytics data in various formats."""
    from .analytics import DataExporter

    tracker = get_analytics_tracker()
    tracker.start_session()

    try:
        exporter = DataExporter()

        # Privacy warning for sensitive data
        if include_sensitive:
            click.echo("⚠️ Including sensitive data (search queries, detailed timestamps)")
            if not click.confirm("Continue with sensitive data export?"):
                click.echo("Export cancelled.")
                return

        # Export data
        exported_file = exporter.export_consumption_data(
            format_type=format_type, days=period, include_sensitive=include_sensitive, output_file=output
        )

        click.echo("✅ Data exported successfully!")
        click.echo(f"📄 File: {exported_file}")
        click.echo(f"📅 Period: {period} days")
        click.echo(f"🔒 Sensitive data: {'Included' if include_sensitive else 'Excluded'}")

        # Privacy reminder
        if include_sensitive:
            click.echo("\n🔐 Privacy Notice:")
            click.echo("Your exported data contains detailed information.")
            click.echo("Keep this file secure and delete when no longer needed.")

        tracker.track_export(format_type, period)

    except Exception as e:
        click.echo(f"❌ Error exporting data: {str(e)}")


@cli.command("privacy")
@click.option("--disable-tracking", is_flag=True, help="Disable analytics tracking")
@click.option("--enable-tracking", is_flag=True, help="Enable analytics tracking")
@click.option("--clear-data", is_flag=True, help="Clear all analytics data")
@click.option("--show-summary", is_flag=True, help="Show privacy summary")
def privacy_command(disable_tracking: bool, enable_tracking: bool, clear_data: bool, show_summary: bool):
    """Manage analytics privacy settings and data."""
    from .analytics import DataExporter

    tracker = get_analytics_tracker()

    try:
        if disable_tracking:
            tracker.disable_tracking()
            click.echo("✅ Analytics tracking disabled")
            click.echo("📊 No new data will be collected")

        elif enable_tracking:
            tracker.enable_tracking()
            click.echo("✅ Analytics tracking enabled")
            click.echo("📊 Usage data collection resumed")

        elif clear_data:
            click.echo("⚠️ This will permanently delete all analytics data")
            if click.confirm("Are you sure you want to clear all data?"):
                tracker.reset_analytics()
                click.echo("✅ All analytics data cleared")
            else:
                click.echo("Data clearing cancelled")

        elif show_summary or True:  # Default action
            exporter = DataExporter()
            privacy_summary = exporter.get_privacy_summary()

            click.echo("🔐 Privacy Summary:")
            click.echo("=" * 30)
            click.echo(f"Tracking Status: {'✅ Enabled' if privacy_summary['tracking_enabled'] else '❌ Disabled'}")
            click.echo(f"Data Retention: {privacy_summary['data_retention_days']} days")
            click.echo(f"Records Stored: {privacy_summary['total_consumption_records']}")
            click.echo(f"Storage Location: {privacy_summary['storage_location']}")

            if privacy_summary.get("oldest_record"):
                click.echo(f"Oldest Record: {privacy_summary['oldest_record'][:10]}")

            click.echo("\n📊 Data Categories:")
            for category in privacy_summary["data_categories"]:
                click.echo(f"• {category}")

            click.echo("\n🛡️ Privacy Controls:")
            for control in privacy_summary["privacy_controls"]:
                click.echo(f"• {control}")

            click.echo("\n💡 Commands:")
            click.echo("• diego privacy --disable-tracking  # Stop data collection")
            click.echo("• diego privacy --enable-tracking   # Resume data collection")
            click.echo("• diego privacy --clear-data        # Delete all data")
            click.echo("• diego export --format json        # Export your data")

    except Exception as e:
        click.echo(f"❌ Error managing privacy settings: {str(e)}")


if __name__ == "__main__":
    cli()
