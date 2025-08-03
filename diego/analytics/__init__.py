"""
Diego Analytics Module

Provides comprehensive news consumption analytics, bias detection,
and personalized recommendations for balanced news consumption.
"""

# Import core modules that don't require external dependencies
from .database import AnalyticsDatabase
from .tracker import AnalyticsTracker

# Import optional modules with external dependencies
try:
    from .bias_detector import BiasDetector
    from .recommender import NewsRecommender
    from .insights import InsightsGenerator
    from .exporter import DataExporter

    __all__ = [
        "AnalyticsTracker",
        "AnalyticsDatabase",
        "BiasDetector",
        "NewsRecommender",
        "InsightsGenerator",
        "DataExporter",
    ]
except ImportError:
    # If dependencies are missing, only export core functionality
    __all__ = [
        "AnalyticsTracker",
        "AnalyticsDatabase",
    ]
