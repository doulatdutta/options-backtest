import pandas as pd
from datetime import datetime, timedelta

class ExpiryCalculator:
    """Calculate option expiry dates with rollover logic"""
    
    WEEKDAY_MAP = {
        'Monday': 0,
        'Tuesday': 1,
        'Wednesday': 2,
        'Thursday': 3,
        'Friday': 4
    }
    
    def __init__(self):
        pass
    
    def calculate_expiry(self, entry_date, expiry_weekday, rollover_weekday):
        """
        Calculate expiry date based on entry date, expiry weekday, and rollover day
        
        Args:
            entry_date: Date when trade was entered
            expiry_weekday: Day of week when options expire (e.g., 'Thursday')
            rollover_weekday: Day of week after which trades roll to next expiry
            
        Returns:
            datetime: Expiry date
        """
        
        if isinstance(entry_date, str):
            entry_date = pd.to_datetime(entry_date)
        
        expiry_day_num = self.WEEKDAY_MAP[expiry_weekday]
        rollover_day_num = self.WEEKDAY_MAP[rollover_weekday]
        
        entry_weekday = entry_date.weekday()
        
        # Check if entry is on or after rollover day
        if entry_weekday >= rollover_day_num:
            # Roll to next week's expiry
            days_ahead = (expiry_day_num - entry_weekday + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
        else:
            # Use current week's expiry
            days_ahead = (expiry_day_num - entry_weekday) % 7
            if days_ahead == 0:
                days_ahead = 7
        
        expiry_date = entry_date + timedelta(days=days_ahead)
        
        return expiry_date
    
    def get_next_expiry(self, current_date, expiry_weekday):
        """Get the next expiry date from current date"""
        
        if isinstance(current_date, str):
            current_date = pd.to_datetime(current_date)
        
        expiry_day_num = self.WEEKDAY_MAP[expiry_weekday]
        current_weekday = current_date.weekday()
        
        days_ahead = (expiry_day_num - current_weekday) % 7
        if days_ahead == 0:
            days_ahead = 7
        
        return current_date + timedelta(days=days_ahead)
    
    def is_expiry_week(self, date, expiry_weekday):
        """Check if given date is in an expiry week"""
        
        expiry_date = self.get_next_expiry(date, expiry_weekday)
        days_to_expiry = (expiry_date - date).days
        
        return 0 <= days_to_expiry <= 7
