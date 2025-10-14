# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
