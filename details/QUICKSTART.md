# Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Extract Files (1 min)
Extract all files to a folder on your computer.

### Step 2: Install (2 min)

**Windows:**
```
Double-click install.bat
```

**macOS/Linux:**
```bash
bash install.sh
```

### Step 3: Configure API (1 min)
Edit `config/credentials.json`:
```json
{
    ""api_key"": ""your_key"",
    ""api_secret"": ""your_secret"",
    ""access_token"": ""your_token""
}
```

### Step 4: Run (1 min)
```bash
# Activate virtual environment
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Run app
streamlit run app.py
```

### Step 5: Test
1. Upload sample file from `data/sample_tradingview_export.csv`
2. Click ""Run Backtest""
3. View results!

## 📚 Full Documentation

- **README.md**: Project overview
- **SETUP.md**: Detailed setup instructions
- **USER_GUIDE.md**: Complete usage guide

## 🆘 Need Help?

1. Check SETUP.md for troubleshooting
2. Review USER_GUIDE.md for usage tips
3. Test with sample data first

**Enjoy backtesting! 📈**
