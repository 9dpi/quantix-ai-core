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

    def _get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Base GET request with retry logic and protection headers."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
        last_error = None
        for attempt in range(3):  # Retry up to 3 times
            try:
                # Add apikey to params
                params["apikey"] = self.api_key
                
                response = requests.get(url, params=params, headers=headers, timeout=15)
                
                if response.status_code == 429:
                    import time
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"⚠️ Rate limited (429). Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "error":
                    logger.error(f"TwelveData API error: {data.get('message')}")
                    return {"status": "error", "message": data.get("message")}
                
                return data
                
            except Exception as e:
                last_error = e
                import time
                time.sleep(1)
                continue
                
        logger.error(f"❌ API call failed after 3 attempts: {last_error}")
        raise last_error

    def get_realtime_price(self, symbol: str = "EUR/USD") -> float:
        """Fetch current price for targeted asset [T0]"""
        params = {"symbol": symbol}
        data = self._get("price", params)
        
        if "price" not in data:
            raise ValueError(f"TwelveData Error: {data.get('message', 'Unknown error')}")
            
        return float(data["price"])

    def get_time_series(self, symbol: str = "EUR/USD", interval: str = "15min", outputsize: int = 50) -> Dict[str, Any]:
        """Fetch historical candles for analysis [T0 + Δ]"""
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize
        }
        return self._get("time_series", params)
