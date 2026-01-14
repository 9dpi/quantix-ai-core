"""
Quantix Outcome Resolver - Market Truth Engine
"""

from typing import List, Dict, Any
from datetime import datetime
from loguru import logger
from schemas.signal import SignalOutput

class OutcomeResolver:
    """The Market Truth: No cheating, just price action"""

    def resolve_signal(self, signal: Dict[str, Any], candles: List[Dict[str, Any]]) -> str:
        """
        Scan candles chronologically to see what price hit first.
        Priority: SL hits before TP in the same candle for conservative scoring.
        """
        for c in candles:
            if signal['direction'] == "BUY":
                # Conservative: check SL first in same candle
                if float(c['low']) <= float(signal['sl']):
                    return "HIT_SL"
                if float(c['high']) >= float(signal['tp']):
                    return "HIT_TP"
            
            elif signal['direction'] == "SELL":
                if float(c['high']) <= float(signal['sl']):
                    return "HIT_SL"
                if float(c['low']) >= float(signal['tp']):
                    return "HIT_TP"
                    
        return "EXPIRED"

    def compute_r_multiple(self, outcome: str, signal: Dict[str, Any]) -> float:
        """
        Standardized Reward-to-Risk scoring
        """
        if outcome == "HIT_TP":
            return float(signal.get('reward_risk_ratio', 1.0))
        if outcome == "HIT_SL":
            return -1.0
        return 0.0

    async def batch_resolve_open_signals(self):
        """
        Process all OPEN signals from Supabase against latest market data
        """
        logger.info("📡 Scanning open signals for market resolution...")
        # Implementation will fetch from backend/database/connection.py
        pass
