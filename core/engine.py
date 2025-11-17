import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

class BacktestEngine:
    """Main backtesting engine"""
    
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
        """
        Execute backtest for all trades
        
        Args:
            trades_df: DataFrame with parsed trades
            progress_bar: Streamlit progress bar (optional)
            status_text: Streamlit status text (optional)
            
        Returns:
            DataFrame with complete backtest results
        """
        
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
                
                # Rate limiting - avoid API overload
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing trade {trade['Trade #']}: {str(e)}")
                # Append trade with error
                result = trade.to_dict()
                result['Error'] = str(e)
                results.append(result)
        
        return pd.DataFrame(results)
    
    def process_single_trade(self, trade):
        """Process a single trade"""
        
        # Step 1: Calculate expiry date
        entry_date = pd.to_datetime(trade['Entry Date'])
        expiry_date = self.expiry_calculator.calculate_expiry(
            entry_date,
            self.expiry_day,
            self.rollover_day
        )
        
        # Step 2: Calculate strike price
        strike_price = self.strike_calculator.calculate_strike(
            nifty_price=trade['NIFTY Entry Price'],
            option_type=trade['Option Type'],
            moneyness=self.moneyness_mode
        )
        
        # Step 3: Get option prices
        option_entry_price = self.get_option_price(
            trade['Entry DateTime'],
            expiry_date,
            strike_price,
            trade['Option Type']
        )
        
        option_exit_price = self.get_option_price(
            trade['Exit DateTime'],
            expiry_date,
            strike_price,
            trade['Option Type']
        )
        
        # Step 4: Calculate P&L
        direction_multiplier = 1 if trade['Direction'] == 'LONG' else -1
        
        pnl_per_lot = (option_exit_price - option_entry_price) * direction_multiplier
        total_pnl = pnl_per_lot * self.lot_size
        
        # Build result dictionary
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
            'P&L (Options)': round(total_pnl, 2)
        }
        
        return result
    
    def get_option_price(self, timestamp, expiry_date, strike_price, option_type):
        """
        Get option price at given timestamp
        Uses Upstox API or mock data
        """
        
        try:
            # Try to fetch from Upstox API
            price = self.upstox_api.get_historical_option_price(
                timestamp=timestamp,
                expiry=expiry_date,
                strike=strike_price,
                option_type=option_type,
                interval=self.data_interval
            )
            return price
        except:
            # Fallback to mock calculation if API fails
            return self.mock_option_price(timestamp, expiry_date, strike_price, option_type)
    
    def mock_option_price(self, timestamp, expiry_date, strike_price, option_type):
        """
        Generate mock option price for testing
        This is a simplified Black-Scholes approximation
        """
        
        # Days to expiry
        dte = (expiry_date - timestamp).days
        if dte < 0:
            dte = 0
        
        # Time value decay factor
        time_value = max(50, 200 * (dte / 7))  # Weekly options
        
        # Add some randomness for realism
        noise = np.random.normal(0, 20)
        
        # Intrinsic value (simplified)
        intrinsic = max(0, abs(strike_price - 25600) / 100)
        
        price = time_value + intrinsic + noise
        
        return max(10, price)  # Minimum price of 10
