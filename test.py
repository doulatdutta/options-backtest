"""
Unified Upstox option data helper
- Live option instrument lookup via /v2/option/chain (handles list-shaped responses)
- Fetches live historical candles via /v2/historical-candle/... for non-expired options
- Fetches expired contracts & candles via /v2/expired-instruments/... for expired options
- Single public method: get_option_price(timestamp, expiry, strike, option_type, interval='1minute')

Usage: replace ACCESS_TOKEN with your valid token and run the examples at the bottom.
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta


class UpstoxOptionAPI:
    BASE_URL = "https://api.upstox.com/v2"

    def __init__(self, access_token, instruments_cache_path='instruments.csv', verbose=True):
        self.access_token = access_token
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        self.verbose = verbose
        self.instruments_cache_path = instruments_cache_path
        self.instruments_df = None  # not used for live chain lookup but left for backward-compat
        self.expired_cache = {}

        if self.verbose:
            print("🔐 Initializing UpstoxOptionAPI...")
        # Try test connection
        if not self.test_connection():
            raise RuntimeError('Unable to connect to Upstox API. Check access token and network.')

        # load instruments if cache exists (legacy)
        if os.path.exists(self.instruments_cache_path):
            try:
                self.instruments_df = pd.read_csv(self.instruments_cache_path)
                if self.verbose:
                    print(f"   ✅ Loaded instruments from cache: {self.instruments_cache_path} ({len(self.instruments_df)} rows)")
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️ Failed reading instruments cache: {e}")
                self.instruments_df = None

    # -------------------------- Connection / Utilities --------------------------
    def test_connection(self):
        try:
            url = f"{self.BASE_URL}/user/profile"
            r = requests.get(url, headers=self.headers, timeout=6)
            if r.status_code == 200:
                if self.verbose:
                    try:
                        data = r.json()
                        print(f"   👤 {data['data'].get('user_name','Unknown')}")
                    except Exception:
                        print("   👤 Connected")
                return True
            if self.verbose:
                print(f"   ⚠️ Connection test failed: {r.status_code}")
            return False
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Connection error: {e}")
            return False

    def _today_date(self):
        return datetime.now().date()

    # -------------------------- Live option chain lookup (robust) --------------------------
    def find_live_instrument_key_via_chain(self, expiry, strike, option_type):
        """
        Robust lookup using /v2/option/chain which in practice returns JSON where
        'data' is a LIST of strike rows, each containing call_options / put_options.
        This function supports:
         - top-level dict with 'data' -> list
         - top-level list
         - call_options / put_options being dict or list
        Returns an instrument_key string (exact strike preferred; otherwise closest).
        """
        url = f"{self.BASE_URL}/option/chain"
        params = {
            "instrument_key": "NSE_INDEX|Nifty 50",  # fixed underlying (you confirmed NIFTY 50)
            "expiry_date": pd.to_datetime(expiry).strftime('%Y-%m-%d')
        }

        if self.verbose:
            print(f"📡 Requesting option chain for expiry {params['expiry_date']} (NIFTY 50)")

        r = requests.get(url, headers=self.headers, params=params, timeout=12)
        r.raise_for_status()

        json_data = r.json()

        # Normalize to list of strike rows
        if isinstance(json_data, dict):
            rows = json_data.get("data", [])
        elif isinstance(json_data, list):
            rows = json_data
        else:
            raise RuntimeError("Unexpected option chain response format")

        if not isinstance(rows, list):
            raise RuntimeError("Option chain 'data' is not a list")

        strike = float(strike)
        opt_field = "call_options" if option_type.upper() in ("CALL", "CE") else "put_options"

        # helper to extract instrument_key from call_options / put_options field
        def extract_inst_key(opt_field_value):
            """
            opt_field_value may be:
             - dict with 'instrument_key'
             - list of dicts each with 'instrument_key'
             - None
            """
            if opt_field_value is None:
                return None
            if isinstance(opt_field_value, dict):
                return opt_field_value.get("instrument_key")
            if isinstance(opt_field_value, list):
                # pick first dict with instrument_key
                for it in opt_field_value:
                    if isinstance(it, dict) and it.get("instrument_key"):
                        return it.get("instrument_key")
            return None

        closest_key = None
        closest_diff = float("inf")

        # iterate rows
        for row in rows:
            # row may be a dict with keys: strike_price, call_options, put_options, expiry...
            try:
                row_strike = float(row.get("strike_price", float("nan")))
            except Exception:
                # skip rows with bad strike
                continue

            # exact match: prefer exact strike
            if abs(row_strike - strike) < 1e-9:
                inst = extract_inst_key(row.get(opt_field))
                if inst:
                    if self.verbose:
                        print(f"   ✅ Exact strike row found: {row_strike}")
                    return inst

            # track closest strike that has a valid instrument_key
            inst = extract_inst_key(row.get(opt_field))
            if inst is not None:
                diff = abs(row_strike - strike)
                if diff < closest_diff:
                    closest_diff = diff
                    closest_key = inst

        # Fallback: return closest if found
        if closest_key is not None:
            if self.verbose:
                print(f"   ⚠️ Exact strike not present — using closest strike (diff={closest_diff})")
            return closest_key

        raise RuntimeError("No valid instrument key found in option chain for requested strike/type")

    # -------------------------- Live candles --------------------------
    def get_live_candles(self, instrument_key, from_dt, to_dt, interval='1minute'):
        """Fetch historical candles for a live instrument."""
        to_date = pd.to_datetime(to_dt).strftime('%Y-%m-%d')
        from_date = pd.to_datetime(from_dt).strftime('%Y-%m-%d')

        if self.verbose:
            print(f"📡 Fetching live candles for {instrument_key} from {from_date} to {to_date}")

        url = f"{self.BASE_URL}/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        try:
            r = requests.get(url, headers=self.headers, timeout=20)
            if r.status_code == 200:
                j = r.json()
                # Upstox historically returns {"data": {"candles": [...]}} or similar
                if isinstance(j, dict):
                    candles = j.get('data', {}).get('candles', [])
                elif isinstance(j, list):
                    # If they return a flat list, treat as candles list
                    candles = j
                else:
                    candles = []
                if self.verbose:
                    print(f"   ✅ Got {len(candles)} candles")
                return candles
            else:
                if self.verbose:
                    print(f"   ⚠️ Live candle fetch status: {r.status_code}")
                return []
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Live candle fetch error: {e}")
            return []

    # -------------------------- Expired instruments/candles --------------------------
    def get_expired_contracts(self, expiry_date, instrument_key_filter='NSE_INDEX|Nifty 50'):
        expiry_str = pd.to_datetime(expiry_date).strftime('%Y-%m-%d')
        if expiry_str in self.expired_cache:
            if self.verbose:
                print("   📦 Using cached expired contracts")
            return self.expired_cache[expiry_str]

        try:
            if self.verbose:
                print(f"📥 Fetching expired contracts for {expiry_str}...")

            url = f"{self.BASE_URL}/expired-instruments/option/contract"
            params = {
                'instrument_key': instrument_key_filter,
                'expiry_date': expiry_str
            }
            r = requests.get(url, headers=self.headers, params=params, timeout=15)
            if r.status_code == 200:
                data = r.json()
                recs = data.get('data', [])
                df = pd.DataFrame(recs)
                self.expired_cache[expiry_str] = df
                if self.verbose:
                    print(f"   ✅ Loaded {len(df)} expired contracts")
                return df
            else:
                if self.verbose:
                    print(f"   ⚠️ API Error: {r.status_code}")
                return pd.DataFrame()
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Error: {e}")
            return pd.DataFrame()

    def get_expired_candles(self, instrument_key, timestamp, interval='1minute'):
        ts = pd.to_datetime(timestamp)
        to_date = ts.strftime('%Y-%m-%d')
        from_date = (ts - timedelta(days=1)).strftime('%Y-%m-%d')

        if self.verbose:
            print(f"📡 Fetching expired candles from {from_date} to {to_date}")

        url = f"{self.BASE_URL}/expired-instruments/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        try:
            r = requests.get(url, headers=self.headers, timeout=20)
            if r.status_code == 200:
                j = r.json()
                if isinstance(j, dict):
                    candles = j.get('data', {}).get('candles', [])
                elif isinstance(j, list):
                    candles = j
                else:
                    candles = []
                if self.verbose:
                    print(f"   ✅ Got {len(candles)} candles")
                return candles
            else:
                if self.verbose:
                    print(f"   ⚠️ Expired candle fetch status: {r.status_code}")
                return []
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Expired candle fetch error: {e}")
            return []

    # -------------------------- Price selection --------------------------
    def find_closest_price_from_candles(self, candles, target_timestamp):
        if len(candles) == 0:
            raise ValueError('No candles')

        # candles expected as list of lists or list of dicts. Normalize adaptable shapes:
        # If each item is list like [timestamp, open, high, low, close, volume, oi], keep as-is.
        # If dicts with named fields, try to extract timestamp/open/high/low/close/volume/oi.
        if isinstance(candles[0], (list, tuple)):
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        else:
            # try to build dataframe from list of dicts
            df = pd.DataFrame(candles)
            # ensure expected columns exist or map common alternatives
            for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi']:
                if col not in df.columns:
                    # look for close-like keys
                    if col == 'timestamp':
                        # try 'time' or 'datetime'
                        for alt in ['time', 'datetime', 'date_time']:
                            if alt in df.columns:
                                df = df.rename(columns={alt: 'timestamp'})
                                break
                    # other columns we assume missing; pandas will fill with NaN
                    pass

            # keep only expected columns, add NaNs if missing
            df = df.reindex(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])

        # parse timestamps
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        target = pd.to_datetime(target_timestamp)
        if target.tz is not None:
            target = target.tz_localize(None)

        # market hours filter (9:15 to 15:30)
        df = df[(df['timestamp'].dt.hour >= 9) & (df['timestamp'].dt.hour <= 15)]
        df = df[~((df['timestamp'].dt.hour == 9) & (df['timestamp'].dt.minute < 15))]
        df = df[~((df['timestamp'].dt.hour == 15) & (df['timestamp'].dt.minute > 30))]

        if len(df) == 0:
            raise ValueError('No market hours candles')

        df['time_diff'] = abs(df['timestamp'] - target)
        idx = df['time_diff'].idxmin()
        row = df.loc[idx]
        if self.verbose:
            try:
                print(f"   📊 {row['timestamp'].strftime('%H:%M')}: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")
            except Exception:
                print(f"   📊 Closest time: {row['timestamp']}")
        return float(row['close'])

    # -------------------------- Public combined method --------------------------
    def get_option_price(self, timestamp, expiry, strike, option_type, interval='1minute', underlying_name='NIFTY 50'):
        """Main helper. Auto-selects live vs expired sources.
        timestamp: string or datetime (the time you want price for)
        expiry: expiry date string 'YYYY-MM-DD'
        strike: numeric
        option_type: 'CALL'/'PUT' or 'CE'/'PE'
        underlying_name: kept for API compatibility (we use NIFTY 50 internally)
        """
        expiry_dt = pd.to_datetime(expiry).date()
        today = self._today_date()

        # If expiry is strictly before today -> expired mode
        if expiry_dt < today:
            if self.verbose:
                print(f"\n=== EXPIRED MODE ({expiry_dt} < {today}) ===")

            # expired flow
            contracts = self.get_expired_contracts(expiry)
            if len(contracts) == 0:
                raise ValueError(f"No expired contracts for {expiry_dt} - not archived yet")

            # ensure timestamp is not after expiry
            ts_date = pd.to_datetime(timestamp).date()
            if ts_date > expiry_dt:
                raise ValueError(f"Requested timestamp {ts_date} is after expiry {expiry_dt}. Expired candles exist only BEFORE expiry.")

            # try exact match among expired contracts
            df = contracts.copy()
            col_strike = next((c for c in df.columns if 'strike' in c.lower()), None)
            col_type = next((c for c in df.columns if 'instrument_type' in c.lower() or c.lower()=='type'), None)
            col_key = next((c for c in df.columns if 'instrument_key' in c.lower()), None)
            col_symbol = next((c for c in df.columns if 'trading_symbol' in c.lower() or 'symbol' in c.lower()), None)

            if col_strike is None or col_type is None or col_key is None:
                raise RuntimeError('Expired contracts missing expected columns')

            opt = 'CE' if option_type.upper() in ('CALL','CE') else 'PE'
            filtered = df[(df[col_strike].astype(float) == float(strike)) & (df[col_type].astype(str).str.upper() == opt)]

            if len(filtered) > 0:
                key = filtered.iloc[0][col_key]
                sym = filtered.iloc[0][col_symbol] if col_symbol else None
                if self.verbose:
                    print(f"   ✅ Found: {sym}")
            else:
                # closest strike
                df2 = df[df[col_type].astype(str).str.upper() == opt].copy()
                df2['__diff'] = abs(df2[col_strike].astype(float) - float(strike))
                df2 = df2.sort_values('__diff')
                if len(df2) == 0:
                    raise ValueError('No expired option contracts found for this type')
                chosen = df2.iloc[0]
                key = chosen[col_key]
                sym = chosen[col_symbol] if col_symbol else None
                if self.verbose:
                    print(f"   ⚠️ Using closest: {sym} (Strike {chosen[col_strike]})")

            candles = self.get_expired_candles(key, timestamp, interval=interval)
            if len(candles) == 0:
                raise ValueError('No expired candles returned')
            price = self.find_closest_price_from_candles(candles, timestamp)
            return price

        else:
            # live mode
            if self.verbose:
                print(f"\n=== LIVE MODE ({expiry_dt} >= {today}) ===")

            # use option chain to find instrument key (robust)
            inst_key = self.find_live_instrument_key_via_chain(expiry, strike, option_type)
            if self.verbose:
                print(f"   ✅ Found LIVE instrument: {inst_key}")

            # build from/to for candles (request previous day -> target day)
            ts = pd.to_datetime(timestamp)
            to_dt = ts
            from_dt = ts - timedelta(days=1)

            candles = self.get_live_candles(inst_key, from_dt, to_dt, interval=interval)
            if len(candles) == 0:
                raise ValueError('No live candles returned (requested period may be future or not yet available)')
            price = self.find_closest_price_from_candles(candles, timestamp)
            return price


# -------------------------- Example usage --------------------------
if __name__ == '__main__':
    # Replace with your access token
    ACCESS_TOKEN = 'YOUR_UPSTOX_ACCESS_TOKEN_HERE'

    api = UpstoxOptionAPI(access_token=ACCESS_TOKEN, instruments_cache_path='instruments.csv', verbose=True)

    print('\n-- LIVE OPTION EXAMPLE (non-expired) --')
    try:
        p = api.get_option_price(
            timestamp='2025-11-19 10:40:00',
            expiry='2025-11-25',
            strike=26000,
            option_type='CALL',
            interval='1minute',
            underlying_name='NIFTY'  # kept for compatibility; we use NIFTY 50 internally
        )
        print(f'Live option price: ₹{p:.2f}')
    except Exception as e:
        print('Live example error:', e)

    print('\n-- EXPIRED OPTION EXAMPLE --')
    try:
        p = api.get_option_price(
            timestamp='2025-11-04 11:30:00',
            expiry='2025-11-11',
            strike=26000,
            option_type='CALL',
            interval='1minute',
            underlying_name='NIFTY 50'
        )
        print(f'Expired option price: ₹{p:.2f}')
    except Exception as e:
        print('Expired example error:', e)
