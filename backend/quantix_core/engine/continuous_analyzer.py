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
from quantix_core.feeds.binance_feed import BinanceFeed
from quantix_core.engine.janitor import Janitor

class ContinuousAnalyzer:
    """
    Quantix AI Core Heartbeat [T0 + Δ]
    Runs every few seconds to detect the highest-confidence moment.
    Implements Frequency Rule: Max 1 signal per day.
    """
    
    def __init__(self):
        self.td_client = TwelveDataClient(api_key=settings.TWELVE_DATA_API_KEY)
        self.binance = BinanceFeed()
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
        
        logger.info(f"💓 Quantix AI Core v3.5 Institutional Initialized (Log: {self.audit_log_path})")

    def convert_to_df(self, data) -> pd.DataFrame:
        """Convert feed data to StructureEngine compatible DataFrame"""
        if isinstance(data, dict) and "values" in data:
            # TwelveData format
            df = pd.DataFrame(data["values"])
            df["datetime"] = pd.to_datetime(df["datetime"])
        elif isinstance(data, list):
            # Binance/Internal list format
            df = pd.DataFrame(data)
            df["datetime"] = pd.to_datetime(df["datetime"])
        else:
            return pd.DataFrame()
        
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
            # Create a copy for DB insertion to avoid modifying the original dictionary used by Telegram
            db_payload = signal_data.copy()
            
            # --- SCHEMA SANITIZATION ---
            # 1. Preserve refinement explanation in explainability field
            if "refinement_reason" in db_payload and db_payload.get("refinement_reason"):
                # Append if not already present (check to avoid duplication)
                if str(db_payload["refinement_reason"]) not in str(db_payload.get("explainability", "")):
                    db_payload["explainability"] = f"{db_payload.get('explainability', '')} | {db_payload['refinement_reason']}"

            # 2. Remove fields not in DB schema to prevent PGRST204 errors
            for key in ["valid_until", "activation_limit_mins", "max_monitoring_mins", "refinement_reason"]:
                if key in db_payload:
                    del db_payload[key]

            res = db.client.table(settings.TABLE_SIGNALS).insert(db_payload).execute()
            if res.data:
                logger.info(f"🔒 Signal LOCKED in [T1]: {res.data[0]['id']} | Telegram: {signal_data.get('telegram_message_id', 'None')}")
                self.last_execution_date = datetime.now(timezone.utc).date()
                return res.data[0]['id']
        except Exception as e:
            logger.error(f"❌ Failed to LOCK signal in [T1]: {e}")
        return None

    def janitor_cleanup(self):
        """
        🧹 AUTO-JANITOR (Fail-Safe)
        Self-cleans the pipeline using robust logic from Janitor module.
        """
        Janitor.run_sync()

    def run_cycle(self):
        """One analysis cycle [T0 + Δ]"""
        # 🔥 EMERGENCY JANITOR: Self-unblock before market check
        # Ensures stuck signals are cleared even if market is closed
        self.janitor_cleanup()

        # 🛡️ Market Hours Safety Check
        if not MarketHours.should_generate_signals():
            return

        try:
            start_time = time.perf_counter()
            self.cycle_count += 1
            logger.info(f"🎬 [v3.5] Starting analysis cycle #{self.cycle_count}...")
            
            # Log market status to DB every 5 cycles with performance metrics
            if self.cycle_count % 5 == 0:
                try:
                    db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "asset": "HEARTBEAT",
                        "direction": "SYSTEM",
                        "status": f"ALIVE_V3.5_C{self.cycle_count}",
                        "confidence": 0.0,
                        "strength": 0.0,
                        "price": 0.0
                    }).execute()
                except: pass
            
            
            # 1. Continuous Feed [T0] - Multi-Source Fallover
            df = pd.DataFrame()
            
            # --- Source A: TwelveData (Primary) ---
            try:
                raw_data = self.td_client.get_time_series(symbol="EUR/USD", interval="15min", outputsize=100)
                if raw_data and "values" in raw_data:
                    df = self.convert_to_df(raw_data)
                    logger.info("📡 Data Source: TWELVEDATA")
            except Exception as e:
                logger.warning(f"⚠️ TwelveData failed: {e}")

            # --- Source B: Binance (Fallback) ---
            if df.empty:
                try:
                    raw_data = self.binance.get_history(symbol="EURUSD", interval="15m", limit=100)
                    if raw_data:
                        df = self.convert_to_df(raw_data)
                        logger.info("📡 Data Source: BINANCE (Quota Protected)")
                except Exception as e:
                    logger.error(f"⚠️ Binance fallback failed: {e}")

            if df.empty:
                logger.error("❌ CRITICAL: All data sources failed. Skipping cycle.")
                return

            # 3. Prepare Common Data
            price = float(df.iloc[-1]["close"])
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # --- HEARTBEAT LOG ---
            heartbeat_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "EURUSD",
                "price": price,
                "direction": "HEARTBEAT",
                "status": f"V3.5_OK_{latency_ms}ms",
                "strength": 0.0,
                "confidence": 0.0
            }
            try:
                db.client.table(settings.TABLE_ANALYSIS_LOG).insert(heartbeat_entry).execute()
                logger.success(f"✅ Cycle #{self.cycle_count} complete in {latency_ms}ms")
            except: pass

            # 2. Market Analysis
            state = self.engine.analyze(df, symbol="EURUSD", timeframe="M15", source="twelve_data")
            
            # Map market state to trading direction
            # STRICT RULE: Only trade clear structure — skip neutral/sideways
            direction_map = {
                "bullish": "BUY",
                "bearish": "SELL"
            }
            direction = direction_map.get(state.state)
            
            if direction is None:
                # Market is neutral/ranging/sideways → No signal, wait for clarity
                logger.info(
                    f"⏸️ Market structure is '{state.state}' (neutral/ranging). "
                    f"Skipping signal — waiting for directional confirmation."
                )
                return
            
            # ============================================
            # v3.5 SMC-LITE ENTRY LOGIC (FVG-Based)
            # ============================================
            
            # --- STRATEGY UPGRADE v3.6 (Win 90% Target) ---
            # 💡 Sáng kiến 1: Market Entry cho tín hiệu mạnh
            is_market_entry = False
            msg_type = "PENDING"
            
            # Nếu tin cậy tối cao (ULTRA) -> Vào Market ngay
            if state.confidence >= 0.95:
                entry_price = price
                is_market_entry = True
                msg_type = "MARKET_EXECUTION"
                logger.success(f"🚀 ULTRA CONFIDENCE ({state.confidence:.2f}) -> MARKET ENTRY")
            else:
                # Ngược lại dùng FVG với offset hẹp hơn (1.5 pips thay vì 2.0)
                entry_calc = EntryCalculator(offset_pips=1.5)
                entry_price, is_valid, validation_msg = entry_calc.calculate_fvg_entry(
                    market_price=price,
                    direction=direction,
                    fvg=getattr(state, 'nearest_fvg', None)
                )
                if not is_valid:
                    logger.warning(f"SKIP_SIGNAL: {validation_msg}")
                    return
                msg_type = validation_msg

            # 💡 Sáng kiến 2: Tight TP (0.8x ATR) / Wide SL (1.8x ATR) 
            # Giúp tăng Win Rate đáng kể bằng cách chốt lời sớm và tránh quét SL
            try:
                high_s = df['high'].astype(float)
                low_s = df['low'].astype(float)
                close_s = df['close'].astype(float)
                tr = pd.concat([high_s - low_s, (high_s - close_s.shift()).abs(), (low_s - close_s.shift()).abs()], axis=1).max(axis=1)
                atr = tr.rolling(14).mean().iloc[-1]
                
                # TP hẹp (8-15 pips), SL rộng (12-35 pips)
                tp_dist = max(0.0008, min(0.0015, atr * 0.8))  
                sl_dist = max(0.0015, min(0.0035, atr * 1.8))  
                
                logger.debug(f"v3.6 R:R: ATR={atr:.5f}, TP_Dist={tp_dist:.5f}, SL_Dist={sl_dist:.5f}")
            except Exception as e:
                logger.error(f"ATR failed, using scaled fallback: {e}")
                tp_dist = 0.0008
                sl_dist = 0.0020

            if direction == "BUY":
                tp = round(entry_price + tp_dist, 5)
                sl = round(entry_price - sl_dist, 5)
            else:  # SELL
                tp = round(entry_price - tp_dist, 5)
                sl = round(entry_price + sl_dist, 5)
            
            rrr = round(tp_dist / sl_dist, 2)
            
            # Calculate expiry time (Entry timeout: 30 minutes)
            now = datetime.now(timezone.utc)
            expiry_at = now + timedelta(minutes=settings.MAX_PENDING_DURATION_MINUTES)

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
                "valid_until": expiry_at.isoformat(), # OFFICIAL TIMING v3.1
                "expiry_at": expiry_at.isoformat(),   # Legacy support
                "activation_limit_mins": settings.MAX_PENDING_DURATION_MINUTES,
                "max_monitoring_mins": settings.MAX_TRADE_DURATION_MINUTES,
                
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
                "explainability": f"Structure {state.state.upper()} | Strength {int(state.strength*100)}% | Type: {msg_type}",
                "is_test": False,
                "is_market_entry": is_market_entry
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
            # 🔁 QUANTIX LIVE WORKFLOW (ACTIVE MODE)
            # ============================================

            # 1. Check Confidence Gate
            if release_score >= settings.MIN_CONFIDENCE:
                # 2. Check Anti-Burst Rule
                is_allowed, gate_reason = self.check_release_gate(signal_base["asset"], signal_base["timeframe"])
                
                if is_allowed:
                    logger.success(f"🎯 Threshold Passive ({release_score*100:.1f}%) -> BIRTH SIGNAL")
                    
                    # Update to LIVE status immediately
                    signal_base["status"] = "PUBLISHED"
                    
                    if signal_base.get("is_market_entry"):
                        signal_base["state"] = "ENTRY_HIT"
                        signal_base["entry_hit_at"] = now.isoformat()
                        logger.success("🚀 MARKET EXECUTION: Signal born in ENTRY_HIT state")
                    else:
                        signal_base["state"] = "WAITING_FOR_ENTRY"
                    
                    # 3. DB COMMIT (Single Phase)
                    signal_id = self.lock_signal(signal_base)
                    
                    if signal_id:
                        # 4. BROADCAST (Telegram)
                        if self.notifier:
                            signal_for_tg = signal_base.copy()
                            signal_for_tg["id"] = signal_id
                            
                            msg_id = self.push_to_telegram(signal_for_tg)
                            if msg_id:
                                # Update signal with Telegram ID
                                try:
                                    db.client.table(settings.TABLE_SIGNALS).update({
                                        "telegram_message_id": msg_id
                                    }).eq("id", signal_id).execute()
                                    self.last_pushed_at = datetime.now(timezone.utc)
                                    logger.success(f"🚀 [LIVE] Signal {signal_id} is active (TG: {msg_id})")
                                except Exception as e:
                                    logger.error(f"Failed to link TG ID to signal {signal_id}: {e}")
                            else:
                                logger.warning(f"⚠️ Telegram broadcast failed for {signal_id}")
                        else:
                            logger.warning(f"⚠️ Notifier not initialized. Signal {signal_id} is LIVE in DB only.")
                    else:
                        logger.error("❌ Failed to create LIVE signal in DB.")
                else:
                    logger.warning(f"🛡️ [ANTI-BURST] Signal rejected by Gate: {gate_reason}")
            else:
                logger.info(f"🔍 Score below threshold ({release_score:.2f} < {settings.MIN_CONFIDENCE}) - No action.")

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
            if signal.get("is_market_entry"):
                msg_id = self.notifier.send_market_execution(signal)
            else:
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
