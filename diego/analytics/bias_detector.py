"""
Bias Detector

Analyzes news sources for political bias and credibility scoring
using external APIs and local fallback methods.
"""

from typing import Dict, Optional, List, Any
from .database import AnalyticsDatabase


class BiasDetector:
    """Detects political bias and credibility of news sources."""

    # Built-in source classifications (fallback data)
    KNOWN_SOURCES = {
        # Left-leaning sources
        "guardian": {"bias": -0.6, "credibility": 0.8},
        "theguardian.com": {"bias": -0.6, "credibility": 0.8},
        "cnn": {"bias": -0.4, "credibility": 0.7},
        "cnn.com": {"bias": -0.4, "credibility": 0.7},
        "msnbc": {"bias": -0.7, "credibility": 0.6},
        "washingtonpost": {"bias": -0.5, "credibility": 0.8},
        "nytimes": {"bias": -0.4, "credibility": 0.9},
        "huffpost": {"bias": -0.8, "credibility": 0.6},
        "vox": {"bias": -0.7, "credibility": 0.7},
        # Right-leaning sources
        "foxnews": {"bias": 0.7, "credibility": 0.6},
        "fox": {"bias": 0.7, "credibility": 0.6},
        "breitbart": {"bias": 0.9, "credibility": 0.4},
        "dailywire": {"bias": 0.8, "credibility": 0.5},
        "nypost": {"bias": 0.5, "credibility": 0.6},
        "wsj": {"bias": 0.3, "credibility": 0.9},
        "wallstreetjournal": {"bias": 0.3, "credibility": 0.9},
        # Center sources
        "reuters": {"bias": 0.0, "credibility": 0.9},
        "ap": {"bias": 0.0, "credibility": 0.9},
        "apnews": {"bias": 0.0, "credibility": 0.9},
        "associated-press": {"bias": 0.0, "credibility": 0.9},
        "bbc": {"bias": -0.1, "credibility": 0.8},
        "bbc.com": {"bias": -0.1, "credibility": 0.8},
        "npr": {"bias": -0.2, "credibility": 0.8},
        "pbs": {"bias": -0.1, "credibility": 0.8},
        "usa-today": {"bias": 0.1, "credibility": 0.7},
        "usatoday": {"bias": 0.1, "credibility": 0.7},
        "bloomberg": {"bias": 0.0, "credibility": 0.9},
        "newsapi": {"bias": 0.0, "credibility": 0.8},  # Aggregator
    }

    def __init__(self, db_path: Optional[str] = None):
        """Initialize bias detector with database connection."""
        self.db = AnalyticsDatabase(db_path)
        self._initialize_known_sources()

    def _initialize_known_sources(self):
        """Initialize database with known source classifications."""
        for source, data in self.KNOWN_SOURCES.items():
            self.db.update_source_analysis(
                source=source, political_bias=data["bias"], credibility_score=data["credibility"]
            )

    def get_source_bias(self, source: str) -> Dict[str, float]:
        """Get bias and credibility scores for a source."""
        # Clean source name
        clean_source = self._clean_source_name(source)

        # Try to get from database first
        source_data = self._get_cached_source_data(clean_source)
        if source_data:
            return {
                "political_bias": source_data["political_bias"],
                "credibility_score": source_data["credibility_score"],
            }

        # Try external API if available
        api_data = self._fetch_from_external_api(clean_source)
        if api_data:
            # Cache the result
            self.db.update_source_analysis(
                source=clean_source,
                political_bias=api_data["political_bias"],
                credibility_score=api_data["credibility_score"],
            )
            return api_data

        # Fallback to neutral scores
        return {"political_bias": 0.0, "credibility_score": 0.5}

    def _clean_source_name(self, source: str) -> str:
        """Clean and normalize source name."""
        if not source:
            return ""

        # Convert to lowercase and remove common suffixes
        clean = source.lower().strip()

        # Remove common domain suffixes
        suffixes = [".com", ".org", ".net", ".co.uk", ".au"]
        for suffix in suffixes:
            if clean.endswith(suffix):
                clean = clean[: -len(suffix)]
                break

        # Handle common variations
        variations = {
            "the-guardian": "guardian",
            "theguardian": "guardian",
            "the-washington-post": "washingtonpost",
            "the-wall-street-journal": "wsj",
            "wall-street-journal": "wsj",
            "new-york-times": "nytimes",
            "the-new-york-times": "nytimes",
            "associated-press": "ap",
            "huffington-post": "huffpost",
            "usa-today": "usatoday",
        }

        return variations.get(clean, clean)

    def _get_cached_source_data(self, source: str) -> Optional[Dict[str, Any]]:
        """Get cached source data from database."""
        source_analysis = self.db.get_source_analysis()
        for data in source_analysis:
            if data["source"] == source:
                return data
        return None

    def _fetch_from_external_api(self, source: str) -> Optional[Dict[str, float]]:
        """Fetch bias data from external APIs (placeholder for future implementation)."""
        # This would integrate with APIs like:
        # - AllSides API (if available)
        # - Ad Fontes Media API
        # - NewsGuard API
        # - Ground News API

        # For now, return None to use local fallback
        return None

    def analyze_source_diversity(self, sources: List[str]) -> Dict[str, Any]:
        """Analyze political diversity of a list of sources."""
        if not sources:
            return {
                "diversity_score": 0.0,
                "political_balance": {"left": 0, "center": 0, "right": 0},
                "average_credibility": 0.0,
                "source_count": 0,
            }

        bias_scores = []
        credibility_scores = []
        political_balance = {"left": 0, "center": 0, "right": 0}

        for source in sources:
            bias_data = self.get_source_bias(source)
            bias = bias_data["political_bias"]
            credibility = bias_data["credibility_score"]

            bias_scores.append(bias)
            credibility_scores.append(credibility)

            # Categorize political leaning
            if bias < -0.3:
                political_balance["left"] += 1
            elif bias > 0.3:
                political_balance["right"] += 1
            else:
                political_balance["center"] += 1

        # Calculate diversity score (lower standard deviation = less diverse)
        import statistics

        if len(bias_scores) > 1:
            diversity_score = statistics.stdev(bias_scores)
        else:
            diversity_score = 0.0

        # Normalize diversity score to 0-1 range
        max_possible_diversity = 1.0  # Theoretical max standard deviation
        normalized_diversity = min(diversity_score / max_possible_diversity, 1.0)

        return {
            "diversity_score": round(normalized_diversity, 3),
            "political_balance": political_balance,
            "average_credibility": round(statistics.mean(credibility_scores), 3),
            "average_bias": round(statistics.mean(bias_scores), 3),
            "source_count": len(sources),
            "bias_distribution": {
                "min": round(min(bias_scores), 3),
                "max": round(max(bias_scores), 3),
                "std_dev": round(diversity_score, 3),
            },
        }

    def detect_echo_chamber(self, recent_sources: List[str], threshold: float = 0.3) -> Dict[str, Any]:
        """Detect if user is in an echo chamber based on source usage."""
        diversity_analysis = self.analyze_source_diversity(recent_sources)

        # Echo chamber indicators
        is_echo_chamber = False
        echo_chamber_type = "balanced"

        diversity_score = diversity_analysis["diversity_score"]
        political_balance = diversity_analysis["political_balance"]
        total_sources = sum(political_balance.values())

        if total_sources > 0:
            # Check for extreme bias toward one side
            left_ratio = political_balance["left"] / total_sources
            right_ratio = political_balance["right"] / total_sources
            center_ratio = political_balance["center"] / total_sources

            # Echo chamber if > 70% from one political side
            if left_ratio > 0.7:
                is_echo_chamber = True
                echo_chamber_type = "left-leaning"
            elif right_ratio > 0.7:
                is_echo_chamber = True
                echo_chamber_type = "right-leaning"
            elif center_ratio > 0.9:
                echo_chamber_type = "center-focused"

            # Also consider diversity score
            if diversity_score < threshold:
                is_echo_chamber = True

        return {
            "is_echo_chamber": is_echo_chamber,
            "echo_chamber_type": echo_chamber_type,
            "diversity_score": diversity_score,
            "political_distribution": {
                "left_ratio": round(left_ratio if total_sources > 0 else 0, 3),
                "center_ratio": round(center_ratio if total_sources > 0 else 0, 3),
                "right_ratio": round(right_ratio if total_sources > 0 else 0, 3),
            },
            "recommendations": self._generate_balance_recommendations(political_balance, total_sources),
        }

    def _generate_balance_recommendations(self, political_balance: Dict[str, int], total_sources: int) -> List[str]:
        """Generate recommendations to improve source balance."""
        if total_sources == 0:
            return ["Start reading news from diverse sources"]

        recommendations = []
        left_ratio = political_balance["left"] / total_sources
        right_ratio = political_balance["right"] / total_sources
        center_ratio = political_balance["center"] / total_sources

        if left_ratio > 0.6:
            recommendations.append("Consider reading more centrist and conservative sources")
            recommendations.append("Try: Reuters, AP News, Wall Street Journal")
        elif right_ratio > 0.6:
            recommendations.append("Consider reading more centrist and liberal sources")
            recommendations.append("Try: Reuters, AP News, NPR, BBC")
        elif center_ratio > 0.8:
            recommendations.append("Consider reading diverse perspectives from different political viewpoints")
            recommendations.append("Try mixing sources like Guardian (left), WSJ (right), and Reuters (center)")

        if len(set(political_balance.values())) == 1 and total_sources < 3:
            recommendations.append("Try reading from at least 3-5 different sources for better coverage")

        return recommendations

    def get_bias_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get bias analysis summary for user's consumption."""
        stats = self.db.get_consumption_stats(days)
        sources = list(stats.get("activities_by_source", {}).keys())

        if not sources:
            return {
                "period_days": days,
                "sources_analyzed": 0,
                "diversity_analysis": {},
                "echo_chamber_analysis": {},
                "recommendations": ["Start reading news to get personalized bias analysis"],
            }

        diversity_analysis = self.analyze_source_diversity(sources)
        echo_chamber_analysis = self.detect_echo_chamber(sources)

        return {
            "period_days": days,
            "sources_analyzed": len(sources),
            "sources_used": sources,
            "diversity_analysis": diversity_analysis,
            "echo_chamber_analysis": echo_chamber_analysis,
            "overall_bias_score": diversity_analysis.get("average_bias", 0.0),
            "credibility_score": diversity_analysis.get("average_credibility", 0.5),
        }
