from datetime import datetime, timezone, time
from loguru import logger

class MarketHours:
    """Utility to check if Forex market is open (UTC based)."""
    
    @staticmethod
    def is_market_open() -> bool:
        """
        Check if Forex market is currently open.
        Opens Sunday 22:00 UTC
        Closes Friday 22:00 UTC
        """
        now = datetime.now(timezone.utc)
        weekday = now.weekday() # 0 = Monday, 1 = Tuesday, ..., 4 = Friday, 5 = Saturday, 6 = Sunday
        hour = now.hour
        
        # Friday close (22:00 UTC)
        if weekday == 4 and hour >= 22:
            return False
        
        # Saturday (Closed)
        if weekday == 5:
            return False
            
        # Sunday open (22:00 UTC)
        if weekday == 6 and hour < 22:
            return False
            
        return True

    @staticmethod
    def should_generate_signals() -> bool:
        """
        Safety check: Don't generate new signals close to weekend gap.
        Avoid Friday after 20:00 UTC.
        """
        if not MarketHours.is_market_open():
            return False
            
        now = datetime.now(timezone.utc)
        # Friday safety buffer (Market gets thin after 17:00 UTC)
        if now.weekday() == 4 and now.hour >= 17:
            logger.warning("🕒 Market liquidity dropping near weekend. Skipping new signal generation.")
            return False
            
        return True
