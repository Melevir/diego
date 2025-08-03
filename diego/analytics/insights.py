"""
Insights Generator

Generates detailed analytics insights and reports about news consumption patterns,
including trend analysis, blind spot detection, and consumption recommendations.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import statistics
from .database import AnalyticsDatabase
from .bias_detector import BiasDetector
from .recommender import NewsRecommender


class InsightsGenerator:
    """Generates comprehensive insights from news consumption analytics."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize insights generator with analytics components."""
        self.db = AnalyticsDatabase(db_path)
        self.bias_detector = BiasDetector(db_path)
        self.recommender = NewsRecommender(db_path)

    def generate_consumption_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive consumption report."""
        stats = self.db.get_consumption_stats(days)
        bias_summary = self.bias_detector.get_bias_summary(days)
        recommendations = self.recommender.get_comprehensive_recommendations(days)

        # Calculate key metrics
        key_metrics = self._calculate_key_metrics(stats, days)

        # Identify trends and patterns
        trends = self._analyze_trends(stats, days)

        # Detect blind spots
        blind_spots = self._detect_blind_spots(stats, bias_summary)

        # Generate insights
        insights = self._generate_key_insights(stats, bias_summary, trends)

        return {
            "report_generated": datetime.now().isoformat(),
            "period_days": days,
            "key_metrics": key_metrics,
            "consumption_patterns": {
                "daily_activity": stats.get("daily_activity", []),
                "peak_activity_days": self._find_peak_activity_days(stats),
                "activity_consistency": self._calculate_activity_consistency(stats),
            },
            "source_analysis": {
                "total_sources": len(stats.get("activities_by_source", {})),
                "diversity_score": bias_summary.get("diversity_analysis", {}).get("diversity_score", 0.0),
                "political_balance": bias_summary.get("diversity_analysis", {}).get("political_balance", {}),
                "echo_chamber_status": bias_summary.get("echo_chamber_analysis", {}),
            },
            "trends": trends,
            "blind_spots": blind_spots,
            "insights": insights,
            "recommendations": recommendations,
            "health_score": self._calculate_consumption_health_score(stats, bias_summary),
        }

    def _calculate_key_metrics(self, stats: Dict[str, Any], days: int) -> Dict[str, Any]:
        """Calculate key consumption metrics."""
        total_activities = stats.get("total_activities", 0)
        activities_by_action = stats.get("activities_by_action", {})
        activities_by_source = stats.get("activities_by_source", {})
        activities_by_topic = stats.get("activities_by_topic", {})

        return {
            "total_activities": total_activities,
            "daily_average": round(total_activities / max(days, 1), 2),
            "unique_sources": len(activities_by_source),
            "unique_topics": len(activities_by_topic),
            "most_used_action": max(activities_by_action.items(), key=lambda x: x[1])[0]
            if activities_by_action
            else "none",
            "most_used_source": max(activities_by_source.items(), key=lambda x: x[1])[0]
            if activities_by_source
            else "none",
            "most_searched_topic": max(activities_by_topic.items(), key=lambda x: x[1])[0]
            if activities_by_topic
            else "none",
            "engagement_score": min(1.0, total_activities / (days * 2)),  # 2 activities per day = 100% engagement
        }

    def _analyze_trends(self, stats: Dict[str, Any], days: int) -> Dict[str, Any]:
        """Analyze consumption trends over time."""
        daily_activity = stats.get("daily_activity", [])
        activities_by_action = stats.get("activities_by_action", {})
        activities_by_source = stats.get("activities_by_source", {})
        activities_by_topic = stats.get("activities_by_topic", {})

        # Calculate trend direction
        if len(daily_activity) >= 7:
            recent_week = daily_activity[-7:]
            previous_week = daily_activity[-14:-7] if len(daily_activity) >= 14 else []

            recent_avg = statistics.mean([count for _, count in recent_week])
            previous_avg = statistics.mean([count for _, count in previous_week]) if previous_week else recent_avg

            trend_direction = (
                "increasing"
                if recent_avg > previous_avg * 1.1
                else "decreasing"
                if recent_avg < previous_avg * 0.9
                else "stable"
            )
            trend_change = round(((recent_avg - previous_avg) / max(previous_avg, 1)) * 100, 1)
        else:
            trend_direction = "insufficient_data"
            trend_change = 0.0

        # Source concentration trend
        source_concentration = self._calculate_concentration_index(activities_by_source)

        # Topic concentration trend
        topic_concentration = self._calculate_concentration_index(activities_by_topic)

        return {
            "activity_trend": {"direction": trend_direction, "change_percentage": trend_change},
            "source_concentration": {
                "index": source_concentration,
                "interpretation": "high"
                if source_concentration > 0.7
                else "medium"
                if source_concentration > 0.4
                else "low",
            },
            "topic_concentration": {
                "index": topic_concentration,
                "interpretation": "high"
                if topic_concentration > 0.7
                else "medium"
                if topic_concentration > 0.4
                else "low",
            },
            "action_preferences": dict(sorted(activities_by_action.items(), key=lambda x: x[1], reverse=True)),
        }

    def _calculate_concentration_index(self, data: Dict[str, int]) -> float:
        """Calculate concentration index (Herfindahl-Hirschman Index)."""
        if not data:
            return 0.0

        total = sum(data.values())
        if total == 0:
            return 0.0

        # Calculate HHI (sum of squared market shares)
        hhi = sum((count / total) ** 2 for count in data.values())
        return round(hhi, 3)

    def _detect_blind_spots(self, stats: Dict[str, Any], bias_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Detect blind spots in news consumption."""
        activities_by_topic = stats.get("activities_by_topic", {})
        activities_by_source = stats.get("activities_by_source", {})

        # Topic blind spots
        all_topics = {"business", "entertainment", "general", "health", "science", "sports", "technology"}
        covered_topics = set(activities_by_topic.keys())
        missing_topics = all_topics - covered_topics

        # Underexplored topics (less than 10% of total activity)
        total_topic_activity = sum(activities_by_topic.values())
        underexplored_topics = {
            topic: count
            for topic, count in activities_by_topic.items()
            if total_topic_activity > 0 and count / total_topic_activity < 0.1
        }

        # Source diversity blind spots
        diversity_analysis = bias_summary.get("diversity_analysis", {})
        political_balance = diversity_analysis.get("political_balance", {})

        # Political perspective gaps
        total_sources = sum(political_balance.values()) if political_balance else 0
        perspective_gaps = []

        if total_sources > 0:
            left_ratio = political_balance.get("left", 0) / total_sources
            center_ratio = political_balance.get("center", 0) / total_sources
            right_ratio = political_balance.get("right", 0) / total_sources

            if left_ratio < 0.15:
                perspective_gaps.append("left-leaning perspectives")
            if center_ratio < 0.15:
                perspective_gaps.append("centrist perspectives")
            if right_ratio < 0.15:
                perspective_gaps.append("right-leaning perspectives")

        # International vs domestic coverage
        international_sources = {"bbc", "guardian", "reuters"}
        domestic_sources = {"cnn", "foxnews", "nytimes", "wsj", "usatoday"}

        user_sources = set(activities_by_source.keys())
        international_coverage = len(user_sources & international_sources)
        domestic_coverage = len(user_sources & domestic_sources)

        coverage_gap = None
        if international_coverage == 0 and domestic_coverage > 0:
            coverage_gap = "international"
        elif domestic_coverage == 0 and international_coverage > 0:
            coverage_gap = "domestic"

        return {
            "missing_topics": list(missing_topics),
            "underexplored_topics": dict(sorted(underexplored_topics.items(), key=lambda x: x[1])),
            "perspective_gaps": perspective_gaps,
            "coverage_gap": coverage_gap,
            "diversity_score": diversity_analysis.get("diversity_score", 0.0),
            "improvement_areas": self._identify_improvement_areas(
                missing_topics, underexplored_topics, perspective_gaps, coverage_gap
            ),
        }

    def _identify_improvement_areas(
        self,
        missing_topics: set,
        underexplored_topics: Dict[str, int],
        perspective_gaps: List[str],
        coverage_gap: Optional[str],
    ) -> List[str]:
        """Identify specific areas for improvement."""
        areas = []

        if len(missing_topics) > 3:
            areas.append("Expand topic coverage - you're missing several important news categories")
        elif missing_topics:
            areas.append(f"Consider exploring: {', '.join(list(missing_topics)[:3])}")

        if len(underexplored_topics) > 2:
            areas.append("Deepen coverage in topics you've barely explored")

        if len(perspective_gaps) > 1:
            areas.append("Diversify political perspectives in your news sources")
        elif perspective_gaps:
            areas.append(f"Add more {perspective_gaps[0]} to your news diet")

        if coverage_gap:
            areas.append(f"Include more {coverage_gap} news sources for broader perspective")

        if not areas:
            areas.append("Your news consumption appears well-balanced!")

        return areas

    def _generate_key_insights(
        self, stats: Dict[str, Any], bias_summary: Dict[str, Any], trends: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate key insights about consumption patterns."""
        insights = []

        # Activity level insights
        total_activities = stats.get("total_activities", 0)
        days = len(stats.get("daily_activity", []))
        daily_avg = total_activities / max(days, 1)

        if daily_avg < 0.5:
            insights.append(
                {
                    "category": "engagement",
                    "insight": "Low news engagement detected",
                    "detail": f"You average {daily_avg:.1f} news activities per day. Consider increasing to stay informed.",
                }
            )
        elif daily_avg > 3:
            insights.append(
                {
                    "category": "engagement",
                    "insight": "High news engagement",
                    "detail": f"You're very active with {daily_avg:.1f} activities per day. Ensure you're not overwhelming yourself.",
                }
            )

        # Source diversity insights
        diversity_score = bias_summary.get("diversity_analysis", {}).get("diversity_score", 0.0)
        if diversity_score < 0.3:
            insights.append(
                {
                    "category": "diversity",
                    "insight": "Limited source diversity",
                    "detail": f"Your diversity score is {diversity_score:.2f}. Adding varied perspectives would improve balance.",
                }
            )
        elif diversity_score > 0.7:
            insights.append(
                {
                    "category": "diversity",
                    "insight": "Excellent source diversity",
                    "detail": f"Your diversity score of {diversity_score:.2f} shows great balance across perspectives.",
                }
            )

        # Echo chamber insights
        echo_chamber = bias_summary.get("echo_chamber_analysis", {})
        if echo_chamber.get("is_echo_chamber", False):
            chamber_type = echo_chamber.get("echo_chamber_type", "unknown")
            insights.append(
                {
                    "category": "bias",
                    "insight": f"Echo chamber detected: {chamber_type}",
                    "detail": "Consider diversifying your sources to get broader perspectives on current events.",
                }
            )

        # Trend insights
        activity_trend = trends.get("activity_trend", {})
        if activity_trend.get("direction") == "decreasing":
            change = activity_trend.get("change_percentage", 0)
            insights.append(
                {
                    "category": "trends",
                    "insight": "Declining news engagement",
                    "detail": f"Your activity decreased by {abs(change):.1f}% recently. Consider re-engaging with current events.",
                }
            )
        elif activity_trend.get("direction") == "increasing":
            change = activity_trend.get("change_percentage", 0)
            insights.append(
                {
                    "category": "trends",
                    "insight": "Growing news engagement",
                    "detail": f"Your activity increased by {change:.1f}% recently. Great job staying informed!",
                }
            )

        # Source concentration insights
        source_concentration = trends.get("source_concentration", {})
        if source_concentration.get("interpretation") == "high":
            insights.append(
                {
                    "category": "habits",
                    "insight": "High source concentration",
                    "detail": "You rely heavily on just a few sources. Diversifying could provide richer perspectives.",
                }
            )

        return insights

    def _find_peak_activity_days(self, stats: Dict[str, Any]) -> List[str]:
        """Find days with highest activity."""
        daily_activity = stats.get("daily_activity", [])
        if not daily_activity:
            return []

        # Sort by activity count and get top days
        sorted_days = sorted(daily_activity, key=lambda x: x[1], reverse=True)
        return [day for day, count in sorted_days[:3] if count > 0]

    def _calculate_activity_consistency(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate how consistent daily activity is."""
        daily_activity = stats.get("daily_activity", [])
        if len(daily_activity) < 3:
            return {"score": 0.0, "interpretation": "insufficient_data"}

        activity_counts = [count for _, count in daily_activity]

        # Calculate coefficient of variation (std dev / mean)
        if statistics.mean(activity_counts) == 0:
            return {"score": 0.0, "interpretation": "no_activity"}

        cv = statistics.stdev(activity_counts) / statistics.mean(activity_counts)
        consistency_score = max(0.0, 1.0 - cv)  # Higher score = more consistent

        interpretation = "high" if consistency_score > 0.7 else "medium" if consistency_score > 0.4 else "low"

        return {
            "score": round(consistency_score, 3),
            "interpretation": interpretation,
            "days_with_activity": sum(1 for count in activity_counts if count > 0),
            "total_days": len(activity_counts),
        }

    def _calculate_consumption_health_score(
        self, stats: Dict[str, Any], bias_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall health score of news consumption habits."""
        # Factors for health score (0-1 each)
        factors = {}

        # Activity level (0.2 weight)
        total_activities = stats.get("total_activities", 0)
        days = len(stats.get("daily_activity", []))
        daily_avg = total_activities / max(days, 1)

        # Optimal range: 0.5-3 activities per day
        if 0.5 <= daily_avg <= 3:
            factors["activity_level"] = 1.0
        elif daily_avg < 0.5:
            factors["activity_level"] = daily_avg / 0.5  # Scale up to 1.0
        else:  # daily_avg > 3
            factors["activity_level"] = max(0.1, 3.0 / daily_avg)  # Scale down from 1.0

        # Source diversity (0.3 weight)
        diversity_score = bias_summary.get("diversity_analysis", {}).get("diversity_score", 0.0)
        factors["source_diversity"] = diversity_score

        # Topic coverage (0.2 weight)
        topics_covered = len(stats.get("activities_by_topic", {}))
        factors["topic_coverage"] = min(1.0, topics_covered / 7)  # 7 total topics

        # Echo chamber penalty (0.15 weight)
        echo_chamber = bias_summary.get("echo_chamber_analysis", {})
        factors["echo_chamber"] = 0.0 if echo_chamber.get("is_echo_chamber", False) else 1.0

        # Credibility (0.15 weight)
        avg_credibility = bias_summary.get("diversity_analysis", {}).get("average_credibility", 0.5)
        factors["credibility"] = avg_credibility

        # Calculate weighted score
        weights = {
            "activity_level": 0.2,
            "source_diversity": 0.3,
            "topic_coverage": 0.2,
            "echo_chamber": 0.15,
            "credibility": 0.15,
        }

        health_score = sum(factors[factor] * weights[factor] for factor in factors)

        # Interpretation
        if health_score >= 0.8:
            interpretation = "excellent"
            message = "Your news consumption habits are very healthy and well-balanced!"
        elif health_score >= 0.6:
            interpretation = "good"
            message = "Good news consumption habits with some room for improvement."
        elif health_score >= 0.4:
            interpretation = "fair"
            message = "Your news habits could benefit from more balance and diversity."
        else:
            interpretation = "needs_improvement"
            message = "Consider improving your news consumption for better information balance."

        return {
            "overall_score": round(health_score, 3),
            "interpretation": interpretation,
            "message": message,
            "factor_scores": {k: round(v, 3) for k, v in factors.items()},
            "improvement_priority": max(factors.items(), key=lambda x: weights[x[0]] * (1 - x[1]))[0],
        }
