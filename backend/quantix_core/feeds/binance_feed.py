"""
BinanceFeed — Phase 1 feed (Binance REST API proxy)
====================================================
Uses Binance EURUSDT 1m klines as a Forex price proxy.
Fallback chain: global → US → developer API endpoint.
"""

import requests
from datetime import datetime, timezone
from typing import Optional, Dict

from .base_feed import BaseFeed

# EURUSD ≈ EURUSDT — close enough for proxy validation
_SYMBOL_MAP = {
    "EURUSD": "EURUSDT",
    "GBPUSD": "GBPUSDT",
    "USDJPY": "USDTJPY",   # Inverted — handled below
    "AUDUSD": "AUDUSDT",
    "USDCAD": "USDTCAD",
}

_ENDPOINTS = [
    "https://api.binance.com/api/v3/klines",
    "https://api.binance.us/api/v3/klines",
    "https://data-api.binance.vision/api/v3/klines",
]

# Typical Binance EURUSDT spread offset (pips) added to bid/ask simulation
_SIMULATED_SPREAD_PIPS = 0.2


class BinanceFeed(BaseFeed):
    """
    Binance REST API proxy feed.

    Strengths : Always available, no credentials, Railway-compatible.
    Weakness  : Not real Pepperstone spread — Phase 1 baseline only.
    """

    def __init__(self, timeout: int = 5):
        self.timeout = timeout

    # ------------------------------------------------------------------
    # BaseFeed contract
    # ------------------------------------------------------------------

    def get_price(self, symbol: str = "EURUSD") -> Optional[Dict]:
        """Fetch latest 1m candle from Binance."""
        binance_symbol = _SYMBOL_MAP.get(symbol.upper(), f"{symbol}T")
        params = {"symbol": binance_symbol, "interval": "1m", "limit": 5}

        for url in _ENDPOINTS:
            try:
                resp = requests.get(url, params=params, timeout=self.timeout)
                if resp.status_code != 200:
                    continue

                data = resp.json()
                if not data:
                    continue

                candle = data[-1]
                close = float(candle[4])
                half_spread = (_SIMULATED_SPREAD_PIPS / 2) * 0.0001

                return {
                    "timestamp": datetime.fromtimestamp(
                        candle[0] / 1000, tz=timezone.utc
                    ).isoformat(),
                    "open":       float(candle[1]),
                    "high":       float(candle[2]),
                    "low":        float(candle[3]),
                    "close":      close,
                    "bid":        round(close - half_spread, 5),
                    "ask":        round(close + half_spread, 5),
                    "spread_pips": _SIMULATED_SPREAD_PIPS,
                    "source":     f"binance_proxy ({url})",
                }
            except Exception:
                continue

        return None  # All endpoints failed

    def get_history(self, symbol: str = "EURUSD", interval: str = "15m", limit: int = 100) -> Optional[list]:
        """Fetch historical candles from Binance."""
        binance_symbol = _SYMBOL_MAP.get(symbol.upper(), f"{symbol}T")
        params = {"symbol": binance_symbol, "interval": interval, "limit": limit}

        for url in _ENDPOINTS:
            try:
                resp = requests.get(url, params=params, timeout=self.timeout)
                if resp.status_code != 200:
                    continue

                data = resp.json()
                if not data:
                    continue

                history = []
                for candle in data:
                    history.append({
                        "datetime": datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc).isoformat(),
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4])
                    })
                return history
            except Exception:
                continue
        return None

    def is_available(self) -> bool:
        try:
            resp = requests.get(
                _ENDPOINTS[0],
                params={"symbol": "EURUSDT", "interval": "1m", "limit": 1},
                timeout=self.timeout,
            )
            return resp.status_code == 200
        except Exception:
            return False
