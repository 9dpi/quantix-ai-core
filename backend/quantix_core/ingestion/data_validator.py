"""
Data Validation - Ensures sufficient data quality for feature calculation
Production-grade guards against insufficient/invalid data
"""

from typing import Dict


class DataNotSufficientError(Exception):
    """Raised when data is insufficient for feature calculation"""
    def __init__(self, required: int, received: int, timeframe: str, symbol: str, reason: str = ""):
        self.required = required
        self.received = received
        self.timeframe = timeframe
        self.symbol = symbol
        self.reason = reason
        
        message = f"Insufficient data for {symbol} @ {timeframe}: need {required}, got {received}"
        if reason:
            message += f" ({reason})"
        
        super().__init__(message)
    
    def to_dict(self) -> Dict:
        """Convert to dict for API response"""
        return {
            "error": "DATA_NOT_SUFFICIENT",
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "required_candles": self.required,
            "received_candles": self.received,
            "reason": self.reason or "Not enough historical data for reliable feature calculation"
        }


class DataValidator:
    """
    Validates data sufficiency for feature calculation.
    
    Principle: Better to refuse calculation than return unreliable results.
    """
    
    # Minimum candles required per timeframe
    MIN_CANDLES_REQUIRED: Dict[str, int] = {
        "M1": 200,   # 1-minute: need ~3 hours
        "M5": 200,   # 5-minute: need ~16 hours
        "M15": 150,  # 15-minute: need ~37 hours
        "M30": 120,  # 30-minute: need ~2.5 days
        "H1": 100,   # 1-hour: need ~4 days
        "H4": 100,   # 4-hour: need ~16 days
        "D1": 60,    # Daily: need ~2 months
        "W1": 52,    # Weekly: need ~1 year
        "MN": 24     # Monthly: need ~2 years
    }
    
    @classmethod
    def validate_candle_count(cls, candles: int, timeframe: str, symbol: str) -> None:
        """
        Validate that we have enough candles for reliable calculation.
        
        Args:
            candles: Number of candles available
            timeframe: Timeframe being analyzed
            symbol: Symbol being analyzed
            
        Raises:
            DataNotSufficientError: If insufficient data
        """
        required = cls.MIN_CANDLES_REQUIRED.get(timeframe.upper(), 100)
        
        if candles < required:
            raise DataNotSufficientError(
                required=required,
                received=candles,
                timeframe=timeframe,
                symbol=symbol,
                reason=f"Feature calculation requires at least {required} candles for {timeframe}"
            )
    
    @classmethod
    def get_required_candles(cls, timeframe: str) -> int:
        """Get minimum required candles for a timeframe"""
        return cls.MIN_CANDLES_REQUIRED.get(timeframe.upper(), 100)
