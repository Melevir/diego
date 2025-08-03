"""
News Recommender

Provides personalized recommendations for balanced news consumption
based on user patterns and source diversity analysis.
"""

from typing import Dict, List, Optional, Any
from .database import AnalyticsDatabase
from .bias_detector import BiasDetector


class NewsRecommender:
    """Generates personalized news recommendations for balanced consumption."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize recommender with database and bias detector."""
        self.db = AnalyticsDatabase(db_path)
        self.bias_detector = BiasDetector(db_path)

    def get_source_recommendations(self, days: int = 30, limit: int = 5) -> Dict[str, Any]:
        """Get recommendations for news sources to improve diversity."""
        stats = self.db.get_consumption_stats(days)
        current_sources = list(stats.get("activities_by_source", {}).keys())

        if not current_sources:
            return self._get_starter_recommendations()

        # Analyze current source diversity
        diversity_analysis = self.bias_detector.analyze_source_diversity(current_sources)
        echo_chamber = self.bias_detector.detect_echo_chamber(current_sources)

        recommendations = []

        # Get balance-focused recommendations
        balance_recs = self._get_balance_recommendations(current_sources, diversity_analysis, limit)
        recommendations.extend(balance_recs)

        # Get credibility-focused recommendations
        credibility_recs = self._get_credibility_recommendations(current_sources, diversity_analysis, limit)
        recommendations.extend(credibility_recs)

        # Remove duplicates and limit results
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec["source"] not in seen and rec["source"] not in current_sources:
                seen.add(rec["source"])
                unique_recommendations.append(rec)
                if len(unique_recommendations) >= limit:
                    break

        return {
            "recommendations": unique_recommendations[:limit],
            "current_diversity_score": diversity_analysis.get("diversity_score", 0.0),
            "echo_chamber_risk": echo_chamber.get("is_echo_chamber", False),
            "improvement_potential": self._calculate_improvement_potential(
                current_sources, unique_recommendations[:limit]
            ),
            "rationale": self._generate_recommendation_rationale(diversity_analysis, echo_chamber),
        }

    def _get_starter_recommendations(self) -> Dict[str, Any]:
        """Get starter recommendations for new users."""
        starter_sources = [
            {
                "source": "reuters",
                "reason": "Highly credible and politically neutral",
                "bias": 0.0,
                "credibility": 0.9,
                "category": "neutral",
            },
            {
                "source": "ap",
                "reason": "Trusted wire service with minimal bias",
                "bias": 0.0,
                "credibility": 0.9,
                "category": "neutral",
            },
            {
                "source": "bbc",
                "reason": "International perspective with high credibility",
                "bias": -0.1,
                "credibility": 0.8,
                "category": "international",
            },
            {
                "source": "npr",
                "reason": "In-depth analysis with slight left lean",
                "bias": -0.2,
                "credibility": 0.8,
                "category": "analysis",
            },
            {
                "source": "wsj",
                "reason": "Business focus with slight right lean",
                "bias": 0.3,
                "credibility": 0.9,
                "category": "business",
            },
        ]

        return {
            "recommendations": starter_sources,
            "current_diversity_score": 0.0,
            "echo_chamber_risk": False,
            "improvement_potential": 1.0,
            "rationale": "Starting with diverse, credible sources for balanced news consumption",
        }

    def _get_balance_recommendations(
        self, current_sources: List[str], diversity_analysis: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations to improve political balance."""
        recommendations = []
        political_balance = diversity_analysis.get("political_balance", {})

        left_count = political_balance.get("left", 0)
        center_count = political_balance.get("center", 0)
        right_count = political_balance.get("right", 0)
        total = left_count + center_count + right_count

        if total == 0:
            return []

        # Recommend based on underrepresented perspectives
        if left_count / total < 0.2:  # Need more left-leaning sources
            left_sources = [
                {
                    "source": "guardian",
                    "reason": "Quality left-leaning international coverage",
                    "bias": -0.6,
                    "credibility": 0.8,
                    "category": "left-balance",
                },
                {
                    "source": "npr",
                    "reason": "In-depth left-leaning analysis",
                    "bias": -0.2,
                    "credibility": 0.8,
                    "category": "left-balance",
                },
            ]
            recommendations.extend(left_sources)

        if right_count / total < 0.2:  # Need more right-leaning sources
            right_sources = [
                {
                    "source": "wsj",
                    "reason": "High-quality right-leaning business news",
                    "bias": 0.3,
                    "credibility": 0.9,
                    "category": "right-balance",
                },
                {
                    "source": "nypost",
                    "reason": "Popular right-leaning perspective",
                    "bias": 0.5,
                    "credibility": 0.6,
                    "category": "right-balance",
                },
            ]
            recommendations.extend(right_sources)

        if center_count / total < 0.3:  # Need more centrist sources
            center_sources = [
                {
                    "source": "reuters",
                    "reason": "Neutral, fact-focused reporting",
                    "bias": 0.0,
                    "credibility": 0.9,
                    "category": "center-balance",
                },
                {
                    "source": "ap",
                    "reason": "Unbiased wire service",
                    "bias": 0.0,
                    "credibility": 0.9,
                    "category": "center-balance",
                },
            ]
            recommendations.extend(center_sources)

        return recommendations

    def _get_credibility_recommendations(
        self, current_sources: List[str], diversity_analysis: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations to improve overall credibility."""
        current_credibility = diversity_analysis.get("average_credibility", 0.5)

        if current_credibility >= 0.8:
            return []  # Already high credibility

        high_credibility_sources = [
            {
                "source": "reuters",
                "reason": "Exceptional credibility and fact-checking",
                "bias": 0.0,
                "credibility": 0.9,
                "category": "high-credibility",
            },
            {
                "source": "ap",
                "reason": "Rigorous journalistic standards",
                "bias": 0.0,
                "credibility": 0.9,
                "category": "high-credibility",
            },
            {
                "source": "wsj",
                "reason": "High-quality business journalism",
                "bias": 0.3,
                "credibility": 0.9,
                "category": "high-credibility",
            },
            {
                "source": "nytimes",
                "reason": "Thorough investigative reporting",
                "bias": -0.4,
                "credibility": 0.9,
                "category": "high-credibility",
            },
            {
                "source": "bbc",
                "reason": "International standards and fact-checking",
                "bias": -0.1,
                "credibility": 0.8,
                "category": "high-credibility",
            },
        ]

        return high_credibility_sources

    def _calculate_improvement_potential(
        self, current_sources: List[str], recommended_sources: List[Dict[str, Any]]
    ) -> float:
        """Calculate potential improvement in diversity score."""
        if not recommended_sources:
            return 0.0

        # Current diversity
        current_diversity = self.bias_detector.analyze_source_diversity(current_sources)
        current_score = current_diversity.get("diversity_score", 0.0)

        # Potential diversity with recommendations
        potential_sources = current_sources + [rec["source"] for rec in recommended_sources]
        potential_diversity = self.bias_detector.analyze_source_diversity(potential_sources)
        potential_score = potential_diversity.get("diversity_score", 0.0)

        improvement = potential_score - current_score
        return max(0.0, min(1.0, improvement))  # Clamp to 0-1 range

    def _generate_recommendation_rationale(
        self, diversity_analysis: Dict[str, Any], echo_chamber: Dict[str, Any]
    ) -> str:
        """Generate explanation for recommendations."""
        diversity_score = diversity_analysis.get("diversity_score", 0.0)
        is_echo_chamber = echo_chamber.get("is_echo_chamber", False)
        echo_type = echo_chamber.get("echo_chamber_type", "balanced")

        if diversity_score < 0.3:
            return f"Your current news sources show low diversity (score: {diversity_score:.2f}). These recommendations will help you access different perspectives."
        elif is_echo_chamber:
            return f"You may be in a {echo_type} echo chamber. These sources will provide broader viewpoints."
        elif diversity_score < 0.6:
            return f"Your source diversity is moderate (score: {diversity_score:.2f}). These recommendations will enhance your perspective range."
        else:
            return "Your sources are well-balanced. These additional sources can further enrich your news consumption."

    def get_topic_recommendations(self, days: int = 30, limit: int = 5) -> Dict[str, Any]:
        """Get recommendations for new topics to explore."""
        stats = self.db.get_consumption_stats(days)
        current_topics = set(stats.get("activities_by_topic", {}).keys())

        # All available topics from Diego
        all_topics = {"business", "entertainment", "general", "health", "science", "sports", "technology"}

        # Topics user hasn't explored much
        unexplored_topics = all_topics - current_topics

        # Topic recommendations with explanations
        topic_explanations = {
            "business": "Stay informed about economic trends and market developments",
            "entertainment": "Discover cultural trends and entertainment industry news",
            "general": "Get broad coverage of current events and breaking news",
            "health": "Learn about medical breakthroughs and health policy updates",
            "science": "Explore scientific discoveries and technological innovations",
            "sports": "Follow major sporting events and athlete stories",
            "technology": "Keep up with tech developments and digital transformation",
        }

        recommendations = []
        for topic in list(unexplored_topics)[:limit]:
            recommendations.append(
                {
                    "topic": topic,
                    "reason": topic_explanations.get(topic, f"Explore {topic} news"),
                    "category": "topic-expansion",
                }
            )

        # If user has covered all topics, suggest revisiting less-used ones
        if not recommendations and current_topics:
            topic_counts = stats.get("activities_by_topic", {})
            sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1])

            for topic, count in sorted_topics[:limit]:
                if count < 3:  # Topics with low usage
                    recommendations.append(
                        {
                            "topic": topic,
                            "reason": f"You've only searched this {count} times - explore more depth",
                            "category": "topic-deepening",
                        }
                    )

        return {
            "recommendations": recommendations,
            "explored_topics": list(current_topics),
            "topic_coverage": f"{len(current_topics)}/{len(all_topics)} topics explored",
            "rationale": self._generate_topic_rationale(current_topics, all_topics),
        }

    def _generate_topic_rationale(self, current_topics: set, all_topics: set) -> str:
        """Generate rationale for topic recommendations."""
        coverage_ratio = len(current_topics) / len(all_topics) if all_topics else 0

        if coverage_ratio == 0:
            return "Start exploring different news topics for well-rounded awareness"
        elif coverage_ratio < 0.5:
            return f"You've explored {len(current_topics)} of {len(all_topics)} topics. Broaden your interests for better coverage."
        elif coverage_ratio < 0.8:
            return f"Good topic diversity! Consider exploring the remaining {len(all_topics) - len(current_topics)} topics."
        else:
            return "Excellent topic coverage! Focus on deepening your understanding in areas of interest."

    def get_comprehensive_recommendations(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive recommendations covering sources, topics, and habits."""
        source_recs = self.get_source_recommendations(days)
        topic_recs = self.get_topic_recommendations(days)

        # Usage pattern analysis
        stats = self.db.get_consumption_stats(days)
        activity_pattern = {
            "total_activities": stats.get("total_activities", 0),
            "daily_average": stats.get("total_activities", 0) / max(days, 1),
            "most_active_actions": list(stats.get("activities_by_action", {}).keys())[:3],
        }

        # Habit recommendations
        habit_recommendations = self._generate_habit_recommendations(activity_pattern, days)

        return {
            "source_recommendations": source_recs,
            "topic_recommendations": topic_recs,
            "habit_recommendations": habit_recommendations,
            "overall_score": self._calculate_overall_balance_score(source_recs, topic_recs),
            "priority_actions": self._get_priority_actions(source_recs, topic_recs),
        }

    def _generate_habit_recommendations(self, activity_pattern: Dict[str, Any], days: int) -> List[Dict[str, str]]:
        """Generate recommendations for improving news consumption habits."""
        recommendations = []
        daily_avg = activity_pattern.get("daily_average", 0)

        if daily_avg < 0.5:
            recommendations.append(
                {
                    "habit": "increase_frequency",
                    "suggestion": "Try reading news at least once every 2 days for better awareness",
                    "rationale": f"You average {daily_avg:.1f} news interactions per day",
                }
            )
        elif daily_avg > 5:
            recommendations.append(
                {
                    "habit": "moderate_consumption",
                    "suggestion": "Consider setting specific times for news to avoid information overload",
                    "rationale": f"You average {daily_avg:.1f} news interactions per day",
                }
            )

        most_actions = activity_pattern.get("most_active_actions", [])
        if "search" in most_actions and "summary" not in most_actions:
            recommendations.append(
                {
                    "habit": "try_summarization",
                    "suggestion": "Try the summary feature to quickly digest longer articles",
                    "rationale": "You search frequently but haven't used article summarization",
                }
            )

        if len(most_actions) < 2:
            recommendations.append(
                {
                    "habit": "explore_features",
                    "suggestion": "Explore different commands like 'sources' and 'summary' for richer experience",
                    "rationale": "You primarily use one type of command",
                }
            )

        return recommendations

    def _calculate_overall_balance_score(self, source_recs: Dict[str, Any], topic_recs: Dict[str, Any]) -> float:
        """Calculate overall balance score (0-1)."""
        source_diversity = source_recs.get("current_diversity_score", 0.0)
        echo_chamber_penalty = 0.3 if source_recs.get("echo_chamber_risk", False) else 0.0
        topic_coverage = len(topic_recs.get("explored_topics", [])) / 7  # 7 total topics

        # Weighted combination
        balance_score = (source_diversity * 0.5) + (topic_coverage * 0.3) + ((1 - echo_chamber_penalty) * 0.2)
        return min(1.0, max(0.0, balance_score))

    def _get_priority_actions(self, source_recs: Dict[str, Any], topic_recs: Dict[str, Any]) -> List[str]:
        """Get priority actions for user to improve balance."""
        actions = []

        if source_recs.get("echo_chamber_risk", False):
            actions.append("Break out of echo chamber by reading recommended sources")

        if source_recs.get("current_diversity_score", 0) < 0.4:
            actions.append("Improve source diversity by adding balanced perspectives")

        topic_coverage = len(topic_recs.get("explored_topics", [])) / 7
        if topic_coverage < 0.5:
            actions.append("Explore more news topics for well-rounded awareness")

        if not actions:
            actions.append("Continue maintaining balanced news consumption habits")

        return actions
