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

## 📊 Dashboard Tabs

1. **Open Positions**: Current floating P/L by magic numbers
2. **Results**: Historical trading results and performance
3. **Distribution**: Profit/loss distribution analysis
4. **Deals by Hour**: Trading activity timeline

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
   git clone <repository-url>
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
BALANCE_START = 8736
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

## 🧪 Testing

Run tests with:
```bash
python tests/run_tests.py
```

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

- **v1.0.0**: Initial release with bug fixes
  - Fixed all import and runtime errors
  - Implemented modular architecture
  - Added comprehensive error handling
