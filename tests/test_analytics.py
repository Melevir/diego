"""
Tests for analytics functionality
"""

import pytest
import tempfile
import os

from diego.analytics import (
    AnalyticsDatabase,
    AnalyticsTracker,
    BiasDetector,
    NewsRecommender,
    InsightsGenerator,
    DataExporter,
)


class TestAnalyticsDatabase:
    """Test analytics database functionality."""

    def setup_method(self):
        """Setup test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db = AnalyticsDatabase(self.temp_db.name)

    def teardown_method(self):
        """Cleanup test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_database_initialization(self):
        """Test database tables are created correctly."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ["consumption_log", "source_analysis", "user_preferences", "analytics_settings"]
            for table in expected_tables:
                assert table in tables

    def test_log_consumption(self):
        """Test logging consumption activity."""
        self.db.log_consumption(
            action="search",
            topic="technology",
            source="newsapi",
            keywords="AI,machine learning",
            country="us",
            language="en",
            duration=120,
            result_count=15,
        )

        # Verify data was logged
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM consumption_log")
            row = cursor.fetchone()

            assert row["action"] == "search"
            assert row["topic"] == "technology"
            assert row["source"] == "newsapi"
            assert row["keywords"] == "AI,machine learning"
            assert row["duration"] == 120
            assert row["result_count"] == 15

    def test_consumption_stats(self):
        """Test getting consumption statistics."""
        # Add test data
        self.db.log_consumption("search", "tech", "newsapi", result_count=10)
        self.db.log_consumption("search", "business", "guardian", result_count=5)
        self.db.log_consumption("summary", source_type="url", duration=30)

        stats = self.db.get_consumption_stats(30)

        assert stats["total_activities"] == 3
        assert stats["activities_by_action"]["search"] == 2
        assert stats["activities_by_action"]["summary"] == 1
        assert stats["activities_by_source"]["newsapi"] == 1
        assert stats["activities_by_source"]["guardian"] == 1

    def test_source_analysis(self):
        """Test source bias analysis storage."""
        self.db.update_source_analysis("cnn", political_bias=-0.4, credibility_score=0.7)
        self.db.update_source_analysis("foxnews", political_bias=0.7, credibility_score=0.6)

        sources = self.db.get_source_analysis()

        assert len(sources) == 2
        cnn_data = next(s for s in sources if s["source"] == "cnn")
        assert cnn_data["political_bias"] == -0.4
        assert cnn_data["credibility_score"] == 0.7

    def test_privacy_settings(self):
        """Test privacy and tracking settings."""
        # Test default tracking enabled
        assert self.db.is_tracking_enabled()

        # Test disable tracking
        self.db.set_tracking_enabled(False)
        assert not self.db.is_tracking_enabled()

        # Test data retention
        self.db.set_data_retention_days(90)
        assert self.db.get_data_retention_days() == 90


class TestAnalyticsTracker:
    """Test analytics tracking functionality."""

    def setup_method(self):
        """Setup test tracker."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.tracker = AnalyticsTracker(self.temp_db.name)

    def teardown_method(self):
        """Cleanup test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_tracking_enabled_by_default(self):
        """Test tracking is enabled by default."""
        assert self.tracker.is_enabled()

    def test_disable_enable_tracking(self):
        """Test disabling and enabling tracking."""
        self.tracker.disable_tracking()
        assert not self.tracker.is_enabled()

        self.tracker.enable_tracking()
        assert self.tracker.is_enabled()

    def test_track_search(self):
        """Test tracking search operations."""
        self.tracker.track_search(topic="technology", source="newsapi", keywords="AI", country="us", result_count=10)

        stats = self.tracker.get_usage_stats(30)
        assert stats["total_activities"] == 1
        assert stats["activities_by_action"]["search"] == 1
        assert stats["activities_by_topic"]["technology"] == 1

    def test_session_tracking(self):
        """Test session duration tracking."""
        self.tracker.start_session()
        # Simulate some time passing
        import time

        time.sleep(0.1)
        duration = self.tracker.end_session()

        assert duration > 0
        assert duration < 1  # Should be less than 1 second

    def test_most_used_sources(self):
        """Test getting most used sources."""
        self.tracker.track_search(source="newsapi", result_count=5)
        self.tracker.track_search(source="newsapi", result_count=3)
        self.tracker.track_search(source="guardian", result_count=2)

        most_used = self.tracker.get_most_used_sources(limit=2)

        assert len(most_used) == 2
        assert most_used["newsapi"] == 2
        assert most_used["guardian"] == 1


class TestBiasDetector:
    """Test bias detection functionality."""

    def setup_method(self):
        """Setup test bias detector."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.detector = BiasDetector(self.temp_db.name)

    def teardown_method(self):
        """Cleanup test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_known_source_bias(self):
        """Test bias detection for known sources."""
        cnn_bias = self.detector.get_source_bias("cnn")
        assert cnn_bias["political_bias"] == -0.4
        assert cnn_bias["credibility_score"] == 0.7

        reuters_bias = self.detector.get_source_bias("reuters")
        assert reuters_bias["political_bias"] == 0.0
        assert reuters_bias["credibility_score"] == 0.9

    def test_unknown_source_bias(self):
        """Test bias detection for unknown sources."""
        unknown_bias = self.detector.get_source_bias("unknown-source")
        assert unknown_bias["political_bias"] == 0.0
        assert unknown_bias["credibility_score"] == 0.5

    def test_source_diversity_analysis(self):
        """Test source diversity analysis."""
        sources = ["cnn", "foxnews", "reuters", "guardian"]
        analysis = self.detector.analyze_source_diversity(sources)

        assert analysis["source_count"] == 4
        assert analysis["diversity_score"] > 0
        assert "political_balance" in analysis
        assert analysis["political_balance"]["left"] > 0
        assert analysis["political_balance"]["center"] > 0
        assert analysis["political_balance"]["right"] > 0

    def test_echo_chamber_detection(self):
        """Test echo chamber detection."""
        # Test left echo chamber
        left_sources = ["cnn", "msnbc", "huffpost", "guardian"]
        left_analysis = self.detector.detect_echo_chamber(left_sources)

        assert left_analysis["is_echo_chamber"]
        assert left_analysis["echo_chamber_type"] == "left-leaning"

        # Test balanced sources
        balanced_sources = ["cnn", "reuters", "wsj", "bbc"]
        balanced_analysis = self.detector.detect_echo_chamber(balanced_sources)

        assert not balanced_analysis["is_echo_chamber"]


class TestNewsRecommender:
    """Test news recommendation functionality."""

    def setup_method(self):
        """Setup test recommender."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.recommender = NewsRecommender(self.temp_db.name)

        # Add some test data
        self.recommender.db.log_consumption("search", "technology", "newsapi")
        self.recommender.db.log_consumption("search", "technology", "cnn")
        self.recommender.db.log_consumption("search", "business", "wsj")

    def teardown_method(self):
        """Cleanup test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_source_recommendations_for_new_user(self):
        """Test source recommendations for users with no data."""
        empty_recommender = NewsRecommender()
        recs = empty_recommender.get_source_recommendations()

        assert len(recs["recommendations"]) > 0
        assert recs["current_diversity_score"] == 0.0
        assert "reuters" in [r["source"] for r in recs["recommendations"]]

    def test_topic_recommendations(self):
        """Test topic recommendations."""
        recs = self.recommender.get_topic_recommendations()

        # Should recommend unexplored topics
        explored_topics = set(recs["explored_topics"])
        recommended_topics = {r["topic"] for r in recs["recommendations"]}

        # Should not recommend already explored topics
        assert not (explored_topics & recommended_topics)

    def test_comprehensive_recommendations(self):
        """Test comprehensive recommendations."""
        recs = self.recommender.get_comprehensive_recommendations()

        assert "source_recommendations" in recs
        assert "topic_recommendations" in recs
        assert "habit_recommendations" in recs
        assert "overall_score" in recs
        assert "priority_actions" in recs


class TestInsightsGenerator:
    """Test insights generation functionality."""

    def setup_method(self):
        """Setup test insights generator."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.insights = InsightsGenerator(self.temp_db.name)

        # Add test data
        for i in range(10):
            self.insights.db.log_consumption("search", "technology", "newsapi", result_count=5, duration=60)

    def teardown_method(self):
        """Cleanup test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_consumption_report_generation(self):
        """Test generating consumption report."""
        report = self.insights.generate_consumption_report(30)

        assert "key_metrics" in report
        assert "consumption_patterns" in report
        assert "source_analysis" in report
        assert "trends" in report
        assert "blind_spots" in report
        assert "insights" in report
        assert "health_score" in report

        # Check key metrics
        key_metrics = report["key_metrics"]
        assert key_metrics["total_activities"] == 10
        assert key_metrics["unique_sources"] == 1
        assert key_metrics["most_used_source"] == "newsapi"

    def test_health_score_calculation(self):
        """Test consumption health score calculation."""
        report = self.insights.generate_consumption_report(30)
        health_score = report["health_score"]

        assert 0.0 <= health_score["overall_score"] <= 1.0
        assert health_score["interpretation"] in ["excellent", "good", "fair", "needs_improvement"]
        assert "message" in health_score
        assert "factor_scores" in health_score


class TestDataExporter:
    """Test data export functionality."""

    def setup_method(self):
        """Setup test data exporter."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.exporter = DataExporter(self.temp_db.name)

        # Add test data
        self.exporter.db.log_consumption("search", "tech", "newsapi", result_count=5)
        self.exporter.db.log_consumption("summary", keywords="source_type:url", duration=30)

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_csv_export(self):
        """Test CSV data export."""
        temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        temp_csv.close()

        try:
            exported_file = self.exporter.export_consumption_data(format_type="csv", days=30, output_file=temp_csv.name)

            assert exported_file == temp_csv.name
            assert os.path.exists(exported_file)

            # Check file content
            with open(exported_file, "r") as f:
                content = f.read()
                assert "Activities by Action" in content
                assert "search" in content
                assert "summary" in content

        finally:
            if os.path.exists(temp_csv.name):
                os.unlink(temp_csv.name)

    def test_json_export(self):
        """Test JSON data export."""
        temp_json = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        temp_json.close()

        try:
            exported_file = self.exporter.export_consumption_data(
                format_type="json", days=30, output_file=temp_json.name
            )

            assert exported_file == temp_json.name
            assert os.path.exists(exported_file)

            # Check file content
            import json

            with open(exported_file, "r") as f:
                data = json.load(f)
                assert "export_metadata" in data
                assert "summary_statistics" in data
                assert data["export_metadata"]["total_activities"] == 2

        finally:
            if os.path.exists(temp_json.name):
                os.unlink(temp_json.name)

    def test_privacy_summary(self):
        """Test privacy summary generation."""
        privacy_summary = self.exporter.get_privacy_summary()

        assert "tracking_enabled" in privacy_summary
        assert "data_retention_days" in privacy_summary
        assert "total_consumption_records" in privacy_summary
        assert "storage_location" in privacy_summary
        assert "data_categories" in privacy_summary
        assert "privacy_controls" in privacy_summary

        assert privacy_summary["total_consumption_records"] == 2
        assert privacy_summary["tracking_enabled"]
        assert "Local SQLite database" in privacy_summary["storage_location"]


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics functionality."""

    def setup_method(self):
        """Setup integration test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

    def teardown_method(self):
        """Cleanup integration test environment."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_full_analytics_workflow(self):
        """Test complete analytics workflow."""
        # Initialize components
        tracker = AnalyticsTracker(self.temp_db.name)
        detector = BiasDetector(self.temp_db.name)
        recommender = NewsRecommender(self.temp_db.name)
        insights = InsightsGenerator(self.temp_db.name)
        exporter = DataExporter(self.temp_db.name)

        # Simulate user activity
        tracker.track_search("technology", "newsapi", "AI", "us", result_count=10)
        tracker.track_search("business", "guardian", "economics", "us", result_count=5)
        tracker.track_summary("url", duration=45)

        # Test bias analysis
        bias_summary = detector.get_bias_summary(30)
        assert bias_summary["sources_analyzed"] == 2
        assert "diversity_analysis" in bias_summary

        # Test recommendations
        source_recs = recommender.get_source_recommendations()
        assert len(source_recs["recommendations"]) > 0

        # Test insights
        report = insights.generate_consumption_report(30)
        assert report["key_metrics"]["total_activities"] == 3
        assert report["key_metrics"]["unique_sources"] == 2

        # Test export
        temp_export = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        temp_export.close()

        try:
            exported_file = exporter.export_consumption_data(format_type="json", days=30, output_file=temp_export.name)

            assert os.path.exists(exported_file)

        finally:
            if os.path.exists(temp_export.name):
                os.unlink(temp_export.name)
