import time
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from loguru import logger
from typing import Optional

from quantix_core.config.settings import settings
from quantix_core.ingestion.twelve_data_client import TwelveDataClient
from quantix_core.engine.structure_engine_v1 import StructureEngineV1
from quantix_core.database.connection import db
from quantix_core.utils.entry_calculator import EntryCalculator

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
        # Robust path detection: try to find the project root (where .env or quantix_core is)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Target: the folder containing 'quantix_core'
        self.project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # In Docker/Railway, heartbeat_audit.jsonl is usually in the root
        # In local dev, it might be in backend/heartbeat_audit.jsonl
        potential_path = os.path.join(self.project_root, "heartbeat_audit.jsonl")
        if not os.path.exists(potential_path) and os.path.exists(os.path.join(self.project_root, "backend")):
             self.audit_log_path = os.path.join(self.project_root, "backend", "heartbeat_audit.jsonl")
        else:
             self.audit_log_path = potential_path
        
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
            
            # Map market state to standard trading actions
            direction_map = {
                "bullish": "BUY",
                "bearish": "SELL"
            }
            direction = direction_map.get(state.state, "BUY") # Default to BUY if structure is ambiguous
            
            # ============================================
            # v2 FUTURE ENTRY LOGIC (5 pips offset)
            # ============================================
            
            # Calculate future entry price (NOT market price)
            entry_calc = EntryCalculator(offset_pips=5.0)
            entry_price, is_valid, validation_msg = entry_calc.calculate_and_validate(
                market_price=price,
                direction=direction
            )
            
            # Validation: Skip signal if entry invalid
            if not is_valid:
                logger.warning(f"SKIP_SIGNAL: {validation_msg}")
                return
            
            # Log entry calculation for dry-run verification
            offset_pips = abs(entry_price - price) / 0.0001
            logger.info(
                f"Entry calculated: market={price}, entry={entry_price}, "
                f"offset={offset_pips:.1f} pips, direction={direction}"
            )
            
            # FIXED RISK/REWARD RULE (AUTO v0)
            # TP = 10 pips, SL = 10 pips from ENTRY (not market)
            FIXED_TP_PIPS = 0.0010  # 10 pips
            FIXED_SL_PIPS = 0.0010  # 10 pips
            
            if direction == "BUY":
                tp = round(entry_price + FIXED_TP_PIPS, 5)
                sl = round(entry_price - FIXED_SL_PIPS, 5)
            else:  # SELL
                tp = round(entry_price - FIXED_TP_PIPS, 5)
                sl = round(entry_price + FIXED_SL_PIPS, 5)
            
            rrr = 1.0  # Fixed 1:1 Risk/Reward Ratio
            
            # Calculate expiry time (15 minutes from now)
            now = datetime.now(timezone.utc)
            expiry_at = now + timedelta(minutes=15)

            # Determine strength label for internal logic/filtering
            strength_label = "ULTRA" if state.confidence >= 0.95 else "HIGH" if state.confidence >= 0.85 else "ACTIVE"
            
            # ============================================
            # v2 SIGNAL STRUCTURE (WAITING_FOR_ENTRY)
            # ============================================
            signal_base = {
                "asset": "EURUSD",
                "direction": direction,
                "strength": state.strength,
                "timeframe": "M15",
                
                # v2 NEW FIELDS
                "state": "WAITING_FOR_ENTRY",  # Initial state
                "entry_price": entry_price,     # Future entry (NOT market)
                "expiry_at": expiry_at.isoformat(),  # 15 min expiry
                
                # Legacy fields (for backward compatibility)
                "entry_low": entry_price,
                "entry_high": entry_price + 0.0002,
                
                # TP/SL (calculated from entry, not market)
                "tp": tp,
                "sl": sl,
                "reward_risk_ratio": rrr,
                
                # Metadata
                "ai_confidence": state.confidence,
                "generated_at": now.isoformat(),
                "explainability": f"Structure {state.state.upper()} | Strength {int(state.strength*100)}% | Entry offset: {offset_pips:.1f} pips",
            }
            
            # Log signal creation for verification
            logger.success(
                f"Signal created: {direction} @ {entry_price} "
                f"(market: {price}, offset: +{offset_pips:.1f} pips) "
                f"| State: WAITING_FOR_ENTRY | Expiry: {expiry_at.strftime('%H:%M:%S UTC')}"
            )

            # 4. Local Audit Log (JSONL) - Robust Absolute Path
            analysis_entry = {
                "timestamp": signal_base["generated_at"],
                "asset": "EURUSD",
                "price": price,
                "direction": direction,
                "strength": state.strength,
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
                logger.debug(f"DB telemetry write failed: {e}")

            # 5. Logic Branching: ULTRA (>95%), LOCK (ACTIVE), or CANDIDATE
            if not db.client:
                logger.warning("DB Client offline - cannot save signals")
                return

            # AUTO-PUSH Logic based on Confidence
            if state.confidence >= 0.95:
                logger.info(f"🚀 ULTRA High Confidence Detected: {state.confidence*100:.1f}%")
                signal_base["status"] = "ACTIVE"
                self.lock_signal(signal_base)
                self.push_to_telegram(signal_base)
            elif state.confidence >= 0.75 and not self.has_traded_today():
                logger.info(f"🎯 High Confidence Moment Detected: {state.confidence*100:.1f}%")
                signal_base["status"] = "ACTIVE"
                self.lock_signal(signal_base)
                # Telegram broadcasting restricted to >= 95% as per user request
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

        # 🛡️ Signal Deduplication (Same asset/direction/entry)
        if not hasattr(self, '_pushed_signals'):
            self._pushed_signals = set()
        
        signal_key = f"{signal['asset']}_{signal['direction']}_{signal['entry_low']}"
        if signal_key in self._pushed_signals:
            logger.info(f"Signal {signal_key} already pushed to Telegram")
            return

        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID

        if not token or not chat_id:
            logger.warning("Telegram pushing skipped: Missing TOKEN or CHAT_ID")
            return

        try:
            # Standard Fields Extraction
            dir_emoji = "🟢" if signal["direction"] == "BUY" else "🔴"
            confidence = int(signal['ai_confidence'] * 100)
            strength_val = signal.get("strength", 0)
            strength_pct = f"{int(strength_val * 100)}%" if isinstance(strength_val, (int, float)) else str(strength_val)
            timeframe = signal.get("timeframe", "M15")
            asset = signal.get("asset", "EURUSD").replace("/", "")
            
            # TEMPLATE 3 – SIGNAL ULTRA (95%+ FAST ALERT)
            if confidence >= 95:
                msg = (
                    f"🚨 *ULTRA SIGNAL (95%+)*\n\n"
                    f"{asset} | {timeframe}\n"
                    f"{dir_emoji} {signal['direction']}\n\n"
                    f"Status: 🟡 WAITING FOR ENTRY\n"
                    f"Entry window: OPEN\n\n"
                    f"Confidence: {confidence}%\n"
                    f"Strength: {strength_pct}\n\n"
                    f"🎯 Entry: {signal['entry_low']}\n"
                    f"💰 TP: {signal['tp']}\n"
                    f"🛑 SL: {signal['sl']}\n\n"
                    f"⚠️ Do NOT enter until entry price is hit.\n"
                    f"You will receive an update when entry is triggered."
                )
            else:
                # TEMPLATE 1 – SIGNAL CÒN HIỆU LỰC (ACTIVE)
                msg = (
                    f"⚡️ *SIGNAL GENIUS AI*\n\n"
                    f"Asset: {asset}\n"
                    f"Timeframe: {timeframe}\n"
                    f"Direction: {dir_emoji} {signal['direction']}\n\n"
                    f"Status: 🟡 WAITING FOR ENTRY\n"
                    f"Entry window: OPEN\n\n"
                    f"Confidence: {confidence}%\n"
                    f"Force/Strength: {strength_pct}\n\n"
                    f"🎯 Entry: {signal['entry_low']}\n"
                    f"💰 TP: {signal['tp']}\n"
                    f"🛑 SL: {signal['sl']}\n\n"
                    f"⚠️ Do NOT enter until entry price is hit.\n"
                    f"You will receive an update when entry is triggered."
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
                self._pushed_signals.add(signal_key)
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
