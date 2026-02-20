import pandas as pd
import numpy as np
from datetime import datetime

class TradingViewParser:
    """Parse TradingView strategy export files"""
    
    def __init__(self):
        # Price column is NO LONGER required - NIFTY price is fetched from API
        self.required_columns = ['Trade #', 'Type', 'Signal', 'Date', 'Time']
    
    def parse_trades(self, df):
        """
        Parse TradingView Excel export and pair Entry/Exit rows.
        
        NIFTY spot price is automatically fetched from the Upstox API 
        based on entry/exit date and time — no manual price input needed.
        
        Args:
            df: Raw DataFrame from TradingView export
            
        Returns:
            DataFrame with paired Entry/Exit trades (no price columns)
        """
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Check required columns (Price is optional now)
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Convert date and time
        df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
        
        # Sort by Trade # and Type to ensure Entry comes before Exit
        df = df.sort_values(['Trade #', 'Type'])
        
        # Separate Entry and Exit rows
        entries = df[df['Type'].str.upper() == 'ENTRY'].copy()
        exits = df[df['Type'].str.upper() == 'EXIT'].copy()
        
        # Merge Entry and Exit by Trade # and Signal (to handle same Trade # for Long & Short)
        trades = pd.merge(
            entries,
            exits,
            on=['Trade #', 'Signal'],
            suffixes=('_entry', '_exit')
        )
        
        # Create clean output DataFrame (no price columns - fetched from API)
        result = pd.DataFrame({
            'Trade #': trades['Trade #'],
            'Direction': trades['Signal'].str.upper(),
            'Entry Date': pd.to_datetime(trades['Date_entry']).dt.date,
            'Entry Time': pd.to_datetime(trades['Time_entry'], format='%H:%M:%S').dt.time,
            'Exit Date': pd.to_datetime(trades['Date_exit']).dt.date,
            'Exit Time': pd.to_datetime(trades['Time_exit'], format='%H:%M:%S').dt.time,
            'Entry DateTime': trades['DateTime_entry'],
            'Exit DateTime': trades['DateTime_exit'],
        })
        
        # Determine Option Type (CALL for LONG, PUT for SHORT)
        result['Option Type'] = result['Direction'].apply(
            lambda x: 'CALL' if x == 'LONG' else 'PUT'
        )
        
        return result
    
    def validate_data(self, df):
        """Validate parsed data"""
        
        issues = []
        
        # Check for missing values
        if df.isnull().any().any():
            issues.append("Found missing values in data")
        
        # Check for valid dates
        if not pd.api.types.is_datetime64_any_dtype(df['Entry DateTime']):
            issues.append("Entry DateTime is not in datetime format")
        
        return issues
