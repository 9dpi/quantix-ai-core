"""
Yahoo Finance Data Fetcher for Quantix AI Core
Provides clean, normalized OHLCV data with explainable metadata
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional
from loguru import logger


class YahooFinanceFetcher:
    """
    Fetches and normalizes forex data from Yahoo Finance.
    Ensures data quality with timezone handling, missing day detection, and confidence scoring.
    """
    
    FOREX_SYMBOLS = {
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "AUDUSD": "AUDUSD=X",
        "USDCAD": "USDCAD=X"
    }
    
    def __init__(self):
        self.source = "yahoo_finance"
        self.version = "1.0.0"
    
    def fetch_daily_ohlcv(
        self, 
        symbol: str, 
        period: str = "1mo"
    ) -> Optional[Dict]:
        """
        Fetch daily OHLCV data for a forex pair.
        
        Args:
            symbol: Forex pair (e.g., "EURUSD")
            period: Time period (e.g., "1mo", "3mo", "1y")
            
        Returns:
            Dictionary with normalized data and metadata
        """
        try:
            yahoo_symbol = self.FOREX_SYMBOLS.get(symbol)
            if not yahoo_symbol:
                logger.error(f"❌ Unknown symbol: {symbol}")
                return None
            
            # Fetch data from Yahoo Finance
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(period=period, interval="1d")
            
            if df.empty:
                logger.warning(f"⚠️ No data returned for {symbol}")
                return None
            
            # Normalize data
            normalized_data = self._normalize_dataframe(df, symbol)
            
            # Calculate metadata
            metadata = self._generate_metadata(df, symbol, period)
            
            logger.info(f"✅ Fetched {len(df)} candles for {symbol}")
            
            return {
                "symbol": symbol,
                "data": normalized_data,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch {symbol}: {e}")
            return None
    
    def _normalize_dataframe(self, df: pd.DataFrame, symbol: str) -> List[Dict]:
        """
        Normalize Yahoo Finance dataframe to Quantix standard format.
        Handles timezone conversion, missing values, and data quality checks.
        """
        normalized = []
        
        for idx, row in df.iterrows():
            # Convert timezone-aware datetime to UTC ISO format
            timestamp = idx.tz_convert('UTC').isoformat() if idx.tzinfo else idx.isoformat() + 'Z'
            
            candle = {
                "timestamp": timestamp,
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume']) if pd.notna(row['Volume']) else 0,
                "source": self.source,
                "symbol": symbol
            }
            
            # Data quality flag
            candle["is_complete"] = all([
                pd.notna(row['Open']),
                pd.notna(row['High']),
                pd.notna(row['Low']),
                pd.notna(row['Close'])
            ])
            
            normalized.append(candle)
        
        return normalized
    
    def _generate_metadata(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        period: str
    ) -> Dict:
        """
        Generate explainable metadata for data quality and freshness tracking.
        """
        now = datetime.now(timezone.utc)
        latest_candle = df.index[-1]
        
        # Calculate freshness (hours since last candle)
        if latest_candle.tzinfo:
            freshness_hours = (now - latest_candle.tz_convert('UTC')).total_seconds() / 3600
        else:
            freshness_hours = (now - latest_candle.replace(tzinfo=timezone.utc)).total_seconds() / 3600
        
        # Detect missing days (weekends excluded)
        expected_days = pd.bdate_range(start=df.index[0], end=df.index[-1])
        actual_days = df.index.normalize()
        missing_days = len(expected_days) - len(actual_days)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(df, freshness_hours, missing_days)
        
        return {
            "source": self.source,
            "version": self.version,
            "fetched_at": now.isoformat(),
            "period": period,
            "total_candles": len(df),
            "date_range": {
                "start": df.index[0].isoformat(),
                "end": df.index[-1].isoformat()
            },
            "freshness_hours": round(freshness_hours, 2),
            "missing_business_days": missing_days,
            "confidence": confidence,
            "quality_flags": {
                "has_volume": df['Volume'].notna().sum() > 0,
                "no_null_ohlc": df[['Open', 'High', 'Low', 'Close']].notna().all().all(),
                "is_fresh": freshness_hours < 48  # Less than 2 days old
            }
        }
    
    def _calculate_confidence(
        self, 
        df: pd.DataFrame, 
        freshness_hours: float, 
        missing_days: int
    ) -> float:
        """
        Calculate data confidence score (0.0 to 1.0).
        Based on freshness, completeness, and missing data.
        """
        score = 1.0
        
        # Penalize stale data
        if freshness_hours > 24:
            score -= 0.1
        if freshness_hours > 48:
            score -= 0.2
        
        # Penalize missing days
        if missing_days > 0:
            score -= min(0.3, missing_days * 0.05)
        
        # Penalize incomplete OHLC data
        null_count = df[['Open', 'High', 'Low', 'Close']].isna().sum().sum()
        if null_count > 0:
            score -= min(0.3, null_count * 0.1)
        
        return max(0.0, min(1.0, score))


# Example usage
if __name__ == "__main__":
    fetcher = YahooFinanceFetcher()
    result = fetcher.fetch_daily_ohlcv("EURUSD", period="1mo")
    
    if result:
        print(f"Symbol: {result['symbol']}")
        print(f"Candles: {len(result['data'])}")
        print(f"Confidence: {result['metadata']['confidence']}")
        print(f"Freshness: {result['metadata']['freshness_hours']} hours")
