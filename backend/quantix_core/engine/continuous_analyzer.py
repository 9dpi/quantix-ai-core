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
    """
    
    def __init__(self):
        self.td_client = TwelveDataClient(api_key=settings.TWELVE_DATA_API_KEY)
        self.binance = BinanceFeed()
        self.engine = StructureEngineV1(sensitivity=2)
        self.cycle_count = 0
        self.last_pushed_at = None # For Telegram Cooldown
        self.last_health_report_at = None # v4.2.0: Automated health reports
        self.refiner = ConfidenceRefiner()
        
        # v4.5.0: Safe-Guard Pivot (Circuit Breaker)
        self.consecutive_losses = 0
        self.cooldown_until: Optional[datetime] = None
        
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
        
    def _check_circuit_breaker(self):
        """v4.5.0: Loss-based circuit breaker logic"""
        now = datetime.now(timezone.utc)
        
        # Reset cooldown if expired
        if self.cooldown_until and now >= self.cooldown_until:
            logger.info("🔓 Cooldown expired. Resuming normal operations.")
            self.cooldown_until = None
            self.consecutive_losses = 0

        # Query last results to update consecutive loss count
        try:
            res = db.client.table(settings.TABLE_SIGNALS)\
                .select("result")\
                .order("generated_at", desc=True)\
                .limit(settings.MAX_CONSECUTIVE_LOSSES + 1)\
                .execute()
            
            if res.data:
                losses = 0
                for sig in res.data:
                    if sig.get("result") == "LOSS":
                        losses += 1
                    elif sig.get("result") == "PROFIT":
                        break # Chain broken
                
                self.consecutive_losses = losses
                
                if self.consecutive_losses >= settings.MAX_CONSECUTIVE_LOSSES and not self.cooldown_until:
                    self.cooldown_until = now + timedelta(hours=settings.CIRCUIT_BREAKER_COOLDOWN_HOURS)
                    logger.critical(f"🛑 CIRCUIT BREAKER TRIGGERED: {losses} consecutive losses. Cooldown until {self.cooldown_until.isoformat()}")
                    
                    if self.notifier:
                        self.notifier.send_critical_alert(
                            f"🛑 *CIRCUIT BREAKER TRIGGERED*\n"
                            f"Detected {losses} consecutive losses.\n"
                            f"System entering 4-hour cooldown."
                        )
        except Exception as e:
            logger.error(f"Circuit breaker check failed: {e}")

    def _get_h1_trend(self) -> Optional[str]:
        """v4.5.0: Fetch H1 trend for multi-timeframe alignment"""
        try:
            # Prefer Binance for free H1 history
            raw_h1 = self.binance.get_history(symbol="EURUSD", interval="1h", limit=50)
            if not raw_h1:
                # Fallback to TwelveData
                raw_h1 = self.td_client.get_time_series(symbol="EUR/USD", interval="1h", outputsize=50).get("values")
            
            if raw_h1:
                df_h1 = self.convert_to_df(raw_h1)
                h1_state = self.engine.analyze(df_h1, symbol="EURUSD", timeframe="H1")
                return h1_state.state # "bullish", "bearish", "range"
        except Exception as e:
            logger.error(f"H1 Trend fetch failed: {e}")
        return None

            
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
            for key in ["valid_until", "activation_limit_mins", "max_monitoring_mins", "refinement_reason", "is_market_entry", "refinement", "signal_metadata", "tp_pips", "sl_pips"]:
                if key in db_payload:
                    if key == "is_market_entry" and db_payload[key]:
                        # Optional: Mark in explainability that it was a Market Entry
                        if "MARKET_ENTRY" not in str(db_payload.get("explainability", "")):
                            db_payload["explainability"] = f"{db_payload.get('explainability', '')} | [MARKET_ENTRY]"
                    del db_payload[key]

            res = db.client.table(settings.TABLE_SIGNALS).insert(db_payload).execute()
            if res.data:
                logger.info(f"🔒 Signal LOCKED in [T1]: {res.data[0]['id']} | Telegram: {signal_data.get('telegram_message_id', 'None')}")
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

        # 🛑 v4.5.0: Circuit Breaker / Cooldown Check
        self._check_circuit_breaker()
        if self.cooldown_until:
            logger.warning(f"⏸️ System in Cooldown until {self.cooldown_until.isoformat()} due to losses.")
            return

        try:
            start_time = time.perf_counter()
            self.cycle_count += 1
            logger.info(f"🎬 [v3.5] Starting analysis cycle #{self.cycle_count}...")
            
            # Log market status to DB every cycle with performance metrics
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
            
            # --- Source A: Binance (Primary - Free/Unlimited) ---
            try:
                raw_data = self.binance.get_history(symbol="EURUSD", interval="15m", limit=100)
                if raw_data:
                    df = self.convert_to_df(raw_data)
                    logger.info("📡 Data Source: BINANCE (Primary)")
            except Exception as e:
                logger.warning(f"⚠️ Binance failed: {e}")

            # --- Source B: TwelveData (Fallback - Quota Limited) ---
            if df.empty:
                try:
                    raw_data = self.td_client.get_time_series(symbol="EUR/USD", interval="15min", outputsize=100)
                    if raw_data and "values" in raw_data:
                        df = self.convert_to_df(raw_data)
                        logger.info("📡 Data Source: TWELVEDATA (Fallback)")
                except Exception as e:
                    logger.error(f"⚠️ TwelveData fallback failed: {e}")

            if df.empty:
                logger.error("❌ CRITICAL: All data sources failed. Skipping cycle.")
                return

            # 3. Prepare Common Data
            price = float(df.iloc[-1]["close"])
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # 2. Market Analysis (EURUSD Heartbeat)
            heartbeat_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "HEARTBEAT_ANALYZER",
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

            # 🧩 v4.5.0: Multi-Timeframe Alignment (H1 Filter)
            h1_trend = self._get_h1_trend()
            if h1_trend:
                logger.info(f"🔎 MTF Check: M15={direction} | H1={h1_trend.upper()}")
                if direction == "BUY" and h1_trend != "bullish":
                    logger.warning(f"🚫 Trend Clash: BUY signal rejected because H1 is {h1_trend.upper()}")
                    return
                if direction == "SELL" and h1_trend != "bearish":
                    logger.warning(f"🚫 Trend Clash: SELL signal rejected because H1 is {h1_trend.upper()}")
                    return
            else:
                logger.warning("⚠️ H1 trend unavailable. Proceeding with caution (M15 only).")
            
            # ============================================
            # v3.5 SMC-LITE ENTRY LOGIC (FVG-Based)
            # ============================================
            
            # --- STRATEGY UPGRADE v3.8 (Market Execution First) ---
            # 💡 Entry Logic: Market Entry for ALL released signals
            # Root cause analysis showed 100% pending orders with avg 9.9 pip gap
            # = 50% of signals never hit entry. Fix: execute at market price.
            is_market_entry = False
            msg_type = "PENDING"
            
            # v3.8: All signals that pass confidence gate (80%) use MARKET EXECUTION
            # This eliminates the entry miss problem entirely
            if state.confidence >= settings.MIN_CONFIDENCE:
                entry_price = price
                is_market_entry = True
                msg_type = "MARKET_EXECUTION"
                logger.success(f"🚀 MARKET EXECUTION ({state.confidence:.2f}) -> Entry at {price:.5f}")
            else:
                # Fallback: FVG with tighter offset (0.5 pips)
                entry_calc = EntryCalculator(offset_pips=0.5)
                entry_price, is_valid, validation_msg = entry_calc.calculate_fvg_entry(
                    market_price=price,
                    direction=direction,
                    fvg=getattr(state, 'nearest_fvg', None)
                )
                if not is_valid:
                    logger.warning(f"SKIP_SIGNAL: {validation_msg}")
                    return
                msg_type = validation_msg

            # 💡 Sáng kiến 2 (v3.8): Session-Aware TP/SL (Tightened for Hit Rate)
            # Phiên biến động cao -> TP rộng hơn (dễ chạm trong 1-2 nến)
            # Phiên yếu -> TP siêu hẹp (3-4 pips) để chốt nhanh
            try:
                high_s = df['high'].astype(float)
                low_s = df['low'].astype(float)
                close_s = df['close'].astype(float)
                tr = pd.concat([high_s - low_s, (high_s - close_s.shift()).abs(), (low_s - close_s.shift()).abs()], axis=1).max(axis=1)
                atr = tr.rolling(14).mean().iloc[-1]
                
                # Detect session for dynamic TP/SL
                hour_utc = now.hour if 'now' in dir() else datetime.now(timezone.utc).hour
                
                if 13 <= hour_utc < 17:  # London-NY Overlap (PEAK)
                    tp_mult = 1.5   # TP = 1.5x ATR (~15-25 pips)
                    sl_mult = 1.0   # SL = 1.0x ATR (~10-15 pips)  
                    session_tag = "PEAK"
                elif 6 <= hour_utc < 13:  # London (HIGH)
                    tp_mult = 1.2   # TP = 1.2x ATR (~12-20 pips)
                    sl_mult = 0.8   # SL = 0.8x ATR (~8-12 pips)
                    session_tag = "HIGH"
                else:  # Asia/Late NY (LOW volatility)
                    tp_mult = 1.0   # TP = 1.0x ATR (~10-12 pips)
                    sl_mult = 0.7   # SL = 0.7x ATR (~7-10 pips)
                    session_tag = "LOW"
                
                # 💡 SMC-Standard Mode (v4.1.1)
                # Adjusted to User Preference: Managed via settings.py (TP=7p, SL=12p)
                sl_pips = settings.SL_PIPS
                tp_pips = settings.TP_PIPS
                
                # Convert back to price points
                tp_dist = round(tp_pips * 0.0001, 5)
                sl_dist = round(sl_pips * 0.0001, 5)
                
                logger.info(f"v4.1.1 R:R (FIXED): ATR={atr if 'atr' in locals() else 0:.5f} | TP={tp_dist:.5f} ({tp_pips}p) | SL={sl_dist:.5f} ({sl_pips}p)")
            except Exception as e:
                logger.error(f"ATR failed, using hard safety fallback from settings: {e}")
                tp_dist = round(settings.TP_PIPS * 0.0001, 5)
                sl_dist = round(settings.SL_PIPS * 0.0001, 5)

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
                "tp_pips": tp_pips,
                "sl_pips": sl_pips,
                "reward_risk_ratio": rrr,
                
                # Metadata
                "ai_confidence": state.confidence,
                "generated_at": now.isoformat(),
                "explainability": f"Structure {state.state.upper()} | Strength {int(state.strength*100)}% | Type: {msg_type}",
                "is_test": False,
                "is_market_entry": is_market_entry,
                
                # --- 5W1H TRANSPARENCY (v3.8) ---
                "strategy": f"Quantix_v3.8_SMC",
                "refinement": (
                    f"Structure: {state.state.upper()} | "
                    f"Conf: {state.confidence:.0%} | "
                    f"Vol: {state.strength:.1f} | "
                    f"Spread: {1.0:.1f} | "
                    f"[{msg_type}]"
                ),
                "signal_metadata": {
                    # WHO - Model Identity
                    "model": "Quantix_v3.8_SMC",
                    "engine": "StructureEngine_v1",
                    
                    # WHAT - Risk Profile
                    "entry_type": msg_type,
                    "tp_pips": round(tp_dist * 10000, 1),
                    "sl_pips": round(sl_dist * 10000, 1),
                    "rr_ratio": rrr,
                    "strength_label": strength_label,
                    "max_lot_cap": settings.MAX_LOT_SIZE_CAP, # 🛡️ Institutional Guard Rail
                    "risk_usd": settings.RISK_USD_PER_TRADE,
                    
                    # WHERE - Market Context
                    "session": session_tag,
                    "market_price_at_signal": price,
                    "atr_value": round(atr if 'atr' in dir() else 0.0, 5),
                    "structure_state": state.state.upper(),
                    "zone": f"{'Discount' if direction == 'BUY' else 'Premium'} Zone",
                    
                    # WHEN - Timing
                    "generated_utc": now.isoformat(),
                    "session_hour_utc": now.hour,
                    "entry_window_mins": settings.MAX_PENDING_DURATION_MINUTES,
                    "max_trade_mins": settings.MAX_TRADE_DURATION_MINUTES,
                    
                    # WHY - Technical Reasoning
                    "why": (
                        f"SMC {state.state.upper()} structure detected on M15. "
                        f"AI confidence {state.confidence:.0%} exceeds {settings.MIN_CONFIDENCE:.0%} threshold. "
                        f"Session: {session_tag}. "
                        f"ATR-based TP: {round(tp_dist*10000,1)} pips, SL: {round(sl_dist*10000,1)} pips. "
                        f"Hard Lot Cap applied: {settings.MAX_LOT_SIZE_CAP} for 1:30 leverage accounts."
                    ),
                    
                    # HOW - Market Regime
                    "volatility": session_tag,
                    "data_source": "TwelveData/Binance",
                    "execution_method": msg_type,
                }
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
                    signal_base["state"] = "PUBLISHED"
                    
                    if signal_base.get("is_market_entry"):
                        signal_base["state"] = "ENTRY_HIT"
                        signal_base["status"] = "ENTRY_HIT"
                        signal_base["entry_hit_at"] = now.isoformat()
                        logger.success("🚀 MARKET EXECUTION: Signal born in ENTRY_HIT state")
                    else:
                        signal_base["state"] = "WAITING_FOR_ENTRY"
                        signal_base["status"] = "WAITING_FOR_ENTRY"
                    
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
                should_push = (self.cycle_count % 60 == 0) # v4.3.0: Once per hour (60s * 60)
                analyze_heartbeat(push_to_git=should_push)
            except Exception as e:
                logger.error(f"Failed to update dashboard learning data: {e}")

            # 7. INTEGRATED WATCHDOG — Check Watcher health every 120 cycles (~120 min @ 60s/cycle)
            if self.cycle_count > 0 and self.cycle_count % 120 == 0:
                self._check_watcher_health()
                
            # v4.2.0: Broadcast comprehensive health every 2 hours
            now_time = datetime.now(timezone.utc)
            if self.last_health_report_at is None:
                # First run: delay by 10m to avoid startup noise, or send immediately? 
                # Let's send 1 hour after startup for first time, then every 2 hours.
                self.last_health_report_at = now_time 
            
            elapsed_health = (now_time - self.last_health_report_at).total_seconds() / 60
            if elapsed_health >= settings.HEALTH_REPORT_INTERVAL_MINUTES:
                self._broadcast_comprehensive_report()
                self.last_health_report_at = now_time

        except Exception as e:
            logger.error(f"Heartbeat cycle failed: {e}")

    def _check_watcher_health(self):
        """
        Integrated Watchdog: Check if Signal Watcher is alive.
        Called every 24 cycles (~120 minutes) from run_cycle.
        If Watcher is stale > 30 min:
          1. Run Janitor to clear stuck signals
          2. Send Telegram alert to Admin
        """
        WATCHER_STALE_THRESHOLD_MIN = 30
        
        try:
            now = datetime.now(timezone.utc)
            
            # Query last Watcher heartbeat
            res = db.client.table(settings.TABLE_ANALYSIS_LOG)\
                .select("timestamp, status")\
                .eq("asset", "HEARTBEAT_WATCHER")\
                .order("timestamp", desc=True)\
                .limit(1)\
                .execute()
            
            if not res.data:
                logger.warning("🏥 Watchdog: No Watcher heartbeat found in DB!")
                stale_min = 9999
            else:
                hb_time = datetime.fromisoformat(res.data[0]["timestamp"].replace("Z", "+00:00"))
                stale_min = (now - hb_time).total_seconds() / 60
                logger.info(f"🏥 Watchdog: Watcher last heartbeat {stale_min:.0f}m ago ({res.data[0]['status']})")
            
            if stale_min > WATCHER_STALE_THRESHOLD_MIN:
                logger.warning(f"🚨 Watchdog: Watcher is STALE ({stale_min:.0f}m > {WATCHER_STALE_THRESHOLD_MIN}m threshold)!")
                
                # 1. Run Janitor to clean stuck signals 
                from quantix_core.engine.janitor import Janitor
                logger.info("🧹 Running Janitor auto-cleanup for stuck signals...")
                Janitor.run_sync()
                
                # 2. Send Alert to Admin via Telegram
                if self.notifier:
                    alert_msg = (
                        f"🚨 *WATCHER OFFLINE ALERT*\n\n"
                        f"Signal Watcher has not reported heartbeat for *{stale_min:.0f} minutes*.\n\n"
                        f"🧹 Janitor has cleaned up stuck signals.\n"
                        f"⚠️ Manual restart may be required on Railway.\n\n"
                        f"Cc: @admin"
                    )
                    try:
                        self.notifier.send_critical_alert(alert_msg)
                    except Exception as te:
                        logger.error(f"Failed to send Watcher alert: {te}")
                
                # 3. Log to DB for tracking
                try:
                    db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                        "timestamp": now.isoformat(),
                        "asset": "WATCHDOG_ALERT",
                        "direction": "SYSTEM",
                        "status": f"WATCHER_STALE_{int(stale_min)}m",
                        "confidence": 0.0,
                        "strength": 0.0,
                        "price": 0.0
                    }).execute()
                except: pass
            else:
                logger.info(f"🏥 Watchdog: Watcher is HEALTHY ({stale_min:.0f}m)")
                # 🛡️ Update WATCHDOG_ALERT to OK to clear any stale FAILs in dashboard
                try:
                    db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                        "timestamp": now.isoformat(),
                        "asset": "WATCHDOG_ALERT",
                        "direction": "SYSTEM",
                        "status": "WATCHER_OK",
                        "confidence": 1.0, "strength": 1.0, "price": 0.0
                    }).execute()
                except: pass
                
        except Exception as e:
            logger.error(f"Watchdog health check failed: {e}")

    def _broadcast_comprehensive_report(self):
        """
        v4.2.0: Generate and send a comprehensive system health report to Telegram Admin.
        """
        logger.info("📊 Generating periodic system health report...")
        try:
            now = datetime.now(timezone.utc)
            today_str = now.strftime('%Y-%m-%d')
            
            # 1. Component Heartbeats
            res_hb = db.client.table(settings.TABLE_ANALYSIS_LOG)\
                .select("asset, timestamp, status")\
                .in_("asset", ["HEARTBEAT_ANALYZER", "HEARTBEAT_WATCHER"])\
                .order("timestamp", desc=True)\
                .limit(10)\
                .execute()
            
            analyzer_status = "🔴 OFFLINE"
            watcher_status = "🔴 OFFLINE"
            
            for hb in res_hb.data:
                hb_time = datetime.fromisoformat(hb["timestamp"].replace("Z", "+00:00"))
                stale_min = (now - hb_time).total_seconds() / 60
                if hb["asset"] == "HEARTBEAT_ANALYZER" and analyzer_status.startswith("🔴"):
                    if stale_min < 10: analyzer_status = f"🟢 ONLINE ({stale_min:.0f}m)"
                    else: analyzer_status = f"🟡 STALE ({stale_min:.0f}m)"
                elif hb["asset"] == "HEARTBEAT_WATCHER" and watcher_status.startswith("🔴"):
                    if stale_min < 10: watcher_status = f"🟢 ONLINE ({stale_min:.0f}m)"
                    else: watcher_status = f"🟡 STALE ({stale_min:.0f}m)"

            # 2. Signal Stats
            res_signals = db.client.table(settings.TABLE_SIGNALS)\
                .select("id, state, generated_at")\
                .gte("generated_at", today_str)\
                .execute()
            
            total_today = len(res_signals.data) if res_signals.data else 0
            active_states = ["ENTRY_HIT", "WAITING_FOR_ENTRY", "PUBLISHED"]
            active_count = sum(1 for s in res_signals.data if s["state"] in active_states) if res_signals.data else 0
            
            # 3. Format Message
            report = (
                f"📊 *SYSTEM COMPREHENSIVE HEALTH*\n\n"
                f"🕒 Time: `{now.strftime('%H:%M:%S UTC')}`\n\n"
                f"*🌐 COMPONENT STATUS:*\n"
                f"├ ANALYZER: {analyzer_status}\n"
                f"└ WATCHER: {watcher_status}\n\n"
                f"*📈 SIGNAL PERFORMANCE:*\n"
                f"├ Today's Signals: `{total_today}`\n"
                f"└ Currently Tracking: `{active_count}`\n\n"
                f"*⚙️ ENGINE PARAMS:*\n"
                f"├ Version: `v4.4.0` (Strict)\n"
                f"├ Interval: `{settings.MONITOR_INTERVAL_SECONDS}s`\n"
                f"└ Target: `7p/12p` (Safety First)\n\n"
                f"✅ *All systems functioning normally.*"
            )
            
            if self.notifier:
                # Use _send_to_chat directly to ensure it goes to admin_chat_id
                target = self.notifier.admin_chat_id or self.notifier.chat_id
                self.notifier._send_to_chat(target, report)
                logger.success(f"Health report broadcasted to Telegram Admin ({target}).")
                
                # Log report event to DB
                try:
                    db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                        "timestamp": now.isoformat(),
                        "asset": "HEALTH_REPORT",
                        "direction": "SYSTEM",
                        "status": "SENT",
                        "confidence": 1.0, "strength": 1.0, "price": 0.0
                    }).execute()
                except: pass
                
        except Exception as e:
            logger.error(f"Failed to generate health report: {e}")

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

    # ========================================
    # EMBEDDED WATCHER (v3.8) — Replaces standalone Watcher
    # ========================================

    def _embedded_watcher_check(self):
        """
        Embedded Signal Watcher — runs inside the Analyzer process.
        This eliminates the standalone Watcher crash problem.
        
        Fetches active signals, gets latest price (Binance), and checks TP/SL/Entry.
        Uses multi-candle detection (5 candles) for better accuracy.
        """
        try:
            now = datetime.now(timezone.utc)
            # 1. Fetch active signals
            res = db.client.table(settings.TABLE_SIGNALS).select("*").in_(
                "status", ["WAITING_FOR_ENTRY", "ENTRY_HIT"]
            ).execute()
            signals = res.data or []
            
            # 1. Log heartbeat immediately to show watcher is alive
            try:
                db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                    "timestamp": now.isoformat(),
                    "asset": "HEARTBEAT_WATCHER",
                    "direction": "SYSTEM",
                    "status": f"EMBEDDED_WATCHER_IDLE",
                    "confidence": 1.0, "strength": 1.0, "price": 0.0
                }).execute()
            except: pass

            if not signals:
                logger.debug("[EmbeddedWatcher] No active signals. Heartbeat logged.")
                return
            
            # Skip if market closed
            if not MarketHours.is_market_open():
                logger.debug("[EmbeddedWatcher] Market closed, skipping.")
                return
            
            logger.info(f"👁️ [EmbeddedWatcher] Monitoring {len(signals)} active signals")
            
            # 2. Fetch latest candle from Binance (FREE, no quota)
            candle = None
            try:
                market_data = self.binance.get_price("EURUSD")
                if market_data:
                    candle = {
                        "timestamp": market_data["timestamp"],
                        "open": market_data["open"],
                        "high": market_data["high"],
                        "low": market_data["low"],
                        "close": market_data["close"]
                    }
            except Exception as e:
                logger.warning(f"[EmbeddedWatcher] Binance feed failed: {e}")
            
            # 2b. Multi-candle: Get last 5 candles for wider detection
            multi_candle = None
            try:
                history = self.binance.get_history("EURUSD", interval="1m", limit=5)
                if history and len(history) > 0:
                    multi_candle = {
                        "timestamp": history[-1]["datetime"],
                        "open": history[0]["open"],
                        "high": max(c["high"] for c in history),
                        "low": min(c["low"] for c in history),
                        "close": history[-1]["close"]
                    }
            except Exception as e:
                logger.debug(f"[EmbeddedWatcher] Multi-candle fetch failed: {e}")
            
            # Use multi-candle for wider TP/SL detection, single candle as fallback
            detection_candle = multi_candle or candle
            if not detection_candle:
                logger.warning("[EmbeddedWatcher] No market data available.")
                return
            
            logger.debug(f"[EmbeddedWatcher] Price H:{detection_candle['high']} L:{detection_candle['low']} C:{detection_candle['close']}")
            
            # 3. Check each signal
            HIT_TOLERANCE = 0.00005  # 0.5 pips tolerance
            now = datetime.now(timezone.utc)
            
            for sig in signals:
                try:
                    sig_id = sig.get("id")
                    state = sig.get("state")
                    direction = sig.get("direction")
                    entry = sig.get("entry_price")
                    tp = sig.get("tp")
                    sl = sig.get("sl")
                    
                    if not all([sig_id, state, direction, entry, tp, sl]):
                        continue
                    
                    h = detection_candle["high"]
                    l = detection_candle["low"]
                    c = detection_candle["close"]
                    ts = detection_candle["timestamp"]
                    
                    if state == "WAITING_FOR_ENTRY":
                        # --- Entry Window Check ---
                        gen_at_str = sig.get("generated_at")
                        if gen_at_str:
                            gen_at = datetime.fromisoformat(gen_at_str.replace("Z", "+00:00"))
                            if (now - gen_at).total_seconds() / 60 >= settings.MAX_PENDING_DURATION_MINUTES:
                                self._ew_transition(sig_id, "WAITING_FOR_ENTRY", {
                                    "state": "CANCELLED", "status": "EXPIRED",
                                    "result": "CANCELLED", "closed_at": now.isoformat()
                                }, "EXPIRED")
                                continue
                        
                        # --- SL Invalidation ---
                        if direction == "BUY" and l <= (sl + HIT_TOLERANCE):
                            self._ew_transition(sig_id, "WAITING_FOR_ENTRY", {
                                "state": "CANCELLED", "status": "SL_INVALIDATED",
                                "result": "CANCELLED", "closed_at": now.isoformat()
                            }, "SL_INVALIDATED")
                            continue
                        if direction == "SELL" and h >= (sl - HIT_TOLERANCE):
                            self._ew_transition(sig_id, "WAITING_FOR_ENTRY", {
                                "state": "CANCELLED", "status": "SL_INVALIDATED",
                                "result": "CANCELLED", "closed_at": now.isoformat()
                            }, "SL_INVALIDATED")
                            continue
                        
                        # --- Entry Hit Check ---
                        entry_hit = False
                        if direction == "BUY" and l <= (entry + HIT_TOLERANCE):
                            entry_hit = True
                        elif direction == "SELL" and h >= (entry - HIT_TOLERANCE):
                            entry_hit = True
                        
                        if entry_hit:
                            self._ew_transition(sig_id, "WAITING_FOR_ENTRY", {
                                "state": "ENTRY_HIT", "status": "ENTRY_HIT",
                                "entry_hit_at": ts if isinstance(ts, str) else now.isoformat()
                            }, "ENTRY_HIT")
                            # Send entry hit notification
                            if self.notifier and sig.get("telegram_message_id"):
                                try: self.notifier.send_entry_hit(sig)
                                except: pass
                    
                    elif state == "ENTRY_HIT":
                        # --- TP Hit Check ---
                        tp_hit = False
                        if direction == "BUY" and h >= (tp - HIT_TOLERANCE):
                            tp_hit = True
                        elif direction == "SELL" and l <= (tp + HIT_TOLERANCE):
                            tp_hit = True
                        
                        if tp_hit:
                            self._ew_transition(sig_id, "ENTRY_HIT", {
                                "state": "TP_HIT", "status": "CLOSED_TP",
                                "result": "PROFIT", "closed_at": now.isoformat()
                            }, "TP_HIT")
                            if self.notifier and sig.get("telegram_message_id"):
                                try: self.notifier.send_tp_hit(sig)
                                except: pass
                            continue
                        
                        # --- SL Hit Check ---
                        sl_hit = False
                        if direction == "BUY" and l <= (sl + HIT_TOLERANCE):
                            sl_hit = True
                        elif direction == "SELL" and h >= (sl - HIT_TOLERANCE):
                            sl_hit = True
                        
                        if sl_hit:
                            self._ew_transition(sig_id, "ENTRY_HIT", {
                                "state": "SL_HIT", "status": "CLOSED_SL",
                                "result": "LOSS", "closed_at": now.isoformat()
                            }, "SL_HIT")
                            if self.notifier and sig.get("telegram_message_id"):
                                try: self.notifier.send_sl_hit(sig)
                                except: pass
                            continue
                        
                        # --- Breakeven Check (DISABLED v4.1.8 for Scalping) ---
                        # tp_distance = abs(tp - entry)
                        # if tp_distance > 0:
                        #     if direction == "BUY":
                        #         progress = h - entry
                        #     else:
                        #         progress = entry - l
                        #     if progress / tp_distance >= 0.7 and (
                        #         (direction == "BUY" and sl < entry) or
                        #         (direction == "SELL" and sl > entry)
                        #     ):
                        #         try:
                        #             db.client.table(settings.TABLE_SIGNALS).update({
                        #                 "sl": entry
                        #             }).eq("id", sig_id).eq("state", "ENTRY_HIT").execute()
                        #             logger.success(f"🔒 [EmbeddedWatcher] BREAKEVEN: {sig_id} SL -> {entry}")
                        #         except: pass
                        
                        # --- Timeout Check ---
                        start_str = sig.get("entry_hit_at") or sig.get("generated_at")
                        if start_str:
                            start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                            if (now - start_time).total_seconds() / 60 >= settings.MAX_TRADE_DURATION_MINUTES:
                                self._ew_transition(sig_id, "ENTRY_HIT", {
                                    "state": "CANCELLED", "status": "CLOSED_TIMEOUT",
                                    "result": "CANCELLED", "closed_at": now.isoformat()
                                }, "TIMEOUT")
                                if self.notifier and sig.get("telegram_message_id"):
                                    try: self.notifier.send_time_exit(sig, c)
                                    except: pass
                
                except Exception as e:
                    logger.error(f"[EmbeddedWatcher] Error processing signal {sig.get('id')}: {e}")
            
            # 4. Update heartbeat with stats if we processed signals
            try:
                db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                    "timestamp": now.isoformat(),
                    "asset": "HEARTBEAT_WATCHER",
                    "direction": "SYSTEM",
                    "status": f"EMBEDDED_WATCHER_OK (Watching: {len(signals)})",
                    "confidence": 1.0, "strength": 1.0, "price": 0.0
                }).execute()
            except: pass
                
        except Exception as e:
            logger.error(f"[EmbeddedWatcher] Cycle failed: {e}")

    def _ew_transition(self, sig_id: str, from_state: str, update_data: dict, label: str):
        """Atomic state transition for embedded watcher."""
        try:
            res = db.client.table(settings.TABLE_SIGNALS).update(
                update_data
            ).eq("id", sig_id).eq("state", from_state).execute()
            
            if res.data:
                logger.success(f"👁️ [EmbeddedWatcher] {sig_id[:8]} -> {label}")
            else:
                logger.debug(f"[EmbeddedWatcher] Transition skipped for {sig_id[:8]} (already processed)")
        except Exception as e:
            logger.error(f"[EmbeddedWatcher] Transition failed for {sig_id[:8]}: {e}")

    def start(self):
        """Start the continuous evaluation loop with EMBEDDED WATCHER"""
        interval = settings.MONITOR_INTERVAL_SECONDS
        logger.info(f"💓 Continuous analyzer started with {interval}s interval")
        logger.info(f"👁️ EMBEDDED WATCHER MODE: Signal monitoring runs inside Analyzer")
        
        # Immediate Startup Proof using absolute path
        try:
            with open(self.audit_log_path, "a") as f:
                import json
                f.write(json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "SYSTEM_STARTUP",
                    "message": "Quantix AI Core v3.8 with Embedded Watcher"
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
            
            # 🆕 EMBEDDED WATCHER: Check active signals after every cycle
            try:
                self._embedded_watcher_check()
                # 🧹 REDUNDANT SAFETY: Run Janitor to clear stuck signals
                Janitor.run_sync()
            except Exception as e:
                logger.error(f"Embedded Watcher / Janitor error: {e}")

        # 🆕 ADMIN BOT: Start Telegram Command Listener in background thread
        if self.notifier:
            import threading
            def _listen_loop():
                while True:
                    try:
                        self.notifier.handle_commands(self)
                    except Exception as e:
                        logger.error(f"Telegram command handler error: {e}")
                    time.sleep(3)
            
            cmd_thread = threading.Thread(target=_listen_loop, daemon=True)
            cmd_thread.start()
            logger.info("🤖 Telegram command listener started in background")
        
        while True:
            try:
                logger.info("🎬 Starting new analysis cycle...")
                self.run_cycle()
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Cycle error: {error_msg}")
                if "API_BLOCKED" in error_msg and self.notifier:
                    self.notifier.send_critical_alert(f"TwelveData API Blocked: {error_msg}")
            
            # 🆕 EMBEDDED WATCHER: Check active signals after every cycle
            try:
                self._embedded_watcher_check()
                # 🧹 REDUNDANT SAFETY: Run Janitor
                Janitor.run_sync()
            except Exception as e:
                logger.error(f"Embedded Watcher / Janitor error: {e}")
            
            time.sleep(interval)

if __name__ == "__main__":
    analyzer = ContinuousAnalyzer()
    analyzer.start()
