import os
import requests
from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime, timezone

class TwelveDataClient:
    """
    Twelve Data Client for Quantix AI Core [T0]
    Continuous feed implementation for market analysis.
    """
    BASE_URL = "https://api.twelvedata.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TWELVE_DATA_API_KEY")
        if not self.api_key:
            logger.warning("TWELVE_DATA_API_KEY not found in environment")

    def get_realtime_price(self, symbol: str = "EUR/USD") -> float:
        """Fetch current price for targeted asset [T0]"""
        try:
            params = {
                "symbol": symbol,
                "apikey": self.api_key
            }
            response = requests.get(f"{self.BASE_URL}/price", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "price" not in data:
                raise ValueError(f"TwelveData Error: {data.get('message', 'Unknown error')}")
                
            return float(data["price"])
        except Exception as e:
            logger.error(f"Failed to fetch [T0] market data: {e}")
            raise

    def get_time_series(self, symbol: str = "EUR/USD", interval: str = "15min", outputsize: int = 50) -> Dict[str, Any]:
        """Fetch historical candles for analysis [T0 + Δ]"""
        try:
            params = {
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": self.api_key
            }
            response = requests.get(f"{self.BASE_URL}/time_series", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch time series for [T0+Δ]: {e}")
            raise
