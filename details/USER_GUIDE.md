# 📖 User Guide

Complete guide to using the Options Backtesting Platform effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Preparing TradingView Data](#preparing-tradingview-data)
3. [Configuring Parameters](#configuring-parameters)
4. [Running Backtests](#running-backtests)
5. [Understanding Results](#understanding-results)
6. [Best Practices](#best-practices)
7. [Advanced Usage](#advanced-usage)

---

## Getting Started

### First-Time Setup

1. **Complete Setup**
   - Follow instructions in `SETUP.md`
   - Install all dependencies
   - Configure Upstox credentials

2. **Launch Application**
   ```bash
   streamlit run app.py
   ```

3. **Verify Interface**
   - Dashboard opens in browser
   - Sidebar shows configuration
   - Upload area is visible

---

## Preparing TradingView Data

### Exporting from TradingView

1. **Run Your Strategy**
   - Open TradingView
   - Apply your strategy to NIFTY
   - Run backtest

2. **Export Results**
   - Click ""List of Trades""
   - Click export icon
   - Choose ""Export to Excel""
   - Save as .xlsx file

### Required Format

Your Excel file must contain these columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Trade # | Integer | Unique trade identifier | 1, 2, 3 |
| Type | String | Entry or Exit | ""Entry"", ""Exit"" |
| Signal | String | Direction of trade | ""Long"", ""Short"" |
| Date | Date | Trade date | ""2025-11-01"" |
| Time | Time | Trade time | ""09:30:00"" |
| Price | Float | NIFTY price | 25550.0 |

### Sample Data

```csv
Trade #,Type,Signal,Date,Time,Price
1,Entry,Long,2025-11-01,09:30:00,25550.0
1,Exit,Long,2025-11-01,15:00:00,25600.0
2,Entry,Short,2025-11-02,10:15:00,25650.0
2,Exit,Short,2025-11-02,14:30:00,25620.0
```

**Key Points:**
- Each trade has 2 rows: Entry and Exit
- Trade # must match for Entry/Exit pairs
- Times must be in IST (Indian Standard Time)
- Prices are NIFTY spot prices

---

## Configuring Parameters

### Sidebar Controls

#### 1. Upstox API Credentials

**API Key**: Your application identifier
- Get from Upstox Developer Portal
- Format: Alphanumeric string
- Example: `abc123def456`

**API Secret**: Authentication secret
- Never share publicly
- Store securely
- Example: `secret_xyz789`

**Access Token**: Session token
- Valid for 24 hours
- Must regenerate daily
- Example: `eyJhbGc...`

#### 2. Expiry Weekday

**What it is**: Day of week when options expire

**Options**:
- Monday
- Tuesday
- Wednesday
- **Thursday** ⭐ (Default - NIFTY weekly options)
- Friday

**Example**:
- Set to ""Thursday"" for NIFTY weekly options
- Set to ""Friday"" for BANKNIFTY weekly options

#### 3. Rollover Day

**What it is**: Day after which trades use next week's expiry

**Logic**:
- Trades before rollover day → Use current week expiry
- Trades on/after rollover day → Use next week expiry

**Example with Rollover = Tuesday**:
| Entry Day | Expiry Used |
|-----------|-------------|
| Monday | This Thursday |
| Tuesday | Next Thursday |
| Wednesday | Next Thursday |
| Thursday | Next Thursday |

**Why it matters**:
- Controls when to roll over to new contracts
- Affects premium decay and liquidity
- Align with your trading strategy

#### 4. Moneyness Mode

**ATM (At The Money)** ⭐ Default
- Strike closest to current NIFTY price
- Most liquid options
- Balanced risk/reward

**ITM1 (In The Money by 1 strike)**
- CALL: ATM + 100 (higher strike)
- PUT: ATM - 100 (lower strike)
- More intrinsic value
- Less time decay

**OTM1 (Out of The Money by 1 strike)**
- CALL: ATM - 50 (lower strike)
- PUT: ATM + 50 (higher strike)
- More leverage
- Higher risk

**Strike Calculation Examples**:

NIFTY Price: 25,574.40

| Mode | CALL Strike | PUT Strike |
|------|------------|-----------|
| ATM | 25,600 | 25,550 |
| ITM1 | 25,700 | 25,450 |
| OTM1 | 25,550 | 25,600 |

#### 5. Lot Size

**Default**: 75 (NIFTY lot size)

**Affects**:
- Total P&L calculation
- Position sizing
- Capital requirement

**Example**:
- Option P&L per lot: ₹15
- Lot size: 75
- Total P&L: 15 × 75 = ₹1,125

#### 6. Data Interval

**1minute** (More accurate)
- Better price precision
- Slower API calls
- Use for short-term strategies

**5minute** ⭐ (Recommended)
- Faster processing
- Good enough accuracy
- Less API load
- Use for most strategies

---

## Running Backtests

### Step-by-Step Process

#### 1. Upload File

1. Click ""Browse files"" or drag-and-drop
2. Select your TradingView .xlsx file
3. Wait for upload confirmation
4. Review raw data preview

**What to check**:
- ✅ All columns present
- ✅ Trade numbers sequential
- ✅ Entry/Exit pairs match
- ✅ Dates are valid

#### 2. Review Parsed Data

After upload, the system shows:
- **Parsed Trades Table**: Entry/Exit paired
- **Total Trades**: Count of trade pairs
- **Option Types**: CALL for Long, PUT for Short

**Verification**:
- Check if trade count is correct
- Verify Direction assignment
- Ensure dates are parsed correctly

#### 3. Configure Parameters

Set all parameters in sidebar:
- Enter API credentials
- Choose expiry and rollover days
- Select moneyness mode
- Set lot size
- Choose data interval

#### 4. Click ""Run Backtest""

**What happens**:
1. ⏳ Initializing Upstox API
2. ⏳ Calculating expiry dates
3. ⏳ Processing trades (shows progress)
4. ⏳ Fetching option prices from API
5. ⏳ Calculating P&L
6. ✅ Backtest completed!

**Duration**: 
- Depends on number of trades
- ~1-2 seconds per trade
- 50 trades ≈ 1-2 minutes

#### 5. View Results

Switch to ""Results & Analysis"" tab:
- See complete trade table
- Download CSV/Excel
- Review all metrics

---

## Understanding Results

### Results Table

Each row contains:

**Trade Information**:
- `Trade #`: Sequential identifier
- `Entry Date/Time`: When position opened
- `Exit Date/Time`: When position closed
- `Expiry Date`: Option expiry used

**Option Details**:
- `Option Type`: CALL or PUT
- `Strike Price`: Selected strike
- `NIFTY Entry/Exit`: Spot prices
- `Option Entry/Exit`: Option prices

**P&L Metrics**:
- `P&L (NIFTY)`: Strategy P&L from TradingView
- `P&L per Lot`: Option P&L per lot
- `P&L (Options)`: Total P&L (per lot × lot size)

### Performance Metrics

#### Key Statistics

**Total Trades**: Count of all trades
- Shows sample size
- More trades = more reliable results

**Win Rate**: Percentage of winning trades
- Formula: (Winning Trades / Total Trades) × 100
- Good: > 50%
- Excellent: > 60%

**Total P&L**:
- Options: Actual simulated P&L
- NIFTY: Strategy P&L from TradingView
- Compare to see effectiveness

**Average Profit/Loss**:
- Avg Profit: Mean of all winning trades
- Avg Loss: Mean of all losing trades
- Profit should be > Loss for profitability

**Max Drawdown**:
- Largest peak-to-trough decline
- Risk metric
- Lower is better

**Profit Factor**:
- Gross Profit / Gross Loss
- > 1.0 = Profitable
- > 1.5 = Good
- > 2.0 = Excellent

### Charts and Visualizations

#### 1. Equity Curve

**What it shows**:
- Cumulative P&L over time
- Overall performance trajectory
- Drawdown periods

**How to read**:
- ↗ Upward trend = Profitable
- Smooth curve = Consistent
- Sharp drops = Significant losses
- Compare Options vs NIFTY lines

#### 2. P&L Distribution

**What it shows**:
- Histogram of trade outcomes
- Distribution of wins/losses
- Outlier identification

**How to read**:
- Peak at positive = More winners
- Wide distribution = Variable results
- Symmetry = Consistent sizing

#### 3. P&L by Trade

**What it shows**:
- Bar chart of individual trades
- Green = Profit
- Red = Loss

**How to read**:
- Identify winning/losing streaks
- Spot outlier trades
- Assess consistency

### Downloading Reports

#### CSV Export
- Quick and simple
- Open in Excel/Google Sheets
- Good for further analysis

#### Excel Export
Multiple sheets:
1. **Trades**: Full trade details
2. **Summary**: Key metrics
3. **Monthly**: Month-by-month breakdown
4. **Win-Loss**: Detailed analysis

**Use for**:
- Comprehensive reporting
- Client presentations
- Strategy comparison

---

## Best Practices

### 1. Data Quality

✅ **DO**:
- Use clean TradingView exports
- Verify all trades have Entry/Exit
- Check for data gaps
- Test with small dataset first

❌ **DON'T**:
- Use incomplete data
- Mix different strategies
- Include manual trades
- Skip data validation

### 2. Parameter Selection

✅ **DO**:
- Start with ATM for baseline
- Use Thursday expiry for NIFTY
- Set rollover based on strategy
- Test different configurations

❌ **DON'T**:
- Change multiple parameters at once
- Use unrealistic lot sizes
- Ignore rollover logic
- Skip parameter documentation

### 3. API Usage

✅ **DO**:
- Keep access token updated
- Monitor API rate limits
- Cache results when possible
- Handle errors gracefully

❌ **DON'T**:
- Share API credentials
- Commit tokens to Git
- Exceed rate limits
- Ignore API errors

### 4. Result Analysis

✅ **DO**:
- Compare Options vs NIFTY P&L
- Check win rate AND profit factor
- Review equity curve smoothness
- Analyze drawdown periods

❌ **DON'T**:
- Focus only on total P&L
- Ignore risk metrics
- Overlook consistency
- Skip outlier analysis

### 5. Backtesting Discipline

✅ **DO**:
- Test multiple time periods
- Run sensitivity analysis
- Document assumptions
- Keep realistic expectations

❌ **DON'T**:
- Cherry-pick best results
- Overfit to historical data
- Ignore transaction costs
- Assume past = future

---

## Advanced Usage

### Testing Different Scenarios

#### Scenario 1: Compare Moneyness

Run 3 backtests with same data:
1. ATM mode
2. ITM1 mode
3. OTM1 mode

**Compare**:
- Total P&L
- Win rate
- Risk metrics

**Learn**: Which moneyness suits your strategy

#### Scenario 2: Rollover Impact

Test different rollover days:
- Monday rollover
- Tuesday rollover
- Wednesday rollover

**Observe**: Impact on expiry selection and P&L

#### Scenario 3: Multiple Strategies

Upload different TradingView strategies:
- Trend following
- Mean reversion
- Breakout
- Range trading

**Compare**: Which converts best to options

### Analyzing Results

#### Create Custom Reports

1. Download CSV
2. Import to Excel/Python
3. Add custom calculations:
   - Sharpe ratio
   - Sortino ratio
   - Win/loss streaks
   - Time-based analysis

#### Monthly Performance

Use Excel report's Monthly sheet:
- Identify best/worst months
- Seasonal patterns
- Consistency metrics

#### Trade Clustering

Analyze:
- Time of day patterns
- Day of week performance
- Winning streak lengths
- Drawdown recovery time

### Strategy Optimization

#### Step 1: Baseline

Run with default parameters:
- ATM
- Thursday expiry
- Tuesday rollover
- 75 lot size

Document results.

#### Step 2: Single Variable

Change one parameter:
- Test ITM1
- Keep others same
- Compare to baseline

#### Step 3: Combination

Test promising combinations:
- ITM1 + Monday rollover
- OTM1 + Wednesday rollover

#### Step 4: Selection

Choose configuration with:
- Best risk-adjusted returns
- Acceptable drawdown
- Consistent performance

---

## Tips and Tricks

### Speed Up Backtests

1. Use 5-minute interval
2. Cache instrument data
3. Process smaller batches
4. Run during off-peak hours

### Improve Accuracy

1. Use 1-minute interval for precise entry/exit
2. Verify expiry dates manually
3. Cross-check sample trades
4. Review outlier trades

### Handle Errors

**""No instrument found""**:
- Check if expiry date is valid
- Verify strike is available
- Use ATM mode for testing

**""API rate limit""**:
- Wait 1 minute
- Reduce trade count
- Use 5-minute interval

**""Access token expired""**:
- Generate new token daily
- Update in sidebar
- Save in config file

### Organize Your Work

```
my_backtests/
├── strategy_a/
│   ├── tradingview_export.xlsx
│   ├── results_atm.csv
│   ├── results_itm.csv
│   └── analysis.xlsx
├── strategy_b/
│   └── ...
└── summary_report.xlsx
```

---

## Keyboard Shortcuts

### Streamlit Commands

- `Ctrl + R`: Rerun app
- `Ctrl + C`: Stop server (in terminal)
- `Ctrl + Shift + R`: Hard refresh browser

### Browser Shortcuts

- `F5`: Refresh page
- `Ctrl + F5`: Clear cache and refresh
- `Ctrl + +/-`: Zoom in/out
- `Ctrl + 0`: Reset zoom

---

## Common Workflows

### Workflow 1: Quick Test

1. Upload file
2. Keep default parameters
3. Run backtest
4. Review results
5. Download CSV

**Time**: 5-10 minutes

### Workflow 2: Comprehensive Analysis

1. Upload file
2. Run with ATM (baseline)
3. Run with ITM1
4. Run with OTM1
5. Compare all three
6. Generate Excel reports
7. Analyze in depth

**Time**: 30-45 minutes

### Workflow 3: Strategy Validation

1. Export multiple strategies from TradingView
2. Run backtests for each
3. Create comparison spreadsheet
4. Rank by risk-adjusted returns
5. Select best strategy

**Time**: 1-2 hours

---

## FAQ

**Q: How often should I regenerate access token?**
A: Daily. Upstox tokens expire in 24 hours.

**Q: Can I backtest BankNIFTY?**
A: Not in current version. Coming in Phase 2.

**Q: Why are my results different from TradingView?**
A: Options P&L differs from futures/spot P&L due to:
- Time decay
- Strike selection
- Liquidity
- Option Greeks

**Q: How accurate are the option prices?**
A: Very accurate when using Upstox API. Uses actual historical data.

**Q: Can I run multiple backtests in parallel?**
A: Not recommended. May hit API rate limits.

**Q: How do I save my configuration?**
A: Use `config/credentials.json` for API keys. Other parameters must be set each time.

**Q: Can I modify the code?**
A: Yes! It's open source. Check `core/` modules.

---

## Next Steps

1. ✅ Master basic workflow
2. ✅ Test different parameters
3. ✅ Analyze multiple strategies
4. ✅ Create custom reports
5. ✅ Share feedback

**Happy Backtesting! 📈**

*For technical issues, see SETUP.md and README.md*
