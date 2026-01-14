"""
Quantix AI Core v3.2 - Candle Quality Gate
============================================
Forex-grade validator. Only clean, tradable candles pass through.

Rules:
- Timestamp must be UTC-aligned
- Spread < 2.5x average
- No abnormal spikes
- Wick ratio within normal range
- Volume above minimum threshold
- Must be during London/NY session
"""

from datetime import datetime, time
from typing import Dict, Tuple
import pytz


class CandleQualityGate:
    """
    Forex-grade candle validator.
    
    Only candles that pass ALL checks are stored in market_candles_clean.
    Failed candles are discarded - not learned from.
    """
    
    # Session definitions (UTC)
    SESSIONS = {
        'london': (time(7, 0), time(16, 0)),
        'newyork': (time(13, 0), time(22, 0)),
        'overlap': (time(13, 0), time(16, 0)),
        'asia': (time(0, 0), time(7, 0))
    }
    
    # Quality thresholds
    MAX_SPREAD_MULTIPLIER = 2.5  # Max 2.5x average spread
    MIN_VOLUME_THRESHOLD = 100   # Minimum tick volume
    MAX_WICK_RATIO = 0.75        # Max wick/body ratio
    MAX_RANGE_MULTIPLIER = 3.0   # Max 3x average range (spike detection)
    
    def __init__(self, asset: str = "EURUSD"):
        self.asset = asset
        self.avg_spread = self._get_avg_spread(asset)
        self.avg_range = self._get_avg_range(asset)
    
    def validate(self, candle: Dict) -> Tuple[bool, float, str]:
        """
        Validate a single candle through the Quality Gate.
        
        Args:
            candle: Dict with keys: time, open, high, low, close, volume, spread
        
        Returns:
            (is_valid, quality_score, session)
            - is_valid: True if candle passes ALL checks
            - quality_score: 0.0 to 1.0 composite score
            - session: 'london', 'newyork', 'overlap', 'asia', or 'off_hours'
        """
        
        checks = []
        
        # Check 1: Timestamp alignment (must be UTC)
        timestamp_valid = self._check_timestamp(candle['time'])
        checks.append(('timestamp', timestamp_valid, 0.15))
        
        # Check 2: Spread validation
        spread_valid = self._check_spread(candle.get('spread', 0))
        checks.append(('spread', spread_valid, 0.25))
        
        # Check 3: Range validation (spike detection)
        range_valid = self._check_range(candle)
        checks.append(('range', range_valid, 0.20))
        
        # Check 4: Wick ratio (no extreme wicks)
        wick_valid = self._check_wick_ratio(candle)
        checks.append(('wick', wick_valid, 0.15))
        
        # Check 5: Volume threshold
        volume_valid = self._check_volume(candle.get('volume', 0))
        checks.append(('volume', volume_valid, 0.15))
        
        # Check 6: Session validation (London/NY preferred)
        session, session_valid = self._check_session(candle['time'])
        checks.append(('session', session_valid, 0.10))
        
        # Calculate composite quality score
        quality_score = sum(weight if passed else 0 for _, passed, weight in checks)
        
        # Candle is valid ONLY if ALL checks pass
        is_valid = all(passed for _, passed, _ in checks)
        
        return is_valid, quality_score, session
    
    def _check_timestamp(self, timestamp: datetime) -> bool:
        """Ensure timestamp is UTC-aligned and not in the future."""
        if timestamp.tzinfo is None:
            return False  # Must have timezone info
        
        utc_time = timestamp.astimezone(pytz.UTC)
        
        # Check if in future
        if utc_time > datetime.now(pytz.UTC):
            return False
        
        # Check if aligned to timeframe (e.g., M15 should be :00, :15, :30, :45)
        if utc_time.minute % 15 != 0:
            return False
        
        return True
    
    def _check_spread(self, spread: float) -> bool:
        """Spread must be < 2.5x average."""
        if spread <= 0:
            return False
        
        return spread < (self.avg_spread * self.MAX_SPREAD_MULTIPLIER)
    
    def _check_range(self, candle: Dict) -> bool:
        """Detect abnormal spikes (range > 3x average)."""
        candle_range = candle['high'] - candle['low']
        
        if candle_range <= 0:
            return False
        
        return candle_range < (self.avg_range * self.MAX_RANGE_MULTIPLIER)
    
    def _check_wick_ratio(self, candle: Dict) -> bool:
        """Wick should not dominate the candle (max 75% of total range)."""
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        
        if total_range == 0:
            return False
        
        upper_wick = candle['high'] - max(candle['open'], candle['close'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        max_wick = max(upper_wick, lower_wick)
        
        wick_ratio = max_wick / total_range if total_range > 0 else 0
        
        return wick_ratio <= self.MAX_WICK_RATIO
    
    def _check_volume(self, volume: int) -> bool:
        """Volume must exceed minimum threshold."""
        return volume >= self.MIN_VOLUME_THRESHOLD
    
    def _check_session(self, timestamp: datetime) -> Tuple[str, bool]:
        """
        Determine session and validate.
        
        Returns:
            (session_name, is_valid)
            - London/NY/Overlap sessions are preferred (valid=True)
            - Asia/Off-hours are less preferred (valid=False for learning)
        """
        utc_time = timestamp.astimezone(pytz.UTC).time()
        
        # Check overlap first (highest priority)
        if self._time_in_range(utc_time, self.SESSIONS['overlap']):
            return 'overlap', True
        
        # Check London
        if self._time_in_range(utc_time, self.SESSIONS['london']):
            return 'london', True
        
        # Check New York
        if self._time_in_range(utc_time, self.SESSIONS['newyork']):
            return 'newyork', True
        
        # Check Asia (valid but not preferred for learning)
        if self._time_in_range(utc_time, self.SESSIONS['asia']):
            return 'asia', False
        
        # Off hours
        return 'off_hours', False
    
    def _time_in_range(self, check_time: time, time_range: Tuple[time, time]) -> bool:
        """Check if time falls within a range."""
        start, end = time_range
        if start <= end:
            return start <= check_time <= end
        else:  # Crosses midnight
            return check_time >= start or check_time <= end
    
    def _get_avg_spread(self, asset: str) -> float:
        """Get average spread for asset (hardcoded for now)."""
        spreads = {
            'EURUSD': 0.00015,  # 1.5 pips
            'GBPUSD': 0.00020,  # 2.0 pips
            'USDJPY': 0.015,    # 1.5 pips (JPY pairs)
        }
        return spreads.get(asset, 0.00020)
    
    def _get_avg_range(self, asset: str) -> float:
        """Get average M15 range for asset (hardcoded for now)."""
        ranges = {
            'EURUSD': 0.00050,  # ~5 pips
            'GBPUSD': 0.00070,  # ~7 pips
            'USDJPY': 0.050,    # ~5 pips
        }
        return ranges.get(asset, 0.00060)


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    gate = CandleQualityGate("EURUSD")
    
    # Example candle
    test_candle = {
        'time': datetime(2026, 1, 14, 14, 0, tzinfo=pytz.UTC),  # 2PM UTC (NY session)
        'open': 1.08500,
        'high': 1.08550,
        'low': 1.08480,
        'close': 1.08520,
        'volume': 1500,
        'spread': 0.00018
    }
    
    is_valid, quality_score, session = gate.validate(test_candle)
    
    print(f"Candle Valid: {is_valid}")
    print(f"Quality Score: {quality_score:.2f}")
    print(f"Session: {session}")
    
    if is_valid:
        print("✅ PASS - Candle will be stored in market_candles_clean")
    else:
        print("❌ FAIL - Candle discarded, not learned from")
