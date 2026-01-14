"""
Symbol Resolver - Normalization layer between Quantix AI and data providers
Quantix uses standard symbols (EURUSD), providers use their own format (EURUSD=X)
"""

from typing import Dict, Optional


class SymbolResolver:
    """
    Resolves Quantix standard symbols to provider-specific formats.
    
    Principle: Feature Engine DOES NOT KNOW about Yahoo/Binance/etc.
    Data Layer handles all provider-specific mappings.
    """
    
    # Yahoo Finance symbol mapping
    YAHOO_FOREX_MAP: Dict[str, str] = {
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "AUDUSD": "AUDUSD=X",
        "USDCAD": "USDCAD=X",
        "NZDUSD": "NZDUSD=X",
        "USDCHF": "USDCHF=X",
        "EURGBP": "EURGBP=X",
        "EURJPY": "EURJPY=X",
        "GBPJPY": "GBPJPY=X"
    }
    
    # Timeframe to Yahoo interval mapping
    YAHOO_INTERVAL_MAP: Dict[str, str] = {
        "M1": "1m",
        "M5": "5m",
        "M15": "15m",
        "M30": "30m",
        "H1": "60m",
        "H4": "60m",  # Will aggregate 4x H1 candles
        "D1": "1d",
        "W1": "1wk",
        "MN": "1mo"
    }
    
    # Aggregation factors for synthetic timeframes
    AGGREGATION_FACTORS: Dict[str, int] = {
        "H4": 4,  # 4x H1 candles
    }
    
    @classmethod
    def resolve_yahoo_symbol(cls, symbol: str) -> Optional[str]:
        """
        Resolve Quantix symbol to Yahoo Finance format.
        
        Args:
            symbol: Quantix standard symbol (e.g., "EURUSD")
            
        Returns:
            Yahoo symbol (e.g., "EURUSD=X") or None if not supported
        """
        return cls.YAHOO_FOREX_MAP.get(symbol.upper())
    
    @classmethod
    def resolve_yahoo_interval(cls, timeframe: str) -> Optional[str]:
        """
        Resolve Quantix timeframe to Yahoo interval.
        
        Args:
            timeframe: Quantix timeframe (e.g., "H4")
            
        Returns:
            Yahoo interval (e.g., "60m") or None if not supported
        """
        return cls.YAHOO_INTERVAL_MAP.get(timeframe.upper())
    
    @classmethod
    def needs_aggregation(cls, timeframe: str) -> bool:
        """Check if timeframe requires candle aggregation"""
        return timeframe.upper() in cls.AGGREGATION_FACTORS
    
    @classmethod
    def get_aggregation_factor(cls, timeframe: str) -> int:
        """Get aggregation factor for synthetic timeframes"""
        return cls.AGGREGATION_FACTORS.get(timeframe.upper(), 1)
    
    @classmethod
    def get_supported_symbols(cls) -> list[str]:
        """Get list of supported Quantix symbols"""
        return list(cls.YAHOO_FOREX_MAP.keys())
    
    @classmethod
    def get_supported_timeframes(cls) -> list[str]:
        """Get list of supported timeframes"""
        return list(cls.YAHOO_INTERVAL_MAP.keys())
