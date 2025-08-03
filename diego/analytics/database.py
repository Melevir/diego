"""
Analytics Database Management

Handles SQLite database operations for storing news consumption analytics,
user preferences, and source analysis data with privacy-first design.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


class AnalyticsDatabase:
    """Manages local SQLite database for analytics data storage."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection."""
        if db_path is None:
            # Store in user's home directory under .diego
            home_dir = os.path.expanduser("~")
            diego_dir = os.path.join(home_dir, ".diego")
            os.makedirs(diego_dir, exist_ok=True)
            db_path = os.path.join(diego_dir, "analytics.db")

        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # User consumption tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consumption_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action TEXT NOT NULL,
                    topic TEXT,
                    source TEXT,
                    keywords TEXT,
                    country TEXT,
                    language TEXT,
                    duration INTEGER DEFAULT 0,
                    result_count INTEGER DEFAULT 0
                )
            """)

            # Source diversity tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS source_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT UNIQUE NOT NULL,
                    political_bias REAL DEFAULT 0.0,
                    credibility_score REAL DEFAULT 0.5,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User preferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preference_type TEXT NOT NULL,
                    preference_value TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Analytics settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def log_consumption(
        self,
        action: str,
        topic: Optional[str] = None,
        source: Optional[str] = None,
        keywords: Optional[str] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        duration: int = 0,
        result_count: int = 0,
    ):
        """Log user consumption activity."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO consumption_log 
                (action, topic, source, keywords, country, language, duration, result_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (action, topic, source, keywords, country, language, duration, result_count),
            )
            conn.commit()

    def get_consumption_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get consumption statistics for the specified period."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Total activities
            cursor.execute(
                """
                SELECT COUNT(*) as total_activities
                FROM consumption_log 
                WHERE timestamp >= ?
            """,
                (start_date,),
            )
            total_activities = cursor.fetchone()["total_activities"]

            # Activities by action
            cursor.execute(
                """
                SELECT action, COUNT(*) as count
                FROM consumption_log 
                WHERE timestamp >= ?
                GROUP BY action
                ORDER BY count DESC
            """,
                (start_date,),
            )
            activities_by_action = {row["action"]: row["count"] for row in cursor.fetchall()}

            # Activities by source
            cursor.execute(
                """
                SELECT source, COUNT(*) as count
                FROM consumption_log 
                WHERE timestamp >= ? AND source IS NOT NULL
                GROUP BY source
                ORDER BY count DESC
            """,
                (start_date,),
            )
            activities_by_source = {row["source"]: row["count"] for row in cursor.fetchall()}

            # Activities by topic
            cursor.execute(
                """
                SELECT topic, COUNT(*) as count
                FROM consumption_log 
                WHERE timestamp >= ? AND topic IS NOT NULL
                GROUP BY topic
                ORDER BY count DESC
            """,
                (start_date,),
            )
            activities_by_topic = {row["topic"]: row["count"] for row in cursor.fetchall()}

            # Daily activity pattern
            cursor.execute(
                """
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM consumption_log 
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """,
                (start_date,),
            )
            daily_activity = [(row["date"], row["count"]) for row in cursor.fetchall()]

            return {
                "period_days": days,
                "total_activities": total_activities,
                "activities_by_action": activities_by_action,
                "activities_by_source": activities_by_source,
                "activities_by_topic": activities_by_topic,
                "daily_activity": daily_activity,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }

    def update_source_analysis(self, source: str, political_bias: float = 0.0, credibility_score: float = 0.5):
        """Update or insert source analysis data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO source_analysis 
                (source, political_bias, credibility_score, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (source, political_bias, credibility_score),
            )
            conn.commit()

    def get_source_analysis(self) -> List[Dict[str, Any]]:
        """Get all source analysis data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT source, political_bias, credibility_score, last_updated
                FROM source_analysis
                ORDER BY source
            """)
            return [dict(row) for row in cursor.fetchall()]

    def set_preference(self, preference_type: str, preference_value: str, weight: float = 1.0):
        """Set or update user preference."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_preferences 
                (preference_type, preference_value, weight, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (preference_type, preference_value, weight),
            )
            conn.commit()

    def get_preferences(self, preference_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user preferences, optionally filtered by type."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if preference_type:
                cursor.execute(
                    """
                    SELECT preference_type, preference_value, weight, created_at, updated_at
                    FROM user_preferences
                    WHERE preference_type = ?
                    ORDER BY weight DESC, updated_at DESC
                """,
                    (preference_type,),
                )
            else:
                cursor.execute("""
                    SELECT preference_type, preference_value, weight, created_at, updated_at
                    FROM user_preferences
                    ORDER BY preference_type, weight DESC, updated_at DESC
                """)
            return [dict(row) for row in cursor.fetchall()]

    def set_setting(self, key: str, value: str):
        """Set analytics setting."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO analytics_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                (key, value),
            )
            conn.commit()

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get analytics setting."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM analytics_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def is_tracking_enabled(self) -> bool:
        """Check if analytics tracking is enabled."""
        return self.get_setting("tracking_enabled", "true").lower() == "true"

    def set_tracking_enabled(self, enabled: bool):
        """Enable or disable analytics tracking."""
        self.set_setting("tracking_enabled", str(enabled).lower())

    def get_data_retention_days(self) -> int:
        """Get data retention period in days."""
        return int(self.get_setting("data_retention_days", "365"))

    def set_data_retention_days(self, days: int):
        """Set data retention period in days."""
        self.set_setting("data_retention_days", str(days))

    def cleanup_old_data(self):
        """Remove data older than retention period."""
        retention_days = self.get_data_retention_days()
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM consumption_log WHERE timestamp < ?", (cutoff_date,))
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count

    def clear_all_data(self):
        """Clear all analytics data (for privacy/reset)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM consumption_log")
            cursor.execute("DELETE FROM user_preferences")
            cursor.execute("DELETE FROM source_analysis")
            conn.commit()

    def export_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export all analytics data for backup/analysis."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Export consumption log
            cursor.execute("SELECT * FROM consumption_log ORDER BY timestamp")
            consumption_log = [dict(row) for row in cursor.fetchall()]

            # Export source analysis
            cursor.execute("SELECT * FROM source_analysis ORDER BY source")
            source_analysis = [dict(row) for row in cursor.fetchall()]

            # Export preferences
            cursor.execute("SELECT * FROM user_preferences ORDER BY preference_type")
            preferences = [dict(row) for row in cursor.fetchall()]

            # Export settings
            cursor.execute("SELECT * FROM analytics_settings ORDER BY key")
            settings = [dict(row) for row in cursor.fetchall()]

            return {
                "consumption_log": consumption_log,
                "source_analysis": source_analysis,
                "preferences": preferences,
                "settings": settings,
            }
