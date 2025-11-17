# 📈 Options Backtesting Platform

A comprehensive Python-based options backtesting platform that converts TradingView strategy reports into simulated NIFTY options trades using real historical data from Upstox API.

![Platform](https://img.shields.io/badge/Platform-Streamlit-red)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 🎯 Features

- ✅ **TradingView Integration**: Upload and parse TradingView strategy exports
- ✅ **Automatic Option Conversion**: Long → CALL, Short → PUT
- ✅ **Flexible Expiry Logic**: Custom expiry weekday and rollover configuration
- ✅ **Strike Selection**: ATM, ITM1, OTM1 modes
- ✅ **Real Data**: Fetch historical option prices via Upstox API
- ✅ **Comprehensive Reports**: Excel exports with multiple analysis sheets
- ✅ **Interactive Dashboard**: Beautiful Streamlit UI with charts
- ✅ **Performance Metrics**: Win rate, P&L, drawdown, profit factor

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│ Streamlit Dashboard (Frontend)     │
│ - Upload TradingView Excel         │
│ - Configure parameters             │
│ - Display results & charts         │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ Data Parser (core/parser.py)       │
│ - Parse Excel structure            │
│ - Pair Entry/Exit rows             │
│ - Validate data                    │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ Backtest Engine (core/engine.py)   │
│ - Process trades                   │
│ - Calculate expiry & strike        │
│ - Fetch option prices              │
│ - Calculate P&L                    │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ Report Generator (core/report.py)  │
│ - Create Excel reports             │
│ - Generate visualizations          │
│ - Calculate statistics             │
└─────────────────────────────────────┘
```

## 📁 Project Structure

```
options_backtester/
│
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── SETUP.md                    # Setup instructions
│
├── config/
│   ├── credentials.json        # Upstox API credentials
│   └── __init__.py
│
├── core/
│   ├── __init__.py
│   ├── parser.py              # TradingView data parser
│   ├── engine.py              # Backtesting engine
│   ├── expiry_rules.py        # Expiry calculation logic
│   ├── strike_rules.py        # Strike price calculation
│   ├── upstox_api.py          # Upstox API wrapper
│   └── report.py              # Report generation
│
├── data/
│   ├── tradingview_raw/       # Raw TradingView exports
│   ├── converted_trades/      # Processed trade data
│   └── cached_data/           # Cached API responses
│
└── reports/
    └── output/                # Generated reports
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Upstox trading account with API access
- TradingView strategy backtest export

### Installation

1. **Clone or download this project**

```bash
cd options_backtester
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure Upstox credentials**

Edit `config/credentials.json`:
```json
{
    ""api_key"": ""YOUR_API_KEY"",
    ""api_secret"": ""YOUR_API_SECRET"",
    ""access_token"": ""YOUR_ACCESS_TOKEN""
}
```

> **Note**: Get your credentials from [Upstox Developer Console](https://upstox.com/developer/apps)

4. **Run the application**

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📊 Usage

### Step 1: Export from TradingView

1. Run your strategy backtest in TradingView
2. Export the results as Excel (.xlsx)
3. Ensure it contains these columns:
   - Trade #
   - Type (Entry/Exit)
   - Signal (Long/Short)
   - Date
   - Time
   - Price

### Step 2: Configure Parameters

In the sidebar, set:
- **Expiry Weekday**: Day when options expire (default: Thursday)
- **Rollover Day**: Day to roll to next expiry (default: Tuesday)
- **Moneyness Mode**: ATM/ITM1/OTM1
- **Lot Size**: NIFTY lot size (default: 75)
- **Data Interval**: 1minute or 5minute

### Step 3: Upload & Process

1. Upload your TradingView Excel file
2. Review the parsed trades
3. Click ""Run Backtest""
4. Wait for processing (uses Upstox API)

### Step 4: Analyze Results

- View trade-by-trade results in the Results tab
- Check performance metrics in the Metrics tab
- Download Excel report with comprehensive analysis
- Review equity curve and P&L distribution charts

## 🔧 Configuration Options

### Expiry Logic

The platform calculates expiry dates based on:
- **Expiry Weekday**: The day of the week when options expire
- **Rollover Day**: Trades entered on or after this day use next week's expiry

**Example**: 
- Expiry = Thursday, Rollover = Tuesday
- Monday trade → Current week Thursday expiry
- Tuesday+ trade → Next week Thursday expiry

### Strike Selection

Three moneyness modes:

| Mode | CALL Strike | PUT Strike |
|------|------------|-----------|
| ATM | Ceiling(NIFTY/50) × 50 | Floor(NIFTY/50) × 50 |
| ITM1 | ATM + 100 | ATM - 100 |
| OTM1 | ATM - 50 | ATM + 50 |

**Example** (NIFTY = 25,574):
- CALL ATM = 25,600
- PUT ATM = 25,550
- CALL ITM1 = 25,700

## 📈 Output Format

### Trade Results

Each row contains:
- Trade number and dates
- Entry/Exit times
- Expiry date
- Option type (CALL/PUT)
- Strike price
- NIFTY entry/exit prices
- Option entry/exit prices
- P&L for both NIFTY and Options

### Excel Report Sheets

1. **Trades**: All trades with full details
2. **Summary**: Key statistics and metrics
3. **Monthly**: Month-by-month breakdown
4. **Win-Loss**: Detailed win/loss analysis

## 🔌 Upstox API Integration

The platform uses Upstox API v2 for:

1. **Instrument Discovery**: Finding option contracts
2. **Historical Data**: Fetching option prices
3. **Data Formats**: 1-minute and 5-minute candles

### API Rate Limits

- Includes automatic rate limiting (0.1s delay between calls)
- Caches instrument data to reduce API calls
- Falls back to mock data if API fails (for testing)

## 🎨 Dashboard Features

### Interactive Components

- **File Uploader**: Drag-and-drop TradingView exports
- **Parameter Controls**: Sidebar configuration
- **Live Progress**: Real-time backtest progress
- **Interactive Charts**: Plotly-based visualizations
- **Data Tables**: Sortable, filterable results
- **Download Buttons**: Export to CSV and Excel

### Visualizations

1. **Equity Curve**: Cumulative P&L over time
2. **P&L Distribution**: Histogram of trade results
3. **Trade Bars**: Individual trade performance
4. **Metrics Cards**: Key statistics at a glance

## 🛠️ Development

### Adding New Features

1. **Custom Strike Logic**: Modify `core/strike_rules.py`
2. **New Expiry Rules**: Update `core/expiry_rules.py`
3. **Additional Metrics**: Extend `core/report.py`
4. **UI Enhancements**: Edit `app.py`

### Testing

The platform includes fallback mock data for testing without API access:

```python
# In core/engine.py
def mock_option_price(self, timestamp, expiry_date, strike_price, option_type):
    # Generates synthetic option prices for testing
    ...
```

## 📝 Requirements

### System Requirements

- **OS**: Windows 10/11 (64-bit), macOS, or Linux
- **RAM**: 8 GB minimum
- **Python**: 3.11+
- **Internet**: Required for Upstox API

### Python Packages

See `requirements.txt`:
- streamlit 1.32.0
- pandas 2.1.4
- openpyxl 3.1.2
- requests 2.31.0
- plotly 5.18.0
- numpy 1.26.3
- pytz 2023.3

## 🚨 Troubleshooting

### Common Issues

1. **""Module not found"" error**
   - Solution: Run `pip install -r requirements.txt`

2. **""Invalid API credentials""**
   - Solution: Check your credentials in sidebar/config file
   - Ensure access token is not expired

3. **""No instrument found""**
   - Solution: Check if the expiry date has active options
   - Verify strike price is valid for that expiry

4. **Slow performance**
   - Solution: Use 5-minute interval instead of 1-minute
   - Reduce number of trades in input file
   - Check internet connection

### Getting Help

- Check `SETUP.md` for detailed setup instructions
- Review code comments in `core/` modules
- Test with sample data first

## 🔮 Future Enhancements

Phase 2 features (planned):

- [ ] BankNIFTY and FINNIFTY support
- [ ] Multiple strike testing
- [ ] Transaction cost simulation
- [ ] Slippage modeling
- [ ] Real-time validation via websocket
- [ ] AI-based trade filtering
- [ ] Strategy optimizer
- [ ] Portfolio backtesting
- [ ] Database storage (SQLite)
- [ ] Scheduled backtests

## 📄 License

This project is provided as-is for educational and research purposes.

## ⚠️ Disclaimer

**This software is for educational and backtesting purposes only.**

- Past performance does not guarantee future results
- Options trading involves substantial risk
- Always do your own research before trading
- The developers are not responsible for any financial losses
- Use at your own risk

## 🙏 Acknowledgments

- **TradingView**: Strategy backtesting platform
- **Upstox**: Options data API
- **Streamlit**: Dashboard framework
- **Plotly**: Visualization library

## 📧 Support

For issues or questions:
1. Review documentation carefully
2. Check troubleshooting section
3. Test with sample data
4. Verify API credentials

---

**Built with ❤️ for options traders**

*Version 1.0 | November 2025*
