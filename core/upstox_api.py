"""
Production Upstox API wrapper for option backtesting
- Auto-detects expired vs live options
- Uses /v2/option/chain for live options
- Uses /v2/expired-instruments for expired options
- Robust error handling and caching
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json

class UpstoxAPI:
    """Unified Upstox API for live and expired option data"""
    
    BASE_URL = "https://api.upstox.com/v2"
    
    def __init__(self, api_key, api_secret, access_token):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        self.expired_cache = {}
        self.live_chain_cache = {}
        
        print(f"🔐 Initializing Upstox API...")
        if self.test_connection():
            print(f"✅ Connected! Auto-detecting expired/live options")
        else:
            raise RuntimeError("❌ Connection failed - check access token")
    
    def test_connection(self):
        """Test API connection"""
        try:
            url = f"{self.BASE_URL}/user/profile"
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                user_name = data['data'].get('user_name', 'Unknown')
                is_plus = data['data'].get('is_plus_user', False)
                print(f"   👤 {user_name}")
                if is_plus:
                    print(f"   ✅ Upstox Plus Active")
                return True
            else:
                print(f"   ❌ Connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    def is_expired(self, expiry_date, trade_date):
        """Check if option is expired relative to trade date"""
        expiry = pd.to_datetime(expiry_date).date()
        trade = pd.to_datetime(trade_date).date()
        return trade > expiry
    
    def get_historical_option_price(self, timestamp, expiry, strike, option_type, interval='1minute'):
        """
        Main method: Get historical option price
        Auto-detects if option is expired or live
        """
        
        try:
            # Parse dates
            timestamp_dt = pd.to_datetime(timestamp)
            expiry_dt = pd.to_datetime(expiry)
            today = pd.Timestamp.now().normalize()
            
            # Check if expired
            is_expired = expiry_dt.date() < today.date()
            
            if is_expired:
                if self.verbose_print:
                    print(f"📜 EXPIRED option ({expiry_dt.date()})")
                return self._get_expired_option_price(timestamp_dt, expiry_dt, strike, option_type, interval)
            else:
                if self.verbose_print:
                    print(f"📡 LIVE option ({expiry_dt.date()})")
                return self._get_live_option_price(timestamp_dt, expiry_dt, strike, option_type, interval)
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            raise e
    
    @property
    def verbose_print(self):
        """Enable verbose printing for debugging"""
        return True
    
    # ================== EXPIRED OPTIONS ==================
    
    def _get_expired_option_price(self, timestamp, expiry, strike, option_type, interval):
        """Handle expired options with fallback to next-week expiry if not archived yet."""
        
        # Validate timestamp is before (or same week as) expiry
        if timestamp.date() > expiry.date():
            raise ValueError(f"Timestamp {timestamp.date()} is after expiry {expiry.date()}")

        # First try original expiry
        contracts = self._get_expired_contracts(expiry)

        # If not archived, try next-week expiry once
        if len(contracts) == 0:
            print(f"   ⚠️ No expired contracts for {expiry.date()} - trying next-week expiry")
            next_week_expiry = expiry + pd.Timedelta(days=7)
            contracts = self._get_expired_contracts(next_week_expiry)

            if len(contracts) == 0:
                # still nothing → give up
                raise ValueError(f"No expired contracts for {expiry.date()} or {next_week_expiry.date()} - not archived yet")

            # use next-week expiry for the rest of the logic
            expiry = next_week_expiry

        # Find instrument key
        instrument_key = self._find_expired_instrument_key(contracts, strike, option_type)

        # Get candles
        candles = self._get_expired_candles(instrument_key, timestamp, interval)

        if len(candles) == 0:
            raise ValueError("No expired candles available")

        price = self._find_closest_price(candles, timestamp)
        return price

    
    def _get_expired_contracts(self, expiry):
        """Get expired contracts for a specific expiry"""
        
        expiry_str = expiry.strftime('%Y-%m-%d')
        
        # Check cache
        if expiry_str in self.expired_cache:
            print(f"   📦 Using cached expired contracts")
            return self.expired_cache[expiry_str]
        
        try:
            print(f"📥 Fetching expired contracts for {expiry_str}...")
            
            url = f"{self.BASE_URL}/expired-instruments/option/contract"
            params = {
                'instrument_key': 'NSE_INDEX|Nifty 50',
                'expiry_date': expiry_str
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                contracts = data.get('data', [])
                
                if len(contracts) > 0:
                    df = pd.DataFrame(contracts)
                    self.expired_cache[expiry_str] = df
                    print(f"   ✅ Loaded {len(df)} expired contracts")
                    return df
                else:
                    print(f"   ⚠️ No expired contracts (not archived yet)")
                    return pd.DataFrame()
            else:
                print(f"   ⚠️ API Error: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"   ⚠️ Error: {str(e)}")
            return pd.DataFrame()
    
    def _find_expired_instrument_key(self, contracts, strike, option_type):
        """Find instrument key in expired contracts"""
        
        opt_type = 'CE' if option_type.upper() in ('CALL', 'CE') else 'PE'
        strike_val = float(strike)
        
        print(f"🔍 Looking for: {opt_type} {int(strike_val)}")
        
        # Exact match
        filtered = contracts[
            (contracts['strike_price'] == strike_val) &
            (contracts['instrument_type'] == opt_type)
        ]
        
        if len(filtered) > 0:
            key = filtered.iloc[0]['instrument_key']
            symbol = filtered.iloc[0]['trading_symbol']
            print(f"   ✅ Found: {symbol}")
            return key
        
        # Closest strike
        print(f"   Trying closest strike...")
        same_type = contracts[contracts['instrument_type'] == opt_type].copy()
        
        if len(same_type) > 0:
            same_type['diff'] = abs(same_type['strike_price'] - strike_val)
            closest = same_type.sort_values('diff').iloc[0]
            key = closest['instrument_key']
            symbol = closest['trading_symbol']
            actual = closest['strike_price']
            print(f"   ⚠️ Using closest: {symbol} (Strike {actual})")
            return key
        
        raise ValueError(f"No {opt_type} options found")
    
    def _get_expired_candles(self, instrument_key, timestamp, interval):
        """Get expired candles"""
        
        to_date = timestamp.strftime('%Y-%m-%d')
        from_date = (timestamp - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"📡 Fetching expired candles from {from_date} to {to_date}")
        
        url = f"{self.BASE_URL}/expired-instruments/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                candles = data.get('data', {}).get('candles', [])
                print(f"   ✅ Got {len(candles)} candles")
                return candles
            else:
                print(f"   ⚠️ Status: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ⚠️ Error: {str(e)}")
            return []


    def get_nifty_spot_price(self, timestamp, interval="1minute"):
        """
        Get NIFTY 50 spot price (index) at closest candle to timestamp.
        Uses NSE_INDEX|Nifty 50 via historical-candle API.
        """
        instrument_key = "NSE_INDEX|Nifty 50"
        ts = pd.to_datetime(timestamp)
        to_date = ts.strftime("%Y-%m-%d")
        from_date = (ts - pd.Timedelta(days=1)).strftime("%Y-%m-%d")

        url = f"{self.BASE_URL}/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        print(f"📡 Fetching NIFTY spot from {from_date} to {to_date}")
        r = requests.get(url, headers=self.headers, timeout=15)
        if r.status_code != 200:
            raise ValueError(f"NIFTY spot API error: {r.status_code}")

        data = r.json()
        candles = data.get("data", {}).get("candles", [])
        if not candles:
            raise ValueError("No NIFTY spot candles returned")

        # reuse price finder
        return float(self._find_closest_price(candles, ts))

    # ================== LIVE OPTIONS ==================
    
    def _get_live_option_price(self, timestamp, expiry, strike, option_type, interval):
        """Handle live (non-expired) options"""
        
        # Get instrument key from option chain
        instrument_key = self._find_live_instrument_key(expiry, strike, option_type)
        
        # Get candles
        candles = self._get_live_candles(instrument_key, timestamp, interval)
        
        if len(candles) == 0:
            raise ValueError("No live candles available")
        
        # Extract price
        price = self._find_closest_price(candles, timestamp)
        
        return price
    
    def _find_live_instrument_key(self, expiry, strike, option_type):
        """Find instrument key from live option chain"""
        
        expiry_str = expiry.strftime('%Y-%m-%d')
        
        # Check cache
        cache_key = f"{expiry_str}_{strike}_{option_type}"
        if cache_key in self.live_chain_cache:
            print(f"   📦 Using cached live instrument")
            return self.live_chain_cache[cache_key]
        
        try:
            print(f"📡 Fetching live option chain for {expiry_str}...")
            
            url = f"{self.BASE_URL}/option/chain"
            params = {
                'instrument_key': 'NSE_INDEX|Nifty 50',
                'expiry_date': expiry_str
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code != 200:
                raise ValueError(f"Option chain API error: {response.status_code}")
            
            data = response.json()
            
            # Parse response (handle different formats)
            if isinstance(data, dict):
                rows = data.get('data', [])
            elif isinstance(data, list):
                rows = data
            else:
                raise ValueError("Unexpected option chain format")
            
            if not isinstance(rows, list):
                raise ValueError("Option chain data is not a list")
            
            # Find strike
            opt_field = 'call_options' if option_type.upper() in ('CALL', 'CE') else 'put_options'
            strike_val = float(strike)
            
            print(f"🔍 Looking for: {option_type} {int(strike_val)}")
            
            for row in rows:
                try:
                    row_strike = float(row.get('strike_price', float('nan')))
                except:
                    continue
                
                # Exact match
                if abs(row_strike - strike_val) < 0.01:
                    opt_data = row.get(opt_field)
                    
                    # Handle different formats
                    if isinstance(opt_data, dict):
                        inst_key = opt_data.get('instrument_key')
                    elif isinstance(opt_data, list) and len(opt_data) > 0:
                        inst_key = opt_data[0].get('instrument_key')
                    else:
                        continue
                    
                    if inst_key:
                        print(f"   ✅ Found live instrument: {inst_key}")
                        self.live_chain_cache[cache_key] = inst_key
                        return inst_key
            
            raise ValueError(f"No live instrument found for {option_type} {strike_val}")
            
        except Exception as e:
            print(f"   ⚠️ Error: {str(e)}")
            raise e
    
    def _get_live_candles(self, instrument_key, timestamp, interval):
        """Get live candles"""
        
        to_date = timestamp.strftime('%Y-%m-%d')
        from_date = (timestamp - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"📡 Fetching live candles from {from_date} to {to_date}")
        
        url = f"{self.BASE_URL}/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                candles = data.get('data', {}).get('candles', [])
                print(f"   ✅ Got {len(candles)} candles")
                return candles
            else:
                print(f"   ⚠️ Status: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ⚠️ Error: {str(e)}")
            return []
    
    # ================== COMMON UTILITIES ==================
    
    def _find_closest_price(self, candles, target_timestamp):
        """Find price from candle closest to target timestamp"""
        
        if len(candles) == 0:
            raise ValueError("No candles")
        
        # Convert to DataFrame
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        
        # Target timestamp
        target = pd.to_datetime(target_timestamp)
        if target.tz is not None:
            target = target.tz_localize(None)
        
        # Filter market hours (9:15 AM to 3:30 PM)
        df = df[
            (df['timestamp'].dt.hour >= 9) & 
            (df['timestamp'].dt.hour <= 15) &
            ~((df['timestamp'].dt.hour == 9) & (df['timestamp'].dt.minute < 15)) &
            ~((df['timestamp'].dt.hour == 15) & (df['timestamp'].dt.minute > 30))
        ]
        
        if len(df) == 0:
            raise ValueError("No market hours candles")
        
        # Find closest
        df['time_diff'] = abs(df['timestamp'] - target)
        closest_idx = df['time_diff'].idxmin()
        
        row = df.loc[closest_idx]
        price = row['close']
        
        print(f"   📊 {row['timestamp'].strftime('%H:%M')}: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")
        
        return price
# # -------------------------- Example usage --------------------------
# if __name__ == '__main__':  
#     # Replace with your access token        
#     ACCESS_TOKEN = "YOUR_REAL_ACCESS_TOKEN_HERE"    
#     api = UpstoxAPI(
#         api_key="upstox_API_KEY", 
#         api_secret="upstox_API_SECRET",
#         access_token=ACCESS_TOKEN
#     )
#     print('\n-- LIVE OPTION EXAMPLE (non-expired) --')

#     try:
#         p = api.get_historical_option_price(
#             timestamp='2025-11-19 10:40:00', # Adjust date as needed
#             expiry='2025-11-25', # Adjust expiry as needed
#             strike=26000, # Adjust strike as needed
#             option_type='CALL',
#             interval='1minute'
#         )
#         print(f"   🎯 Price: {p:.2f}")
#     except Exception as e:
#         print(f"   ⚠️ Error fetching price: {e}")
#     print('\n-- EXPIRED OPTION EXAMPLE --')
#     try:
#         p = api.get_historical_option_price(
#             timestamp='2025-11-04 11:30:00', # Adjust date as needed
#             expiry='2025-11-11', # Adjust expiry as needed
#             strike=26000, # Adjust strike as needed
#             option_type='CALL',
#             interval='1minute'
#         )
#         print(f"   🎯 Price: {p:.2f}")
#     except Exception as e:
#         print(f"   ⚠️ Error fetching price: {e}")   
