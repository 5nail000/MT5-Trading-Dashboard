# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-15

### Added
- **Dynamic Balance Calculation Function**: New `calculate_balance_at_date()` function that calculates account balance at any historical date
- **Timezone Support**: Proper handling of `LOCAL_TIMESHIFT` for accurate timezone conversions
- **Beginning/End of Day Options**: Function supports both beginning (00:00:00) and end (23:59:59) of day calculations
- **Comprehensive Testing**: Full test suite with 24 passing tests covering all major functionality
- **Command Line Tool**: New `python tests/balance_calculation/balance_by_date.py --date 2025-09-27` script for quick balance calculations from terminal

### Changed
- **Replaced BALANCE_START**: Removed hardcoded `BALANCE_START` constant - now all balance calculations are dynamic
- **Improved Accuracy**: Balance calculations now use actual trade history instead of static values
- **Better Error Handling**: Enhanced error handling in database operations and balance calculations

### Fixed
- **Percentage Calculation**: Fixed `calculate_percentage_change()` formula to return correct percentage values
- **Database Testing**: Fixed database initialization issues in test suite
- **Timezone Issues**: Resolved weekend balance discrepancies caused by incorrect timezone handling

### Technical Details
- Function calculates balance from trade history starting with 0 initial balance
- Supports both regular trades and balance change deals (deposits/withdrawals)
- Proper UTC/local time conversion using `LOCAL_TIMESHIFT` configuration
- Comprehensive test coverage with mock data and real-world scenarios

## [1.0.0] - 2025-10-14

### Added
- Initial release of MT5 Trading Dashboard
- Modular architecture with separate modules for config, database, MT5, UI, and utils
- Real-time trading data integration with MetaTrader 5
- Interactive dashboard with multiple tabs:
  - Open Positions monitoring
  - Historical Results analysis
  - Profit/Loss Distribution
  - Deals by Hour timeline
- Magic number management with SQLite database
- Auto-refresh functionality
- Customizable configuration settings
- Comprehensive error handling
- Plotly charts and visualizations
- Streamlit web interface

### Fixed
- Fixed import path errors in modular architecture
- Fixed AttributeError: DateUtils object has no attribute timedelta
- Fixed NameError: name timedelta is not defined
- Fixed ValueError: Invalid property specified for Plotly margins
- Fixed NameError: name px is not defined
- Updated CHART_MARGINS to use Plotly-compatible property names
- Added missing imports for plotly.express and timedelta

### Technical Details
- Python 3.8+ compatibility
- Streamlit web framework
- Plotly for interactive charts
- SQLite for data persistence
- MetaTrader 5 Python API integration
- Modular design for easy maintenance and extension

### Dependencies
- streamlit
- plotly
- pandas
- MetaTrader5
- psutil
- sqlite3 (built-in)
