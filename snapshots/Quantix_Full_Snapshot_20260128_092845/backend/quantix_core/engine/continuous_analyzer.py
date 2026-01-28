import time
import requests
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
        self.cycle_count = 0
        self.last_pushed_at = None # For Telegram Cooldown
        
        # Absolute path to prevent "reset to 0" issues on machine restart
        import os
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.audit_log_path = os.path.join(self.base_dir, "backend", "heartbeat_audit.jsonl")
        
        logger.info(f"💓 Quantix Heartbeat [T0+Δ] Initialized (Log: {self.audit_log_path})")

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
                .eq("status", "ACTIVE")\
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
            self.cycle_count += 1
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
                "explainability": "Structure Alpha v1.0",
            }

            # 4. Local Audit Log (JSONL) - Robust Absolute Path
            analysis_entry = {
                "timestamp": signal_base["generated_at"],
                "asset": "EURUSD",
                "price": price,
                "direction": direction,
                "confidence": state.confidence,
                "status": "ANALYZED"
            }
            try:
                with open(self.audit_log_path, "a") as f:
                    import json
                    f.write(json.dumps(analysis_entry) + "\n")
            except Exception as e:
                logger.error(f"Failed to write heartbeat log: {e}")

            # 4b. Push Analysis to Supabase [T1] for persistent telemetry
            try:
                db.client.table(settings.TABLE_ANALYSIS_LOG).insert(analysis_entry).execute()
            except Exception as e:
                logger.debug(f"Failed to push telemetry to DB (Expected if table missing): {e}")

            # 5. Logic Branching: ULTRA (>95%), LOCK (ACTIVE), or CANDIDATE
            if not db.client:
                logger.warning("DB Client offline - cannot save signals")
                return

            # AUTO-PUSH Logic based on Confidence
            if state.confidence >= 0.95:
                logger.info(f"🚀 ULTRA High Confidence Detected: {state.confidence*100:.1f}%")
                signal_base["status"] = "ACTIVE"
                # ULTRA ignores daily cap for visibility, but respects telegram cooldown
                self.lock_signal(signal_base)
                self.push_to_telegram(signal_base)
            elif state.confidence >= 0.75 and not self.has_traded_today():
                logger.info(f"🎯 High Confidence Moment Detected: {state.confidence*100:.1f}%")
                signal_base["status"] = "ACTIVE"
                self.lock_signal(signal_base)
                self.push_to_telegram(signal_base)
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
                # Auto-sync with GitHub every 15 cycles (30 mins)
                should_push = (self.cycle_count % 15 == 0)
                analyze_heartbeat(push_to_git=should_push)
            except Exception as e:
                logger.error(f"Failed to update dashboard learning data: {e}")

        except Exception as e:
            logger.error(f"Heartbeat cycle failed: {e}")

    def push_to_telegram(self, signal: dict):
        """Proactive Broadcast for High Confidence Signals"""
        # 🛡️ Cooldown Check (1 push per 60 minutes)
        now = datetime.now(timezone.utc)
        if self.last_pushed_at and (now - self.last_pushed_at) < pd.Timedelta(minutes=60):
            logger.debug("Telegram push on cooldown")
            return

        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID

        if not token or not chat_id:
            logger.warning("Telegram pushing skipped: Missing TOKEN or CHAT_ID")
            return

        try:
            # Simple format for immediate visibility
            dir_emoji = "🟢" if signal["direction"] == "BUY" else "🔴"
            msg = (
                f"⚡️ *QUANTIX HIGH-CONFIDENCE SIGNAL*\n\n"
                f"Asset: {signal['asset']}\n"
                f"Direction: {dir_emoji} {signal['direction']}\n"
                f"Confidence: {round(signal['ai_confidence'] * 100, 1)}%\n\n"
                f"🎯 Entry: {signal['entry_low']}\n"
                f"💰 TP: {signal['tp']}\n"
                f"🛑 SL: {signal['sl']}\n\n"
                f"🔗 [View Live Dashboard](https://9dpi.github.io/quantix-ai-core/dashboard/)"
            )

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            res = requests.post(url, json={
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown"
            }, timeout=10)
            
            if res.ok:
                logger.info("🚀 Signal pushed to Telegram successfully")
                self.last_pushed_at = now
            else:
                logger.error(f"Telegram push failed: {res.text}")

        except Exception as e:
            logger.error(f"Telegram push error: {e}")

    def start(self):
        """Start the continuous evaluation loop"""
        interval = settings.MONITOR_INTERVAL_SECONDS
        logger.info(f"💓 Continuous analyzer started with {interval}s interval")
        
        # Immediate Startup Proof using absolute path
        try:
            with open(self.audit_log_path, "a") as f:
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
