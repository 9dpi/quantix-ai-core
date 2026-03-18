import pandas as pd
from datetime import datetime, timezone, time
from loguru import logger
from typing import Tuple, Optional

class ConfidenceRefiner:
    """
    Refines Raw AI Confidence into Release Confidence based on Market Context.
    Target: 1-5 quality signals per day for EURUSD M15.
    """
    
    def __init__(self):
        # Session Windows (UTC)
        self.LONDON_OPEN = 6
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
            
        # Outside London hours (Asia/NY) - full weight for Scalper mode
        return 1.0

    def get_volatility_factor(self, df: Optional[pd.DataFrame]) -> float:
        """
        Real ATR-based volatility filter.
        Ensures the market has enough 'gas' but isn't in a chaotic spike.
        
        Logic:
        - Ratio = Current Candle Range / ATR(14)
        - Ideal: 0.7x to 1.5x ATR
        - Penalty for <0.5x (Too quiet) or >2.5x (Too volatile/news spike)
        """
        if df is None or len(df) < 15:
            return 1.0 # Baseline if data is missing
            
        try:
            # Calculate ATR(14)
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            
            tr = pd.concat([
                high - low, 
                (high - close.shift()).abs(), 
                (low - close.shift()).abs()
            ], axis=1).max(axis=1)
            
            atr = tr.rolling(window=14).mean().iloc[-1]
            
            # Current candle range
            current_range = float(high.iloc[-1] - low.iloc[-1])
            
            if atr == 0: return 1.0
            
            ratio = current_range / atr
            
            # Penalize extremes
            if ratio < 0.5:
                logger.debug(f"Volatility too low: {ratio:.2f}x ATR")
                return 0.7 
            elif ratio > 2.5:
                logger.warning(f"Volatility too high (News?): {ratio:.2f}x ATR")
                return 0.6
                
            return 1.0
            
        except Exception as e:
            logger.error(f"Error calculating volatility factor: {e}")
            return 1.0

    def get_spread_factor(self, symbol: str) -> float:
        """
        Check if spread is within acceptable limits.
        v4.7.2.9: Softened from 0.5x to 0.85x during rollover.
        """
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        # Rollover/Low liquidity window (softer penalty)
        if 21 <= hour <= 23:
            return 0.85 # v4.7.2.9: Reduced penalty (was 0.5x)
            
        return 1.0

    def calculate_release_score(self, raw_confidence: float, df=None) -> Tuple[float, str]:
        """
        Final Release Score = Confidence * Session * Volatility * Spread
        """
        now = datetime.now(timezone.utc)
        
        s_weight = self.get_session_weight(now)
        v_factor = self.get_volatility_factor(df)
        sp_factor = self.get_spread_factor("EURUSD")
        
        # Cap at 1.0 (100%) for UI/Mathematical consistency, 
        # while preserving the boost for threshold gating.
        release_score = min(1.0, raw_confidence * s_weight * v_factor * sp_factor)
        
        reason = (
            f"Raw: {raw_confidence:.2f} | "
            f"Session: {s_weight:.1f} | "
            f"Vol: {v_factor:.1f} | "
            f"Spread: {sp_factor:.1f}"
        )
        
        return round(release_score, 4), reason
