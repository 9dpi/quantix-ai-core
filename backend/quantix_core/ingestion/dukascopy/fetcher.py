"""
Dukascopy Fetcher - High-level OHLCV data fetcher
Wraps DukascopyClient + TickParser + CandleResampler

Purpose: Provide Yahoo Finance-compatible interface for API routes
"""

from typing import Dict, List
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd

from quantix_core.ingestion.dukascopy.client import DukascopyClient, DukascopyClientError
from quantix_core.ingestion.dukascopy.tick_parser import TickParser
from quantix_core.ingestion.dukascopy.resampler import CandleResampler


class DukascopyFetcherError(Exception):
    """Dukascopy fetcher error with error_code for API responses"""
    def __init__(self, error_code: str, message: str, details: dict = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class DukascopyFetcher:
    """
    High-level fetcher for OHLCV data from Dukascopy.
    
    Compatible with YahooFinanceFetcher interface for drop-in replacement.
    
    Features:
    - Tick-level precision
    - UTC timezone (no broker bias)
    - BID price (deterministic)
    - Free, no auth required
    """
    
    # Period mapping (Yahoo-style → days)
    PERIOD_MAP = {
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "2y": 730
    }
    
    # Timeframe mapping
    TIMEFRAME_MAP = {
        "H1": "1h",
        "H4": "4h",
        "D1": "1d"
    }
    
    def __init__(self):
        self.client = DukascopyClient()
        self.parser = TickParser()
        logger.info("✅ DukascopyFetcher initialized")
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "H4",
        period: str = "3mo"
    ) -> Dict:
        """
        Fetch OHLCV data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            timeframe: Timeframe (H1, H4, D1)
            period: Data period (1mo, 3mo, 6mo, 1y, 2y)
            
        Returns:
            Dict with structure:
            {
                "symbol": str,
                "timeframe": str,
                "data": [
                    {
                        "timestamp": datetime,
                        "open": float,
                        "high": float,
                        "low": float,
                        "close": float,
                        "volume": float
                    },
                    ...
                ],
                "source": "dukascopy",
                "fetched_at": datetime
            }
            
        Raises:
            DukascopyFetcherError: On fetch/processing failure
        """
        logger.info(f"📊 Fetching {symbol} @ {timeframe} for {period}")
        
        try:
            # 1. Calculate date range
            end_date = datetime.utcnow()
            days = self.PERIOD_MAP.get(period, 90)
            start_date = end_date - timedelta(days=days)
            
            logger.debug(f"📅 Date range: {start_date.date()} → {end_date.date()}")
            
            # 2. Download tick data
            try:
                tick_data_by_date = self.client.download_date_range(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
            except DukascopyClientError as e:
                raise DukascopyFetcherError(
                    error_code="DOWNLOAD_FAILED",
                    message=f"Failed to download tick data: {str(e)}",
                    details={"symbol": symbol, "period": period}
                )
            
            if not tick_data_by_date:
                raise DukascopyFetcherError(
                    error_code="NO_DATA",
                    message=f"No tick data available for {symbol}",
                    details={
                        "symbol": symbol,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    }
                )
            
            # 3. Parse ticks
            all_ticks = []
            for date, tick_chunks in tick_data_by_date.items():
                for chunk in tick_chunks:
                    try:
                        ticks = self.parser.parse(chunk)
                        all_ticks.extend(ticks)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to parse tick chunk for {date}: {e}")
                        continue
            
            if not all_ticks:
                raise DukascopyFetcherError(
                    error_code="PARSE_FAILED",
                    message="Failed to parse any ticks",
                    details={"symbol": symbol, "chunks_downloaded": len(tick_data_by_date)}
                )
            
            logger.info(f"✅ Parsed {len(all_ticks)} ticks")
            
            # 4. Resample to candles
            if timeframe == "H4":
                candles = CandleResampler.resample_h4(all_ticks)
            elif timeframe == "D1":
                candles = CandleResampler.resample_d1(all_ticks)
            elif timeframe == "H1":
                # TODO: Implement H1 resampling
                raise DukascopyFetcherError(
                    error_code="TIMEFRAME_NOT_SUPPORTED",
                    message="H1 timeframe not yet implemented",
                    details={"supported": ["H4", "D1"]}
                )
            else:
                raise DukascopyFetcherError(
                    error_code="INVALID_TIMEFRAME",
                    message=f"Invalid timeframe: {timeframe}",
                    details={"supported": ["H4", "D1"]}
                )
            
            if not candles:
                raise DukascopyFetcherError(
                    error_code="RESAMPLE_FAILED",
                    message="Failed to create any candles",
                    details={"symbol": symbol, "timeframe": timeframe, "ticks": len(all_ticks)}
                )
            
            # 5. Convert to API format
            data = [
                {
                    "timestamp": candle.timestamp,
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume
                }
                for candle in candles
                if candle.complete  # CRITICAL: Only include complete candles
            ]
            
            logger.info(f"✅ Fetched {len(data)} complete {timeframe} candles")
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "data": data,
                "source": "dukascopy",
                "fetched_at": datetime.utcnow()
            }
            
        except DukascopyFetcherError:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching {symbol}: {e}")
            raise DukascopyFetcherError(
                error_code="UNKNOWN_ERROR",
                message=str(e),
                details={"symbol": symbol, "timeframe": timeframe, "period": period}
            )
