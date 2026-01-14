"""
OANDA Client - Read-only market data fetcher
Production-grade with retry logic and error handling

Principle: Single source of truth, no writes, deterministic
"""

import requests
from typing import List, Dict, Optional
from loguru import logger
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import os


class OandaClientError(Exception):
    """Base exception for OANDA client errors"""
    pass


class OandaAuthError(OandaClientError):
    """Authentication failed - FAIL HARD"""
    pass


class OandaRateLimitError(OandaClientError):
    """Rate limit hit - needs backoff"""
    pass


class OandaClient:
    """
    Read-only OANDA API client for market data.
    
    Features:
    - Automatic retry with exponential backoff
    - Rate limit handling
    - Clean error messages
    - Audit logging
    """
    
    # OANDA granularity mapping
    GRANULARITY_MAP = {
        "M1": "M1",
        "M5": "M5",
        "M15": "M15",
        "M30": "M30",
        "H1": "H1",
        "H4": "H4",
        "D": "D",
        "W": "W",
        "M": "M"
    }
    
    def __init__(self, api_key: Optional[str] = None, practice: bool = True):
        """
        Initialize OANDA client.
        
        Args:
            api_key: OANDA API key (defaults to env OANDA_API_KEY)
            practice: Use practice account (default True for safety)
        """
        self.api_key = api_key or os.getenv("OANDA_API_KEY")
        if not self.api_key:
            raise OandaAuthError("OANDA_API_KEY not found in environment")
        
        # Use practice or live endpoint
        if practice:
            self.base_url = "https://api-fxpractice.oanda.com/v3"
        else:
            self.base_url = "https://api-fxtrade.oanda.com/v3"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"🔌 OANDA Client initialized ({'practice' if practice else 'live'} mode)")
    
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((requests.Timeout, OandaRateLimitError)),
        reraise=True
    )
    def fetch_candles(
        self,
        instrument: str,
        granularity: str,
        count: int = 500,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch candles from OANDA.
        
        Args:
            instrument: OANDA instrument (e.g., "EUR_USD")
            granularity: Timeframe (e.g., "H1", "H4")
            count: Number of candles (max 5000)
            from_time: Start time (RFC3339 format)
            to_time: End time (RFC3339 format)
            
        Returns:
            List of candle dictionaries
            
        Raises:
            OandaAuthError: Authentication failed
            OandaRateLimitError: Rate limit exceeded
            OandaClientError: Other API errors
        """
        # Validate granularity
        if granularity not in self.GRANULARITY_MAP:
            raise ValueError(f"Invalid granularity: {granularity}")
        
        oanda_granularity = self.GRANULARITY_MAP[granularity]
        
        # Build request
        url = f"{self.base_url}/instruments/{instrument}/candles"
        
        params = {
            "granularity": oanda_granularity,
            "price": "M",  # Mid price (most stable for analysis)
        }
        
        # Add time constraints if provided
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        if not from_time and not to_time:
            params["count"] = min(count, 5000)  # OANDA max
        
        logger.info(f"📥 Fetching {instrument} {granularity} candles from OANDA...")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            # Handle specific error codes
            if response.status_code == 401:
                raise OandaAuthError("Invalid API key or unauthorized")
            elif response.status_code == 429:
                raise OandaRateLimitError("Rate limit exceeded")
            elif response.status_code >= 500:
                raise OandaClientError(f"OANDA server error: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            candles = data.get("candles", [])
            
            logger.info(f"✅ Received {len(candles)} candles from OANDA")
            
            return candles
            
        except requests.Timeout:
            logger.warning("⏱️ OANDA request timeout - will retry")
            raise
        except requests.RequestException as e:
            logger.error(f"❌ OANDA request failed: {e}")
            raise OandaClientError(f"Request failed: {e}")
    
    def get_latest_candles(
        self,
        instrument: str = "EUR_USD",
        granularity: str = "H4",
        count: int = 500
    ) -> List[Dict]:
        """
        Convenience method to get latest N candles.
        
        This is the primary method for ingestion workers.
        """
        return self.fetch_candles(instrument, granularity, count)
    
    def health_check(self) -> bool:
        """
        Check if OANDA API is accessible.
        
        Returns:
            True if API is healthy
        """
        try:
            # Try to fetch 1 candle as health check
            self.fetch_candles("EUR_USD", "H1", count=1)
            return True
        except Exception as e:
            logger.error(f"❌ OANDA health check failed: {e}")
            return False
