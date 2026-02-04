from datetime import datetime, timezone, time
from loguru import logger
from typing import Tuple

class ConfidenceRefiner:
    """
    Refines Raw AI Confidence into Release Confidence based on Market Context.
    Target: 1-5 quality signals per day for EURUSD M15.
    """
    
    def __init__(self):
        # Session Windows (UTC)
        self.LONDON_OPEN = 8
        self.LONDON_NY_OVERLAP_START = 13
        self.LONDON_CLOSE = 17
        self.NY_CLOSE = 22

    def get_session_weight(self, current_time: datetime) -> float:
        """
        Calculate session weight based on London and NY market hours.
        Only allows release during London or London-NY Overlap.
        """
        hour = current_time.hour
        
        # London-NY Overlap (Maximum priority)
        if self.LONDON_NY_OVERLAP_START <= hour < self.LONDON_CLOSE:
            return 1.2
            
        # Pure London session (High priority)
        if self.LONDON_OPEN <= hour < self.LONDON_NY_OVERLAP_START:
            return 1.0
            
        # Outside London hours (Asia/NY) - allow with minor penalty
        return 0.8

    def get_volatility_factor(self, df_last_rows) -> float:
        """
        Sanity check on volatility. 
        In v1, we return 1.0 as a baseline.
        Future: ATR comparison.
        """
        return 1.0

    def get_spread_factor(self, symbol: str) -> float:
        """
        Check if spread is within acceptable limits.
        Rollover hours (21:00-23:00 UTC) usually have high spread.
        """
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        # Rollover/Low liquidity window
        if 21 <= hour <= 23:
            return 0.5 # Penalty for high spread
            
        return 1.0

    def calculate_release_score(self, raw_confidence: float, df=None) -> Tuple[float, str]:
        """
        Final Release Score = Confidence * Session * Volatility * Spread
        """
        now = datetime.now(timezone.utc)
        
        s_weight = self.get_session_weight(now)
        v_factor = self.get_volatility_factor(df)
        sp_factor = self.get_spread_factor("EURUSD")
        
        release_score = raw_confidence * s_weight * v_factor * sp_factor
        
        reason = (
            f"Raw: {raw_confidence:.2f} | "
            f"Session: {s_weight:.1f} | "
            f"Vol: {v_factor:.1f} | "
            f"Spread: {sp_factor:.1f}"
        )
        
        return round(release_score, 4), reason
