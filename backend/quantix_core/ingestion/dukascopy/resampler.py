"""
Candle Resampler - Tick to OHLC conversion
Production-grade with deterministic rules

Principle: BID price, UTC boundaries, no broker timezone bias
"""

from typing import List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

from quantix_core.ingestion.dukascopy.tick_parser import Tick


@dataclass
class Candle:
    """
    OHLC Candle representation.
    
    Attributes:
        timestamp: Candle open time (UTC)
        open: Open price
        high: High price
        low: Low price
        close: Close price
        volume: Total volume
        tick_count: Number of ticks in candle
        complete: True only if full window has ticks (CRITICAL for Structure Engine)
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    tick_count: int
    complete: bool = True  # Default True, set False if partial window


class CandleResampler:
    """
    Resamples ticks into OHLC candles.
    
    Rules (FROZEN):
    - Use BID price (consistent, deterministic)
    - UTC boundaries (no broker timezone)
    - H4: 00-04, 04-08, 08-12, 12-16, 16-20, 20-24
    - D1: 00:00 - 23:59
    """
    
    # H4 boundaries (UTC hours)
    H4_BOUNDARIES = [0, 4, 8, 12, 16, 20, 24]
    
    @staticmethod
    def resample_h4(ticks: List[Tick]) -> List[Candle]:
        """
        Resample ticks to H4 candles.
        
        Args:
            ticks: List of ticks (must be sorted by timestamp)
            
        Returns:
            List of H4 candles
        """
        if not ticks:
            return []
        
        logger.info(f"🔄 Resampling {len(ticks)} ticks to H4")
        
        # Group ticks by H4 window
        windows = CandleResampler._group_by_h4_window(ticks)
        
        # Build candles
        candles = []
        for window_start, window_ticks in sorted(windows.items()):
            if window_ticks:
                candle = CandleResampler._build_candle(window_start, window_ticks)
                candles.append(candle)
        
        logger.info(f"✅ Created {len(candles)} H4 candles")
        
        return candles
    
    @staticmethod
    def resample_d1(ticks: List[Tick]) -> List[Candle]:
        """
        Resample ticks to D1 candles.
        
        Args:
            ticks: List of ticks (must be sorted by timestamp)
            
        Returns:
            List of D1 candles
        """
        if not ticks:
            return []
        
        logger.info(f"🔄 Resampling {len(ticks)} ticks to D1")
        
        # Group ticks by day
        windows = CandleResampler._group_by_day(ticks)
        
        # Build candles
        candles = []
        for window_start, window_ticks in sorted(windows.items()):
            if window_ticks:
                candle = CandleResampler._build_candle(window_start, window_ticks)
                candles.append(candle)
        
        logger.info(f"✅ Created {len(candles)} D1 candles")
        
        return candles
    
    @staticmethod
    def _group_by_h4_window(ticks: List[Tick]) -> Dict[datetime, List[Tick]]:
        """
        Group ticks by H4 window.
        
        H4 windows: 00-04, 04-08, 08-12, 12-16, 16-20, 20-24 UTC
        """
        windows = {}
        
        for tick in ticks:
            # Determine H4 window start
            hour = tick.timestamp.hour
            
            # Find window boundary
            window_hour = 0
            for boundary in CandleResampler.H4_BOUNDARIES:
                if hour >= boundary:
                    window_hour = boundary
                else:
                    break
            
            # Create window start timestamp
            window_start = tick.timestamp.replace(
                hour=window_hour,
                minute=0,
                second=0,
                microsecond=0
            )
            
            # Add to window
            if window_start not in windows:
                windows[window_start] = []
            windows[window_start].append(tick)
        
        return windows
    
    @staticmethod
    def _group_by_day(ticks: List[Tick]) -> Dict[datetime, List[Tick]]:
        """
        Group ticks by day (00:00 UTC).
        """
        windows = {}
        
        for tick in ticks:
            # Day start = 00:00 UTC
            day_start = tick.timestamp.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )
            
            if day_start not in windows:
                windows[day_start] = []
            windows[day_start].append(tick)
        
        return windows
    
    @staticmethod
    def _build_candle(
        window_start: datetime, 
        ticks: List[Tick],
        min_ticks: int = 10
    ) -> Candle:
        """
        Build OHLC candle from ticks.
        
        Rules (FROZEN):
        - Use BID price (CRITICAL for Structure Engine)
        - Open = first tick bid
        - High = max tick bid
        - Low = min tick bid
        - Close = last tick bid
        - Volume = sum of bid volumes
        - Complete = True only if tick_count >= min_ticks
        
        Args:
            window_start: Candle open time
            ticks: List of ticks in window
            min_ticks: Minimum ticks required for complete candle
            
        Returns:
            Candle object
            
        Raises:
            ValueError: If ticks list is empty
        """
        if not ticks:
            raise ValueError("Cannot build candle from empty tick list")
        
        # Extract bid prices (CRITICAL: Use BID, not ASK)
        bid_prices = [tick.bid for tick in ticks]
        
        # OHLC from BID
        open_price = ticks[0].bid
        high = max(bid_prices)
        low = min(bid_prices)
        close = ticks[-1].bid
        
        # Volume from BID side
        volume = sum(tick.bid_volume for tick in ticks)
        
        # CRITICAL: Complete flag logic
        # Only mark complete if we have sufficient ticks
        # This prevents partial windows from contaminating Structure Engine
        complete = len(ticks) >= min_ticks
        
        if not complete:
            logger.warning(
                f"⚠️ Partial candle at {window_start}: "
                f"{len(ticks)} ticks (min {min_ticks} required)"
            )
        
        return Candle(
            timestamp=window_start,
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume,
            tick_count=len(ticks),
            complete=complete
        )
