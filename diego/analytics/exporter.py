"""
Data Exporter

Handles exporting analytics data in various formats (CSV, JSON)
with privacy controls and flexible filtering options.
"""

import json
import csv
import os
from datetime import datetime
from typing import Dict, Optional, Any
from .database import AnalyticsDatabase
from .insights import InsightsGenerator


class DataExporter:
    """Exports analytics data in various formats with privacy controls."""

    SUPPORTED_FORMATS = ["csv", "json", "html"]

    def __init__(self, db_path: Optional[str] = None):
        """Initialize exporter with database connection."""
        self.db = AnalyticsDatabase(db_path)
        self.insights = InsightsGenerator(db_path)

    def export_consumption_data(
        self,
        format_type: str = "csv",
        days: int = 30,
        include_sensitive: bool = False,
        output_file: Optional[str] = None,
    ) -> str:
        """Export consumption data in specified format."""
        if format_type not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format_type}. Supported: {self.SUPPORTED_FORMATS}")

        # Get consumption stats
        stats = self.db.get_consumption_stats(days)

        # Prepare data based on privacy settings
        export_data = self._prepare_export_data(stats, include_sensitive)

        # Generate filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"diego_analytics_{timestamp}.{format_type}"

        # Export based on format
        if format_type == "csv":
            return self._export_csv(export_data, output_file)
        elif format_type == "json":
            return self._export_json(export_data, output_file)
        elif format_type == "html":
            return self._export_html(export_data, days, output_file)

    def _prepare_export_data(self, stats: Dict[str, Any], include_sensitive: bool) -> Dict[str, Any]:
        """Prepare data for export based on privacy settings."""
        export_data = {
            "export_metadata": {
                "generated_at": datetime.now().isoformat(),
                "period_days": stats.get("period_days", 0),
                "total_activities": stats.get("total_activities", 0),
                "include_sensitive_data": include_sensitive,
            },
            "summary_statistics": {
                "activities_by_action": stats.get("activities_by_action", {}),
                "activities_by_source": stats.get("activities_by_source", {}),
                "activities_by_topic": stats.get("activities_by_topic", {}),
                "daily_activity": stats.get("daily_activity", []),
            },
        }

        if include_sensitive:
            # Include more detailed data if user consents
            raw_data = self.db.export_data()
            export_data["detailed_consumption_log"] = raw_data.get("consumption_log", [])
            export_data["source_analysis"] = raw_data.get("source_analysis", [])
            export_data["user_preferences"] = raw_data.get("preferences", [])

        return export_data

    def _export_csv(self, data: Dict[str, Any], output_file: str) -> str:
        """Export data to CSV format."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write metadata
            writer.writerow(["# Diego Analytics Export"])
            writer.writerow(["# Generated:", data["export_metadata"]["generated_at"]])
            writer.writerow(["# Period (days):", data["export_metadata"]["period_days"]])
            writer.writerow(["# Total Activities:", data["export_metadata"]["total_activities"]])
            writer.writerow([])

            # Activities by Action
            writer.writerow(["Activities by Action"])
            writer.writerow(["Action", "Count"])
            for action, count in data["summary_statistics"]["activities_by_action"].items():
                writer.writerow([action, count])
            writer.writerow([])

            # Activities by Source
            writer.writerow(["Activities by Source"])
            writer.writerow(["Source", "Count"])
            for source, count in data["summary_statistics"]["activities_by_source"].items():
                writer.writerow([source, count])
            writer.writerow([])

            # Activities by Topic
            writer.writerow(["Activities by Topic"])
            writer.writerow(["Topic", "Count"])
            for topic, count in data["summary_statistics"]["activities_by_topic"].items():
                writer.writerow([topic, count])
            writer.writerow([])

            # Daily Activity
            writer.writerow(["Daily Activity"])
            writer.writerow(["Date", "Activity Count"])
            for date, count in data["summary_statistics"]["daily_activity"]:
                writer.writerow([date, count])

            # Detailed data if included
            if data["export_metadata"]["include_sensitive_data"]:
                writer.writerow([])
                writer.writerow(["Detailed Consumption Log"])
                if data.get("detailed_consumption_log"):
                    log_entry = data["detailed_consumption_log"][0]
                    writer.writerow(log_entry.keys())  # Headers
                    for entry in data["detailed_consumption_log"]:
                        writer.writerow(entry.values())

        return output_file

    def _export_json(self, data: Dict[str, Any], output_file: str) -> str:
        """Export data to JSON format."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)

        return output_file

    def _export_html(self, data: Dict[str, Any], days: int, output_file: str) -> str:
        """Export data as HTML dashboard."""
        # Generate comprehensive insights report
        insights_report = self.insights.generate_consumption_report(days)

        # Create HTML content
        html_content = self._generate_html_dashboard(data, insights_report)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as htmlfile:
            htmlfile.write(html_content)

        return output_file

    def _generate_html_dashboard(self, data: Dict[str, Any], insights: Dict[str, Any]) -> str:
        """Generate HTML dashboard content."""
        metadata = data["export_metadata"]
        stats = data["summary_statistics"]
        key_metrics = insights.get("key_metrics", {})
        health_score = insights.get("health_score", {})

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diego News Analytics Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #007acc;
            padding-bottom: 20px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007acc;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #007acc;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #007acc;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }}
        .chart-placeholder {{
            background: #f8f9fa;
            border: 2px dashed #ddd;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            color: #666;
            margin: 20px 0;
        }}
        .health-score {{
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .health-excellent {{ background: #d4edda; color: #155724; }}
        .health-good {{ background: #d1ecf1; color: #0c5460; }}
        .health-fair {{ background: #fff3cd; color: #856404; }}
        .health-needs-improvement {{ background: #f8d7da; color: #721c24; }}
        .insights-list {{
            list-style: none;
            padding: 0;
        }}
        .insights-list li {{
            background: #f8f9fa;
            margin: 10px 0;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #007acc;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .data-table th, .data-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        .data-table th {{
            background: #007acc;
            color: white;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Diego News Analytics Dashboard</h1>
            <p>Generated: {metadata["generated_at"]}</p>
            <p>Analysis Period: {metadata["period_days"]} days | Total Activities: {metadata["total_activities"]}</p>
        </div>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{key_metrics.get("daily_average", 0)}</div>
                <div class="metric-label">Daily Average Activities</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{key_metrics.get("unique_sources", 0)}</div>
                <div class="metric-label">Unique Sources Used</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{key_metrics.get("unique_topics", 0)}</div>
                <div class="metric-label">Topics Explored</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{health_score.get("overall_score", 0):.2f}</div>
                <div class="metric-label">Health Score</div>
            </div>
        </div>
        
        <div class="health-score health-{health_score.get("interpretation", "fair").replace("_", "-")}">
            <h3>Consumption Health: {health_score.get("interpretation", "Fair").replace("_", " ").title()}</h3>
            <p>{health_score.get("message", "Your news consumption analysis.")}</p>
        </div>
        
        <div class="section">
            <h2>📈 Activity Breakdown</h2>
            <table class="data-table">
                <tr><th>Action Type</th><th>Count</th><th>Percentage</th></tr>
"""

        # Add activity breakdown
        total_activities = sum(stats["activities_by_action"].values())
        for action, count in sorted(stats["activities_by_action"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_activities * 100) if total_activities > 0 else 0
            html += f"                <tr><td>{action.title()}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>\n"

        html += """
            </table>
        </div>
        
        <div class="section">
            <h2>📰 Source Usage</h2>
            <table class="data-table">
                <tr><th>Source</th><th>Usage Count</th><th>Percentage</th></tr>
"""

        # Add source breakdown
        total_source_activities = sum(stats["activities_by_source"].values())
        for source, count in sorted(stats["activities_by_source"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_source_activities * 100) if total_source_activities > 0 else 0
            html += f"                <tr><td>{source}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>\n"

        html += """
            </table>
        </div>
        
        <div class="section">
            <h2>🎯 Topic Interest</h2>
            <table class="data-table">
                <tr><th>Topic</th><th>Search Count</th><th>Interest Level</th></tr>
"""

        # Add topic breakdown
        total_topic_activities = sum(stats["activities_by_topic"].values())
        for topic, count in sorted(stats["activities_by_topic"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_topic_activities * 100) if total_topic_activities > 0 else 0
            interest_level = "High" if percentage > 20 else "Medium" if percentage > 10 else "Low"
            html += f"                <tr><td>{topic.title()}</td><td>{count}</td><td>{interest_level}</td></tr>\n"

        html += """
            </table>
        </div>
        
        <div class="section">
            <h2>💡 Key Insights</h2>
            <ul class="insights-list">
"""

        # Add insights
        for insight in insights.get("insights", []):
            html += f"                <li><strong>{insight.get('insight', '')}</strong><br>{insight.get('detail', '')}</li>\n"

        html += """
            </ul>
        </div>
        
        <div class="section">
            <h2>🎯 Recommendations</h2>
            <div class="chart-placeholder">
                <p>📊 Interactive recommendations and charts would appear here in a full implementation</p>
                <p>Consider the priority actions from your analytics for improved news balance</p>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Diego News Analytics | Privacy-First Local Analytics</p>
            <p>Data stored locally on your device • No cloud sync • You control your data</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def export_insights_report(
        self, days: int = 30, format_type: str = "json", output_file: Optional[str] = None
    ) -> str:
        """Export comprehensive insights report."""
        insights_report = self.insights.generate_consumption_report(days)

        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"diego_insights_{timestamp}.{format_type}"

        if format_type == "json":
            return self._export_json(insights_report, output_file)
        elif format_type == "html":
            return self._export_html(
                {
                    "export_metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "period_days": days,
                        "total_activities": insights_report.get("key_metrics", {}).get("total_activities", 0),
                        "include_sensitive_data": False,
                    },
                    "summary_statistics": {},
                },
                output_file,
            )

        raise ValueError(f"Unsupported format for insights: {format_type}")

    def get_privacy_summary(self) -> Dict[str, Any]:
        """Get summary of privacy settings and data stored."""
        total_data = self.db.export_data()

        return {
            "tracking_enabled": self.db.is_tracking_enabled(),
            "data_retention_days": self.db.get_data_retention_days(),
            "total_consumption_records": len(total_data.get("consumption_log", [])),
            "total_preferences": len(total_data.get("preferences", [])),
            "oldest_record": self._get_oldest_record_date(total_data),
            "storage_location": "Local SQLite database (~/.diego/analytics.db)",
            "data_categories": [
                "Search queries and topics",
                "News sources accessed",
                "Usage timestamps and duration",
                "Personal preferences and settings",
            ],
            "privacy_controls": [
                "Disable tracking completely",
                "Set data retention period",
                "Export all data",
                "Delete all data",
            ],
        }

    def _get_oldest_record_date(self, data: Dict[str, Any]) -> Optional[str]:
        """Get the date of the oldest consumption record."""
        consumption_log = data.get("consumption_log", [])
        if not consumption_log:
            return None

        timestamps = [record.get("timestamp") for record in consumption_log if record.get("timestamp")]
        if timestamps:
            return min(timestamps)

        return None
