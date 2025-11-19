import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import math

class BacktestEngine:
    """Main backtesting engine with hybrid API + improved mock"""
    
    def __init__(self, upstox_api, expiry_calculator, strike_calculator,
                 expiry_day, rollover_day, moneyness_mode, lot_size, data_interval):
        self.upstox_api = upstox_api
        self.expiry_calculator = expiry_calculator
        self.strike_calculator = strike_calculator
        self.expiry_day = expiry_day
        self.rollover_day = rollover_day
        self.moneyness_mode = moneyness_mode
        self.lot_size = lot_size
        self.data_interval = data_interval
        
    def run_backtest(self, trades_df, progress_bar=None, status_text=None):
        """Execute backtest for all trades"""
        
        results = []
        total_trades = len(trades_df)
        
        for idx, trade in trades_df.iterrows():
            if status_text:
                status_text.text(f"Processing trade {idx + 1}/{total_trades}...")
            
            if progress_bar:
                progress = 30 + int((idx / total_trades) * 60)
                progress_bar.progress(progress)
            
            try:
                result = self.process_single_trade(trade)
                results.append(result)
                time.sleep(0.05)
                
            except Exception as e:
                print(f"❌ Error processing trade {trade['Trade #']}: {str(e)}")
                result = trade.to_dict()
                result['Error'] = str(e)
                results.append(result)
        
        return pd.DataFrame(results)
    
    def process_single_trade(self, trade):
        """Process a single trade"""
        
        # Calculate expiry date
        entry_date = pd.to_datetime(trade['Entry Date'])
        expiry_date = self.expiry_calculator.calculate_expiry(
            entry_date,
            self.expiry_day,
            self.rollover_day
        )
        
        # Calculate strike price
        strike_price = self.strike_calculator.calculate_strike(
            nifty_price=trade['NIFTY Entry Price'],
            option_type=trade['Option Type'],
            moneyness=self.moneyness_mode
        )
        
        # Get option prices (with NIFTY spot for better calculation)
        option_entry_price, entry_source = self.get_option_price(
            trade['Entry DateTime'],
            expiry_date,
            strike_price,
            trade['Option Type'],
            trade['NIFTY Entry Price']
        )
        
        option_exit_price, exit_source = self.get_option_price(
            trade['Exit DateTime'],
            expiry_date,
            strike_price,
            trade['Option Type'],
            trade['NIFTY Exit Price']
        )
        
        # Calculate P&L
        direction_multiplier = 1 if trade['Direction'] == 'LONG' else -1
        pnl_per_lot = (option_exit_price - option_entry_price) * direction_multiplier
        total_pnl = pnl_per_lot * self.lot_size
        
        # Build result
        result = {
            'Trade #': trade['Trade #'],
            'Entry Date': trade['Entry Date'],
            'Entry Time': trade['Entry Time'],
            'Exit Date': trade['Exit Date'],
            'Exit Time': trade['Exit Time'],
            'Expiry Date': expiry_date.date(),
            'Option Type': trade['Option Type'],
            'Strike Price': int(strike_price),
            'NIFTY Entry': trade['NIFTY Entry Price'],
            'NIFTY Exit': trade['NIFTY Exit Price'],
            'Option Entry Price': round(option_entry_price, 2),
            'Option Exit Price': round(option_exit_price, 2),
            'P&L (NIFTY)': round(trade['P&L (NIFTY)'], 2),
            'P&L per Lot': round(pnl_per_lot, 2),
            'P&L (Options)': round(total_pnl, 2),
            'Data Source': f"{entry_source}/{exit_source}"
        }
        
        return result
    
    def get_option_price(self, timestamp, expiry_date, strike_price, option_type, nifty_spot):
        """Get option price - try API first, then improved mock"""
        
        try:
            # Try Upstox API
            price = self.upstox_api.get_historical_option_price(
                timestamp=timestamp,
                expiry=expiry_date,
                strike=strike_price,
                option_type=option_type,
                interval=self.data_interval
            )
            
            if price is not None and price > 0:
                return price, 'API'
            else:
                raise ValueError("Invalid API price")
                
        except Exception as e:
            # Use improved Black-Scholes calculation
            calc_price = self.calculate_option_price_realistic(
                timestamp, expiry_date, strike_price, option_type, nifty_spot
            )
            print(f"🔧 CALC: {option_type} {strike_price} @ {pd.to_datetime(timestamp).strftime('%H:%M')} = ₹{calc_price:.2f}")
            return calc_price, 'CALCULATED'
    
    def calculate_option_price_realistic(self, timestamp, expiry_date, strike, option_type, spot_price):
        """
        Realistic option price calculation using Black-Scholes principles
        Much better than random mock data
        """
        
        # Convert timestamps
        if isinstance(timestamp, pd.Timestamp):
            timestamp_dt = timestamp.to_pydatetime()
        elif isinstance(timestamp, str):
            timestamp_dt = pd.to_datetime(timestamp).to_pydatetime()
        else:
            timestamp_dt = timestamp
        
        if isinstance(expiry_date, pd.Timestamp):
            expiry_date_obj = expiry_date.date()
        elif isinstance(expiry_date, datetime):
            expiry_date_obj = expiry_date.date()
        else:
            expiry_date_obj = expiry_date
        
        # Days to expiry
        entry_date = timestamp_dt.date()
        days_to_expiry = (expiry_date_obj - entry_date).days
        
        if days_to_expiry < 0:
            days_to_expiry = 0
        
        # Time to expiry in years
        T = max(days_to_expiry / 365.0, 0.001)
        
        # Intrinsic value
        if option_type == 'CALL':
            intrinsic = max(0, spot_price - strike)
        else:  # PUT
            intrinsic = max(0, strike - spot_price)
        
        # Time value calculation
        moneyness = abs(spot_price - strike) / spot_price
        
        # NIFTY volatility (typical 15-18%)
        volatility = 0.17
        
        # Time decay factor
        if days_to_expiry == 0:
            time_decay = 0.05  # Almost no time value on expiry
        elif days_to_expiry <= 1:
            time_decay = 0.15
        elif days_to_expiry <= 7:
            time_decay = 0.4 + (days_to_expiry / 7) * 0.4
        else:
            time_decay = 0.85
        
        # Base time value (ATM has highest)
        atm_time_value = spot_price * volatility * math.sqrt(T) * 100
        
        # Moneyness adjustment (Gaussian decay)
        moneyness_factor = math.exp(-12 * moneyness**2)
        
        # Final time value
        time_value = atm_time_value * moneyness_factor * time_decay
        
        # Total price
        option_price = intrinsic + time_value
        
        # Ensure minimum reasonable price
        option_price = max(5, option_price)
        
        return option_price
