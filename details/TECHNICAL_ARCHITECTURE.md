# 🏗️ Technical Architecture Document

## Options Backtesting Platform - Version 1.0

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Layers](#architecture-layers)
3. [Component Design](#component-design)
4. [Data Flow](#data-flow)
5. [API Integration](#api-integration)
6. [Error Handling](#error-handling)
7. [Performance Considerations](#performance-considerations)
8. [Security](#security)
9. [Scalability](#scalability)
10. [Testing Strategy](#testing-strategy)

---

## System Overview

### Purpose
Convert TradingView strategy backtests into simulated NIFTY options trades using real historical data.

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Streamlit 1.32.0 | Interactive dashboard |
| Data Processing | Pandas 2.1.4 | Data manipulation |
| Visualization | Plotly 5.18.0 | Interactive charts |
| API Client | Requests 2.31.0 | HTTP communication |
| Spreadsheet | Openpyxl 3.1.2 | Excel I/O |
| Numerical | NumPy 1.26.3 | Calculations |
| Timezone | Pytz 2023.3 | Time handling |

### Deployment
- **Type**: Local deployment
- **Environment**: Python 3.11+
- **Platform**: Windows/macOS/Linux
- **Architecture**: Monolithic

---

## Architecture Layers

### Layer 1: Presentation (Streamlit)

**File**: `app.py`

**Responsibilities**:
- User interface rendering
- File upload handling
- Parameter configuration
- Result visualization
- Report downloads

**Key Components**:
```python
main()                    # Entry point
run_backtest()           # Orchestrate backtest
calculate_metrics()      # Compute statistics
plot_equity_curve()      # Visualization
```

### Layer 2: Business Logic (Core Modules)

#### Parser Module (`core/parser.py`)

**Responsibilities**:
- Read TradingView Excel exports
- Parse Entry/Exit rows
- Pair trades
- Data validation

**Classes**:
```python
class TradingViewParser:
    parse_trades(df)     # Main parsing
    validate_data(df)    # Validation
```

#### Engine Module (`core/engine.py`)

**Responsibilities**:
- Orchestrate backtest execution
- Process trades sequentially
- Calculate P&L
- Handle errors

**Classes**:
```python
class BacktestEngine:
    run_backtest(trades_df)           # Main loop
    process_single_trade(trade)       # Per-trade logic
    get_option_price()                # Price fetching
    mock_option_price()               # Fallback
```

#### Expiry Rules (`core/expiry_rules.py`)

**Responsibilities**:
- Calculate expiry dates
- Apply rollover logic
- Handle weekly options

**Classes**:
```python
class ExpiryCalculator:
    calculate_expiry(entry, expiry_day, rollover_day)
    get_next_expiry(current_date, expiry_day)
    is_expiry_week(date, expiry_day)
```

**Algorithm**:
```
IF entry_weekday >= rollover_day:
    expiry = NEXT week's expiry_weekday
ELSE:
    expiry = CURRENT week's expiry_weekday
```

#### Strike Rules (`core/strike_rules.py`)

**Responsibilities**:
- Calculate strike prices
- Implement ATM/ITM/OTM logic
- Handle rounding

**Classes**:
```python
class StrikeCalculator:
    calculate_strike(nifty_price, option_type, moneyness)
    get_atm_strike(nifty_price, option_type)
    get_itm_strike(atm_strike, option_type)
    get_otm_strike(atm_strike, option_type)
```

**Strike Selection Logic**:
```
ATM CALL: CEIL(nifty_price / 50) * 50
ATM PUT:  FLOOR(nifty_price / 50) * 50
ITM CALL: ATM + 100
ITM PUT:  ATM - 100
OTM CALL: ATM - 50
OTM PUT:  ATM + 50
```

### Layer 3: Data Access (API)

#### Upstox API Module (`core/upstox_api.py`)

**Responsibilities**:
- Authenticate with Upstox
- Fetch instrument master
- Get historical candles
- Handle rate limits

**Classes**:
```python
class UpstoxAPI:
    load_instruments()                    # Master data
    find_option_instrument()              # Lookup
    get_historical_option_price()         # Price fetch
    find_closest_price()                  # Time matching
    test_connection()                     # Health check
```

**API Endpoints Used**:
```
GET /v2/user/profile
GET /historical-candle/{instrument}/{interval}/{to}/{from}
GET /market-quote/instruments/exchange/NSE_FO.csv
```

### Layer 4: Reporting

#### Report Module (`core/report.py`)

**Responsibilities**:
- Generate Excel reports
- Calculate statistics
- Create visualizations

**Classes**:
```python
class ReportGenerator:
    create_excel_report(results_df)      # Multi-sheet Excel
    calculate_summary(results_df)        # Statistics
    monthly_breakdown(results_df)        # Monthly stats
    win_loss_analysis(results_df)        # Win/loss analysis
```

---

## Data Flow

### Input Processing Flow

```
1. User uploads TradingView Excel
   ↓
2. TradingViewParser reads file
   ↓
3. Parse Entry/Exit rows
   ↓
4. Pair trades by Trade #
   ↓
5. Validate data structure
   ↓
6. Return parsed DataFrame
```

### Backtest Execution Flow

```
FOR each trade in parsed_df:

    1. Calculate expiry date
       ├─→ ExpiryCalculator.calculate_expiry()
       └─→ Uses entry_date, expiry_day, rollover_day

    2. Calculate strike price
       ├─→ StrikeCalculator.calculate_strike()
       └─→ Uses nifty_price, option_type, moneyness

    3. Fetch option entry price
       ├─→ UpstoxAPI.get_historical_option_price()
       ├─→ Find instrument key
       ├─→ Get historical candles
       └─→ Find price at entry_time

    4. Fetch option exit price
       └─→ Same as entry but at exit_time

    5. Calculate P&L
       ├─→ pnl_per_lot = (exit - entry) * direction
       └─→ total_pnl = pnl_per_lot * lot_size

    6. Append to results

NEXT trade

Return results_df
```

### Result Presentation Flow

```
results_df
   ↓
1. Display in Streamlit table
   ↓
2. Calculate performance metrics
   ├─→ Win rate
   ├─→ Total P&L
   ├─→ Drawdown
   └─→ Profit factor
   ↓
3. Generate visualizations
   ├─→ Equity curve
   ├─→ P&L distribution
   └─→ Trade bars
   ↓
4. Create Excel report
   ├─→ Trades sheet
   ├─→ Summary sheet
   ├─→ Monthly sheet
   └─→ Win-Loss sheet
   ↓
5. Provide downloads
   ├─→ CSV export
   └─→ Excel export
```

---

## API Integration

### Upstox API v2 Integration

#### Authentication Flow

```
1. User provides credentials
   ├─→ API Key
   ├─→ API Secret
   └─→ Access Token (24hr validity)

2. Add to Authorization header
   └─→ "Bearer {access_token}"

3. Make API calls
```

#### Instrument Lookup

```
1. Download instrument master CSV
   └─→ https://assets.upstox.com/market-quote/instruments/exchange/NSE_FO.csv

2. Parse CSV to DataFrame

3. Filter by criteria
   ├─→ name = 'NIFTY'
   ├─→ expiry = calculated_date
   ├─→ strike = calculated_strike
   └─→ instrument_type = 'CE' or 'PE'

4. Extract instrument_key
   └─→ Format: "NSE_FO|{exchange_token}"
```

#### Historical Price Fetch

```
1. Prepare request
   ├─→ instrument_key from lookup
   ├─→ interval (1minute or 5minute)
   ├─→ from_date (timestamp - 1 day)
   └─→ to_date (timestamp + 1 day)

2. Call API
   └─→ GET /historical-candle/{key}/{interval}/{to}/{from}

3. Parse response
   └─→ JSON with candles array
       └─→ [timestamp, open, high, low, close, volume, oi]

4. Find closest candle
   ├─→ Calculate time difference
   ├─→ Find minimum
   └─→ Return (open + close) / 2
```

#### Rate Limiting

```python
# Built-in delay between API calls
time.sleep(0.1)  # 100ms delay

# Prevents:
- API throttling
- Connection errors
- Rate limit violations
```

---

## Error Handling

### Hierarchical Error Strategy

#### Level 1: User Input Validation

```python
# File upload
if uploaded_file is None:
    st.info("Please upload file")
    return

# Missing columns
missing = [col for col in required if col not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

# API credentials
if not api_key or not access_token:
    st.error("API credentials required")
    return
```

#### Level 2: Trade Processing

```python
try:
    result = process_single_trade(trade)
    results.append(result)
except Exception as e:
    # Log error but continue
    print(f"Error processing trade {trade['Trade #']}: {e}")
    result = trade.to_dict()
    result['Error'] = str(e)
    results.append(result)
```

#### Level 3: API Fallback

```python
try:
    # Try real API
    price = upstox_api.get_historical_option_price(...)
except:
    # Fallback to mock data
    price = mock_option_price(...)
```

### Error Types Handled

| Error Type | Handler | Action |
|-----------|---------|--------|
| File parsing | TradingViewParser | Show error message |
| Missing data | Validation | Highlight issues |
| API failure | UpstoxAPI | Use mock data |
| Rate limit | Engine | Add delay |
| Invalid credentials | App | Request re-entry |
| Network error | Try/except | Retry or skip |

---

## Performance Considerations

### Optimization Strategies

#### 1. Caching

```python
# Instrument master caching
if self.instruments is None:
    self.load_instruments()  # Load once

# Use cached data for all lookups
```

#### 2. Batch Processing

```python
# Process trades sequentially but efficiently
for idx, trade in enumerate(trades_df):
    # Progress tracking
    progress = 30 + (idx / total) * 60
    progress_bar.progress(progress)

    # Rate limiting
    time.sleep(0.1)
```

#### 3. Data Interval Selection

```
1-minute: More accurate, slower (6x API calls)
5-minute: Good accuracy, faster (default)
```

#### 4. Memory Management

```python
# Stream large datasets
df = pd.read_csv(file, chunksize=1000)

# Clean up after processing
del large_dataframe
```

### Performance Metrics

| Operation | Time (avg) | Optimization |
|-----------|-----------|--------------|
| File parse | < 1s | Pandas vectorization |
| Expiry calc | < 0.01s | Pure Python |
| Strike calc | < 0.01s | NumPy |
| API call | 0.5-2s | Caching + rate limit |
| Per trade | 1-2s | API latency |
| 50 trades | 1-2 min | Acceptable |
| Report gen | < 5s | Efficient algorithms |

---

## Security

### Credential Management

#### Storage
```json
// config/credentials.json
{
    "api_key": "YOUR_KEY",
    "api_secret": "YOUR_SECRET",
    "access_token": "YOUR_TOKEN"
}
```

**Security Measures**:
- ❌ Never commit to version control
- ✅ Add to .gitignore
- ✅ Store locally only
- ✅ Regenerate if compromised

#### Usage
```python
# Load from config
with open('config/credentials.json') as f:
    creds = json.load(f)

# Use in headers only
headers = {'Authorization': f'Bearer {creds["access_token"]}'}
```

### Data Security

1. **Local Processing**: All data stays on user's machine
2. **No Cloud Storage**: No data sent to external servers
3. **API HTTPS**: Encrypted communication with Upstox
4. **Token Expiry**: 24-hour token validity

---

## Scalability

### Current Limitations

| Aspect | Limit | Reason |
|--------|-------|--------|
| Concurrent users | 1 | Local deployment |
| Trades per run | ~500 | API rate limits |
| File size | 10 MB | Streamlit default |
| Historical range | API dependent | Upstox limits |

### Future Enhancements (Phase 2)

1. **Database Integration**
   - SQLite for caching
   - Store historical prices
   - Reduce API calls

2. **Multi-Symbol Support**
   - BankNIFTY
   - FINNIFTY
   - Stocks

3. **Parallel Processing**
   - Multi-threading for API calls
   - Async/await implementation
   - Faster backtests

4. **Cloud Deployment**
   - Heroku/AWS hosting
   - Multi-user support
   - Scheduled backtests

---

## Testing Strategy

### Unit Testing

```python
# Test expiry calculation
def test_expiry_calculator():
    calc = ExpiryCalculator()
    entry = datetime(2025, 11, 1)  # Monday
    expiry = calc.calculate_expiry(entry, 'Thursday', 'Tuesday')
    assert expiry.weekday() == 3  # Thursday
```

### Integration Testing

```python
# Test full backtest flow
def test_full_backtest():
    # Create sample data
    trades_df = create_sample_trades()

    # Run backtest
    engine = BacktestEngine(...)
    results = engine.run_backtest(trades_df)

    # Verify results
    assert len(results) == len(trades_df)
    assert 'P&L (Options)' in results.columns
```

### API Testing

```python
# Test with mock data
def test_api_fallback():
    # Force API failure
    with pytest.raises(APIError):
        upstox.get_historical_price(...)

    # Verify fallback works
    price = engine.mock_option_price(...)
    assert price > 0
```

### UI Testing

Manual testing checklist:
- ✅ File upload works
- ✅ Parameters can be set
- ✅ Backtest executes
- ✅ Results display
- ✅ Charts render
- ✅ Downloads work

---

## Module Dependencies

### Dependency Graph

```
app.py
├── core.parser
│   └── pandas
├── core.engine
│   ├── core.expiry_rules
│   ├── core.strike_rules
│   ├── core.upstox_api
│   │   ├── requests
│   │   └── pandas
│   └── numpy
├── core.report
│   ├── pandas
│   ├── openpyxl
│   └── plotly
└── streamlit
    └── plotly
```

### Import Structure

```python
# Standard library
import os, sys, json, time
from datetime import datetime, timedelta
from io import BytesIO

# Third-party
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import requests
from openpyxl import Workbook

# Local modules
from core.parser import TradingViewParser
from core.engine import BacktestEngine
from core.expiry_rules import ExpiryCalculator
from core.strike_rules import StrikeCalculator
from core.upstox_api import UpstoxAPI
from core.report import ReportGenerator
```

---

## Configuration Management

### Environment Variables (Optional)

```bash
export UPSTOX_API_KEY="your_key"
export UPSTOX_API_SECRET="your_secret"
export UPSTOX_ACCESS_TOKEN="your_token"
```

### Config File (Current)

```json
{
    "api_key": "...",
    "api_secret": "...",
    "access_token": "...",
    "lot_size": 75,
    "default_interval": "5minute",
    "cache_enabled": true
}
```

---

## Logging & Monitoring

### Current Implementation

```python
# Console logging
print(f"Processing trade {idx + 1}/{total}")
print(f"Error: {str(e)}")

# Streamlit status
st.info("Loading...")
st.success("Complete!")
st.error("Error occurred!")
```

### Future Enhancement

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backtest.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting backtest...")
```

---

## Deployment Architecture

### Current (Local)

```
User's Laptop
│
├── Python 3.11+
├── Virtual Environment
│   └── pip packages
│
├── Streamlit Server (localhost:8501)
│   └── app.py
│
└── Data Files
    ├── config/
    ├── data/
    └── reports/
```

### Future (Cloud)

```
Cloud Platform (AWS/Heroku)
│
├── Web Server
│   └── Streamlit App
│
├── Database
│   └── PostgreSQL/MongoDB
│
├── Cache Layer
│   └── Redis
│
└── Storage
    └── S3 Bucket
```

---

## Code Style & Standards

### Python Style Guide (PEP 8)

- Indentation: 4 spaces
- Line length: 88 characters (Black formatter)
- Naming: snake_case for functions, PascalCase for classes
- Docstrings: Google style

### Example

```python
class BacktestEngine:
    """
    Main backtesting engine.

    Args:
        upstox_api: UpstoxAPI instance
        expiry_calculator: ExpiryCalculator instance
        ...

    Returns:
        DataFrame with backtest results

    Raises:
        ValueError: If invalid parameters
    """

    def run_backtest(self, trades_df):
        """Execute backtest for all trades."""
        ...
```

---

## Version Control

### Git Structure (Recommended)

```
.gitignore:
venv/
__pycache__/
*.pyc
config/credentials.json
.env
*.log
reports/*.xlsx
data/*.csv

.git/
├── main branch (stable)
├── develop branch (features)
└── feature/* branches (new features)
```

---

**Document Version**: 1.0
**Last Updated**: November 2025
**Author**: Options Backtesting Platform Team
**Status**: Production Ready ✅
