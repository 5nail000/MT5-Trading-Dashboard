# MT5 Trading Dashboard

A comprehensive trading dashboard for MetaTrader 5 with modular architecture, built with Streamlit and Plotly.

## 🚀 Features

- **Real-time Trading Data**: Connect to MetaTrader 5 terminal
- **Open Positions Monitoring**: Track current floating P/L by magic numbers
- **Historical Analysis**: Analyze past trading performance with detailed charts
- **Magic Number Management**: Organize and describe trading strategies
- **Interactive Charts**: Visualize data with Plotly charts and graphs
- **Auto-refresh**: Keep data up-to-date automatically
- **Multi-tab Interface**: Organized view of different trading aspects
- **Performance Tracking**: Monitor profit/loss with customizable thresholds
- **Magic/Group Selection**: Filter and display specific magics/groups with interactive checkboxes
- **Group Details Breakdown**: View individual histograms for each magic group
- **Information Panel**: Display period, balance, and performance metrics directly on charts
- **Advanced Filtering**: Filter out incomplete positions and customize data views

## 📊 Dashboard Tabs

1. **Open Positions**: Current floating P/L by magic numbers
2. **Results**: Historical trading results and performance with magic/group filtering, information panel, and group details breakdown
3. **Deals (Aggregated by Position)**: Detailed table of closed positions with independent magic/group filtering, showing only fully closed positions within selected period
4. **Distribution**: Profit/loss distribution analysis
5. **Deals by Hour**: Trading activity timeline

## 🏗️ Project Structure

```
MT5_Trading_Dashboard/
├── src/                    # Source code
│   ├── config/            # Configuration settings
│   │   ├── __init__.py
│   │   └── settings.py    # Main configuration
│   ├── database/          # Database operations
│   │   ├── __init__.py
│   │   └── db_manager.py  # SQLite database manager
│   ├── mt5/              # MetaTrader 5 integration
│   │   ├── __init__.py
│   │   └── mt5_client.py  # MT5 API client
│   ├── ui/               # User interface
│   │   ├── components/   # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   └── ui_components.py
│   │   └── pages/       # Application pages
│   │       ├── __init__.py
│   │       └── pages.py
│   └── utils/           # Utility functions
│       ├── __init__.py
│       └── helpers.py    # Helper functions
├── assets/              # Static resources
│   ├── css/            # Custom styles
│   │   └── custom.css
│   └── images/         # Images and icons
├── tests/              # Test files
│   ├── run_tests.py
│   └── test_main.py
├── docs/              # Documentation
├── venv/             # Virtual environment (excluded from git)
├── app.py            # Main Streamlit application
├── calculate_profits_dashbords.py  # Legacy calculation script
├── requirements.txt  # Python dependencies
├── magics.db        # SQLite database (excluded from git)
├── .gitignore       # Git ignore rules
└── README.md        # This file
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- MetaTrader 5 terminal installed and running
- MetaTrader 5 Python package

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/5nail000/MT5-Trading-Dashboard/
   cd MT5_Trading_Dashboard
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

1. **Start MetaTrader 5** terminal
2. **Run the application**:
   ```bash
   streamlit run app.py
   ```
3. **Open your browser** to the provided URL (usually http://localhost:8501)

## ⚙️ Configuration

Edit `src/config/settings.py` to customize:

- **Trading Parameters**: Balance start, time shift, custom text
- **UI Settings**: Chart heights, margins, color schemes
- **Performance Thresholds**: Warning and critical levels
- **Auto-refresh**: Enable/disable and set interval

### Key Configuration Options

```python
# Trading settings
CUSTOM_TEXT = "2nd week of October"
LOCAL_TIMESHIFT = 3

# Auto-refresh settings
AUTO_REFRESH_INTERVAL = 60  # seconds
AUTO_REFRESH_ENABLED = True

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "warning": -12,
    "critical": -20
}
```

### Balance Calculation Function

The dashboard now includes a sophisticated balance calculation function:

```python
from src.mt5.mt5_client import mt5_calculator

# Calculate balance at beginning of day (default)
balance = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 10),
    deals=trade_history
)

# Calculate balance at end of day
balance = mt5_calculator.calculate_balance_at_date(
    target_date=datetime(2025, 10, 10),
    deals=trade_history,
    end_of_day=True
)
```

**Features:**
- ✅ **Automatic balance calculation** based on trade history
- ✅ **Timezone support** with `LOCAL_TIMESHIFT` configuration
- ✅ **Beginning/end of day** options
- ✅ **No more hardcoded BALANCE_START** - everything is calculated dynamically

### Command Line Tool

The project includes a command-line tool for quick balance calculations:

```bash
# Calculate balance at beginning of day

