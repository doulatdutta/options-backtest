# 🔧 Setup Instructions

Complete step-by-step guide to set up the Options Backtesting Platform.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Python Installation](#python-installation)
3. [Project Setup](#project-setup)
4. [Upstox API Setup](#upstox-api-setup)
5. [Running the Application](#running-the-application)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11 (64-bit), macOS 10.14+, or Linux
- **RAM**: 8 GB
- **Storage**: 500 MB free space
- **Internet**: Stable connection (for API calls)

### Software Requirements
- **Python**: Version 3.11 or higher
- **pip**: Python package installer (comes with Python)
- **Excel**: For viewing reports (optional)

---

## Python Installation

### Windows

1. **Download Python**
   - Visit https://www.python.org/downloads/
   - Download Python 3.11 or later
   - **Important**: Check ""Add Python to PATH"" during installation

2. **Verify Installation**
   ```cmd
   python --version
   pip --version
   ```

### macOS

1. **Using Homebrew** (recommended)
   ```bash
   brew install python@3.11
   ```

2. **Or download from python.org**
   - Visit https://www.python.org/downloads/macos/
   - Download and install

3. **Verify Installation**
   ```bash
   python3 --version
   pip3 --version
   ```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.11 python3-pip
```

Verify:
```bash
python3 --version
pip3 --version
```

---

## Project Setup

### Step 1: Extract Project Files

Extract the `options_backtester` folder to your desired location:
```
C:\Users\YourName\Documents\options_backtester    # Windows
~/Documents/options_backtester                        # macOS/Linux
```

### Step 2: Open Terminal/Command Prompt

**Windows:**
- Press `Win + R`
- Type `cmd` and press Enter
- Navigate to project folder:
  ```cmd
  cd C:\Users\YourName\Documents\options_backtester
  ```

**macOS/Linux:**
- Open Terminal
- Navigate to project folder:
  ```bash
  cd ~/Documents/options_backtester
  ```

### Step 3: Create Virtual Environment (Recommended)

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your command prompt.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- streamlit (Dashboard framework)
- pandas (Data manipulation)
- openpyxl (Excel reading/writing)
- requests (API calls)
- plotly (Interactive charts)
- numpy (Numerical computing)
- pytz (Timezone handling)

**Installation time**: 2-5 minutes depending on internet speed

### Step 5: Verify Installation

```bash
pip list
```

Ensure all packages from requirements.txt are listed.

---

## Upstox API Setup

### Step 1: Create Upstox Account

1. Visit https://upstox.com/
2. Sign up for an account
3. Complete KYC verification (if trading)

### Step 2: Register for API Access

1. Go to https://upstox.com/developer/apps
2. Click ""Create App""
3. Fill in details:
   - **App Name**: Options Backtester
   - **Redirect URL**: http://localhost:8501
   - **Description**: Options backtesting platform
4. Submit and wait for approval

### Step 3: Get Credentials

After approval, you'll receive:
- **API Key**: Your application identifier
- **API Secret**: Secret key for authentication

### Step 4: Generate Access Token

1. **Authorization URL**:
   ```
   https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id=YOUR_API_KEY&redirect_uri=http://localhost:8501
   ```
   Replace `YOUR_API_KEY` with your actual API key

2. **Login and Authorize**:
   - Visit the URL in browser
   - Login with Upstox credentials
   - Authorize the app
   - You'll be redirected with a `code` parameter

3. **Get Access Token**:
   Use the code to get access token via API:
   ```bash
   curl -X POST https://api.upstox.com/v2/login/authorization/token \
     -H ""Content-Type: application/x-www-form-urlencoded"" \
     -d ""code=YOUR_CODE"" \
     -d ""client_id=YOUR_API_KEY"" \
     -d ""client_secret=YOUR_API_SECRET"" \
     -d ""redirect_uri=http://localhost:8501"" \
     -d ""grant_type=authorization_code""
   ```

4. **Save Token**:
   The response contains `access_token`. This token is valid for 24 hours.

### Step 5: Configure Application

Edit `config/credentials.json`:
```json
{
    ""api_key"": ""your_actual_api_key"",
    ""api_secret"": ""your_actual_api_secret"",
    ""access_token"": ""your_actual_access_token""
}
```

**Security Note**: 
- Never commit credentials.json to version control
- Keep credentials secure
- Regenerate tokens if compromised

---

## Running the Application

### Step 1: Activate Virtual Environment

**Windows:**
```cmd
cd C:\Users\YourName\Documents\options_backtester
venv\Scripts\activate
```

**macOS/Linux:**
```bash
cd ~/Documents/options_backtester
source venv/bin/activate
```

### Step 2: Start Streamlit

```bash
streamlit run app.py
```

### Step 3: Open Browser

The application should automatically open in your browser at:
```
http://localhost:8501
```

If it doesn't open automatically, visit the URL manually.

### Step 4: Stop Application

Press `Ctrl+C` in the terminal to stop the server.

---

## Verification

### Test 1: Application Loads

✅ Streamlit dashboard opens in browser
✅ Sidebar shows configuration options
✅ Main page shows upload area

### Test 2: File Upload

1. Prepare a sample TradingView export
2. Upload via the file uploader
3. Check if data preview appears

### Test 3: API Connection

1. Enter credentials in sidebar
2. Click ""Run Backtest""
3. Check for connection errors

If everything works, you're ready to backtest!

---

## Troubleshooting

### Issue: ""Command not found: streamlit""

**Cause**: Streamlit not installed or virtual environment not activated

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall
pip install streamlit
```

### Issue: ""ModuleNotFoundError: No module named 'pandas'""

**Cause**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: ""Port 8501 is already in use""

**Cause**: Another Streamlit instance is running

**Solution**:
```bash
# Kill existing process
# Windows: Open Task Manager, end Python processes
# macOS/Linux:
lsof -ti:8501 | xargs kill -9

# Or use different port
streamlit run app.py --server.port 8502
```

### Issue: ""Invalid API credentials""

**Cause**: Wrong credentials or expired token

**Solution**:
1. Verify credentials in `config/credentials.json`
2. Generate new access token (expires in 24 hours)
3. Update the JSON file

### Issue: ""Permission denied"" (macOS/Linux)

**Cause**: File permissions

**Solution**:
```bash
chmod +x app.py
chmod -R 755 core/
```

### Issue: Excel file not parsing

**Cause**: Wrong file format or missing columns

**Solution**:
1. Ensure file is .xlsx format
2. Check required columns:
   - Trade #
   - Type
   - Signal
   - Date
   - Time
   - Price
3. Export fresh file from TradingView

### Issue: Slow performance

**Solutions**:
1. Use 5-minute interval instead of 1-minute
2. Reduce number of trades
3. Check internet connection
4. Clear browser cache

### Issue: Charts not displaying

**Cause**: Plotly not installed or browser issue

**Solution**:
```bash
pip install plotly --upgrade
```
Then refresh browser (Ctrl+F5)

---

## Common Command Reference

### Virtual Environment

```bash
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Deactivate
deactivate
```

### Package Management

```bash
# Install all dependencies
pip install -r requirements.txt

# Install single package
pip install package_name

# Upgrade package
pip install package_name --upgrade

# List installed packages
pip list

# Show package info
pip show package_name
```

### Streamlit Commands

```bash
# Run app
streamlit run app.py

# Run on different port
streamlit run app.py --server.port 8502

# Run with specific config
streamlit run app.py --server.maxUploadSize 200

# Show Streamlit version
streamlit --version

# Clear cache
streamlit cache clear
```

---

## Next Steps

1. ✅ **Test with Sample Data**
   - Create a small TradingView export
   - Run a test backtest
   - Verify results

2. ✅ **Configure Parameters**
   - Experiment with different expiry settings
   - Try ATM/ITM/OTM modes
   - Adjust lot sizes

3. ✅ **Run Real Backtests**
   - Upload your actual TradingView strategies
   - Analyze results
   - Download reports

4. ✅ **Explore Features**
   - Review performance metrics
   - Study equity curves
   - Export to Excel

---

## Additional Resources

### Documentation
- **Streamlit**: https://docs.streamlit.io/
- **Upstox API**: https://upstox.com/developer/api-documentation/
- **Pandas**: https://pandas.pydata.org/docs/
- **Plotly**: https://plotly.com/python/

### Getting Help
- Check README.md for usage guide
- Review code comments in core/ modules
- Test with provided sample data

---

## Updates and Maintenance

### Updating Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Updating Application

Replace files with new versions and restart:
```bash
# Stop app (Ctrl+C)
# Replace files
# Restart
streamlit run app.py
```

---

**Setup Complete! 🎉**

You're now ready to backtest your options strategies. Happy backtesting!

*Last updated: November 2025*
