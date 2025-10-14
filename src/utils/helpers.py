"""
Utility functions and helpers for MT5 Trading Dashboard
"""

import pprint
import time as time_mod
from datetime import datetime, timedelta, time
from typing import Dict, Any, List, Optional
from ..config.settings import Config


class PrettyPrinter:
    """Pretty printer utility"""
    
    def __init__(self, indent: int = 4):
        self.pp = pprint.PrettyPrinter(indent=indent)
    
    def print(self, obj: Any):
        """Print object with pretty formatting"""
        self.pp.pprint(obj)


class DateUtils:
    """Date and time utilities"""
    
    @staticmethod
    def get_current_time() -> datetime:
        """Get current time with timezone shift"""
        return datetime.now() + timedelta(hours=Config.LOCAL_TIMESHIFT)
    
    @staticmethod
    def get_today() -> datetime:
        """Get today's date at midnight with timezone shift"""
        now = datetime.now()
        return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=Config.LOCAL_TIMESHIFT)
    
    @staticmethod
    def get_start_of_week() -> datetime:
        """Get start of current week"""
        today = DateUtils.get_today()
        now = datetime.now()
        return today - timedelta(days=now.weekday())
    
    @staticmethod
    def get_start_of_month() -> datetime:
        """Get start of current month"""
        now = datetime.now()
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=Config.LOCAL_TIMESHIFT)
    
    @staticmethod
    def get_start_of_year() -> datetime:
        """Get start of current year"""
        now = datetime.now()
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=Config.LOCAL_TIMESHIFT)
    
    @staticmethod
    def is_weekend() -> bool:
        """Check if current day is weekend"""
        return datetime.now().weekday() in [5, 6]  # Saturday or Sunday
    
    @staticmethod
    def format_datetime_range(from_date: datetime, to_date: datetime) -> str:
        """Format datetime range for display"""
        return f"From {from_date} to {to_date}"


class PerformanceUtils:
    """Performance calculation utilities"""
    
    @staticmethod
    def calculate_percentage_change(current: float, start: float) -> float:
        """Calculate percentage change"""
        if start == 0:
            return 0
        return (current / start) * 100
    
    @staticmethod
    def get_performance_color(percentage: float) -> str:
        """Get color based on performance percentage"""
        if percentage >= 0:
            return Config.COLOR_SCHEMES["positive"]
        elif percentage >= Config.PERFORMANCE_THRESHOLDS["warning"]:
            return Config.COLOR_SCHEMES["negative_warning"]
        elif percentage >= Config.PERFORMANCE_THRESHOLDS["critical"]:
            return Config.COLOR_SCHEMES["negative_critical"]
        else:
            return Config.COLOR_SCHEMES["negative_danger"]
    
    @staticmethod
    def format_currency(amount: float, currency: str = "USD") -> str:
        """Format currency amount"""
        return f"{amount:.2f} {currency}"
    
    @staticmethod
    def format_percentage(percentage: float) -> str:
        """Format percentage with sign"""
        return f"{percentage:+.2f}%"


class DataUtils:
    """Data processing utilities"""
    
    @staticmethod
    def create_labels_dict(magics: List[int], descriptions: Dict[int, str], 
                          account_id: str, reverse_order: bool = False) -> Dict[int, str]:
        """Create labels dictionary for magic numbers"""
        labels = {}
        for magic in magics:
            description = descriptions.get(magic)
            if description:
                if reverse_order:
                    labels[magic] = f"{description} - {magic}"
                else:
                    labels[magic] = f"{magic} - {description}"
            else:
                labels[magic] = str(magic)
        return labels
    
    @staticmethod
    def prepare_chart_data(data: Dict[str, Any], sort_option: str) -> Dict[str, Any]:
        """Prepare data for chart display"""
        # This would contain chart-specific data preparation logic
        return data
    
    @staticmethod
    def filter_deals_by_period(deals: List, from_date: datetime, to_date: datetime) -> List:
        """Filter deals by time period"""
        filtered_deals = []
        for deal in deals:
            if deal.type == 2:  # Skip balance changes
                continue
            if from_date and deal.time < from_date.timestamp():
                continue
            if to_date and deal.time > to_date.timestamp():
                continue
            filtered_deals.append(deal)
        return filtered_deals


class SessionUtils:
    """Session management utilities"""
    
    @staticmethod
    def init_session_state(session_state: Any):
        """Initialize session state variables"""
        if 'from_date' not in session_state:
            session_state.from_date = DateUtils.get_today()
        if 'to_date' not in session_state:
            session_state.to_date = DateUtils.get_current_time()
        if 'pending_from_date' not in session_state:
            session_state.pending_from_date = session_state.from_date
        if 'pending_to_date' not in session_state:
            session_state.pending_to_date = session_state.to_date
        if 'last_update' not in session_state:
            session_state.last_update = time_mod.time()
    
    @staticmethod
    def should_auto_refresh(session_state: Any) -> bool:
        """Check if auto-refresh should trigger"""
        current_time = time_mod.time()
        return (current_time - session_state.last_update >= Config.AUTO_REFRESH_INTERVAL)
    
    @staticmethod
    def update_session_timestamp(session_state: Any):
        """Update session timestamp"""
        session_state.last_update = time_mod.time()


class ValidationUtils:
    """Data validation utilities"""
    
    @staticmethod
    def validate_account_data(account: Dict[str, Any]) -> bool:
        """Validate account data"""
        required_fields = ['login', 'password', 'server']
        return all(field in account for field in required_fields)
    
    @staticmethod
    def validate_date_range(from_date: datetime, to_date: datetime) -> bool:
        """Validate date range"""
        return from_date <= to_date
    
    @staticmethod
    def validate_magic_number(magic: int) -> bool:
        """Validate magic number"""
        return isinstance(magic, int) and magic >= 0


# Global utility instances
pp = PrettyPrinter()
date_utils = DateUtils()
performance_utils = PerformanceUtils()
data_utils = DataUtils()
session_utils = SessionUtils()
validation_utils = ValidationUtils()
