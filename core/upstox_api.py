import requests
import pandas as pd
from datetime import datetime, timedelta
import json

class UpstoxAPI:
    """Wrapper for Upstox API interactions"""
    
    BASE_URL = "https://api.upstox.com/v2"
    
    def __init__(self, api_key, api_secret, access_token):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        self.instruments = None
    
    def load_instruments(self):
        """Load instrument master file from Upstox"""
        
        try:
            # Download NSE FO instruments
            url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE_FO.csv"
            df = pd.read_csv(url)
            self.instruments = df
            return df
        except Exception as e:
            print(f"Error loading instruments: {e}")
            return None
    
    def find_option_instrument(self, expiry, strike, option_type):
        """
        Find option instrument key
        
        Args:
            expiry: Expiry date
            strike: Strike price
            option_type: 'CALL' or 'PUT' (will be converted to CE/PE)
            
        Returns:
            str: Instrument key
        """
        
        if self.instruments is None:
            self.load_instruments()
        
        # Convert option type
        opt_type = 'CE' if option_type == 'CALL' else 'PE'
        
        # Format expiry date
        if isinstance(expiry, str):
            expiry = pd.to_datetime(expiry)
        expiry_str = expiry.strftime('%Y-%m-%d')
        
        # Filter instruments
        filtered = self.instruments[
            (self.instruments['name'] == 'NIFTY') &
            (self.instruments['expiry'] == expiry_str) &
            (self.instruments['strike'] == strike) &
            (self.instruments['instrument_type'] == opt_type)
        ]
        
        if len(filtered) > 0:
            return filtered.iloc[0]['instrument_key']
        else:
            return None
    
    def get_historical_option_price(self, timestamp, expiry, strike, option_type, interval='1minute'):
        """
        Fetch historical option price at specific timestamp
        
        Args:
            timestamp: DateTime when to fetch price
            expiry: Option expiry date
            strike: Strike price
            option_type: 'CALL' or 'PUT'
            interval: Data interval (1minute, 5minute, etc.)
            
        Returns:
            float: Option price
        """
        
        try:
            # Find instrument key
            instrument_key = self.find_option_instrument(expiry, strike, option_type)
            
            if instrument_key is None:
                raise ValueError(f"Instrument not found for {strike} {option_type} {expiry}")
            
            # Format dates for API
            if isinstance(timestamp, str):
                timestamp = pd.to_datetime(timestamp)
            
            from_date = (timestamp - timedelta(days=1)).strftime('%Y-%m-%d')
            to_date = (timestamp + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Call Upstox API
            url = f"{self.BASE_URL}/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and 'candles' in data['data']:
                    candles = data['data']['candles']
                    
                    # Find candle closest to timestamp
                    price = self.find_closest_price(candles, timestamp)
                    return price
                else:
                    raise ValueError("No candle data found")
            else:
                raise ValueError(f"API error: {response.status_code}")
                
        except Exception as e:
            # If API call fails, raise exception to trigger mock data
            raise e
    
    def find_closest_price(self, candles, target_timestamp):
        """Find price from candle closest to target timestamp"""
        
        # Convert candles to DataFrame
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Find closest timestamp
        df['time_diff'] = abs(df['timestamp'] - target_timestamp)
        closest_idx = df['time_diff'].idxmin()
        
        # Return average of open and close
        row = df.loc[closest_idx]
        return (row['open'] + row['close']) / 2
    
    def test_connection(self):
        """Test API connection"""
        
        try:
            url = f"{self.BASE_URL}/user/profile"
            response = requests.get(url, headers=self.headers)
            return response.status_code == 200
        except:
            return False
# # Example usage
# if __name__ == "__main__":
#     api_key = "your_api_key"
#     api_secret = "your_api_secret"
#     access_token = "your_access_token"

#     upstox_api = UpstoxAPI(api_key, api_secret, access_token)       
#     if upstox_api.test_connection():
#         print("Connection successful")
#         price = upstox_api.get_historical_option_price(
#             timestamp="2024-06-01 10:30:00",
#             expiry="2024-06-27",
#             strike=17500,
#             option_type="CALL",
#             interval="1minute"
#         )
#         print(f"Option Price: {price}")
#     else:
#         print("Connection failed")
#         # Handle connection failure 
#         # (e.g., use mock data or notify user)