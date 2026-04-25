"""
Website Phishing Detection Test Tool
Analyze live websites using ScraperAPI with the trained DistilBERT model.
"""

__version__ = '1.0.0'
__author__ = 'AI Phishing Detection Project'

from .scraper import ScraperAPIClient
from .processor import ContentProcessor
from .model_handler import PhishingModelHandler
from .dashboard_generator import DashboardGenerator

__all__ = [
    'ScraperAPIClient',
    'ContentProcessor',
    'PhishingModelHandler',
    'DashboardGenerator'
]
