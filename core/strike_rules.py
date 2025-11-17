import numpy as np

class StrikeCalculator:
    """Calculate option strike prices based on moneyness"""
    
    STRIKE_INTERVAL = 50  # NIFTY strike interval
    
    def __init__(self):
        pass
    
    def calculate_strike(self, nifty_price, option_type, moneyness='ATM'):
        """
        Calculate strike price based on NIFTY price and moneyness
        
        Args:
            nifty_price: Current NIFTY spot price
            option_type: 'CALL' or 'PUT'
            moneyness: 'ATM', 'ITM1', or 'OTM1'
            
        Returns:
            float: Strike price
        """
        
        # First, calculate ATM strike
        atm_strike = self.get_atm_strike(nifty_price, option_type)
        
        # Then adjust based on moneyness
        if moneyness == 'ATM':
            return atm_strike
        elif moneyness == 'ITM1':
            return self.get_itm_strike(atm_strike, option_type)
        elif moneyness == 'OTM1':
            return self.get_otm_strike(atm_strike, option_type)
        else:
            raise ValueError(f"Invalid moneyness: {moneyness}")
    
    def get_atm_strike(self, nifty_price, option_type):
        """
        Get ATM (At The Money) strike
        
        CALL: Round UP to nearest 50 (ceiling)
        PUT: Round DOWN to nearest 50 (floor)
        """
        
        if option_type == 'CALL':
            # Round up (ceiling) to nearest 50
            strike = np.ceil(nifty_price / self.STRIKE_INTERVAL) * self.STRIKE_INTERVAL
        else:  # PUT
            # Round down (floor) to nearest 50
            strike = np.floor(nifty_price / self.STRIKE_INTERVAL) * self.STRIKE_INTERVAL
        
        return strike
    
    def get_itm_strike(self, atm_strike, option_type):
        """
        Get ITM1 (In The Money by 1 strike) strike
        
        CALL ITM: ATM + 100 (higher strike)
        PUT ITM: ATM - 100 (lower strike)
        """
        
        if option_type == 'CALL':
            return atm_strike + 100
        else:  # PUT
            return atm_strike - 100
    
    def get_otm_strike(self, atm_strike, option_type):
        """
        Get OTM1 (Out of The Money by 1 strike) strike
        
        CALL OTM: ATM - 50 (lower strike)
        PUT OTM: ATM + 50 (higher strike)
        """
        
        if option_type == 'CALL':
            return atm_strike - 50
        else:  # PUT
            return atm_strike + 50
    
    def get_strike_range(self, nifty_price, num_strikes=10):
        """Get a range of strikes around current price"""
        
        atm = self.get_atm_strike(nifty_price, 'CALL')
        
        strikes = []
        for i in range(-num_strikes, num_strikes + 1):
            strike = atm + (i * self.STRIKE_INTERVAL)
            strikes.append(strike)
        
        return sorted(strikes)
