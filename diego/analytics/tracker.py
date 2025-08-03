"""
Analytics Tracker

Handles tracking of user interactions with the news CLI,
including search queries, reading patterns, and source usage.
"""

import time
from typing import Optional, Dict, Any
from .database import AnalyticsDatabase


class AnalyticsTracker:
    """Tracks user interactions for analytics purposes."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize tracker with database connection."""
        self.db = AnalyticsDatabase(db_path)
        self._session_start_time = None

    def is_enabled(self) -> bool:
        """Check if tracking is enabled."""
        return self.db.is_tracking_enabled()

    def enable_tracking(self):
        """Enable analytics tracking."""
        self.db.set_tracking_enabled(True)

    def disable_tracking(self):
        """Disable analytics tracking."""
        self.db.set_tracking_enabled(False)

    def start_session(self):
        """Start tracking session duration."""
        self._session_start_time = time.time()

    def end_session(self) -> int:
        """End tracking session and return duration in seconds."""
        if self._session_start_time is None:
            return 0

        duration = int(time.time() - self._session_start_time)
        self._session_start_time = None
        return duration

    def track_search(
        self,
        topic: Optional[str] = None,
        source: Optional[str] = None,
        keywords: Optional[str] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        result_count: int = 0,
    ):
        """Track a news search operation."""
        if not self.is_enabled():
            return

        duration = self.end_session()
        self.db.log_consumption(
            action="search",
            topic=topic,
            source=source,
            keywords=keywords,
            country=country,
            language=language,
            duration=duration,
            result_count=result_count,
        )

    def track_view(self, topic: Optional[str] = None, source: Optional[str] = None, keywords: Optional[str] = None):
        """Track viewing news articles."""
        if not self.is_enabled():
            return

        duration = self.end_session()
        self.db.log_consumption(action="view", topic=topic, source=source, keywords=keywords, duration=duration)

    def track_summary(self, source_type: str = "url", duration: int = 0):
        """Track article summarization usage."""
        if not self.is_enabled():
            return

        self.db.log_consumption(action="summary", keywords=f"source_type:{source_type}", duration=duration)

    def track_sources_list(
        self,
        source: Optional[str] = None,
        topic: Optional[str] = None,
        country: Optional[str] = None,
        result_count: int = 0,
    ):
        """Track sources listing operations."""
        if not self.is_enabled():
            return

        duration = self.end_session()
        self.db.log_consumption(
            action="sources", topic=topic, source=source, country=country, duration=duration, result_count=result_count
        )

    def track_config_view(self):
        """Track configuration viewing."""
        if not self.is_enabled():
            return

        duration = self.end_session()
        self.db.log_consumption(action="config", duration=duration)

    def track_topics_list(self):
        """Track topics listing."""
        if not self.is_enabled():
            return

        duration = self.end_session()
        self.db.log_consumption(action="list-topics", duration=duration)

    def track_analytics_view(self, period: int = 30, report_type: str = "basic"):
        """Track analytics viewing."""
        if not self.is_enabled():
            return

        duration = self.end_session()
        self.db.log_consumption(action="analytics", keywords=f"period:{period},type:{report_type}", duration=duration)

    def track_export(self, format_type: str, period: int = 30):
        """Track data export operations."""
        if not self.is_enabled():
            return

        duration = self.end_session()
        self.db.log_consumption(action="export", keywords=f"format:{format_type},period:{period}", duration=duration)

    def track_recommendations_view(self, recommendation_type: str = "sources"):
        """Track recommendations viewing."""
        if not self.is_enabled():
            return

        duration = self.end_session()
        self.db.log_consumption(action="recommend", keywords=f"type:{recommendation_type}", duration=duration)

    def update_user_preference(self, preference_type: str, preference_value: str, weight: float = 1.0):
        """Update user preferences based on behavior."""
        if not self.is_enabled():
            return

        self.db.set_preference(preference_type, preference_value, weight)

    def get_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics for the specified period."""
        return self.db.get_consumption_stats(days)

    def get_most_used_sources(self, days: int = 30, limit: int = 10) -> Dict[str, int]:
        """Get most frequently used news sources."""
        stats = self.get_usage_stats(days)
        sources = stats.get("activities_by_source", {})

        # Sort by usage count and limit results
        sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_sources[:limit])

    def get_most_searched_topics(self, days: int = 30, limit: int = 10) -> Dict[str, int]:
        """Get most frequently searched topics."""
        stats = self.get_usage_stats(days)
        topics = stats.get("activities_by_topic", {})

        # Sort by usage count and limit results
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_topics[:limit])

    def get_activity_pattern(self, days: int = 30) -> Dict[str, Any]:
        """Get daily activity patterns."""
        stats = self.get_usage_stats(days)
        return {
            "total_activities": stats.get("total_activities", 0),
            "daily_average": stats.get("total_activities", 0) / max(days, 1),
            "daily_activity": stats.get("daily_activity", []),
            "activities_by_action": stats.get("activities_by_action", {}),
        }

    def cleanup_old_data(self) -> int:
        """Clean up old tracking data based on retention policy."""
        return self.db.cleanup_old_data()

    def reset_analytics(self):
        """Reset all analytics data (for privacy)."""
        self.db.clear_all_data()

    def export_analytics_data(self) -> Dict[str, Any]:
        """Export all analytics data."""
        return self.db.export_data()
