"""
Configuration settings for MT5 Trading Dashboard
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any


class Config:
    """Main configuration class"""
    
    # Application settings
    APP_NAME = "MT5 Trading Dashboard"
    APP_VERSION = "1.0.0"
    PAGE_TITLE = "Trading Dashboard"
    
    # Database settings
    DATABASE_PATH = "magics.db"
    
    # Trading settings
    BALANCE_START = 8736
    CUSTOM_TEXT = "2nd week of October"
    LOCAL_TIMESHIFT = 3
    
    # Auto-refresh settings
    AUTO_REFRESH_INTERVAL = 60  # seconds
    AUTO_REFRESH_ENABLED = True
    
    # Date range presets
    @staticmethod
    def get_date_presets() -> Dict[str, Dict[str, datetime]]:
        """Get predefined date ranges"""
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=Config.LOCAL_TIMESHIFT)
        start_of_week = today - timedelta(days=now.weekday())
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=Config.LOCAL_TIMESHIFT)
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=Config.LOCAL_TIMESHIFT)
        
        return {
            "today": {
                "from": today,
                "to": now + timedelta(hours=Config.LOCAL_TIMESHIFT)
            },
            "this_week": {
                "from": start_of_week,
                "to": now + timedelta(hours=Config.LOCAL_TIMESHIFT)
            },
            "this_month": {
                "from": start_of_month,
                "to": now + timedelta(hours=Config.LOCAL_TIMESHIFT)
            },
            "this_year": {
                "from": start_of_year,
                "to": now + timedelta(hours=Config.LOCAL_TIMESHIFT)
            }
        }
    
    # UI settings
    CHART_HEIGHT_MULTIPLIER = 30
    MIN_CHART_HEIGHT = 300
    CHART_MARGINS = {
        "t": 120,
        "b": 40,
        "l": 40,
        "r": 20
    }
    
    # Color schemes
    COLOR_SCHEMES = {
        "profit_loss": "RdYlGn",
        "positive": "lime",
        "negative_warning": "orange",
        "negative_critical": "OrangeRed",
        "negative_danger": "red"
    }
    
    # Performance thresholds (as percentages)
    PERFORMANCE_THRESHOLDS = {
        "warning": -12,
        "critical": -20
    }


class UIConfig:
    """UI-specific configuration"""
    
    # CSS styles
    CUSTOM_CSS = """
    <style>
    div.stToast {
        position: fixed;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        width: auto;
        max-width: 80%;
    }
    div.stToast > div {
        background-color: #28a745;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    </style>
    """
    
    # Tab configuration
    TABS = [
        "Open Positions",
        "Results", 
        "Distribution",
        "Deals by Hour"
    ]
    
    # Sort options
    SORT_OPTIONS = {
        "results": ["Results ↓", "Results ↑", "Magics ↓", "Magics ↑"],
        "open_positions": ["Floating ↓", "Floating ↑", "Magics ↓", "Magics ↑"]
    }


class DatabaseConfig:
    """Database configuration"""
    
    TABLES = {
        "magic_descriptions": {
            "name": "magic_descriptions",
            "schema": """
                CREATE TABLE IF NOT EXISTS magic_descriptions
                (account TEXT, magic INTEGER, description TEXT, 
                 PRIMARY KEY(account, magic))
            """
        }
    }


# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    LOG_LEVEL = "INFO"


# Configuration factory
def get_config(env: str = None) -> Config:
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv("ENVIRONMENT", "development")
    
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig
    }
    
    return config_map.get(env, DevelopmentConfig)()
