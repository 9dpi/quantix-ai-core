"""
Dukascopy Tick Parser - bi5 binary format decoder
Converts compressed binary ticks to structured data

Format: Each tick = 20 bytes
- timestamp_delta: 4 bytes (ms from hour start)
- ask: 4 bytes (price * 100000)
- bid: 4 bytes (price * 100000)
- ask_volume: 4 bytes
- bid_volume: 4 bytes
"""

import struct
from typing import List, NamedTuple
from datetime import datetime, timedelta
from loguru import logger


class Tick(NamedTuple):
    """
    Represents a single tick.
    
    Attributes:
        timestamp: UTC timestamp
        bid: Bid price
        ask: Ask price
        bid_volume: Bid volume
        ask_volume: Ask volume
    """
    timestamp: datetime
    bid: float
    ask: float
    bid_volume: float
    ask_volume: float


class TickParser:
    """
    Parses Dukascopy bi5 binary tick format.
    
    Principle: Deterministic, fail-fast on corruption
    """
    
    TICK_SIZE = 20  # bytes per tick
    PRICE_SCALE = 100000  # Dukascopy stores price * 100000
    
    @staticmethod
    def parse_ticks(
        data: bytes,
        hour_start: datetime
    ) -> List[Tick]:
        """
        Parse binary tick data.
        
        CRITICAL: Timestamps are CUMULATIVE deltas from hour start.
        
        Args:
            data: Decompressed bi5 data
            hour_start: Hour start time (for timestamp calculation)
            
        Returns:
            List of Tick objects
            
        Raises:
            ValueError: If data is corrupted or tick order violated
        """
        if len(data) % TickParser.TICK_SIZE != 0:
            raise ValueError(
                f"Invalid data size: {len(data)} bytes "
                f"(not multiple of {TickParser.TICK_SIZE})"
            )
        
        num_ticks = len(data) // TickParser.TICK_SIZE
        ticks = []
        cumulative_ms = 0  # CRITICAL: Cumulative time delta
        
        for i in range(num_ticks):
            offset = i * TickParser.TICK_SIZE
            tick_data = data[offset:offset + TickParser.TICK_SIZE]
            
            try:
                tick, cumulative_ms = TickParser._parse_single_tick(
                    tick_data, 
                    hour_start, 
                    cumulative_ms
                )
                ticks.append(tick)
            except struct.error as e:
                raise ValueError(f"Failed to parse tick {i}: {e}")
        
        # STRICT VALIDATION: Tick order must be increasing
        if not TickParser.validate_tick_order(ticks):
            raise ValueError("Tick timestamp order violation detected")
        
        logger.debug(f"✅ Parsed {len(ticks)} ticks")
        
        return ticks
    
    @staticmethod
    def _parse_single_tick(
        data: bytes, 
        hour_start: datetime,
        _unused_cumulative_ms: int = 0
    ) -> tuple[Tick, int]:
        """
        Parse a single 20-byte tick.
        
        Binary format (big-endian):
        - 4 bytes: timestamp delta (ms from HOUR START)
        - 4 bytes: ask price (scaled by 100000)
        - 4 bytes: bid price (scaled by 100000)
        - 4 bytes: ask volume
        - 4 bytes: bid volume
        
        Returns:
            (Tick, timestamp_delta)
        """
        # Unpack big-endian unsigned integers
        (
            timestamp_delta,
            ask_scaled,
            bid_scaled,
            ask_volume,
            bid_volume
        ) = struct.unpack('>IIIII', data)
        
        # CRITICAL FIX: timestamp_delta is from HOUR START, not cumulative
        timestamp = hour_start + timedelta(milliseconds=timestamp_delta)
        
        # Descale prices (CRITICAL: Must normalize to float)
        ask = ask_scaled / TickParser.PRICE_SCALE
        bid = bid_scaled / TickParser.PRICE_SCALE
        
        # VALIDATION: Bid/Ask sanity
        if bid <= 0 or ask <= 0:
            raise ValueError(f"Invalid prices: bid={bid}, ask={ask}")
        
        tick = Tick(
            timestamp=timestamp,
            bid=bid,  # CRITICAL: Use BID for Structure Engine
            ask=ask,
            bid_volume=float(bid_volume),
            ask_volume=float(ask_volume)
        )
        
        return tick, timestamp_delta
    
    @staticmethod
    def validate_tick_order(ticks: List[Tick]) -> bool:
        """
        Validate that ticks are in chronological order.
        
        Returns:
            True if valid, False otherwise
        """
        if len(ticks) < 2:
            return True
        
        for i in range(1, len(ticks)):
            if ticks[i].timestamp < ticks[i-1].timestamp:
                logger.error(
                    f"❌ Tick order violation at index {i}: "
                    f"{ticks[i-1].timestamp} -> {ticks[i].timestamp}"
                )
                return False
        
        return True
