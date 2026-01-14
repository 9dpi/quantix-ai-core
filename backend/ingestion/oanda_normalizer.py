"""
OANDA Data Normalization & Integrity Guard
Ensures clean, validated data enters the system

Principle: Validate early, fail fast, audit everything
"""

from typing import Dict, Optional
from datetime import datetime
from loguru import logger


class CandleIntegrityError(Exception):
    """Raised when candle data violates OHLC integrity"""
    pass


class OandaNormalizer:
    """
    Normalizes OANDA raw candles to Quantix standard format.
    
    Responsibilities:
    - Format conversion
    - Integrity validation
    - Completeness filtering
    """
    
    @staticmethod
    def normalize_candle(
        raw: Dict,
        instrument: str,
        timeframe: str
    ) -> Optional[Dict]:
        """
        Normalize OANDA candle to Quantix format.
        
        Args:
            raw: Raw candle from OANDA API
            instrument: Instrument name (e.g., "EUR_USD")
            timeframe: Timeframe (e.g., "H4")
            
        Returns:
            Normalized candle dict or None if invalid
            
        Raises:
            CandleIntegrityError: If OHLC integrity violated
        """
        try:
            # Extract mid prices
            mid = raw.get("mid", {})
            
            # Parse values
            open_price = float(mid.get("o", 0))
            high = float(mid.get("h", 0))
            low = float(mid.get("l", 0))
            close = float(mid.get("c", 0))
            volume = int(raw.get("volume", 0))
            complete = raw.get("complete", False)
            timestamp = raw.get("time")
            
            # Validate OHLC integrity
            OandaNormalizer._validate_ohlc(open_price, high, low, close)
            
            # Build normalized candle
            candle = {
                "provider": "oanda",
                "instrument": instrument,
                "timeframe": timeframe,
                "timestamp": timestamp,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "complete": complete,
                "source_id": f"oanda:{instrument}:{timeframe}:{timestamp}"
            }
            
            return candle
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"❌ Failed to normalize candle: {e}")
            return None
    
    @staticmethod
    def _validate_ohlc(open_price: float, high: float, low: float, close: float) -> None:
        """
        Validate OHLC integrity constraints.
        
        Rules:
        - low <= open <= high
        - low <= close <= high
        - low <= high (obviously)
        
        Raises:
            CandleIntegrityError: If any constraint violated
        """
        if not (low <= open_price <= high):
            raise CandleIntegrityError(
                f"Open {open_price} outside range [{low}, {high}]"
            )
        
        if not (low <= close <= high):
            raise CandleIntegrityError(
                f"Close {close} outside range [{low}, {high}]"
            )
        
        if low > high:
            raise CandleIntegrityError(
                f"Low {low} greater than High {high}"
            )
        
        # Additional sanity checks
        if low <= 0 or high <= 0:
            raise CandleIntegrityError(
                f"Invalid price: low={low}, high={high}"
            )
    
    @staticmethod
    def filter_complete(candles: list[Dict]) -> list[Dict]:
        """
        Filter to only complete candles.
        
        Incomplete candles are skipped silently - next run will pick them up.
        
        Args:
            candles: List of normalized candles
            
        Returns:
            List of complete candles only
        """
        complete_candles = [c for c in candles if c.get("complete", False)]
        
        skipped = len(candles) - len(complete_candles)
        if skipped > 0:
            logger.info(f"⏭️ Skipped {skipped} incomplete candles (will retry next run)")
        
        return complete_candles
    
    @staticmethod
    def normalize_batch(
        raw_candles: list[Dict],
        instrument: str,
        timeframe: str
    ) -> list[Dict]:
        """
        Normalize a batch of candles.
        
        Args:
            raw_candles: List of raw OANDA candles
            instrument: Instrument name
            timeframe: Timeframe
            
        Returns:
            List of normalized, complete candles
        """
        normalized = []
        
        for raw in raw_candles:
            try:
                candle = OandaNormalizer.normalize_candle(raw, instrument, timeframe)
                if candle:
                    normalized.append(candle)
            except CandleIntegrityError as e:
                logger.warning(f"⚠️ Integrity violation: {e} - skipping candle")
                continue
        
        # Filter to complete only
        complete = OandaNormalizer.filter_complete(normalized)
        
        logger.info(f"✅ Normalized {len(complete)}/{len(raw_candles)} candles")
        
        return complete
