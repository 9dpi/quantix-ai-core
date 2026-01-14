"""
Candle Validator - Gatekeeper of Truth
Ensures only clean, complete, explainable candles enter the system

Principle: FAIL HARD, no fixes, no inference
"""

from typing import List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

from ingestion.dukascopy.resampler import Candle


@dataclass
class ValidationResult:
    """
    Result of candle validation.
    
    Attributes:
        valid: Whether candle passed all checks
        errors: List of validation errors (empty if valid)
        warnings: List of warnings (non-fatal)
    """
    valid: bool
    errors: List[str]
    warnings: List[str]


class CandleValidator:
    """
    Validates candles before persistence.
    
    Rules (FROZEN v1):
    1. OHLC integrity
    2. Time integrity
    3. Completeness gate
    4. Price sanity (FX-specific)
    5. Audit metadata
    
    NO fixes, NO fills, NO inference.
    """
    
    VERSION = "v1"
    
    # FX-specific limits
    MAX_SPREAD_PERCENT = 0.5  # 0.5% max spread
    MAX_RANGE_PERCENT = 5.0   # 5% max candle range
    
    def __init__(self, timeframe: str):
        """
        Initialize validator.
        
        Args:
            timeframe: Timeframe being validated (H4, D1, etc.)
        """
        self.timeframe = timeframe
        
        # Timeframe boundaries (minutes)
        self.tf_minutes = {
            "H1": 60,
            "H4": 240,
            "D1": 1440
        }
    
    def validate(self, candle: Candle) -> ValidationResult:
        """
        Validate a single candle.
        
        Args:
            candle: Candle to validate
            
        Returns:
            ValidationResult with pass/fail and errors
        """
        errors = []
        warnings = []
        
        # 1. OHLC Integrity (FAIL HARD)
        ohlc_errors = self._validate_ohlc_integrity(candle)
        errors.extend(ohlc_errors)
        
        # 2. Time Integrity
        time_errors = self._validate_time_integrity(candle)
        errors.extend(time_errors)
        
        # 3. Completeness Gate (CRITICAL)
        if not candle.complete:
            errors.append(
                f"Candle not complete (only {candle.tick_count} ticks)"
            )
        
        # 4. Price Sanity (FX-specific)
        sanity_warnings = self._validate_price_sanity(candle)
        warnings.extend(sanity_warnings)
        
        valid = len(errors) == 0
        
        if not valid:
            logger.warning(
                f"❌ Validation failed for {candle.timestamp}: {errors}"
            )
        
        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_ohlc_integrity(self, candle: Candle) -> List[str]:
        """
        Validate OHLC integrity constraints.
        
        Rules:
        - high >= max(open, close)
        - low <= min(open, close)
        - high >= low
        - no NaN/inf
        """
        errors = []
        
        # Check for NaN/inf
        values = [candle.open, candle.high, candle.low, candle.close]
        for i, val in enumerate(values):
            if not isinstance(val, (int, float)):
                errors.append(f"OHLC[{i}] is not numeric: {val}")
            elif val != val:  # NaN check
                errors.append(f"OHLC[{i}] is NaN")
            elif abs(val) == float('inf'):
                errors.append(f"OHLC[{i}] is infinite")
        
        if errors:
            return errors
        
        # High >= max(open, close)
        if candle.high < max(candle.open, candle.close):
            errors.append(
                f"High ({candle.high}) < max(open, close) "
                f"({max(candle.open, candle.close)})"
            )
        
        # Low <= min(open, close)
        if candle.low > min(candle.open, candle.close):
            errors.append(
                f"Low ({candle.low}) > min(open, close) "
                f"({min(candle.open, candle.close)})"
            )
        
        # High >= Low
        if candle.high < candle.low:
            errors.append(
                f"High ({candle.high}) < Low ({candle.low})"
            )
        
        # All prices > 0
        if any(v <= 0 for v in values):
            errors.append("OHLC contains non-positive values")
        
        return errors
    
    def _validate_time_integrity(self, candle: Candle) -> List[str]:
        """
        Validate timestamp alignment to timeframe boundary.
        
        Rules:
        - Timestamp must align to TF boundary
        - H4: must be 00:00, 04:00, 08:00, 12:00, 16:00, or 20:00
        - D1: must be 00:00
        """
        errors = []
        
        if self.timeframe == "H4":
            # H4 boundaries: 0, 4, 8, 12, 16, 20
            valid_hours = [0, 4, 8, 12, 16, 20]
            if candle.timestamp.hour not in valid_hours:
                errors.append(
                    f"H4 timestamp hour {candle.timestamp.hour} "
                    f"not in valid boundaries {valid_hours}"
                )
            
            # Must be at minute 0
            if candle.timestamp.minute != 0:
                errors.append(
                    f"H4 timestamp minute must be 0, got {candle.timestamp.minute}"
                )
        
        elif self.timeframe == "D1":
            # D1 must be 00:00
            if candle.timestamp.hour != 0 or candle.timestamp.minute != 0:
                errors.append(
                    f"D1 timestamp must be 00:00, got "
                    f"{candle.timestamp.hour:02d}:{candle.timestamp.minute:02d}"
                )
        
        # Seconds and microseconds must be 0
        if candle.timestamp.second != 0 or candle.timestamp.microsecond != 0:
            errors.append("Timestamp has non-zero seconds/microseconds")
        
        return errors
    
    def _validate_price_sanity(self, candle: Candle) -> List[str]:
        """
        Validate price sanity (FX-specific).
        
        These are warnings, not hard errors.
        """
        warnings = []
        
        # Calculate candle range
        candle_range = candle.high - candle.low
        range_percent = (candle_range / candle.close) * 100
        
        if range_percent > self.MAX_RANGE_PERCENT:
            warnings.append(
                f"Large candle range: {range_percent:.2f}% "
                f"(max {self.MAX_RANGE_PERCENT}%)"
            )
        
        # Check for suspicious zero range
        if candle_range == 0:
            warnings.append("Zero range candle (high == low)")
        
        return warnings
    
    def validate_batch(
        self, 
        candles: List[Candle]
    ) -> tuple[List[Candle], List[Candle]]:
        """
        Validate a batch of candles.
        
        Args:
            candles: List of candles to validate
            
        Returns:
            (valid_candles, invalid_candles)
        """
        valid = []
        invalid = []
        
        for candle in candles:
            result = self.validate(candle)
            if result.valid:
                valid.append(candle)
            else:
                invalid.append(candle)
        
        logger.info(
            f"✅ Validation: {len(valid)} valid, {len(invalid)} invalid"
        )
        
        return valid, invalid
    
    def validate_sequence(self, candles: List[Candle]) -> List[str]:
        """
        Validate sequence integrity (strictly increasing, no overlap).
        
        Args:
            candles: List of candles (must be sorted by timestamp)
            
        Returns:
            List of errors (empty if valid)
        """
        errors = []
        
        if len(candles) < 2:
            return errors
        
        for i in range(1, len(candles)):
            prev = candles[i-1]
            curr = candles[i]
            
            # Timestamps must be strictly increasing
            if curr.timestamp <= prev.timestamp:
                errors.append(
                    f"Timestamp not increasing: "
                    f"{prev.timestamp} -> {curr.timestamp}"
                )
            
            # Check for expected gap
            expected_gap = timedelta(
                minutes=self.tf_minutes.get(self.timeframe, 60)
            )
            actual_gap = curr.timestamp - prev.timestamp
            
            if actual_gap != expected_gap:
                errors.append(
                    f"Unexpected gap at {curr.timestamp}: "
                    f"expected {expected_gap}, got {actual_gap}"
                )
        
        return errors
