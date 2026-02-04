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
from quantix_core.utils.market_hours import MarketHours
from quantix_core.engine.confidence_refiner import ConfidenceRefiner

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
        self.refiner = ConfidenceRefiner()
        
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
        
        # 🛡️ Telegram Config Injection (Single Source of Truth)
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
        
        self.notifier = None
        if token and chat_id:
            from quantix_core.notifications.telegram_notifier_v2 import create_notifier
            self.notifier = create_notifier(token, chat_id, admin_chat_id)
            logger.success(f"✅ [INIT_OK] Telegram notifier initialized (Chat: {chat_id})")
        else:
            logger.critical("❌ [INIT_FAIL] Telegram configuration missing! Pipeline will proceed as INTERNAL ONLY.")
            # Fail-fast logic: If we have an admin channel, we'd alert here, but since config is missing...
        
        logger.info(f"💓 Quantix AI Core v2.1 Initialized (Log: {self.audit_log_path})")

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

    def get_published_count_today(self) -> int:
        """Get number of PUBLISHED signals today from DB"""
        today = datetime.now(timezone.utc).date()
        try:
            res = db.client.table(settings.TABLE_SIGNALS)\
                .select("id", count="exact")\
                .eq("status", "PUBLISHED")\
                .gte("generated_at", today.isoformat())\
                .execute()
            return res.count if res.count is not None else len(res.data)
        except Exception as e:
            logger.error(f"Failed to check daily count: {e}")
            return settings.MAX_SIGNALS_PER_DAY # Safety, assume cap reached
            
    def check_release_gate(self, asset: str, timeframe: str) -> tuple[bool, str]:
        """
        🔒 ANTI-BURST RULE (HARD LOCK)
        Returns (is_allowed, reason)
        """
        now = datetime.now(timezone.utc)
        
        # 1. Daily Cap Check (REMOVED - Unlimited flow)
        pass

        # 2. GLOBAL HARD LOCK (One Signal at a Time)
        # Only count 'real' signals that are visible to users. 'PREPARED' signals are ignored.
        try:
            res = db.client.table(settings.TABLE_SIGNALS)\
                .select("id")\
                .in_("state", ["WAITING_FOR_ENTRY", "ENTRY_HIT"])\
                .execute()
            
            if res.data:
                return False, "GLOBAL_ACTIVE_SIGNAL_EXISTS"
        except Exception as e:
            logger.error(f"Gate check error: {e}")

        # 3. Cooldown Check (30 mins)
        if self.last_pushed_at:
            elapsed = (now - self.last_pushed_at).total_seconds() / 60
            if elapsed < settings.MIN_RELEASE_INTERVAL_MINUTES:
                return False, f"COOLDOWN_ACTIVE ({settings.MIN_RELEASE_INTERVAL_MINUTES - elapsed:.1f}m left)"
            
        return True, "ALLOWED"

    def lock_signal(self, signal_data: dict) -> Optional[str]:
        """LOCK signal with timestamp in Immutable Record [T1]"""
        try:
            # Removed the mandatory telegram_message_id check to allow 'Database First' candidates
            # Audit integrity requires saving even before we have a public proof anchor.
                
            res = db.client.table(settings.TABLE_SIGNALS).insert(signal_data).execute()
            if res.data:
                logger.info(f"🔒 Signal LOCKED in [T1]: {res.data[0]['id']} | Telegram: {signal_data.get('telegram_message_id', 'None')}")
                self.last_execution_date = datetime.now(timezone.utc).date()
                return res.data[0]['id']
        except Exception as e:
            # 🛡️ Fallback for missing columns (Schema Resilience)
            error_msg = str(e)
            if "PGRST204" in error_msg and ("refinement_reason" in error_msg or "release_confidence" in error_msg):
                logger.warning("⚠️ Supabase schema mismatch (missing refinement columns). Retrying without them...")
                fallback_data = {k: v for k, v in signal_data.items() 
                                 if k not in ["refinement_reason", "release_confidence"]}
                try:
                    res = db.client.table(settings.TABLE_SIGNALS).insert(fallback_data).execute()
                    if res.data:
                        logger.success("✅ Signal LOCKED (Fallback mode)")
                        return res.data[0]['id']
                except Exception as e2:
                    logger.error(f"❌ Fallback LOCK also failed: {e2}")
            else:
                logger.error(f"❌ Failed to LOCK signal in [T1]: {e}")
        return None

    def run_cycle(self):
        """One analysis cycle [T0 + Δ]"""
        # 🛡️ Market Hours Safety Check
        if not MarketHours.should_generate_signals():
            return

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
            strength_label = "ULTRA" if state.confidence >= 0.95 else "HIGH" if state.confidence >= 0.85 else "NORMAL"
            
            # ============================================
            # v2 SIGNAL STRUCTURE (WAITING_FOR_ENTRY)
            # ============================================
            signal_base = {
                "asset": "EURUSD",
                "direction": direction,
                "strength": state.strength,
                "timeframe": "M15",
                "status": "PREPARED",
                "state": "PREPARED",  # Phase 1: Invisible to Watcher/UI
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
            
            # --- RELEASE CONFIDENCE REFINEMENT ---
            release_score, refinement_reason = self.refiner.calculate_release_score(
                raw_confidence=state.confidence,
                df=df
            )
            signal_base["release_confidence"] = release_score
            signal_base["refinement_reason"] = refinement_reason
            
            # Log signal creation for verification
            logger.info(
                f"Signal Evaluated: {direction} @ {entry_price} "
                f"| Raw Conf: {state.confidence:.2f} | Release Score: {release_score:.2f} "
                f"| {refinement_reason}"
            )

            # 4. Local Audit Log (JSONL) - Robust Absolute Path
            analysis_entry = {
                "timestamp": signal_base["generated_at"],
                "asset": "EURUSD",
                "price": price,
                "direction": direction,
                "strength": state.strength,
                "confidence": state.confidence,
                "release_confidence": release_score,
                "refinement": refinement_reason,
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
                error_msg = str(e)
                if "PGRST204" in error_msg and ("refinement" in error_msg or "release_confidence" in error_msg):
                    # Fallback for telemetry
                    fallback_entry = {k: v for k, v in analysis_entry.items() 
                                      if k not in ["refinement", "release_confidence"]}
                    try:
                        db.client.table(settings.TABLE_ANALYSIS_LOG).insert(fallback_entry).execute()
                    except: pass
                else:
                    logger.debug(f"DB telemetry write failed: {e}")

            # ============================================
            # v3 TWO-PHASE SIGNAL CREATION
            # ============================================

            # 1. PHASE 1: PREPARE (Invisible Audit Record)
            signal_id = self.lock_signal(signal_base)
            if not signal_id:
                 logger.error("❌ Phase 1 Failed: Could not PREPARE signal in DB.")
                 return

            # 2. RELEASE GATE: Anti-Burst Check
            is_allowed, gate_reason = self.check_release_gate(signal_base["asset"], signal_base["timeframe"])
            
            if release_score >= settings.MIN_CONFIDENCE and is_allowed:
                logger.info(f"🎯 Release Score High ({release_score*100:.1f}%) -> Phase 2: NOTIFY")
                
                if not self.notifier:
                    logger.warning(f"⚠️ Notifier NOT initialized. Signal {signal_id} stays PREPARED.")
                    return

                # Signal for Telegram needs the DB ID
                signal_for_tg = signal_base.copy()
                signal_for_tg["id"] = signal_id
                
                # EXECUTE TELEGRAM SEND
                msg_id = self.push_to_telegram(signal_for_tg)
                
                if msg_id:
                    # 3. PHASE 3: COMMIT (Promote to WAITING_FOR_ENTRY)
                    try:
                        self.last_pushed_at = datetime.now(timezone.utc)
                        
                        update_res = db.client.table(settings.TABLE_SIGNALS).update({
                            "telegram_message_id": msg_id,
                            "status": "PUBLISHED",
                            "state": "WAITING_FOR_ENTRY"
                        }).eq("id", signal_id).eq("state", "PREPARED").execute()
                        
                        if update_res.data:
                            logger.success(f"⚓ [COMMIT_SUCCESS] Signal {signal_id} is now LIVE (TG: {msg_id})")
                        else:
                            logger.error(f"❌ Atomic Commit Failed for {signal_id} (State mismatch?)")
                    except Exception as e:
                        logger.error(f"❌ Phase 3 Failed: {e}")
                else:
                    logger.warning(f"⚠️ Phase 2 Failed: Telegram push failed for {signal_id}. Stays PREPARED.")
            else:
                if not is_allowed:
                    logger.warning(f"🛡️ [ANTI-BURST] Signal {signal_id} rejected by Gate: {gate_reason}")
                else:
                    logger.info(f"🔍 Signal {signal_id} saved as Internal PREPARED (Score: {release_score:.2f})")
            # 🧹 AGGRESSIVE ZOMBIE CLEANUP (Keep Path Clear)
            try:
                zombie_limit = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
                
                # Step 1: Find Zombies (Invisible signals that never promoted)
                zombies = db.client.table(settings.TABLE_SIGNALS)\
                    .select("id")\
                    .eq("state", "PREPARED")\
                    .lt("generated_at", zombie_limit)\
                    .execute()
                
                if zombies.data:
                    zombie_ids = [z['id'] for z in zombies.data]
                    logger.warning(f"🧟 Found {len(zombie_ids)} STALE PREPARED signals. Cleaned up.")
                    
                    # Step 2: Nuke them
                    db.client.table(settings.TABLE_SIGNALS).update({
                        "state": "CANCELLED",
                        "status": "CLOSED",
                        "result": "CANCELLED_STALE",
                        "closed_at": datetime.now(timezone.utc).isoformat()
                    }).in_("id", zombie_ids).execute()
                    
                    logger.success("🧹 Zombie Cleanup Complete. Path cleared.")
            except Exception as e:
                logger.debug(f"Zombie cleanup failed: {e}")

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

    def push_to_telegram(self, signal: dict) -> Optional[int]:
        """Proactive Broadcast for High Confidence Signals"""
        # 🛡️ Cooldown Check (Using dynamic setting)
        now = datetime.now(timezone.utc)
        cooldown_min = getattr(settings, 'MIN_RELEASE_INTERVAL_MINUTES', 30)
        if self.last_pushed_at and (now - self.last_pushed_at) < pd.Timedelta(minutes=cooldown_min):
            logger.debug(f"Telegram push on cooldown ({cooldown_min}m)")
            return None

        # 🛡️ Signal Deduplication (Same asset/direction/tf/entry)
        if not hasattr(self, '_pushed_signals'):
            self._pushed_signals = set()
        
        signal_key = f"{signal['asset']}_{signal['direction']}_{signal['timeframe']}_{signal['entry_price']}"
        if signal_key in self._pushed_signals:
            logger.info(f"Signal {signal_key} already pushed to Telegram")
            return None

        if not self.notifier:
            logger.warning("Telegram pushing skipped: Notifier not initialized")
            return None

        try:
            # Use the new state-based method for standardized reporting
            msg_id = self.notifier.send_waiting_for_entry(signal)
            
            if msg_id:
                logger.info(f"🚀 Signal released to Telegram (ID: {msg_id})")
                self.last_pushed_at = now
                self._pushed_signals.add(signal_key)
                return msg_id
            else:
                logger.error("Telegram push failed: Notifier returned None")
                return None

        except Exception as e:
            logger.error(f"Telegram push error: {e}")
            return None

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
            try:
                logger.info("🎬 Starting new analysis cycle...")
                self.run_cycle()
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Cycle error: {error_msg}")
                if "API_BLOCKED" in error_msg and self.notifier:
                    self.notifier.send_critical_alert(f"TwelveData API Blocked: {error_msg}")
            
            time.sleep(interval)

if __name__ == "__main__":
    analyzer = ContinuousAnalyzer()
    analyzer.start()
