"""
Yahoo Finance Data Fetcher for Quantix AI Core (Production-grade)
Provides clean, normalized OHLCV data with explainable metadata
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional
from loguru import logger

from ingestion.symbol_resolver import SymbolResolver
from ingestion.candle_aggregator import CandleAggregator


class DataFetchError(Exception):
    """Rich error for data fetching failures"""
    def __init__(self, error_code: str, symbol: str, details: Dict):
        self.error_code = error_code
        self.symbol = symbol
        self.details = details
        super().__init__(f"{error_code}: {details}")


class YahooFinanceFetcher:
    """
    Fetches and normalizes forex data from Yahoo Finance.
    
    Production-grade with:
    - Symbol resolution
    - Timeframe aggregation
    - Rich error messages
    - Explainable metadata
    """
    
    def __init__(self):
        self.source = "yahoo_finance"
        self.version = "2.0.0"  # Updated for production
        self.resolver = SymbolResolver
        self.aggregator = CandleAggregator
    
    def fetch_ohlcv(
        self, 
        symbol: str,
        timeframe: str = "D1",
        period: str = "3mo"
    ) -> Optional[Dict]:
        """
        Fetch OHLCV data for any supported timeframe.
        
        Args:
            symbol: Quantix standard symbol (e.g., "EURUSD")
            timeframe: Quantix timeframe (e.g., "H4", "D1")
            period: Time period (e.g., "1mo", "3mo", "1y")
            
        Returns:
            Dictionary with normalized data and metadata
            
        Raises:
            DataFetchError: With rich error details for debugging
        """
        try:
            # Step 1: Resolve symbol
            yahoo_symbol = self.resolver.resolve_yahoo_symbol(symbol)
            if not yahoo_symbol:
                raise DataFetchError(
                    error_code="SYMBOL_NOT_SUPPORTED",
                    symbol=symbol,
                    details={
                        "message": f"Symbol '{symbol}' not supported",
                        "supported_symbols": self.resolver.get_supported_symbols()
                    }
                )
            
            # Step 2: Resolve interval
            yahoo_interval = self.resolver.resolve_yahoo_interval(timeframe)
            if not yahoo_interval:
                raise DataFetchError(
                    error_code="TIMEFRAME_NOT_SUPPORTED",
                    symbol=symbol,
                    details={
                        "message": f"Timeframe '{timeframe}' not supported",
                        "supported_timeframes": self.resolver.get_supported_timeframes()
                    }
                )
            
            logger.info(f"📊 Fetching {symbol} ({yahoo_symbol}) @ {timeframe} (interval={yahoo_interval})")
            
            # Step 3: Fetch from Yahoo
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(period=period, interval=yahoo_interval)
            
            logger.info(f"📦 Received {len(df)} candles from Yahoo")
            
            if df.empty:
                raise DataFetchError(
                    error_code="DATA_NOT_AVAILABLE",
                    symbol=symbol,
                    details={
                        "resolved_symbol": yahoo_symbol,
                        "interval": yahoo_interval,
                        "period": period,
                        "message": "Yahoo returned empty dataset"
                    }
                )
            
            # Step 4: Aggregate if needed (e.g., H1 → H4)
            if self.resolver.needs_aggregation(timeframe):
                factor = self.resolver.get_aggregation_factor(timeframe)
                logger.info(f"🔄 Aggregating {yahoo_interval} → {timeframe} (factor={factor})")
                df = self.aggregator.aggregate(df, factor)
                logger.info(f"✅ Aggregated to {len(df)} {timeframe} candles")
            
            # Step 5: Normalize data
            normalized_data = self._normalize_dataframe(df, symbol)
            
            # Step 6: Generate metadata
            metadata = self._generate_metadata(df, symbol, timeframe, period)
            
            logger.info(f"✅ Successfully fetched {len(normalized_data)} candles for {symbol} @ {timeframe}")
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "data": normalized_data,
                "metadata": metadata
            }
            
        except DataFetchError:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching {symbol}: {e}")
            raise DataFetchError(
                error_code="FETCH_FAILED",
                symbol=symbol,
                details={
                    "message": str(e),
                    "type": type(e).__name__
                }
            )
    
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
