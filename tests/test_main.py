"""
Test suite for MT5 Trading Dashboard
"""

import unittest
from datetime import datetime, timedelta
from src.config.settings import Config, get_config
from src.database.db_manager import DatabaseManager
from src.utils.helpers import DateUtils, PerformanceUtils, ValidationUtils


class TestConfig(unittest.TestCase):
    """Test configuration settings"""
    
    def test_config_initialization(self):
        """Test config initialization"""
        config = get_config()
        self.assertIsInstance(config, Config)
        self.assertEqual(config.APP_NAME, "MT5 Trading Dashboard")
    
    def test_date_presets(self):
        """Test date presets generation"""
        config = get_config()
        presets = config.get_date_presets()
        
        self.assertIn("today", presets)
        self.assertIn("this_week", presets)
        self.assertIn("this_month", presets)
        self.assertIn("this_year", presets)
        
        for preset_name, preset_data in presets.items():
            self.assertIn("from", preset_data)
            self.assertIn("to", preset_data)
            self.assertIsInstance(preset_data["from"], datetime)
            self.assertIsInstance(preset_data["to"], datetime)


class TestDateUtils(unittest.TestCase):
    """Test date utilities"""
    
    def test_get_current_time(self):
        """Test current time with timezone"""
        current_time = DateUtils.get_current_time()
        self.assertIsInstance(current_time, datetime)
    
    def test_is_weekend(self):
        """Test weekend detection"""
        is_weekend = DateUtils.is_weekend()
        self.assertIsInstance(is_weekend, bool)
    
    def test_format_datetime_range(self):
        """Test datetime range formatting"""
        from_date = datetime(2024, 1, 1)
        to_date = datetime(2024, 1, 31)
        
        formatted = DateUtils.format_datetime_range(from_date, to_date)
        self.assertIsInstance(formatted, str)
        self.assertIn("From", formatted)
        self.assertIn("to", formatted)


class TestPerformanceUtils(unittest.TestCase):
    """Test performance utilities"""
    
    def test_calculate_percentage_change(self):
        """Test percentage change calculation"""
        # Test positive change
        result = PerformanceUtils.calculate_percentage_change(110, 100)
        self.assertEqual(result, 10.0)
        
        # Test negative change
        result = PerformanceUtils.calculate_percentage_change(90, 100)
        self.assertEqual(result, -10.0)
        
        # Test zero start
        result = PerformanceUtils.calculate_percentage_change(100, 0)
        self.assertEqual(result, 0)
    
    def test_get_performance_color(self):
        """Test performance color selection"""
        # Test positive performance
        color = PerformanceUtils.get_performance_color(5.0)
        self.assertEqual(color, "lime")
        
        # Test negative performance
        color = PerformanceUtils.get_performance_color(-5.0)
        self.assertEqual(color, "orange")
    
    def test_format_currency(self):
        """Test currency formatting"""
        formatted = PerformanceUtils.format_currency(1234.56)
        self.assertEqual(formatted, "1234.56 USD")
    
    def test_format_percentage(self):
        """Test percentage formatting"""
        formatted = PerformanceUtils.format_percentage(5.5)
        self.assertEqual(formatted, "+5.50%")


class TestValidationUtils(unittest.TestCase):
    """Test validation utilities"""
    
    def test_validate_account_data(self):
        """Test account data validation"""
        # Valid account data
        valid_account = {
            'login': '12345',
            'password': 'password',
            'server': 'server'
        }
        self.assertTrue(ValidationUtils.validate_account_data(valid_account))
        
        # Invalid account data
        invalid_account = {
            'login': '12345',
            'password': 'password'
            # Missing 'server'
        }
        self.assertFalse(ValidationUtils.validate_account_data(invalid_account))
    
    def test_validate_date_range(self):
        """Test date range validation"""
        from_date = datetime(2024, 1, 1)
        to_date = datetime(2024, 1, 31)
        
        self.assertTrue(ValidationUtils.validate_date_range(from_date, to_date))
        self.assertFalse(ValidationUtils.validate_date_range(to_date, from_date))
    
    def test_validate_magic_number(self):
        """Test magic number validation"""
        self.assertTrue(ValidationUtils.validate_magic_number(12345))
        self.assertTrue(ValidationUtils.validate_magic_number(0))
        self.assertFalse(ValidationUtils.validate_magic_number(-1))
        self.assertFalse(ValidationUtils.validate_magic_number("123"))


class TestDatabaseManager(unittest.TestCase):
    """Test database manager"""
    
    def setUp(self):
        """Set up test database"""
        self.db_manager = DatabaseManager(":memory:")
        self.db_manager.init_database()
    
    def test_init_database(self):
        """Test database initialization"""
        # Database should be initialized without errors
        self.db_manager.init_database()
    
    def test_magic_description_operations(self):
        """Test magic description CRUD operations"""
        account = "test_account"
        magic = 12345
        description = "Test Strategy"
        
        # Test set description
        self.db_manager.set_magic_description(account, magic, description)
        
        # Test get description
        retrieved = self.db_manager.get_magic_description(account, magic)
        self.assertEqual(retrieved, description)
        
        # Test get all descriptions
        all_descriptions = self.db_manager.get_all_magic_descriptions(account)
        self.assertIn(magic, all_descriptions)
        self.assertEqual(all_descriptions[magic], description)
        
        # Test delete description
        self.db_manager.delete_magic_description(account, magic)
        retrieved_after_delete = self.db_manager.get_magic_description(account, magic)
        self.assertIsNone(retrieved_after_delete)


if __name__ == '__main__':
    unittest.main()
