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
        self.td_client = TwelveDataClient(api_key=settings.TWELVE_DATA_API_KEY)
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
                logger.warning("Empty data from TwelveData")
                return

            # 2. Market Analysis
            state = self.engine.analyze(df, symbol="EURUSD", timeframe="M15", source="twelve_data")
            
            # 3. Prepare Common Data
            price = float(df.iloc[-1]["close"])
            direction = state.state.upper() if state.state in ["bullish", "bearish"] else "BUY"
            
            # RRR Calculation
            tp = price + 0.0020 if state.state == "bullish" else price - 0.0020
            sl = price - 0.0015 if state.state == "bullish" else price + 0.0015
            rrr = round(abs(tp - price) / abs(price - sl), 2) if abs(price - sl) > 0 else 2.0

            signal_base = {
                "asset": "EURUSD",
                "direction": direction,
                "timeframe": "M15",
                "entry_low": price,
                "entry_high": price + 0.0002,
                "tp": tp,
                "sl": sl,
                "reward_risk_ratio": rrr,
                "ai_confidence": state.confidence,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "strategy": "Structure Alpha v1.0",
            }

            # 4. Local Audit Log (JSONL) - Proof of 24/7 Operation
            try:
                with open("heartbeat_audit.jsonl", "a") as f:
                    import json
                    f.write(json.dumps({
                        "timestamp": signal_base["generated_at"],
                        "asset": "EURUSD",
                        "price": price,
                        "confidence": state.confidence,
                        "status": "ANALYZED"
                    }) + "\n")
            except Exception as e:
                logger.error(f"Failed to write heartheat log: {e}")

            # 5. Logic Branching: LOCK (ACTIVE) or CANDIDATE
            if not db.client:
                logger.warning("DB Client offline - cannot save signals")
                return

            if state.confidence >= 0.75 and not self.has_traded_today():
                logger.info(f"🎯 High Confidence Moment Detected: {state.confidence*100:.1f}%")
                signal_base["status"] = "ACTIVE"
                self.lock_signal(signal_base)
            else:
                # Save as CANDIDATE for Quantix Lab [T0] visibility
                signal_base["status"] = "CANDIDATE"
                try:
                    db.client.table(settings.TABLE_SIGNALS).insert(signal_base).execute()
                    
                    # 🧹 Cleanup OLD candidates (older than 1 hour)
                    expiry = (datetime.now(timezone.utc) - pd.Timedelta(hours=1)).isoformat()
                    db.client.table(settings.TABLE_SIGNALS)\
                        .delete()\
                        .eq("status", "CANDIDATE")\
                        .lt("generated_at", expiry)\
                        .execute()
                except Exception as e:
                    logger.debug(f"Candidate not saved: {e}")

            # 6. Dashboard Telemetry Update (Learning Lab Preview)
            try:
                from analyze_heartbeat import analyze_heartbeat
                analyze_heartbeat()
            except Exception as e:
                logger.error(f"Failed to update dashboard learning data: {e}")

        except Exception as e:
            logger.error(f"Heartbeat cycle failed: {e}")

    def start(self):
        """Start the continuous evaluation loop"""
        interval = settings.MONITOR_INTERVAL_SECONDS
        logger.info(f"💓 Continuous analyzer started with {interval}s interval")
        
        # Immediate Startup Proof
        try:
            with open("heartbeat_audit.jsonl", "a") as f:
                import json
                f.write(json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "SYSTEM_STARTUP",
                    "message": "Quantix AI Core Heartbeat Thread Initialized"
                }) + "\n")
        except Exception as e:
            logger.error(f"Startup log failed: {e}")

        while True:
            logger.info("🎬 Starting new analysis cycle...")
            self.run_cycle()
            time.sleep(interval)

if __name__ == "__main__":
    analyzer = ContinuousAnalyzer()
    analyzer.start()
