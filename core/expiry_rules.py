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
        Calculate expiry date based on entry date, expiry weekday, and rollover day,
        treating the selected expiry weekday as the start of the 'options week'.

        Behaviour:
        - BEFORE rollover weekday  -> use NEXT expiry
        - FROM rollover weekday up to and including next expiry weekday -> use NEXT-TO-NEXT expiry
        """
        if isinstance(entry_date, str):
            entry_date = pd.to_datetime(entry_date)

        # Allow "No rollover" - use current week's expiry if on/before expiry day
        if rollover_weekday == "No rollover":
            return self.get_next_expiry(entry_date, expiry_weekday, include_today=True)

        expiry_day_num = self.WEEKDAY_MAP[expiry_weekday]      # e.g. Tuesday = 1
        rollover_day_num = self.WEEKDAY_MAP[rollover_weekday]  # e.g. Thursday = 3
        entry_weekday = entry_date.weekday()                    # 0..6

        # Compute the "next expiry" from the entry date
        days_to_next = (expiry_day_num - entry_weekday) % 7
        if days_to_next == 0:
            days_to_next = 7
        next_expiry = entry_date + timedelta(days=days_to_next)

        # Compute the "start of current options week" for this entry date.
        # Week starts on expiry weekday.
        # Move backwards from entry_date to the most recent expiry weekday.
        days_back_to_week_start = (entry_weekday - expiry_day_num) % 7
        week_start = entry_date - timedelta(days=days_back_to_week_start)

        # Rollover boundary = week_start + (rollover_day_num - expiry_day_num) days
        # (mod 7 to stay within 0..6)
        offset = (rollover_day_num - expiry_day_num) % 7
        rollover_boundary = week_start + timedelta(days=offset)

        # If entry is BEFORE rollover_boundary -> use next expiry
        # If entry is ON/AFTER rollover_boundary -> use next-to-next expiry
        if entry_date < rollover_boundary:
            expiry_date = next_expiry
        else:
            expiry_date = next_expiry + timedelta(days=7)

        return expiry_date
    
    def get_next_expiry(self, current_date, expiry_weekday, include_today=False):
        """
        Get the next expiry date from current date
        
        Args:
            current_date: The reference date
            expiry_weekday: Target expiry weekday (e.g., 'Tuesday')
            include_today: If True and current_date is the expiry weekday, return current_date
        """
        if isinstance(current_date, str):
            current_date = pd.to_datetime(current_date)
        
        expiry_day_num = self.WEEKDAY_MAP[expiry_weekday]
        current_weekday = current_date.weekday()
        
        days_ahead = (expiry_day_num - current_weekday) % 7
        
        # If today is the expiry day and include_today is True, use today
        if days_ahead == 0 and include_today:
            return current_date
        elif days_ahead == 0:
            days_ahead = 7
        
        return current_date + timedelta(days=days_ahead)
    
    def is_expiry_week(self, date, expiry_weekday):
        """Check if given date is in an expiry week"""
        
        expiry_date = self.get_next_expiry(date, expiry_weekday)
        days_to_expiry = (expiry_date - date).days
        
        return 0 <= days_to_expiry <= 7
