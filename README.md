# MT5 Trading Dashboard

A comprehensive trading dashboard for MetaTrader 5 with modular architecture.

## Features

- **Real-time Trading Data**: Connect to MetaTrader 5 terminal
- **Open Positions Monitoring**: Track current floating P/L
- **Historical Analysis**: Analyze past trading performance
- **Magic Number Management**: Organize trades by strategy
- **Interactive Charts**: Visualize data with Plotly
- **Auto-refresh**: Keep data up-to-date automatically

## Project Structure

```
MT5_Trading_Dashboard/
├── src/                    # Source code
│   ├── config/            # Configuration settings
│   ├── database/          # Database operations
│   ├── mt5/              # MetaTrader 5 integration
│   ├── ui/               # User interface
│   │   ├── components/   # Reusable UI components
│   │   └── pages/       # Application pages
│   └── utils/           # Utility functions
├── assets/              # Static resources
│   ├── css/            # Custom styles
│   └── images/         # Images and icons
├── tests/              # Test files
├── docs/              # Documentation
├── venv/             # Virtual environment
├── app.py            # Main application
├── requirements.txt  # Dependencies
└── README.md        # This file
```

## Installation

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate virtual environment:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Make sure MetaTrader 5 is running
2. Start the application:
   ```bash
   streamlit run app.py
   ```
3. Open your browser to the provided URL (usually http://localhost:8501)

## Configuration

Edit `src/config/settings.py` to customize:
- Trading parameters
- UI settings
- Database configuration
- Performance thresholds

## Development

The project uses a modular architecture for easy maintenance and extension:

- **Config Module**: Centralized configuration management
- **Database Module**: SQLite operations for magic descriptions
- **MT5 Module**: MetaTrader 5 API integration
- **UI Module**: Reusable components and pages
- **Utils Module**: Helper functions and utilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