python tests/balance_calculation/balance_by_date.py --date 2025-09-27

# Calculate balance at end of day
python tests/balance_calculation/balance_by_date.py --date 2025-09-27 --end-of-day

# Calculate with custom initial balance
python tests/balance_calculation/balance_by_date.py --date 2025-10-10 --initial-balance 1000

# Detailed output with verbose mode
python tests/balance_calculation/balance_by_date.py --date 2025-09-30 --verbose
```

**Supported date formats:**
- `2025-09-27` (ISO format)
- `27-09-2025` (European format)
- `27/09/2025` (Slash format)
- `27.09.2025` (Dot format)

## 🏛️ Architecture

The project uses a modular architecture for easy maintenance and extension:

### Core Modules

- **Config Module** (`src/config/`): Centralized configuration management
- **Database Module** (`src/database/`): SQLite operations for magic descriptions
- **MT5 Module** (`src/mt5/`): MetaTrader 5 API integration
- **UI Module** (`src/ui/`): Reusable components and pages
- **Utils Module** (`src/utils/`): Helper functions and utilities

### Key Classes

- `DatabaseManager`: Handles SQLite operations
- `MT5Connection`: Manages MT5 terminal connection
- `MT5DataProvider`: Fetches trading data
- `MT5Calculator`: Processes trading calculations
- `ChartComponent`: Creates Plotly charts
- `DateUtils`: Date and time utilities

## 🐛 Recent Bug Fixes

This version includes several important bug fixes:

- ✅ **Fixed import path errors** in modular architecture
- ✅ **Fixed AttributeError**: DateUtils object has no attribute timedelta
- ✅ **Fixed NameError**: name timedelta is not defined
- ✅ **Fixed ValueError**: Invalid property specified for Plotly margins
- ✅ **Fixed NameError**: name px is not defined
- ✅ **Updated CHART_MARGINS** to use Plotly-compatible property names
- ✅ **Added missing imports** for plotly.express and timedelta

## 🔗 Linear Integration

This project is integrated with Linear for issue tracking and project management:

- **Linear Project**: [MT5 Trading Dashboard](https://linear.app/mt5-trading-dashboard)
- **Issue Tracking**: [MT5-3: Connect Your Tools](https://linear.app/mt5-trading-dashboard/issue/MT5-3/connect-your-tools-3)

### Linear Setup

1. **Get API Key**: Visit [Linear API Settings](https://linear.app/settings/api)
2. **Configure Environment**: Copy `linear_config.env` to `.env` and fill in your API key
3. **Install Dependencies**: `pip install requests python-dotenv`

### Linear Commands

```bash
# Sync with Linear
python linear/linear_sync.py

# Create new issue
python linear/linear_integration.py

# Update issue status
python -c "from linear_integration import LinearIntegration; LinearIntegration().update_issue_status('MT5-3', 'completed')"
```

### Integration Features

- ✅ **Automatic Issue Creation**: From Git commits
- ✅ **Status Synchronization**: Between Linear and GitHub
- ✅ **Progress Tracking**: Monitor development progress
- ✅ **Issue Management**: Create, update, and track issues

## 📝 Dependencies

- **streamlit**: Web application framework
- **plotly**: Interactive charts and graphs
- **pandas**: Data manipulation and analysis
- **MetaTrader5**: MT5 Python API
- **sqlite3**: Database operations (built-in)
- **psutil**: Process management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:

1. Check that MetaTrader 5 is running
2. Verify your Python environment is set up correctly
3. Check the console for error messages
4. Open an issue on GitHub with detailed error information

## 🔄 Version History

- **v1.2.0** (2025-11-15): Major UI improvements and feature enhancements
  - Added magic/group selection checkboxes with Show All/Hide All/Refresh buttons
  - Added information panel on Results histogram
  - Added group details breakdown in Results tab
  - Enhanced Deals tab with independent filtering and incomplete positions filtering
  - Improved filtering and sorting functionality
  - Enhanced balance calculation accuracy
  - Improved content width and histogram label formatting

- **v1.1.0** (2025-10-15): Dynamic balance calculation
  - Added `calculate_balance_at_date()` function
  - Timezone support and beginning/end of day options
  - Command line tool for balance calculations

- **v1.0.0** (2025-10-14): Initial release with bug fixes
  - Fixed all import and runtime errors
  - Implemented modular architecture
  - Added comprehensive error handling
