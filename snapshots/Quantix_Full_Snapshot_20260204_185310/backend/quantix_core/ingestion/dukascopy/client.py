"""
Dukascopy Client - Tick data downloader
Production-grade with retry logic and decompression

Principle: Ground truth FX feed, no geo-block, UTC timezone
"""

import requests
import lzma
import struct
from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type


class DukascopyClientError(Exception):
    """Base exception for Dukascopy client errors"""
    pass


class DukascopyClient:
    """
    Downloads tick data from Dukascopy datafeed.
    
    Features:
    - Free, no auth required
    - No geo-blocking
    - UTC timezone (clean boundaries)
    - Tick-level precision
    """
    
    BASE_URL = "https://datafeed.dukascopy.com/datafeed"
    
    # Symbol mapping (Quantix -> Dukascopy)
    SYMBOL_MAP = {
        "EURUSD": "EURUSD",
        "GBPUSD": "GBPUSD",
        "USDJPY": "USDJPY",
        "AUDUSD": "AUDUSD",
        "USDCAD": "USDCAD",
        "NZDUSD": "NZDUSD",
        "USDCHF": "USDCHF"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
        reraise=True
    )
    def download_hour_ticks(
        self,
        symbol: str,
        date: datetime,
        hour: int
    ) -> Optional[bytes]:
        """
        Download tick data for a specific hour.
        
        Args:
            symbol: Quantix symbol (e.g., "EURUSD")
            date: Date to download
            hour: Hour (0-23)
            
        Returns:
            Decompressed tick data bytes or None if not available
            
        Raises:
            DukascopyClientError: On download/decompression failure
        """
        # Resolve symbol
        dukascopy_symbol = self.SYMBOL_MAP.get(symbol)
        if not dukascopy_symbol:
            raise DukascopyClientError(f"Symbol {symbol} not supported")
        
        # Build URL
        # Format: {SYMBOL}/{YYYY}/{MM}/{DD}/{HH}h_ticks.bi5
        # CRITICAL: MM is 0-indexed (0-11), not 1-indexed!
        url = (
            f"{self.BASE_URL}/{dukascopy_symbol}/"
            f"{date.year:04d}/"
            f"{date.month-1:02d}/"  # 0-indexed: January = 00, December = 11
            f"{date.day:02d}/"
            f"{hour:02d}h_ticks.bi5"
        )
        
        logger.debug(f"📥 Downloading: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            
            # 404 = no data for this hour (weekends, holidays)
            if response.status_code == 404:
                logger.debug(f"⏭️ No data for {symbol} {date.date()} {hour:02d}:00")
                return None
            
            response.raise_for_status()
            
            # FAIL HARD: HTTP 200 but empty content
            if len(response.content) == 0:
                raise DukascopyClientError(
                    f"Empty response (0 bytes) for {symbol} {date.date()} {hour:02d}:00"
                )
            
            # Decompress LZMA (.bi5 format)
            try:
                decompressed = lzma.decompress(response.content)
                
                # FAIL HARD: Decompressed but empty
                if len(decompressed) == 0:
                    raise DukascopyClientError(
                        f"Decompressed to 0 bytes for {symbol} {date.date()} {hour:02d}:00"
                    )
                
                logger.debug(f"✅ Downloaded {len(decompressed)} bytes")
                return decompressed
                
            except lzma.LZMAError as e:
                # FAIL HARD: Corruption
                raise DukascopyClientError(
                    f"LZMA decompression failed for {symbol} {date.date()} {hour:02d}:00: {e}"
                )
            
        except requests.Timeout:
            logger.warning(f"⏱️ Timeout downloading {url}")
            raise
        except requests.RequestException as e:
            raise DukascopyClientError(f"Download failed: {e}")
    
    def download_day_ticks(
        self,
        symbol: str,
        date: datetime
    ) -> List[bytes]:
        """
        Download all tick data for a day (24 hours).
        
        Args:
            symbol: Quantix symbol
            date: Date to download
            
        Returns:
            List of decompressed tick data (one per hour)
        """
        logger.info(f"📦 Downloading {symbol} for {date.date()}")
        
        tick_chunks = []
        
        for hour in range(24):
            try:
                data = self.download_hour_ticks(symbol, date, hour)
                if data:
                    tick_chunks.append(data)
            except Exception as e:
                logger.error(f"❌ Failed to download hour {hour}: {e}")
                # Continue with other hours
                continue
        
        logger.info(f"✅ Downloaded {len(tick_chunks)}/24 hours for {date.date()}")
        
        return tick_chunks
    
    def download_date_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        Download tick data for a date range.
        
        Args:
            symbol: Quantix symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Dict mapping date -> list of tick chunks
        """
        logger.info(f"📚 Downloading {symbol} from {start_date.date()} to {end_date.date()}")
        
        data_by_date = {}
        current_date = start_date
        
        while current_date <= end_date:
            tick_chunks = self.download_day_ticks(symbol, current_date)
            if tick_chunks:
                data_by_date[current_date.date()] = tick_chunks
            
            current_date += timedelta(days=1)
        
        logger.info(f"✅ Downloaded {len(data_by_date)} days")
        
        return data_by_date
