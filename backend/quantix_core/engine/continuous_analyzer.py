import time
import pandas as pd
from datetime import datetime, timezone
from loguru import logger
from typing import Optional

from quantix_core.config.settings import settings
from quantix_core.ingestion.twelve_data_client import TwelveDataClient
from quantix_core.engine.structure_engine_v1 import StructureEngineV1
from quantix_core.database.connection import db

class ContinuousAnalyzer:
    """
    Quantix AI Core Heartbeat [T0 + Δ]
    Runs every few seconds to detect the highest-confidence moment.
    Implements Frequency Rule: Max 1 signal per day.
    """
    
    def __init__(self):
        self.td_client = TwelveDataClient()
        self.engine = StructureEngineV1(sensitivity=2)
        self.last_execution_date = None
        logger.info("💓 Quantix Heartbeat [T0+Δ] Initialized")

    def convert_to_df(self, td_data: dict) -> pd.DataFrame:
        """Convert TwelveData series to StructureEngine compatible DataFrame"""
        if "values" not in td_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(td_data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime")
        
        # Structure Engine expects float columns
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype(float)
        
        return df

    def has_traded_today(self) -> bool:
        """Check [T1] for Daily Execution Cap [1/day]"""
        today = datetime.now(timezone.utc).date()
        if self.last_execution_date == today:
            return True
            
        # Check database as fallback/persistent check
        try:
            res = db.client.table(settings.TABLE_SIGNALS)\
                .select("id")\
                .gte("generated_at", today.isoformat())\
                .limit(1)\
                .execute()
            
            if res.data:
                self.last_execution_date = today
                return True
        except Exception as e:
            logger.error(f"Failed to check daily cap in [T1]: {e}")
            
        return False

    def lock_signal(self, signal_data: dict):
        """LOCK signal with timestamp in Immutable Record [T1]"""
        try:
            res = db.client.table(settings.TABLE_SIGNALS).insert(signal_data).execute()
            if res.data:
                logger.info(f"🔒 Signal LOCKED in [T1]: {res.data[0]['id']}")
                self.last_execution_date = datetime.now(timezone.utc).date()
        except Exception as e:
            logger.error(f"❌ Failed to LOCK signal in [T1]: {e}")

    def run_cycle(self):
        """One analysis cycle [T0 + Δ]"""
        try:
            # 1. Continuous Feed [T0]
            raw_data = self.td_client.get_time_series(symbol="EUR/USD", interval="15min", outputsize=100)
            df = self.convert_to_df(raw_data)
            
            if df.empty:
                return

            # 2. Market Analysis
            state = self.engine.analyze(df, symbol="EURUSD", timeframe="M15", source="twelve_data")
            
            # 3. Detect Highest Confidence Moment
            # Ngưỡng tối thiểu để tạo signal là 75%
            if state.confidence >= 0.75:
                logger.info(f"🎯 High Confidence Moment Detected: {state.confidence*100:.1f}%")
                
                # 4. Frequency Rule: Max 1/day
                if not self.has_traded_today():
                    # CREATE signal
                    price = float(df.iloc[-1]["close"])
                    signal = {
                        "asset": "EURUSD",
                        "direction": state.state.upper() if state.state in ["bullish", "bearish"] else "BUY",
                        "timeframe": "M15",
                        "entry_low": price,
                        "entry_high": price + 0.0002,
                        "tp": price + 0.0020 if state.state == "bullish" else price - 0.0020,
                        "sl": price - 0.0015 if state.state == "bullish" else price + 0.0015,
                        "ai_confidence": state.confidence,
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "strategy": "Structure Alpha v1.0",
                        "status": "ACTIVE"
                    }
                    
                    # 5. LOCK signal [T1]
                    self.lock_signal(signal)
                else:
                    logger.info("⏭️ Signal creation skipped: Daily cap [1/day] reached.")
            else:
                logger.debug(f"⚖️ Evaluating... Confidence: {state.confidence*100:.1f}%")

        except Exception as e:
            logger.error(f"Heartbeat cycle failed: {e}")

    def start(self):
        """Start the continuous evaluation loop"""
        interval = settings.MONITOR_INTERVAL_SECONDS
        while True:
            self.run_cycle()
            time.sleep(interval)

if __name__ == "__main__":
    analyzer = ContinuousAnalyzer()
    analyzer.start()
