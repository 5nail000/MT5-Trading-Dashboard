# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-11-15

### Added
- **Magic/Group Selection Checkboxes**: Interactive checkboxes to enable/disable display of specific magics/groups in Results and Deals tabs
- **Show All/Hide All/Refresh Buttons**: Quick controls for managing checkbox selections
- **Collapsible Checkbox Sections**: Checkbox sections wrapped in `st.expander` for better UI organization
- **Information Panel on Results Histogram**: Display period, initial balance, total result, and percentage change directly on the chart
- **Group Details Breakdown**: Individual histograms for each magic group in Results tab when grouped view is enabled
- **Total P/L Summary**: Summary calculations (Total P/L, Total Positions) for selected magics/groups in both Results and Deals tabs
- **Alphabetical Sorting**: Magic/group names displayed in alphabetical order within checkboxes
- **Two-Column Legend Format**: Histogram labels show name and formatted value side-by-side
- **Independent Filtering**: Separate magic/group selection for Results and Deals tabs
- **Deals Tab Enhancements**: 
  - Independent magic/group filtering in "Deals (Aggregated by Position)" table
  - Filter out incomplete/open positions showing only fully closed positions within selected period
  - Total P/L and Total Positions summary for filtered data
  - Real-time filtering that updates table based on checkbox selections

### Changed
- **Results Histogram Layout**: Increased left margin to 280px for wider two-column legend
- **Histogram Label Font**: Changed to JetBrains Mono monospace font for better readability and alignment
- **Content Width**: Expanded overall content area width using custom CSS (max-width: 1400px)
- **Total Result Formatting**: Added +/- sign before dollar sign (e.g., "+ $1,234.56" instead of "+$1,234.56")
- **Session State Management**: Improved checkbox state persistence across page reruns using update counters
- **Balance Calculation**: Enhanced to use full trade history for accurate initial balance calculation

### Fixed
- **Main Histogram Sorting**: Fixed sorting functionality in Results tab main histogram
- **Percentage Calculation**: Corrected percentage change calculation to use proper initial balance from full trade history
- **Incomplete Positions Filtering**: Filter out open/incomplete positions from Deals (Aggregated by Position) table
- **Infinite Rerun Loop**: Prevented page refresh loop when all checkboxes are cleared
- **Checkbox State Updates**: Fixed visual updates of checkboxes after Show All/Hide All button clicks
- **Deprecated Parameters**: Removed deprecated `width='stretch'` parameter from `st.plotly_chart` calls
- **Data Consistency**: Ensured all calculations use unified dataset (`full_trade_history`) for positions active within selected period

### Technical Details
- Improved session state management with `update_counter_key` to force widget recreation
- Added `button_action_key` to prevent session state overwriting during button actions
- Enhanced data filtering logic to respect selected magics/groups across all views
- Updated Plotly chart configurations for better label display and spacing
- Improved error handling for empty checkbox selections

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
